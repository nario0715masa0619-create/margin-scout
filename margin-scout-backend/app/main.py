import os
from dotenv import load_dotenv

# Load environment variables from .env file explicitly
load_dotenv()

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import auth, research_jobs, captures, saved_searches
import traceback
import logging

logger = logging.getLogger(__name__)

app = FastAPI(
    title="MarginScout SaaS API",
    description="日本国内ソース×eBay価格照合リサーチツール API",
    version="2.1.0"
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"Unhandled error: {exc}")
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"error": str(exc), "type": type(exc).__name__},
        headers={
            "Access-Control-Allow-Origin": request.headers.get("origin", "*"),
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
        }
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://margin-scout.vercel.app",
        "http://localhost:3000",  # ローカル開発用
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(research_jobs.router, prefix="/api/v1/research-jobs", tags=["Research Jobs"])
app.include_router(captures.router, prefix="/api/v1/captures", tags=["Captures"])
app.include_router(captures.saved_items_router, prefix="/api/v1/saved-items", tags=["Saved Items"])
app.include_router(saved_searches.router)

from app.routers import monitoring
app.include_router(monitoring.router)

@app.on_event("startup")
async def startup():
    from app.db.database import engine
    from app.db.base import Base
    import app.models.user
    import app.models.research
    
    # Auto-create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    from app.celery_app import celery_app
    # Celery 初期化確認
    pass

@app.on_event("startup")
def log_config():
    print(f"=== REDIS_URL: {settings.REDIS_URL} ===")
    print(f"=== CELERY_BROKER_URL: {settings.CELERY_BROKER_URL} ===")
    print(f"=== CELERY_RESULT_BACKEND: {settings.CELERY_RESULT_BACKEND} ===")
    logger.info(f"REDIS_URL: {settings.REDIS_URL}")
    logger.info(f"CELERY_BROKER_URL: {settings.CELERY_BROKER_URL}")
    logger.info(f"CELERY_RESULT_BACKEND: {settings.CELERY_RESULT_BACKEND}")

@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
