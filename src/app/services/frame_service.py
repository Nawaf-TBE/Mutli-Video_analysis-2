"""
Frame service that wraps the existing frame extractor functionality.
"""

from sqlalchemy.orm import Session
from .frame_extractor import FrameExtractorService
from ..models.video import Video
import logging

class FrameService:
    """
    Frame service using the full FrameExtractorService.
    
    This service provides a high-level interface for extracting frames from videos
    with proper error handling and database integration.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.frame_extractor = FrameExtractorService(db)
        self.logger = logging.getLogger(__name__)
    
    def extract_frames(self, video_id: int, interval: int = 10):
        """
        Extract frames from video using FrameExtractorService.
        
        Args:
            video_id (int): The ID of the video to extract frames from
            interval (int): Interval between frame extractions in seconds (default: 10)
            
        Returns:
            dict: Result containing extraction status and frame count
        """
        # Check if video exists
        video = self.db.query(Video).filter(Video.id == video_id).first()
        if not video:
            self.logger.warning(f"Video with ID {video_id} not found")
            return {"error": "Video not found", "extracted_count": 0}
        
        try:
            self.logger.info(f"Starting frame extraction for video {video_id}")
            frames = self.frame_extractor.process_video_frames(video_id, video.url, interval=interval)
            self.logger.info(f"Successfully extracted {len(frames)} frames from video {video_id}")
            return {
                "message": "Frame extraction completed successfully",
                "video_id": video_id,
                "extracted_count": len(frames),
                "status": "success"
            }
        except Exception as e:
            self.logger.error(f"Frame extraction failed for video {video_id}: {str(e)}")
            return {
                "message": f"Frame extraction failed: {str(e)}",
                "video_id": video_id,
                "extracted_count": 0,
                "status": "error"
            } 

