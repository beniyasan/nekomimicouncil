from fastapi import APIRouter
from datetime import datetime
from ..config import settings

router = APIRouter()

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "ai_provider": settings.ai_provider,
        "debug": settings.debug
    }

@router.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "NekoMimi Council API",
        "docs": "/docs",
        "health": "/api/health"
    }