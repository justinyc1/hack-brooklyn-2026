import logging
from datetime import datetime, timezone
from fastapi import Depends, HTTPException, status
from auth.clerk import require_auth
from db import db

logger = logging.getLogger(__name__)

# ensure a TTL index is created so old rate limit records are automatically deleted.
try:
    db.rate_limits.create_index("expire_at", expireAfterSeconds=0)
except Exception as e:
    logger.warning(f"Failed to create TTL index for rate limits: {e}")

class RateLimiter:
    """
    A FastAPI dependency that implements user-based rate limiting via MongoDB.
    It counts the number of requests made by `clerk_user_id` within the last `window_seconds`.
    """
    def __init__(self, calls: int, window_seconds: int, scope: str = "default"):
        self.calls = calls
        self.window_seconds = window_seconds
        self.scope = scope

    async def __call__(self, clerk_user_id: str = Depends(require_auth)):
        now = datetime.now(timezone.utc)
        cutoff_timestamp = now.timestamp() - self.window_seconds
        
        # count existing requests in the current window
        count = db.rate_limits.count_documents({
            "user_id": clerk_user_id,
            "scope": self.scope,
            "timestamp": {"$gte": cutoff_timestamp}
        })
        
        if count >= self.calls:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded for {self.scope}. Try again in {self.window_seconds} seconds."
            )
            
        # log this request if under the limit
        db.rate_limits.insert_one({
            "user_id": clerk_user_id,
            "scope": self.scope,
            "timestamp": now.timestamp(),
            "expire_at": datetime.fromtimestamp(now.timestamp() + self.window_seconds, timezone.utc)
        })
        
        return clerk_user_id
