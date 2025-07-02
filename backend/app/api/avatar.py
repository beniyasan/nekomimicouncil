from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
import logging
from ..services.avatar_service import avatar_service

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/avatar/{persona_id}")
async def get_avatar(persona_id: str):
    """Get avatar image for a specific persona"""
    try:
        avatar_path = avatar_service.get_avatar_path(persona_id)
        
        if not avatar_path or not Path(avatar_path).exists():
            # Return default avatar or 404
            default_path = avatar_service.get_avatar_path("ai")
            if default_path and Path(default_path).exists():
                return FileResponse(
                    default_path,
                    media_type="image/png",
                    headers={"Cache-Control": "public, max-age=3600"}
                )
            raise HTTPException(status_code=404, detail="Avatar not found")
        
        return FileResponse(
            avatar_path,
            media_type="image/png",
            headers={"Cache-Control": "public, max-age=3600"}
        )
        
    except Exception as e:
        logger.error(f"Error serving avatar for {persona_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error serving avatar")

@router.get("/avatars")
async def list_avatars():
    """List all available avatars"""
    try:
        return avatar_service.list_available_avatars()
    except Exception as e:
        logger.error(f"Error listing avatars: {str(e)}")
        raise HTTPException(status_code=500, detail="Error listing avatars")