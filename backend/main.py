from fastapi import FastAPI
from routes.health import router as health_router
from routes.interviews import router as interviews_router
from config import settings
from db import db
import httpx

app = FastAPI(title="Hack Brooklyn 2026 Backend")

app.include_router(health_router)
app.include_router(interviews_router)

@app.get("/")
def root():
    return {
        "message": "Backend running",
        "has_elevenlabs_key": bool(settings.elevenlabs_api_key),
        "has_tavily_key": bool(settings.tavily_api_key),
        "has_mongodb_uri": bool(settings.mongodb_uri),
    }

@app.get("/db-test")
def db_test():
    try:
        collections = db.list_collection_names()
        return {"connected": True, "collections": collections}
    except Exception as e:
        return {"connected": False, "error": str(e)}
    
@app.get("/tavily-test")
async def tavily_test():
    url = "https://api.tavily.com/search"
    payload = {
        "api_key": settings.tavily_api_key,
        "query": "software engineer interview at Google",
        "search_depth": "basic",
        "max_results": 3,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)
        return response.json()

@app.get("/eleven-test")
async def eleven_test():
    url = "https://api.elevenlabs.io/v1/models"
    headers = {
        "xi-api-key": settings.elevenlabs_api_key
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        return response.json()