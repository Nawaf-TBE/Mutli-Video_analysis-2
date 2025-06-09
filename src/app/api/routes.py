# API routes
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Dict, List, Optional, Any
from ..db.database import get_db
from ..models.section import Section
from ..models.frame import Frame
from pydantic import BaseModel
import os
import tempfile
from ..models.video import Video
from ..services.video_service import VideoService
from ..services.frame_service import FrameService
from ..services.langchain_service import LangChainVideoService
import json

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

@router.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Multi-Video Analysis API", "version": "2.0 - LangChain Enhanced"}

@router.post("/upload")
async def upload_video(
    request: VideoUploadRequest,
    db: Session = Depends(get_db)
):
    """Upload a video and process with LangChain."""
    url = request.url
    try:
        video_service = VideoService(db)
        langchain_service = LangChainVideoService(db)
        
        # Create video record
        video = video_service.create_video(url)
        
        # Process transcript with LangChain (much more reliable!)
        transcript_result = langchain_service.process_transcript(video.id, url)
        
        # Generate AI sections if transcript is available
        if transcript_result["success"]:
            sections_data = langchain_service.generate_sections(video.id)
            
            # Save sections to database
            for i, section_data in enumerate(sections_data):
                section = Section(
                    video_id=video.id,
                    title=section_data["title"],
                    start_time=i * 60,  # Approximate timing
                    end_time=(i + 1) * 60
                )
                db.add(section)
        else:
            # Create fallback section
            section = Section(
                video_id=video.id,
                title="Video Content",
                start_time=0,
                end_time=300
            )
            db.add(section)
        
        db.commit()
        
        return {
            "video_id": video.id,
            "message": "Video uploaded and processed",
            "transcript": transcript_result,
            "url": url
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/videos/{video_id}")
async def get_video(video_id: int, db: Session = Depends(get_db)):
    """Get video details."""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return video

@router.get("/sections/{video_id}")
async def get_sections(video_id: int, db: Session = Depends(get_db)):
    """Get video sections."""
    sections = db.query(Section).filter(Section.video_id == video_id).all()
    return sections

@router.post("/sections/{section_id}/regenerate")
async def regenerate_section(section_id: int, db: Session = Depends(get_db)):
    """Regenerate section using LangChain."""
    section = db.query(Section).filter(Section.id == section_id).first()
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")
    
    try:
        langchain_service = LangChainVideoService(db)
        sections_data = langchain_service.generate_sections(section.video_id)
        
        if sections_data:
            # Update the section with fresh AI-generated content
            section.title = sections_data[0]["title"]
            db.commit()
        
        return {"message": "Section regenerated", "section": section}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/chat/{video_id}")
async def chat_with_video(
    video_id: int,
    request: Dict[str, str],
    db: Session = Depends(get_db)
):
    """Chat with video using LangChain QA."""
    question = request.get("message", "")
    if not question:
        raise HTTPException(status_code=400, detail="Message is required")
    
    # Check if video exists
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    try:
        langchain_service = LangChainVideoService(db)
        result = langchain_service.ask_question(video_id, question)
        
        return {
            "response": result["answer"],
            "success": result["success"],
            "sources": result.get("sources", [])
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))





# Simplified endpoints using FrameService (no old dependencies)
@router.get("/frames/{video_id}")
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

@router.post("/videos/{video_id}/extract-frames")
async def extract_frames(
    video_id: int,
    db: Session = Depends(get_db)
):
    """Extract frames from video using FrameService."""
    try:
        frame_service = FrameService(db)
        result = frame_service.extract_frames(video_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting frames: {str(e)}")

@router.post("/videos/{video_id}/generate-embeddings")
async def generate_embeddings(
    video_id: int,
    db: Session = Depends(get_db)
):
    """Generate CLIP embeddings for video frames."""
    try:
        from ..services.simple_embeddings import SimpleEmbeddingService
        
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

@router.get("/videos/{video_id}/embeddings-status")
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

# Visual Search Endpoints

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
    """Image search - simplified for LangChain system."""
    return {"message": "Image search not implemented", "results": []}

@router.get("/visual-search/{video_id}/timestamp/{timestamp}")
async def visual_search_by_timestamp(
    video_id: int,
    timestamp: float,
    time_window: float = 30.0,
    limit: int = 10,
    db: Session = Depends(get_db)
) -> Dict:
    """Timestamp search - simplified for LangChain system."""
    return {"message": "Timestamp search not implemented", "results": []}

@router.get("/visual-search/{video_id}/thumbnails")
async def get_frame_thumbnails(
    video_id: int,
    frame_ids: str,  
    size: str = "200x150",
    db: Session = Depends(get_db)
) -> Dict:
    """Thumbnails - simplified for LangChain system."""
    return {"message": "Thumbnails not implemented", "thumbnails": []}

@router.get("/visual-search/{video_id}/summary")
async def get_video_frame_summary(
    video_id: int,
    db: Session = Depends(get_db)
) -> Dict:
    """Frame summary - simplified for LangChain system."""
    return {"message": "Frame summary not implemented", "summary": {}}

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

# New LangChain-specific endpoints
@router.post("/langchain/process/{video_id}")
async def process_with_langchain(video_id: int, db: Session = Depends(get_db)):
    """Process video with LangChain (transcript + embeddings)."""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    try:
        langchain_service = LangChainVideoService(db)
        result = langchain_service.process_transcript(video_id, video.url)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/langchain/status/{video_id}")
async def get_langchain_status(video_id: int, db: Session = Depends(get_db)):
    """Check if LangChain processing is complete for a video."""
    from pathlib import Path
    
    chroma_dir = Path(f"storage/chroma/video_{video_id}")
    
    return {
        "video_id": video_id,
        "processed": chroma_dir.exists(),
        "chroma_path": str(chroma_dir) if chroma_dir.exists() else None
    } 