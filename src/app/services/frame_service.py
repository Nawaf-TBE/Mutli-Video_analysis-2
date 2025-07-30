"""
Frame service that wraps the existing frame extractor functionality.
"""

from sqlalchemy.orm import Session
from .frame_extractor import FrameExtractorService
from ..models.video import Video

class FrameService:
    """Frame service using the full FrameExtractorService."""
    
    def __init__(self, db: Session):
        self.db = db
        self.frame_extractor = FrameExtractorService(db)
    
    def extract_frames(self, video_id: int, interval: int = 10):
        """Extract frames from video using FrameExtractorService."""
        # Check if video exists
        video = self.db.query(Video).filter(Video.id == video_id).first()
        if not video:
            return {"error": "Video not found", "extracted_count": 0}
        
        try:
            frames = self.frame_extractor.process_video_frames(video_id, video.url, interval=interval)
            return {
                "message": "Frame extraction completed successfully",
                "video_id": video_id,
                "extracted_count": len(frames),
                "status": "success"
            }
        except Exception as e:
            return {
                "message": f"Frame extraction failed: {str(e)}",
                "video_id": video_id,
                "extracted_count": 0,
                "status": "error"
            } 

