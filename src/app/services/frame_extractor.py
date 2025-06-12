# Frame extraction
import ffmpeg
import os
import tempfile
from pathlib import Path
from sqlalchemy.orm import Session
from ..models.video import Video
from ..models.frame import Frame
from typing import List, Optional
import shutil
import yt_dlp

class FrameExtractorService:
    def __init__(self, db: Session):
        self.db = db
        self.frames_dir = Path("storage/frames")
        self.temp_dir = Path("storage/temp")
        
        # Create directories if they don't exist
        self.frames_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def download_video(self, video_url: str, output_path: str) -> str:
        """Download YouTube video to a temporary location using yt-dlp."""
        try:
            # Configure yt-dlp options for downloading
            ydl_opts = {
                'outtmpl': os.path.join(output_path, 'video_%(id)s.%(ext)s'),
                'format': 'best[ext=mp4]/best',  # Prefer mp4, fallback to best
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract info first to get the filename
                info = ydl.extract_info(video_url, download=False)
                video_id = info.get('id', 'unknown')
                ext = info.get('ext', 'mp4')
                
                # Set the expected output filename
                output_filename = os.path.join(output_path, f'video_{video_id}.{ext}')
                
                # Download the video
                ydl.download([video_url])
                
                # Check if file exists and return the path
                if os.path.exists(output_filename):
                    return output_filename
                else:
                    # Fallback: look for any video file in the directory
                    for file in os.listdir(output_path):
                        if file.startswith('video_') and file.endswith(('.mp4', '.webm', '.mkv')):
                            return os.path.join(output_path, file)
                    
                    raise Exception("Downloaded video file not found")
            
        except Exception as e:
            raise Exception(f"Error downloading video with yt-dlp: {str(e)}")

    def extract_frames_from_video(self, video_path: str, video_id: int, interval: int = 10) -> List[str]:
        """
        Extract frames from video at specified intervals using FFmpeg.
        
        Args:
            video_path: Path to the video file
            video_id: Database ID of the video
            interval: Interval in seconds between frame extractions
            
        Returns:
            List of frame file paths
        """
        try:
            # Create output directory for this video
            video_frames_dir = self.frames_dir / str(video_id)
            video_frames_dir.mkdir(exist_ok=True)
            
            # Get video info
            probe = ffmpeg.probe(video_path)
            video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')
            duration = float(video_info['duration'])
            
            frame_paths = []
            timestamps = []
            
            # Calculate timestamps for frame extraction
            current_time = 0
            frame_count = 0
            
            while current_time < duration:
                timestamp = current_time
                frame_filename = f"frame_{frame_count:06d}_{timestamp:.2f}s.jpg"
                frame_path = video_frames_dir / frame_filename
                
                # Extract frame at specific timestamp
                (
                    ffmpeg
                    .input(video_path, ss=timestamp)
                    .output(str(frame_path), vframes=1, format='image2', vcodec='mjpeg')
                    .overwrite_output()
                    .run(capture_stdout=True, capture_stderr=True)
                )
                
                if frame_path.exists():
                    frame_paths.append(str(frame_path))
                    timestamps.append(timestamp)
                
                current_time += interval
                frame_count += 1
            
            return list(zip(frame_paths, timestamps))
            
        except Exception as e:
            raise Exception(f"Error extracting frames: {str(e)}")

    def save_frame_records(self, video_id: int, frame_data: List[tuple]) -> List[Frame]:
        """
        Save frame records to database.
        
        Args:
            video_id: Database ID of the video
            frame_data: List of (file_path, timestamp) tuples
            
        Returns:
            List of created Frame objects
        """
        frames = []
        
        for file_path, timestamp in frame_data:
            frame = Frame(
                video_id=video_id,
                timestamp=timestamp,
                path=file_path
            )
            self.db.add(frame)
            frames.append(frame)
        
        self.db.commit()
        return frames

    def process_video_frames(self, video_id: int, video_url: str, interval: int = 10) -> List[Frame]:
        """
        Complete frame extraction pipeline.
        
        Args:
            video_id: Database ID of the video
            video_url: YouTube video URL
            interval: Interval in seconds between frame extractions
            
        Returns:
            List of created Frame objects
        """
        temp_video_path = None
        
        try:
            # Check if frames already exist for this video
            existing_frames = self.db.query(Frame).filter(Frame.video_id == video_id).first()
            if existing_frames:
                print(f"Frames already exist for video {video_id}")
                return self.db.query(Frame).filter(Frame.video_id == video_id).all()
            
            # Download video to temporary location
            temp_video_path = self.download_video(video_url, str(self.temp_dir))
            print(f"Downloaded video to: {temp_video_path}")
            
            # Extract frames
            frame_data = self.extract_frames_from_video(temp_video_path, video_id, interval)
            print(f"Extracted {len(frame_data)} frames")
            
            # Save frame records to database
            frames = self.save_frame_records(video_id, frame_data)
            print(f"Saved {len(frames)} frame records to database")
            
            return frames
            
        except Exception as e:
            raise Exception(f"Error processing video frames: {str(e)}")
        
        finally:
            # Clean up temporary video file
            if temp_video_path and os.path.exists(temp_video_path):
                os.remove(temp_video_path)
                print(f"Cleaned up temporary file: {temp_video_path}")

    def get_frames_by_video_id(self, video_id: int) -> List[Frame]:
        """Get all frames for a specific video."""
        return self.db.query(Frame).filter(Frame.video_id == video_id).order_by(Frame.timestamp).all()

    def get_frame_by_timestamp(self, video_id: int, timestamp: float, tolerance: float = 5.0) -> Optional[Frame]:
        """
        Get a frame closest to a specific timestamp.
        
        Args:
            video_id: Database ID of the video
            timestamp: Target timestamp in seconds
            tolerance: Maximum time difference in seconds
            
        Returns:
            Frame object closest to the timestamp, or None if not found
        """
        frames = self.db.query(Frame).filter(
            Frame.video_id == video_id,
            Frame.timestamp >= timestamp - tolerance,
            Frame.timestamp <= timestamp + tolerance
        ).order_by(Frame.timestamp).all()
        
        if not frames:
            return None
        
        # Find the closest frame
        closest_frame = min(frames, key=lambda f: abs(f.timestamp - timestamp))
        return closest_frame

    def cleanup_video_frames(self, video_id: int):
        """Remove all frames and files for a specific video."""
        try:
            # Delete database records
            frames = self.db.query(Frame).filter(Frame.video_id == video_id).all()
            for frame in frames:
                # Delete physical file
                if os.path.exists(frame.path):
                    os.remove(frame.path)
                # Delete database record
                self.db.delete(frame)
            
            # Remove video frames directory if empty
            video_frames_dir = self.frames_dir / str(video_id)
            if video_frames_dir.exists() and not any(video_frames_dir.iterdir()):
                video_frames_dir.rmdir()
            
            self.db.commit()
            
        except Exception as e:
            raise Exception(f"Error cleaning up video frames: {str(e)}") 