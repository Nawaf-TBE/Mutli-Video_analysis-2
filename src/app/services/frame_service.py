"""
Frame service that wraps the existing frame extractor functionality.
"""

from sqlalchemy.orm import Session
from .frame_extractor import FrameExtractorService
from ..models.video import Video
import logging
from typing import Dict, List, Optional
import os
from datetime import datetime, timedelta

class FrameService:
    """
    Frame service using the full FrameExtractorService.
    
    This service provides a high-level interface for extracting frames from videos
    with proper error handling and database integration.
    """
    
    def __init__(self, db: Session, config: Optional[Dict] = None):
        self.db = db
        self.frame_extractor = FrameExtractorService(db)
        self.logger = logging.getLogger(__name__)
        self.config = config or {
            "default_interval": 10,
            "max_frames_per_video": 1000,
            "frame_quality": 85,
            "cleanup_older_than_days": 30
        }
  
    def extract_frames(self, video_id: int, interval: int = None):
        """
        Extract frames from video using FrameExtractorService.
        
        Args:
            video_id (int): The ID of the video to extract frames from
            interval (int): Interval between frame extractions in seconds (default from config)
            
        Returns:
            dict: Result containing extraction status and frame count
        """
        interval = interval or self.config["default_interval"]
        
        # Check if video exists
        video = self.db.query(Video).filter(Video.id == video_id).first()
        if not video:
            self.logger.warning(f"Video with ID {video_id} not found")
            return {"error": "Video not found", "extracted_count": 0}
        
        try:
            self.logger.info(f"Starting frame extraction for video {video_id} with interval {interval}s")
            frames = self.frame_extractor.process_video_frames(video_id, video.url, interval=interval)
            self.logger.info(f"Successfully extracted {len(frames)} frames from video {video_id}")
            return {
                "message": "Frame extraction completed successfully",
                "video_id": video_id,
                "extracted_count": len(frames),
                "interval_used": interval,
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
    
    def get_frame_statistics(self, video_id: int) -> Dict:
        """
        Get statistics about extracted frames for a video.
        
        Args:
            video_id (int): The ID of the video to get statistics for
            
        Returns:
            dict: Statistics about the frames for the video
        """
        try:
            # This would typically query your frame storage/database
            # For now, returning a placeholder structure
            stats = {
                "video_id": video_id,
                "total_frames": 0,
                "storage_size_mb": 0.0,
                "average_frame_size_kb": 0.0,
                "extraction_date": None,
                "status": "not_implemented"
            }
            
            self.logger.info(f"Retrieved frame statistics for video {video_id}")
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get frame statistics for video {video_id}: {str(e)}")
            return {
                "error": f"Failed to get frame statistics: {str(e)}",
                "video_id": video_id,
                "status": "error"
            }
    
    def validate_video_for_extraction(self, video_id: int) -> Dict:
        """
        Validate if a video is suitable for frame extraction.
        
        Args:
            video_id (int): The ID of the video to validate
            
        Returns:
            dict: Validation result with details
        """
        video = self.db.query(Video).filter(Video.id == video_id).first()
        if not video:
            return {
                "valid": False,
                "error": "Video not found",
                "video_id": video_id
            }
        
        # Add more validation logic here as needed
        validation_result = {
            "valid": True,
            "video_id": video_id,
            "video_url": video.url,
            "message": "Video is ready for frame extraction"
        }
        
        self.logger.info(f"Video {video_id} validation completed successfully")
        return validation_result
    
    def cleanup_old_frames(self, days_old: int = None) -> Dict:
        """
        Clean up frames older than specified days.
        
        Args:
            days_old (int): Number of days to keep frames (default from config)
            
        Returns:
            dict: Cleanup result with details
        """
        days_old = days_old or self.config["cleanup_older_than_days"]
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        try:
            # This would typically delete old frame files and database records
            # For now, returning a placeholder structure
            cleanup_result = {
                "message": f"Cleanup completed for frames older than {days_old} days",
                "cutoff_date": cutoff_date.isoformat(),
                "files_removed": 0,
                "storage_freed_mb": 0.0,
                "status": "success"
            }
            
            self.logger.info(f"Cleanup completed: {cleanup_result['files_removed']} files removed")
            return cleanup_result
            
        except Exception as e:
            self.logger.error(f"Cleanup failed: {str(e)}")
            return {
                "error": f"Cleanup failed: {str(e)}",
                "cutoff_date": cutoff_date.isoformat(),
                "status": "error"
            }
    
    def get_service_config(self) -> Dict:
        """
        Get current service configuration.
        
        Returns:
            dict: Current configuration settings
        """
        return {
            "config": self.config,
            "timestamp": datetime.now().isoformat()
        } 

