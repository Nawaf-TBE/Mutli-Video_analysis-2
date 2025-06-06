# API routes
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Dict, List, Optional
from ..db.database import get_db
from ..services.youtube import YouTubeService
from ..services.sectionizer import SectionizerService
from ..services.frame_extractor import FrameExtractorService
from ..services.embeddings import EmbeddingService
from ..services.rag_chat import RAGChatService
from ..models.section import Section
from ..models.frame import Frame
from pydantic import BaseModel
import os
import tempfile

router = APIRouter()

class VideoUploadRequest(BaseModel):
    url: str

class FrameExtractionRequest(BaseModel):
    interval: int = 10  # Default to 10 seconds

class EmbeddingGenerationRequest(BaseModel):
    include_text: bool = True
    include_visual: bool = True

class TextSearchRequest(BaseModel):
    query: str
    video_id: Optional[int] = None
    limit: int = 10

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    include_visual: bool = False

class SectionResponse(BaseModel):
    id: int
    video_id: int
    title: str
    start_time: float
    end_time: float
    
    class Config:
        from_attributes = True

class FrameResponse(BaseModel):
    id: int
    video_id: int
    timestamp: float
    path: str
    
    class Config:
        from_attributes = True

@router.post("/upload")
async def upload_video(
    request: VideoUploadRequest,
    db: Session = Depends(get_db)
) -> Dict:
    """
    Upload a YouTube video for processing.
    This endpoint will:
    1. Extract video metadata
    2. Fetch the transcript
    3. Create sections from the transcript using AI
    4. Save everything to the database
    """
    try:
        youtube_service = YouTubeService(db)
        video = youtube_service.process_video(request.url)
        
        return {
            "message": "Video processed successfully",
            "video_id": video.id,
            "title": video.title,
            "sections_count": len(video.sections)
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing video: {str(e)}")

@router.post("/videos/{video_id}/extract-frames")
async def extract_frames(
    video_id: int,
    request: FrameExtractionRequest,
    db: Session = Depends(get_db)
) -> Dict:
    """
    Extract frames from a video at specified intervals.
    This is a potentially long-running operation.
    """
    try:
        # Get video from database
        from ..models.video import Video
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")
        
        frame_extractor = FrameExtractorService(db)
        frames = frame_extractor.process_video_frames(video_id, video.url, request.interval)
        
        return {
            "message": "Frame extraction completed",
            "video_id": video_id,
            "frames_extracted": len(frames),
            "interval": request.interval
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting frames: {str(e)}")

@router.post("/videos/{video_id}/generate-embeddings")
async def generate_embeddings(
    video_id: int,
    request: EmbeddingGenerationRequest,
    db: Session = Depends(get_db)
) -> Dict:
    """
    Generate embeddings for video content (text and/or visual).
    This processes sections and frames to create searchable embeddings.
    """
    try:
        embedding_service = EmbeddingService(db)
        
        text_points = []
        visual_points = []
        
        if request.include_text:
            text_points = embedding_service.process_video_text_embeddings(video_id)
        
        if request.include_visual:
            visual_points = embedding_service.process_video_visual_embeddings(video_id)
        
        return {
            "message": "Embeddings generated successfully",
            "video_id": video_id,
            "text_embeddings": len(text_points),
            "visual_embeddings": len(visual_points)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating embeddings: {str(e)}")

@router.post("/chat/{video_id}")
async def chat_with_video(
    video_id: int,
    request: ChatRequest,
    db: Session = Depends(get_db)
) -> Dict:
    """
    Chat with a specific video using RAG (Retrieval-Augmented Generation).
    
    This endpoint:
    1. Searches for relevant content in the video using embeddings
    2. Builds context from retrieved information
    3. Generates AI responses with timestamped citations
    4. Maintains conversation history
    """
    try:
        # Verify video exists
        from ..models.video import Video
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")
        
        # Initialize chat service
        chat_service = RAGChatService(db)
        
        # Generate response
        response = chat_service.chat(
            query=request.message,
            video_id=video_id,
            conversation_id=request.conversation_id,
            include_visual=request.include_visual
        )
        
        return {
            "response": response.response,
            "citations": response.citations,
            "conversation_id": response.conversation_id,
            "video_info": response.context_used.video_info,
            "relevance_score": response.context_used.combined_score,
            "sources_found": len(response.context_used.text_results) + len(response.context_used.visual_results)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in chat: {str(e)}")

@router.get("/chat/{video_id}/suggestions")
async def get_chat_suggestions(
    video_id: int,
    db: Session = Depends(get_db)
) -> Dict:
    """
    Get suggested questions for a video to help users start conversations.
    """
    try:
        # Verify video exists
        from ..models.video import Video
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")
        
        chat_service = RAGChatService(db)
        suggestions = chat_service.get_suggested_questions(video_id)
        
        return {
            "video_id": video_id,
            "video_title": video.title,
            "suggested_questions": suggestions
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting suggestions: {str(e)}")

@router.get("/chat/history/{conversation_id}")
async def get_conversation_history(
    conversation_id: str,
    db: Session = Depends(get_db)
) -> Dict:
    """
    Get the conversation history for a specific conversation ID.
    """
    try:
        chat_service = RAGChatService(db)
        history = chat_service.get_conversation_history(conversation_id)
        
        return {
            "conversation_id": conversation_id,
            "message_count": len(history),
            "messages": history
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching conversation history: {str(e)}")

@router.delete("/chat/history/{conversation_id}")
async def clear_conversation_history(
    conversation_id: str,
    db: Session = Depends(get_db)
) -> Dict:
    """
    Clear the conversation history for a specific conversation ID.
    """
    try:
        chat_service = RAGChatService(db)
        cleared = chat_service.clear_conversation(conversation_id)
        
        if cleared:
            return {
                "message": "Conversation history cleared successfully",
                "conversation_id": conversation_id
            }
        else:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing conversation: {str(e)}")

@router.post("/search/text")
async def search_text(
    request: TextSearchRequest,
    db: Session = Depends(get_db)
) -> Dict:
    """
    Search for similar text content using embeddings.
    Returns relevant sections based on semantic similarity.
    """
    try:
        embedding_service = EmbeddingService(db)
        results = embedding_service.search_text_embeddings(
            query=request.query,
            video_id=request.video_id,
            limit=request.limit
        )
        
        return {
            "query": request.query,
            "results": results,
            "total_results": len(results)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching text: {str(e)}")

@router.post("/search/visual")
async def search_visual(
    video_id: Optional[int] = None,
    limit: int = 10,
    image: UploadFile = File(...),
    db: Session = Depends(get_db)
) -> Dict:
    """
    Search for similar visual content using image embeddings.
    Upload an image to find similar frames in videos.
    """
    try:
        # Save uploaded image temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
            content = await image.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            embedding_service = EmbeddingService(db)
            results = embedding_service.search_visual_embeddings(
                image_path=tmp_file_path,
                video_id=video_id,
                limit=limit
            )
            
            return {
                "results": results,
                "total_results": len(results)
            }
            
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching visual content: {str(e)}")

@router.get("/sections/{video_id}", response_model=List[SectionResponse])
async def get_video_sections(
    video_id: int,
    db: Session = Depends(get_db)
) -> List[Section]:
    """
    Get all sections for a specific video.
    Returns a list of sections with their titles and timestamps.
    """
    try:
        sectionizer = SectionizerService(db)
        sections = sectionizer.get_sections_by_video_id(video_id)
        
        if not sections:
            raise HTTPException(status_code=404, detail="No sections found for this video")
        
        return sections
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching sections: {str(e)}")

@router.get("/frames/{video_id}", response_model=List[FrameResponse])
async def get_video_frames(
    video_id: int,
    db: Session = Depends(get_db)
) -> List[Frame]:
    """
    Get all frames for a specific video.
    Returns a list of frames with their timestamps and file paths.
    """
    try:
        frame_extractor = FrameExtractorService(db)
        frames = frame_extractor.get_frames_by_video_id(video_id)
        
        if not frames:
            raise HTTPException(status_code=404, detail="No frames found for this video")
        
        return frames
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching frames: {str(e)}")

@router.get("/frames/{video_id}/timestamp/{timestamp}")
async def get_frame_by_timestamp(
    video_id: int,
    timestamp: float,
    tolerance: float = 5.0,
    db: Session = Depends(get_db)
):
    """
    Get a frame closest to a specific timestamp.
    Returns the frame file as an image response.
    """
    try:
        frame_extractor = FrameExtractorService(db)
        frame = frame_extractor.get_frame_by_timestamp(video_id, timestamp, tolerance)
        
        if not frame:
            raise HTTPException(status_code=404, detail="No frame found for the specified timestamp")
        
        if not os.path.exists(frame.path):
            raise HTTPException(status_code=404, detail="Frame file not found")
        
        return FileResponse(
            path=frame.path,
            media_type="image/jpeg",
            filename=f"frame_{video_id}_{timestamp}s.jpg"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching frame: {str(e)}")

@router.post("/sections/{video_id}/regenerate")
async def regenerate_video_sections(
    video_id: int,
    db: Session = Depends(get_db)
) -> Dict:
    """
    Regenerate sections for a video using the stored transcript.
    Useful for testing different AI parameters or re-processing.
    """
    try:
        # This would require implementing the regenerate_sections method
        # For now, return a placeholder response
        return {
            "message": "Section regeneration not yet implemented",
            "video_id": video_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error regenerating sections: {str(e)}")

@router.delete("/frames/{video_id}")
async def delete_video_frames(
    video_id: int,
    db: Session = Depends(get_db)
) -> Dict:
    """
    Delete all frames for a specific video.
    This will remove both database records and physical files.
    """
    try:
        frame_extractor = FrameExtractorService(db)
        frame_extractor.cleanup_video_frames(video_id)
        
        return {
            "message": "All frames deleted successfully",
            "video_id": video_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting frames: {str(e)}")

@router.delete("/embeddings/{video_id}")
async def delete_video_embeddings(
    video_id: int,
    db: Session = Depends(get_db)
) -> Dict:
    """
    Delete all embeddings for a specific video.
    This will remove embeddings from the vector database.
    """
    try:
        embedding_service = EmbeddingService(db)
        embedding_service.delete_video_embeddings(video_id)
        
        return {
            "message": "All embeddings deleted successfully",
            "video_id": video_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting embeddings: {str(e)}")

# Visual Search Endpoints

@router.get("/visual-search/{video_id}")
async def visual_search_query(
    video_id: int,
    query: str,
    search_type: str = "hybrid",
    limit: int = 10,
    db: Session = Depends(get_db)
) -> Dict:
    """
    Search video frames using natural language queries.
    Supports text-based and visual-based semantic search.
    
    Args:
        video_id: ID of the video to search within
        query: Natural language search query
        search_type: "text", "visual", or "hybrid" search mode
        limit: Maximum number of results to return
    """
    try:
        from ..services.visual_search import VisualSearchService
        
        visual_search = VisualSearchService(db)
        results = visual_search.search_by_text_query(
            video_id=video_id,
            query=query,
            search_type=search_type,
            limit=limit
        )
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in visual search: {str(e)}")

@router.post("/visual-search/{video_id}/image")
async def visual_search_by_image(
    video_id: int,
    limit: int = 10,
    image: UploadFile = File(...),
    db: Session = Depends(get_db)
) -> Dict:
    """
    Search video frames using an uploaded image for visual similarity.
    Finds frames that are visually similar to the uploaded image.
    """
    try:
        from ..services.visual_search import VisualSearchService
        
        # Read uploaded image
        image_data = await image.read()
        
        visual_search = VisualSearchService(db)
        results = visual_search.search_by_image(
            video_id=video_id,
            image_data=image_data,
            limit=limit
        )
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in image-based visual search: {str(e)}")

@router.get("/visual-search/{video_id}/timestamp/{timestamp}")
async def visual_search_by_timestamp(
    video_id: int,
    timestamp: float,
    time_window: float = 30.0,
    limit: int = 10,
    db: Session = Depends(get_db)
) -> Dict:
    """
    Search frames around a specific timestamp.
    Returns frames within a time window around the target timestamp.
    """
    try:
        from ..services.visual_search import VisualSearchService
        
        visual_search = VisualSearchService(db)
        results = visual_search.search_by_timestamp(
            video_id=video_id,
            timestamp=timestamp,
            time_window=time_window,
            limit=limit
        )
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in timestamp-based search: {str(e)}")

@router.get("/visual-search/{video_id}/thumbnails")
async def get_frame_thumbnails(
    video_id: int,
    frame_ids: str,  # Comma-separated list of frame IDs
    size: str = "200x150",  # Format: "widthxheight"
    db: Session = Depends(get_db)
) -> Dict:
    """
    Generate thumbnails for specific frames.
    Returns base64-encoded thumbnails for the requested frames.
    
    Args:
        video_id: ID of the video
        frame_ids: Comma-separated list of frame IDs (e.g., "1,2,3")
        size: Thumbnail size in format "widthxheight" (default: "200x150")
    """
    try:
        from ..services.visual_search import VisualSearchService
        
        # Parse frame IDs
        frame_id_list = [int(fid.strip()) for fid in frame_ids.split(',') if fid.strip()]
        
        # Parse size
        try:
            width, height = map(int, size.split('x'))
            thumbnail_size = (width, height)
        except ValueError:
            thumbnail_size = (200, 150)  # Default size
        
        visual_search = VisualSearchService(db)
        thumbnails = visual_search.get_frame_thumbnails(
            video_id=video_id,
            frame_ids=frame_id_list,
            size=thumbnail_size
        )
        
        return {
            "video_id": video_id,
            "thumbnails": thumbnails,
            "total_thumbnails": len(thumbnails)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating thumbnails: {str(e)}")

@router.get("/visual-search/{video_id}/summary")
async def get_video_frame_summary(
    video_id: int,
    db: Session = Depends(get_db)
) -> Dict:
    """
    Get summary information about available frames for a video.
    Returns statistics about frame coverage, intervals, and sample frames.
    """
    try:
        from ..services.visual_search import VisualSearchService
        
        visual_search = VisualSearchService(db)
        summary = visual_search.get_video_frame_summary(video_id)
        
        return summary
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting frame summary: {str(e)}")

# Static file serving for frames
@router.get("/frames/storage/{file_path:path}")
async def serve_frame_image(file_path: str):
    """
    Serve frame images from the storage directory.
    This endpoint provides access to extracted frame images.
    """
    try:
        # Construct the full path to the frame file
        storage_path = os.path.join("storage", file_path)
        
        # Check if file exists and is within storage directory (security check)
        if not os.path.exists(storage_path):
            raise HTTPException(status_code=404, detail="Frame image not found")
        
        # Ensure the path is within the storage directory (prevent directory traversal)
        abs_storage_path = os.path.abspath(storage_path)
        abs_storage_dir = os.path.abspath("storage")
        if not abs_storage_path.startswith(abs_storage_dir):
            raise HTTPException(status_code=403, detail="Access denied")
        
        return FileResponse(
            path=storage_path,
            media_type="image/jpeg",
            filename=os.path.basename(file_path)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error serving frame image: {str(e)}") 