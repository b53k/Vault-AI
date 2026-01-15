from fastapi import FastAPI
from app.api.routes.search import router as search_router

app = FastAPI(
    title="Vectorstore Service",
    description="API for searching policy documents",
    version="1.0.0"
)

app.include_router(search_router)

@app.get("/")
async def root():
    return {"service": "Vectorstore Service", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
