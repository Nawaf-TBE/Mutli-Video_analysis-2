"""Video management routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
from ..db.database import get_db
from ..models.video import Video
from ..models.section import Section
from ..services.video_service import VideoService
from ..services.langchain_service import LangChainVideoService
from pydantic import BaseModel

router = APIRouter(prefix="/videos", tags=["videos"])

class VideoUploadRequest(BaseModel):
    url: str

class SectionResponse(BaseModel):
    id: int
    video_id: int
    title: str
    start_time: float
    end_time: float
    
    class Config:
        from_attributes = True

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

@router.get("/{video_id}")
async def get_video(video_id: int, db: Session = Depends(get_db)):
    """Get video details."""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return video

@router.get("/{video_id}/sections")
async def get_sections(video_id: int, db: Session = Depends(get_db)):
    """Get video sections."""
    sections = db.query(Section).filter(Section.video_id == video_id).all()
    return sections

@router.post("/{video_id}/regenerate-sections")
async def regenerate_all_sections(video_id: int, db: Session = Depends(get_db)):
    """Regenerate all sections for a video using LangChain."""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    try:
        langchain_service = LangChainVideoService(db)
        sections_data = langchain_service.generate_sections(video_id)
        
        # Delete existing sections
        db.query(Section).filter(Section.video_id == video_id).delete()
        
        # Create new sections
        for i, section_data in enumerate(sections_data):
            section = Section(
                video_id=video_id,
                title=section_data["title"],
                start_time=section_data.get("start_time", i * 60),
                end_time=section_data.get("end_time", (i + 1) * 60)
            )
            db.add(section)
        
        db.commit()
        
        # Return the new sections
        new_sections = db.query(Section).filter(Section.video_id == video_id).all()
        return new_sections
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

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