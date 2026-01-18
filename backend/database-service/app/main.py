from fastapi import FastAPI
from app.api.routes.analytics import router_spending, router_balance

app = FastAPI(
    title="Database Service",
    description="API for searching policy documents",
    version="1.0.0"
)

app.include_router(router_spending)
app.include_router(router_balance)

@app.get("/")
async def root():
    return {"service": "Database Service", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
