"""
Basic video service for creating and managing video records.
"""

import re
from sqlalchemy.orm import Session
from ..models.video import Video

class VideoService:
    """Simple service for video management."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def extract_video_id(self, url: str) -> str:
        """Extract YouTube video ID from URL."""
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([^&\n?#]+)',
            r'youtube\.com/.*[?&]v=([^&\n?#]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        raise ValueError(f"Could not extract video ID from URL: {url}")
    
    def create_video(self, url: str, title: str = None) -> Video:
        """Create a new video record."""
        try:
            video_id_str = self.extract_video_id(url)
            
            # Check if video already exists
            existing = self.db.query(Video).filter(Video.url == url).first()
            if existing:
                return existing
            
            # Create new video record
            video = Video(
                url=url,
                title=title or f"Video {video_id_str}"
            )
            
            self.db.add(video)
            self.db.commit()
            self.db.refresh(video)
            
            return video
            
        except Exception as e:
            self.db.rollback()
            raise e 