"""
    Main FastAPI application for the Agent Service.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes.chat import router as chat_router

# FastAPI app instance
app = FastAPI(
    title = "Agent Service",
    description = "AI Agent Orchestration service for Vault-AI",
    version = "1.0.0"
)

# CORS middleware to allow frontend to make requests to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins = ["http://localhost:3000"],
    allow_credentials = True,
    allow_methods = ["*"],  # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers = ["*"],  # Allow all headers
)

# Include the chat router
app.include_router(chat_router)

# Health check endpoint
@app.get("/")
async def health_check():
    return {"service": "agent-service", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}