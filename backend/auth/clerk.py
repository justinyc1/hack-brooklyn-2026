import base64
from datetime import datetime, timezone
from functools import lru_cache

import jwt
from jwt import PyJWKClient
from fastapi import Depends, Header, HTTPException, status

from config import settings
from db import db


def _jwks_url() -> str:
    raw = settings.clerk_publishable_key
    b64 = raw.split("_", 2)[2]
    b64 += "=" * (-len(b64) % 4)
    domain = base64.b64decode(b64).decode().rstrip("$")
    return f"https://{domain}/.well-known/jwks.json"


@lru_cache(maxsize=1)
def _jwks_client() -> PyJWKClient:
    """Cached JWKS client — keys are refreshed automatically on cache miss."""
    return PyJWKClient(_jwks_url(), cache_keys=True)


def verify_token(token: str) -> dict:
    """Verify a Clerk session JWT and return its claims.

    Raises HTTP 401 on any verification failure.
    """
    try:
        client = _jwks_client()
        signing_key = client.get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            options={"verify_aud": False},  # Clerk tokens have no aud by default
        )
        return claims
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {exc}")
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not verify token")


def require_auth(authorization: str | None = Header(default=None)) -> str:
    """FastAPI dependency — verifies the Bearer token and returns clerk_user_id.

    Usage:
        @router.get("/protected")
        def my_route(clerk_user_id: str = Depends(require_auth)):
            ...
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = authorization.removeprefix("Bearer ")
    claims = verify_token(token)
    clerk_user_id: str = claims["sub"]
    _upsert_user(clerk_user_id)
    return clerk_user_id


def _upsert_user(clerk_user_id: str) -> None:
    db.users.update_one(
        {"clerk_user_id": clerk_user_id},
        {"$setOnInsert": {"clerk_user_id": clerk_user_id, "email": "", "created_at": datetime.now(timezone.utc), "preferences": {}}},
        upsert=True,
    )
