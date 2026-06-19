from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import auth, research_jobs, captures, saved_searches

app = FastAPI(
    title="MarginScout SaaS API",
    description="日本国内ソース×eBay価格照合リサーチツール API",
    version="2.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
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

@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
