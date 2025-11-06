from fastapi import FastAPI

app = FastAPI(title="Content API")

@app.get("/")
async def root():
    return {"message": "Content API is running successfully!"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "artify-content-api",
        "version": "1.0.0"
    }
