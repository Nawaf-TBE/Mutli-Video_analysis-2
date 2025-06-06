# YouTube transcript fetch
import httpx
from sqlalchemy.orm import Session
from ..models.video import Video
from ..models.section import Section
from .sectionizer import SectionizerService
from .frame_extractor import FrameExtractorService
from typing import Optional, Dict, List
import re

class YouTubeService:
    def __init__(self, db: Session):
        self.db = db

    def extract_video_id(self, url: str) -> Optional[str]:
        """Extract video ID from various YouTube URL formats."""
        patterns = [
            r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
            r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})',
            r'(?:embed\/)([0-9A-Za-z_-]{11})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def get_video_metadata(self, video_id: str) -> Dict:
        """Fetch video metadata using pytube."""
        try:
            from pytube import YouTube
            yt = YouTube(f"https://www.youtube.com/watch?v={video_id}")
            return {
                "title": yt.title,
                "description": yt.description,
                "duration": yt.length,
                "author": yt.author,
                "views": yt.views
            }
        except Exception as e:
            raise Exception(f"Error fetching video metadata: {str(e)}")

    def get_transcript(self, video_id: str) -> List[Dict]:
        """Fetch video transcript using Node.js transcript API."""
        try:
            response = httpx.post(
                "http://localhost:4000/transcript",
                json={"videoId": video_id},
                timeout=30
            )
            response.raise_for_status()
            return response.json()["transcript"]
        except Exception as e:
            raise Exception(f"Error fetching transcript from Node.js API: {str(e)}")

    def process_video(self, url: str, extract_frames: bool = False, frame_interval: int = 10) -> Video:
        """Process a YouTube video: fetch metadata, transcript, create sections, and optionally extract frames."""
        # Extract video ID
        video_id = self.extract_video_id(url)
        if not video_id:
            raise ValueError("Invalid YouTube URL")

        # Check if video already exists
        existing_video = self.db.query(Video).filter(Video.url == url).first()
        if existing_video:
            return existing_video

        # Get video metadata
        metadata = self.get_video_metadata(video_id)
        
        # Create video record
        video = Video(
            url=url,
            title=metadata["title"]
        )
        self.db.add(video)
        self.db.flush()  # Get the video ID

        # Get transcript
        transcript = self.get_transcript(video_id)
        
        # Process transcript into sections using AI
        sectionizer = SectionizerService(self.db)
        sections = sectionizer.process_transcript_sections(video.id, transcript)

        # Optionally extract frames
        if extract_frames:
            try:
                frame_extractor = FrameExtractorService(self.db)
                frames = frame_extractor.process_video_frames(video.id, url, frame_interval)
                print(f"Extracted {len(frames)} frames for video {video.id}")
            except Exception as e:
                print(f"Warning: Frame extraction failed: {str(e)}")
                # Continue processing even if frame extraction fails

        # Commit all changes
        self.db.commit()
        self.db.refresh(video)
        
        return video 