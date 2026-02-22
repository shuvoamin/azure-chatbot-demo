from fastapi import APIRouter, Response
from app_state import APP_NAME

router = APIRouter()

@router.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {"status": "ok"}