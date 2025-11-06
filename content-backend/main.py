from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.config import settings
from app.database import init_db
from routers import auth, segments, generate, metrics
from utils.rate_limiter import clean_expired_entries

# Logging configuration
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.VERSION}")
    logger.info(f"Environment: {'Development' if settings.DEBUG else 'Production'}")
    logger.info(f"Database: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'configured'}")

    # Initialize database tables
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")

    logger.info("API is ready!")

    yield

    # Shutdown
    logger.info("Shutting down...")
    clean_expired_entries()
    logger.info("Shutdown complete")

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered content generation and management backend",
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(segments.router, prefix="/api/segments", tags=["Segments"])
app.include_router(generate.router, prefix="/api/generate", tags=["Generation"])
app.include_router(metrics.router, prefix="/api/metrics", tags=["Metrics"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.APP_NAME,
        "version": settings.VERSION,
        "status": "running",
        "docs": "/docs" if settings.DEBUG else "disabled"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "version": settings.VERSION
    }

@app.get("/info")
async def info():
    """API information endpoint"""
    return {
        "name": settings.APP_NAME,
        "version": settings.VERSION,
        "environment": "development" if settings.DEBUG else "production",
        "features": {
            "authentication": "JWT",
            "database": "PostgreSQL + SQLAlchemy",
            "vector_db": "ChromaDB (embedded)",
            "ai": "OpenAI GPT-4 & DALL-E"
        },
        "endpoints": {
            "docs": "/docs" if settings.DEBUG else None,
            "health": "/health",
            "auth": "/api/auth",
            "segments": "/api/segments",
            "generate": "/api/generate",
            "metrics": "/api/metrics"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
