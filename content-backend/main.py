from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

# 라우터 임포트
from routers import auth, segments, generate, metrics, recommend

# 앱 생명주기 관리
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 시작 시
    print("Starting Content API...")
    yield
    # 종료 시
    print("Shutting down Content API...")

app = FastAPI(
    title="Artify Content API",
    description="AI-powered content generation and analysis",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(auth.router)
app.include_router(segments.router)
app.include_router(generate.router)
app.include_router(metrics.router)
app.include_router(recommend.router)

@app.get("/")
async def root():
    return {
        "message": "Artify Content API",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "content-api",
        "version": "1.0.0",
        "endpoints": [
            "/auth",
            "/segments",
            "/generate",
            "/metrics",
            "/recommend"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)
