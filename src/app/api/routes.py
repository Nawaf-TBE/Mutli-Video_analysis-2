"""
DEPRECATED: This file has been refactored into modular components.
Use main_routes.py instead which imports from:
- video_routes.py
- chat_routes.py  
- frame_routes.py
"""

# This file is kept temporarily for reference and will be removed after verification
from .main_routes import router

__all__ = ["router"]

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