"""Chat and conversation routes."""
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, validator

from ..db.database import get_db
from ..models.video import Video
from ..services.langchain_service import LangChainVideoService

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

class ChatRequest(BaseModel):
    """Request model for chat messages."""
    message: str = Field(..., min_length=1, max_length=1000, description="The chat message")
    conversation_id: Optional[str] = Field(None, description="Optional conversation ID")
    include_visual: bool = Field(False, description="Whether to include visual analysis")
    
    @validator('message')
    def validate_message(cls, v):
        if not v or not v.strip():
            raise ValueError('Message cannot be empty')
        return v.strip()

class ChatResponse(BaseModel):
    """Response model for chat messages."""
    response: str = Field(..., description="The AI response")
    success: bool = Field(..., description="Whether the request was successful")
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="Source citations")
    conversation_id: Optional[str] = Field(None, description="Conversation ID")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")

class LangChainProcessResponse(BaseModel):
    """Response model for LangChain processing."""
    success: bool = Field(..., description="Whether processing was successful")
    message: str = Field(..., description="Processing status message")
    video_id: int = Field(..., description="Video ID that was processed")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")

class LangChainStatusResponse(BaseModel):
    """Response model for LangChain status."""
    video_id: int = Field(..., description="Video ID")
    processed: bool = Field(..., description="Whether video is processed")
    chroma_path: Optional[str] = Field(None, description="Path to ChromaDB storage")
    last_modified: Optional[str] = Field(None, description="Last modification time")

@router.post("/{video_id}", response_model=ChatResponse)
async def chat_with_video(
    video_id: int,
    request: ChatRequest,
    db: Session = Depends(get_db)
) -> ChatResponse:
    """Chat with video using LangChain QA."""
    import time
    start_time = time.time()
    
    logger.info(f"Chat request for video {video_id}: {request.message[:50]}...")
    
    # Validate video exists
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        logger.warning(f"Video {video_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Video with ID {video_id} not found"
        )
    
    # Check if video is processed
    if not _is_video_processed(video_id):
        logger.warning(f"Video {video_id} not processed yet")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Video must be processed before chatting. Please process the video first."
        )
    
    try:
        langchain_service = LangChainVideoService(db)
        result = langchain_service.ask_question(video_id, request.message)
        
        processing_time = time.time() - start_time
        
        return ChatResponse(
            response=result["answer"],
            success=result["success"],
            sources=result.get("sources", []),
            conversation_id=request.conversation_id,
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"Error in chat_with_video for video {video_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="An error occurred while processing your request"
        )

@router.post("/langchain/process/{video_id}", response_model=LangChainProcessResponse)
async def process_with_langchain(
    video_id: int, 
    db: Session = Depends(get_db)
) -> LangChainProcessResponse:
    """Process video with LangChain (transcript + embeddings)."""
    import time
    start_time = time.time()
    
    logger.info(f"Starting LangChain processing for video {video_id}")
    
    # Validate video exists
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        logger.warning(f"Video {video_id} not found for processing")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Video with ID {video_id} not found"
        )
    
    # Check if already processed
    if _is_video_processed(video_id):
        logger.info(f"Video {video_id} already processed")
        return LangChainProcessResponse(
            success=True,
            message="Video already processed",
            video_id=video_id,
            processing_time=0.0
        )
    
    try:
        langchain_service = LangChainVideoService(db)
        result = langchain_service.process_transcript(video_id, video.url)
        
        processing_time = time.time() - start_time
        
        if result.get("success", False):
            logger.info(f"Successfully processed video {video_id} in {processing_time:.2f}s")
            return LangChainProcessResponse(
                success=True,
                message="Video processed successfully",
                video_id=video_id,
                processing_time=processing_time
            )
        else:
            logger.error(f"Failed to process video {video_id}: {result.get('error', 'Unknown error')}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process video: {result.get('error', 'Unknown error')}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing video {video_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="An unexpected error occurred during processing"
        )

@router.get("/langchain/status/{video_id}", response_model=LangChainStatusResponse)
async def get_langchain_status(
    video_id: int, 
    db: Session = Depends(get_db)
) -> LangChainStatusResponse:
    """Check if LangChain processing is complete for a video."""
    logger.info(f"Checking LangChain status for video {video_id}")
    
    # Validate video exists
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        logger.warning(f"Video {video_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Video with ID {video_id} not found"
        )
    
    chroma_dir = Path(f"storage/chroma/video_{video_id}")
    is_processed = chroma_dir.exists() and any(chroma_dir.iterdir())
    
    last_modified = None
    if is_processed:
        try:
            last_modified = chroma_dir.stat().st_mtime
            last_modified = str(last_modified)
        except OSError:
            pass
    
    return LangChainStatusResponse(
        video_id=video_id,
        processed=is_processed,
        chroma_path=str(chroma_dir) if is_processed else None,
        last_modified=last_modified
    )

# Helper functions
def _is_video_processed(video_id: int) -> bool:
    """Check if a video has been processed by LangChain."""
    chroma_dir = Path(f"storage/chroma/video_{video_id}")
    return chroma_dir.exists() and any(chroma_dir.iterdir()) 