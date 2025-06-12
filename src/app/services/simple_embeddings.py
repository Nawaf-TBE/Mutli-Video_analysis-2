"""
Simple embedding service using CLIP for visual embeddings.
Stores embeddings locally without Qdrant dependency.
"""

import os
import numpy as np
import pickle
from pathlib import Path
from PIL import Image
import open_clip
import torch
from sqlalchemy.orm import Session
from ..models.frame import Frame
from ..models.video import Video

class SimpleEmbeddingService:
    """Simple embedding service using CLIP without external vector databases."""
    
    def __init__(self, db: Session):
        self.db = db
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = None
        self.preprocess = None
        self.tokenizer = None
        
    def _load_clip_model(self):
        """Load CLIP model if not already loaded."""
        if self.model is None:
            print("Loading CLIP model...")
            self.model, _, self.preprocess = open_clip.create_model_and_transforms(
                'ViT-B-32', 
                pretrained='openai'
            )
            self.tokenizer = open_clip.get_tokenizer('ViT-B-32')
            self.model.to(self.device)
            self.model.eval()
            print("CLIP model loaded successfully")
    
    def generate_frame_embeddings(self, video_id: int):
        """Generate CLIP embeddings for all frames of a video."""
        try:
            self._load_clip_model()
            
            # Get all frames for the video
            frames = self.db.query(Frame).filter(Frame.video_id == video_id).all()
            if not frames:
                return {"error": "No frames found", "processed": 0}
            
            embeddings = []
            processed_count = 0
            
            # Create embeddings directory
            embeddings_dir = Path(f"storage/embeddings/video_{video_id}")
            embeddings_dir.mkdir(parents=True, exist_ok=True)
            
            for frame in frames:
                try:
                    # Load frame image
                    if not os.path.exists(frame.path):
                        print(f"Frame image not found: {frame.path}")
                        continue
                    
                    image = Image.open(frame.path).convert('RGB')
                    image_tensor = self.preprocess(image).unsqueeze(0).to(self.device)
                    
                    # Generate embedding
                    with torch.no_grad():
                        embedding = self.model.encode_image(image_tensor)
                        embedding = embedding / embedding.norm(dim=-1, keepdim=True)  # Normalize
                    
                    embeddings.append({
                        'frame_id': frame.id,
                        'timestamp': frame.timestamp,
                        'embedding': embedding.cpu().numpy()
                    })
                    processed_count += 1
                    
                except Exception as e:
                    print(f"Error processing frame {frame.id}: {str(e)}")
                    continue
            
            # Save embeddings to file
            if embeddings:
                embeddings_file = embeddings_dir / "frame_embeddings.pkl"
                with open(embeddings_file, 'wb') as f:
                    pickle.dump(embeddings, f)
                
                print(f"Saved {len(embeddings)} embeddings to {embeddings_file}")
            
            return {
                "success": True,
                "processed": processed_count,
                "total_frames": len(frames),
                "embeddings_file": str(embeddings_file) if embeddings else None
            }
            
        except Exception as e:
            print(f"Error generating embeddings: {str(e)}")
            return {"error": str(e), "processed": 0}
    
    def search_visual_content(self, video_id: int, query: str, limit: int = 10):
        """Search frames using text query against visual embeddings."""
        try:
            self._load_clip_model()
            
            # Load embeddings
            embeddings_file = Path(f"storage/embeddings/video_{video_id}/frame_embeddings.pkl")
            if not embeddings_file.exists():
                return []
            
            with open(embeddings_file, 'rb') as f:
                embeddings_data = pickle.load(f)
            
            if not embeddings_data:
                return []
            
            # Generate query embedding
            text_tokens = self.tokenizer([query]).to(self.device)
            with torch.no_grad():
                text_embedding = self.model.encode_text(text_tokens)
                text_embedding = text_embedding / text_embedding.norm(dim=-1, keepdim=True)
            
            # Calculate similarities
            similarities = []
            for item in embeddings_data:
                frame_embedding = torch.from_numpy(item['embedding']).to(self.device)
                similarity = torch.cosine_similarity(text_embedding, frame_embedding).item()
                similarities.append({
                    'frame_id': item['frame_id'],
                    'timestamp': item['timestamp'],
                    'similarity': similarity
                })
            
            # Sort by similarity and return top results
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            results = similarities[:limit]
            
            # Get frame details from database
            detailed_results = []
            for result in results:
                frame = self.db.query(Frame).filter(Frame.id == result['frame_id']).first()
                if frame:
                    detailed_results.append({
                        'frame_id': frame.id,
                        'timestamp': frame.timestamp,
                        'path': frame.path,
                        'similarity': result['similarity']
                    })
            
            return detailed_results
            
        except Exception as e:
            print(f"Error in visual search: {str(e)}")
            return []
    
    def get_embeddings_status(self, video_id: int):
        """Check if embeddings exist for a video."""
        embeddings_file = Path(f"storage/embeddings/video_{video_id}/frame_embeddings.pkl")
        return {
            "video_id": video_id,
            "embeddings_exist": embeddings_file.exists(),
            "embeddings_file": str(embeddings_file) if embeddings_file.exists() else None
        } 