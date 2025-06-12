"""Chat and conversation routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, List
from ..db.database import get_db
from ..models.video import Video
from ..services.langchain_service import LangChainVideoService
from pydantic import BaseModel

router = APIRouter(prefix="/chat", tags=["chat"])

class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None
    include_visual: bool = False

@router.post("/{video_id}")
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

@router.post("/langchain/process/{video_id}")
async def process_with_langchain(video_id: int, db: Session = Depends(get_db)):
    """Process video with LangChain (transcript + embeddings)."""
    from ..models.video import Video
    
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