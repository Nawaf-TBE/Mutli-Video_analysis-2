"""Main API router that combines all route modules."""
from fastapi import APIRouter
from .video_routes import router as video_router
from .chat_routes import router as chat_router
from .frame_routes import router as frame_router

router = APIRouter()

# Include all route modules
router.include_router(video_router, prefix="/api")
router.include_router(chat_router, prefix="/api")
router.include_router(frame_router, prefix="/api")

@router.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Multi-Video Analysis API", "version": "3.0 - Modular Architecture"} 