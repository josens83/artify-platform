from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, campaigns, segments, creatives, vector_search
from utils.config import settings
import logging

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Content Management API",
    description="AI-powered content generation and management backend with Supabase and ChromaDB",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(campaigns.router, prefix="/api/campaigns", tags=["Campaigns"])
app.include_router(segments.router, prefix="/api/segments", tags=["Segments"])
app.include_router(creatives.router, prefix="/api/creatives", tags=["Creatives"])
app.include_router(vector_search.router, prefix="/api/vector", tags=["Vector Search"])

@app.get("/")
async def root():
    return {
        "message": "Content Management API",
        "version": "1.0.0",
        "status": "running",
        "database": "Supabase",
        "vector_db": "ChromaDB (embedded)"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "database": "connected",
        "vector_db": "ready"
    }

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting Content Management API...")
    logger.info(f"Supabase URL: {settings.SUPABASE_URL}")
    logger.info(f"ChromaDB persist dir: {settings.CHROMA_PERSIST_DIR}")
    logger.info("API is ready!")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Content Management API...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG
    )
