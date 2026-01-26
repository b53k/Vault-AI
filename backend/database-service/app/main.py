from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes.analytics import router_spending, router_balance
from app.api.routes.admin import router as admin_router

app = FastAPI(
    title="Database Service",
    description="API for searching policy documents",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router_spending)
app.include_router(router_balance)
app.include_router(admin_router)  # Add admin router

@app.get("/")
async def root():
    return {"service": "Database Service", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
