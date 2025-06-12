"""Frame extraction and visual search routes."""
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Dict, List, Optional
from ..db.database import get_db
from ..models.frame import Frame
from ..services.frame_service import FrameService
from pydantic import BaseModel
import tempfile
import os

router = APIRouter(prefix="/frames", tags=["frames"])

class FrameExtractionRequest(BaseModel):
    interval: int = 10  # Default to 10 seconds

class EmbeddingGenerationRequest(BaseModel):
    include_text: bool = True
    include_visual: bool = True

class TextSearchRequest(BaseModel):
    query: str
    video_id: Optional[int] = None
    limit: int = 10

class FrameResponse(BaseModel):
    id: int
    video_id: int
    timestamp: float
    path: str
    
    class Config:
        from_attributes = True

@router.get("/{video_id}")
async def get_video_frames(
    video_id: int,
    db: Session = Depends(get_db)
):
    """Get frames using simplified FrameService."""
    try:
        frame_service = FrameService(db)
        frames = db.query(Frame).filter(Frame.video_id == video_id).all()
        return frames or []
    except Exception as e:
        return []

@router.post("/{video_id}/extract")
async def extract_frames(
    video_id: int,
    db: Session = Depends(get_db)
):
    """Extract frames from video."""
    try:
        frame_service = FrameService(db)
        result = frame_service.extract_frames(video_id, interval=10)
        return {"message": "Frames extracted successfully", "count": result.get("count", 0)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{video_id}/embeddings")
async def generate_embeddings(
    video_id: int,
    db: Session = Depends(get_db)
):
    """Generate CLIP embeddings for video frames."""
    try:
        from ..services.simple_embeddings import SimpleEmbeddingService
        from ..models.video import Video
        
        # Check if video exists
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            return {"error": "Video not found", "status": "error"}
        
        # Check if frames exist
        frames = db.query(Frame).filter(Frame.video_id == video_id).all()
        if not frames:
            return {"error": "No frames found. Extract frames first.", "status": "error"}
        
        # Generate embeddings
        embedding_service = SimpleEmbeddingService(db)
        result = embedding_service.generate_frame_embeddings(video_id)
        
        if result.get("success"):
            return {
                "message": f"Generated embeddings for {result['processed']} frames",
                "status": "success",
                "processed": result["processed"],
                "total_frames": result["total_frames"]
            }
        else:
            return {
                "error": result.get("error", "Unknown error"),
                "status": "error"
            }
        
    except Exception as e:
        return {
            "error": f"Failed to generate embeddings: {str(e)}",
            "status": "error"
        }

@router.get("/{video_id}/embeddings-status")
async def get_embeddings_status(
    video_id: int,
    db: Session = Depends(get_db)
):
    """Check if embeddings exist for a video."""
    try:
        from ..services.simple_embeddings import SimpleEmbeddingService
        
        embedding_service = SimpleEmbeddingService(db)
        status = embedding_service.get_embeddings_status(video_id)
        return status
        
    except Exception as e:
        return {"error": f"Failed to check embeddings status: {str(e)}"}

@router.get("/visual-search/{video_id}")
async def visual_search(
    video_id: int,
    query: str,
    search_type: str = "hybrid",
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Visual search using CLIP embeddings."""
    try:
        from ..services.simple_embeddings import SimpleEmbeddingService
        from ..services.langchain_service import LangChainVideoService
        from ..models.video import Video
        
        # Check if video exists
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            return {"error": "Video not found", "results": []}
        
        embedding_service = SimpleEmbeddingService(db)
        
        if search_type == "visual" or search_type == "hybrid":
            # Use visual search with CLIP
            raw_results = embedding_service.search_visual_content(video_id, query, limit)
            
            # Format results for frontend (convert similarity to score and add match_type)
            formatted_results = []
            for result in raw_results:
                formatted_results.append({
                    "frame_id": result["frame_id"],
                    "timestamp": result["timestamp"],
                    "path": result["path"],
                    "score": result["similarity"],  # Convert similarity to score
                    "match_type": "visual" if search_type == "visual" else "hybrid"
                })
            
            # Add LangChain text search for hybrid mode
            if search_type == "hybrid":
                try:
                    langchain_service = LangChainVideoService(db)
                    qa_result = langchain_service.ask_question(video_id, f"Find information about: {query}")
                    
                    # Add context from LangChain if available
                    context = qa_result.get("answer", "") if qa_result.get("success") else ""
                    
                    return {
                        "query": query,
                        "search_type": search_type,
                        "results": formatted_results,
                        "total_results": len(formatted_results),
                        "context": context[:200] + "..." if len(context) > 200 else context
                    }
                except Exception as e:
                    print(f"LangChain search failed: {str(e)}")
            
            return {
                "query": query,
                "search_type": search_type,
                "results": formatted_results,
                "total_results": len(formatted_results)
            }
        else:
            # Text-only search using LangChain
            try:
                langchain_service = LangChainVideoService(db)
                qa_result = langchain_service.ask_question(video_id, query)
                
                return {
                    "query": query,
                    "search_type": "text",
                    "answer": qa_result.get("answer", "No answer found"),
                    "success": qa_result.get("success", False),
                    "sources": qa_result.get("sources", [])
                }
            except Exception as e:
                return {"error": f"Text search failed: {str(e)}", "results": []}
        
    except Exception as e:
        return {"error": f"Search failed: {str(e)}", "results": []}

@router.post("/visual-search/{video_id}/image")
async def visual_search_by_image(
    video_id: int,
    limit: int = 10,
    image: UploadFile = File(...),
    db: Session = Depends(get_db)
) -> Dict:
    """Search by uploaded image."""
    try:
        # Save uploaded image temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
            content = await image.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        frame_service = FrameService(db)
        results = frame_service.visual_search_by_image(video_id, tmp_path, limit)
        
        # Clean up temporary file
        os.unlink(tmp_path)
        
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/visual-search/{video_id}/timestamp/{timestamp}")
async def visual_search_by_timestamp(
    video_id: int,
    timestamp: float,
    time_window: float = 30.0,
    limit: int = 10,
    db: Session = Depends(get_db)
) -> Dict:
    """Find visually similar frames around a timestamp."""
    try:
        frame_service = FrameService(db)
        results = frame_service.find_similar_frames(video_id, timestamp, time_window, limit)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/storage/{file_path:path}")
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