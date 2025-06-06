# Visual search logic 

# Visual Search Service
import os
import tempfile
from typing import List, Dict, Optional, Union, Any
from pathlib import Path
import base64
import io

# Database
from sqlalchemy.orm import Session
from ..models.video import Video
from ..models.frame import Frame
from .embeddings import EmbeddingService

# Image processing
from PIL import Image
import torch

class VisualSearchService:
    def __init__(self, db: Session):
        self.db = db
        self.embedding_service = EmbeddingService(db)

    def search_by_text_query(self, 
                            video_id: int, 
                            query: str, 
                            limit: int = 10,
                            search_type: str = "hybrid") -> Dict[str, Any]:
        """
        Search frames using natural language query.
        
        Args:
            video_id: Video ID to search within
            query: Natural language search query
            limit: Maximum number of results
            search_type: "text", "visual", or "hybrid"
            
        Returns:
            Dictionary containing search results with frames and metadata
        """
        try:
            results = []
            
            if search_type in ["text", "hybrid"]:
                # Search text embeddings (section titles, descriptions)
                text_results = self.embedding_service.search_text_embeddings(
                    query=query,
                    video_id=video_id,
                    limit=limit
                )
                
                # Convert text results to frame results
                for result in text_results:
                    metadata = result["metadata"]
                    if "start_time" in metadata and "end_time" in metadata:
                        # Find frames within the section time range
                        section_frames = self._get_frames_in_time_range(
                            video_id=video_id,
                            start_time=metadata["start_time"],
                            end_time=metadata["end_time"],
                            max_frames=3
                        )
                        
                        for frame in section_frames:
                            results.append({
                                "frame_id": frame.id,
                                "timestamp": frame.timestamp,
                                "image_path": frame.path,
                                "image_url": self._get_frame_url(frame.path),
                                "score": result["score"],
                                "match_type": "text",
                                "matched_content": metadata.get("text", ""),
                                "section_title": metadata.get("text", "") if metadata.get("content_type") == "section_title" else None
                            })
            
            if search_type in ["visual", "hybrid"]:
                # Generate visual embedding from text query using CLIP
                visual_results = self._search_by_clip_text(
                    video_id=video_id,
                    text_query=query,
                    limit=limit
                )
                
                for result in visual_results:
                    metadata = result["metadata"]
                    if metadata.get("frame_id"):
                        frame = self.db.query(Frame).filter(Frame.id == metadata["frame_id"]).first()
                        if frame:
                            results.append({
                                "frame_id": frame.id,
                                "timestamp": frame.timestamp,
                                "image_path": frame.path,
                                "image_url": self._get_frame_url(frame.path),
                                "score": result["score"],
                                "match_type": "visual",
                                "matched_content": query,
                                "section_title": None
                            })
            
            # Remove duplicates and sort by score
            unique_results = self._deduplicate_results(results)
            sorted_results = sorted(unique_results, key=lambda x: x["score"], reverse=True)[:limit]
            
            return {
                "video_id": video_id,
                "query": query,
                "search_type": search_type,
                "total_results": len(sorted_results),
                "results": sorted_results
            }
            
        except Exception as e:
            raise Exception(f"Error in text query search: {str(e)}")

    def search_by_image(self, 
                       video_id: int, 
                       image_data: Union[str, bytes],
                       limit: int = 10) -> Dict[str, Any]:
        """
        Search frames using an uploaded image.
        
        Args:
            video_id: Video ID to search within
            image_data: Base64 encoded image or raw bytes
            limit: Maximum number of results
            
        Returns:
            Dictionary containing similar frame results
        """
        try:
            # Save uploaded image to temporary file
            temp_image_path = self._save_temp_image(image_data)
            
            try:
                # Search for similar visual embeddings
                visual_results = self.embedding_service.search_visual_embeddings(
                    image_path=temp_image_path,
                    video_id=video_id,
                    limit=limit
                )
                
                results = []
                for result in visual_results:
                    metadata = result["metadata"]
                    if metadata.get("frame_id"):
                        frame = self.db.query(Frame).filter(Frame.id == metadata["frame_id"]).first()
                        if frame:
                            results.append({
                                "frame_id": frame.id,
                                "timestamp": frame.timestamp,
                                "image_path": frame.path,
                                "image_url": self._get_frame_url(frame.path),
                                "score": result["score"],
                                "match_type": "visual_similarity",
                                "matched_content": "uploaded_image"
                            })
                
                return {
                    "video_id": video_id,
                    "search_type": "image_similarity",
                    "total_results": len(results),
                    "results": results
                }
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_image_path):
                    os.unlink(temp_image_path)
                    
        except Exception as e:
            raise Exception(f"Error in image search: {str(e)}")

    def search_by_timestamp(self, 
                           video_id: int, 
                           timestamp: float,
                           time_window: float = 30.0,
                           limit: int = 10) -> Dict[str, Any]:
        """
        Search frames around a specific timestamp.
        
        Args:
            video_id: Video ID to search within
            timestamp: Target timestamp in seconds
            time_window: Time window around timestamp (seconds)
            limit: Maximum number of results
            
        Returns:
            Dictionary containing frame results around the timestamp
        """
        try:
            start_time = max(0, timestamp - time_window / 2)
            end_time = timestamp + time_window / 2
            
            frames = self._get_frames_in_time_range(
                video_id=video_id,
                start_time=start_time,
                end_time=end_time,
                max_frames=limit
            )
            
            results = []
            for frame in frames:
                # Calculate similarity score based on distance from target timestamp
                time_distance = abs(frame.timestamp - timestamp)
                score = max(0, 1 - (time_distance / (time_window / 2)))
                
                results.append({
                    "frame_id": frame.id,
                    "timestamp": frame.timestamp,
                    "image_path": frame.path,
                    "image_url": self._get_frame_url(frame.path),
                    "score": score,
                    "match_type": "temporal",
                    "matched_content": f"timestamp_{timestamp}",
                    "time_distance": time_distance
                })
            
            # Sort by timestamp
            results.sort(key=lambda x: x["timestamp"])
            
            return {
                "video_id": video_id,
                "search_type": "timestamp",
                "target_timestamp": timestamp,
                "time_window": time_window,
                "total_results": len(results),
                "results": results
            }
            
        except Exception as e:
            raise Exception(f"Error in timestamp search: {str(e)}")

    def get_frame_thumbnails(self, 
                           video_id: int, 
                           frame_ids: List[int],
                           size: tuple = (200, 150)) -> Dict[int, str]:
        """
        Generate thumbnails for specific frames.
        
        Args:
            video_id: Video ID
            frame_ids: List of frame IDs
            size: Thumbnail size (width, height)
            
        Returns:
            Dictionary mapping frame_id to base64 encoded thumbnail
        """
        try:
            thumbnails = {}
            
            frames = self.db.query(Frame).filter(
                Frame.video_id == video_id,
                Frame.id.in_(frame_ids)
            ).all()
            
            for frame in frames:
                if os.path.exists(frame.path):
                    try:
                        # Load and resize image
                        image = Image.open(frame.path)
                        image.thumbnail(size, Image.Resampling.LANCZOS)
                        
                        # Convert to base64
                        buffer = io.BytesIO()
                        image.save(buffer, format='JPEG', quality=85)
                        thumbnail_b64 = base64.b64encode(buffer.getvalue()).decode()
                        
                        thumbnails[frame.id] = f"data:image/jpeg;base64,{thumbnail_b64}"
                        
                    except Exception as e:
                        print(f"Error generating thumbnail for frame {frame.id}: {e}")
                        
            return thumbnails
            
        except Exception as e:
            raise Exception(f"Error generating thumbnails: {str(e)}")

    def _search_by_clip_text(self, 
                            video_id: int, 
                            text_query: str, 
                            limit: int) -> List[Dict]:
        """
        Search visual embeddings using CLIP text encoding.
        
        Args:
            video_id: Video ID to search within
            text_query: Text query to encode with CLIP
            limit: Maximum results
            
        Returns:
            List of visual search results
        """
        try:
            if not self.embedding_service.clip_model:
                return []
            
            # Generate text embedding using CLIP
            import open_clip
            
            text_tokens = self.embedding_service.clip_tokenizer([text_query])
            
            with torch.no_grad():
                text_features = self.embedding_service.clip_model.encode_text(text_tokens)
                text_features = text_features / text_features.norm(dim=-1, keepdim=True)
            
            query_embedding = text_features.squeeze().numpy().tolist()
            
            # Search visual embeddings using CLIP text embedding
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            
            query_filter = Filter(
                must=[FieldCondition(key="video_id", match=MatchValue(value=video_id))]
            )
            
            results = self.embedding_service.qdrant_client.search(
                collection_name=self.embedding_service.visual_collection,
                query_vector=query_embedding,
                query_filter=query_filter,
                limit=limit
            )
            
            return [
                {
                    "id": result.id,
                    "score": result.score,
                    "metadata": result.payload
                }
                for result in results
            ]
            
        except Exception as e:
            print(f"Warning: CLIP text search failed: {e}")
            return []

    def _get_frames_in_time_range(self, 
                                 video_id: int, 
                                 start_time: float, 
                                 end_time: float,
                                 max_frames: int = None) -> List[Frame]:
        """Get frames within a specific time range."""
        query = self.db.query(Frame).filter(
            Frame.video_id == video_id,
            Frame.timestamp >= start_time,
            Frame.timestamp <= end_time
        ).order_by(Frame.timestamp)
        
        if max_frames:
            query = query.limit(max_frames)
            
        return query.all()

    def _save_temp_image(self, image_data: Union[str, bytes]) -> str:
        """Save uploaded image data to a temporary file."""
        if isinstance(image_data, str):
            # Assume base64 encoded
            if image_data.startswith('data:image/'):
                # Remove data URL prefix
                image_data = image_data.split(',')[1]
            image_bytes = base64.b64decode(image_data)
        else:
            image_bytes = image_data
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
        temp_file.write(image_bytes)
        temp_file.close()
        
        return temp_file.name

    def _get_frame_url(self, frame_path: str) -> str:
        """Convert frame file path to accessible URL."""
        try:
            # Convert absolute path to relative URL
            if frame_path.startswith('/'):
                # Absolute path - extract relative part
                storage_dir = "storage"
                if storage_dir in frame_path:
                    relative_path = frame_path.split(storage_dir)[-1].lstrip('/')
                    return f"/api/frames/storage/{relative_path}"
                else:
                    return f"/api/frames/{os.path.basename(frame_path)}"
            else:
                # Already relative
                return f"/api/frames/{frame_path}"
                
        except Exception:
            return f"/api/frames/{os.path.basename(frame_path)}"

    def _deduplicate_results(self, results: List[Dict]) -> List[Dict]:
        """Remove duplicate frame results, keeping the highest score."""
        seen_frames = {}
        
        for result in results:
            frame_id = result["frame_id"]
            if frame_id not in seen_frames or result["score"] > seen_frames[frame_id]["score"]:
                seen_frames[frame_id] = result
                
        return list(seen_frames.values())

    def get_video_frame_summary(self, video_id: int) -> Dict[str, Any]:
        """Get summary of available frames for a video."""
        try:
            frames = self.db.query(Frame).filter(Frame.video_id == video_id).all()
            
            if not frames:
                return {
                    "video_id": video_id,
                    "total_frames": 0,
                    "duration_covered": 0,
                    "frame_intervals": [],
                    "message": "No frames available for this video"
                }
            
            # Calculate statistics
            timestamps = [frame.timestamp for frame in frames]
            min_time = min(timestamps)
            max_time = max(timestamps)
            
            # Calculate intervals between frames
            sorted_timestamps = sorted(timestamps)
            intervals = [sorted_timestamps[i+1] - sorted_timestamps[i] for i in range(len(sorted_timestamps)-1)]
            avg_interval = sum(intervals) / len(intervals) if intervals else 0
            
            return {
                "video_id": video_id,
                "total_frames": len(frames),
                "duration_covered": max_time - min_time,
                "start_time": min_time,
                "end_time": max_time,
                "average_interval": avg_interval,
                "frame_intervals": intervals[:10],  # First 10 intervals
                "sample_frames": [
                    {
                        "frame_id": frame.id,
                        "timestamp": frame.timestamp,
                        "image_url": self._get_frame_url(frame.path)
                    }
                    for frame in frames[:5]  # First 5 frames as samples
                ]
            }
            
        except Exception as e:
            raise Exception(f"Error getting video frame summary: {str(e)}") 