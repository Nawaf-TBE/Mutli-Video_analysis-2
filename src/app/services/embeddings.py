# Embedding generation
import os
import uuid
import numpy as np
from typing import List, Dict, Optional, Union, Any
from pathlib import Path

# Vector database
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct, Filter, FieldCondition, MatchValue

# Text embeddings
from sentence_transformers import SentenceTransformer
from openai import OpenAI

# Visual embeddings
import open_clip
import torch
from PIL import Image
import torchvision.transforms as transforms

# Database
from sqlalchemy.orm import Session
from ..models.video import Video
from ..models.section import Section
from ..models.frame import Frame

class EmbeddingService:
    def __init__(self, db: Session):
        self.db = db
        
        # Qdrant client
        self.qdrant_client = QdrantClient(
            host=os.getenv("QDRANT_HOST", "localhost"),
            port=int(os.getenv("QDRANT_PORT", "6333")),
            api_key=os.getenv("QDRANT_API_KEY")
        )
        
        # Text embedding models
        self.sentence_transformer = SentenceTransformer('all-MiniLM-L6-v2')
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) if os.getenv("OPENAI_API_KEY") else None
        
        # Visual embedding model (CLIP)
        self.clip_model = None
        self.clip_preprocess = None
        self.clip_tokenizer = None
        self._load_clip_model()
        
        # Collection names
        self.text_collection = "text_embeddings"
        self.visual_collection = "visual_embeddings"
        
        # Initialize collections
        self._initialize_collections()

    def _load_clip_model(self):
        """Load CLIP model for visual embeddings."""
        try:
            self.clip_model, _, self.clip_preprocess = open_clip.create_model_and_transforms('ViT-B-32', pretrained='openai')
            self.clip_tokenizer = open_clip.get_tokenizer('ViT-B-32')
            self.clip_model.eval()
            print("CLIP model loaded successfully")
        except Exception as e:
            print(f"Warning: Failed to load CLIP model: {e}")

    def _initialize_collections(self):
        """Initialize Qdrant collections for embeddings."""
        try:
            # Text embeddings collection (384 dimensions for all-MiniLM-L6-v2)
            collections = self.qdrant_client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self.text_collection not in collection_names:
                self.qdrant_client.create_collection(
                    collection_name=self.text_collection,
                    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
                )
                print(f"Created collection: {self.text_collection}")
            
            # Visual embeddings collection (512 dimensions for CLIP ViT-B-32)
            if self.visual_collection not in collection_names:
                self.qdrant_client.create_collection(
                    collection_name=self.visual_collection,
                    vectors_config=VectorParams(size=512, distance=Distance.COSINE)
                )
                print(f"Created collection: {self.visual_collection}")
                
        except Exception as e:
            print(f"Warning: Failed to initialize Qdrant collections: {e}")

    def generate_text_embedding(self, text: str, model: str = "sentence_transformer") -> List[float]:
        """
        Generate text embeddings using different models.
        
        Args:
            text: Input text
            model: 'sentence_transformer' or 'openai'
        """
        try:
            if model == "openai" and self.openai_client:
                response = self.openai_client.embeddings.create(
                    input=text,
                    model="text-embedding-ada-002"
                )
                return response.data[0].embedding
            else:
                # Default to sentence transformer
                embedding = self.sentence_transformer.encode(text)
                return embedding.tolist()
        except Exception as e:
            raise Exception(f"Error generating text embedding: {str(e)}")

    def generate_visual_embedding(self, image_path: str) -> List[float]:
        """
        Generate visual embeddings using CLIP.
        
        Args:
            image_path: Path to the image file
        """
        try:
            if not self.clip_model:
                raise Exception("CLIP model not loaded")
            
            # Load and preprocess image
            image = Image.open(image_path).convert('RGB')
            image_input = self.clip_preprocess(image).unsqueeze(0)
            
            # Generate embedding
            with torch.no_grad():
                image_features = self.clip_model.encode_image(image_input)
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
                
            return image_features.squeeze().numpy().tolist()
            
        except Exception as e:
            raise Exception(f"Error generating visual embedding: {str(e)}")

    def store_text_embedding(self, 
                           text: str, 
                           video_id: int,
                           section_id: Optional[int] = None,
                           metadata: Optional[Dict] = None) -> str:
        """
        Store text embedding in Qdrant.
        
        Args:
            text: The text content
            video_id: Associated video ID
            section_id: Associated section ID (optional)
            metadata: Additional metadata
            
        Returns:
            Point ID in Qdrant
        """
        try:
            # Generate embedding
            embedding = self.generate_text_embedding(text)
            
            # Prepare metadata
            point_metadata = {
                "video_id": video_id,
                "text": text[:500],  # Truncate for storage
                "type": "text",
                "created_at": str(np.datetime64('now'))
            }
            
            if section_id:
                point_metadata["section_id"] = section_id
            
            if metadata:
                point_metadata.update(metadata)
            
            # Generate unique point ID
            point_id = str(uuid.uuid4())
            
            # Store in Qdrant
            self.qdrant_client.upsert(
                collection_name=self.text_collection,
                points=[
                    PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload=point_metadata
                    )
                ]
            )
            
            return point_id
            
        except Exception as e:
            raise Exception(f"Error storing text embedding: {str(e)}")

    def store_visual_embedding(self,
                             image_path: str,
                             video_id: int,
                             frame_id: Optional[int] = None,
                             timestamp: Optional[float] = None,
                             metadata: Optional[Dict] = None) -> str:
        """
        Store visual embedding in Qdrant.
        
        Args:
            image_path: Path to the image file
            video_id: Associated video ID
            frame_id: Associated frame ID (optional)
            timestamp: Frame timestamp (optional)
            metadata: Additional metadata
            
        Returns:
            Point ID in Qdrant
        """
        try:
            # Generate embedding
            embedding = self.generate_visual_embedding(image_path)
            
            # Prepare metadata
            point_metadata = {
                "video_id": video_id,
                "image_path": image_path,
                "type": "visual",
                "created_at": str(np.datetime64('now'))
            }
            
            if frame_id:
                point_metadata["frame_id"] = frame_id
                
            if timestamp is not None:
                point_metadata["timestamp"] = timestamp
            
            if metadata:
                point_metadata.update(metadata)
            
            # Generate unique point ID
            point_id = str(uuid.uuid4())
            
            # Store in Qdrant
            self.qdrant_client.upsert(
                collection_name=self.visual_collection,
                points=[
                    PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload=point_metadata
                    )
                ]
            )
            
            return point_id
            
        except Exception as e:
            raise Exception(f"Error storing visual embedding: {str(e)}")

    def process_video_text_embeddings(self, video_id: int) -> List[str]:
        """
        Process all text content for a video and generate embeddings.
        
        Args:
            video_id: Video ID to process
            
        Returns:
            List of point IDs created in Qdrant
        """
        try:
            point_ids = []
            
            # Get video sections
            sections = self.db.query(Section).filter(Section.video_id == video_id).all()
            
            for section in sections:
                # Create embedding for section title
                if section.title:
                    point_id = self.store_text_embedding(
                        text=section.title,
                        video_id=video_id,
                        section_id=section.id,
                        metadata={
                            "content_type": "section_title",
                            "start_time": section.start_time,
                            "end_time": section.end_time
                        }
                    )
                    point_ids.append(point_id)
            
            return point_ids
            
        except Exception as e:
            raise Exception(f"Error processing video text embeddings: {str(e)}")

    def process_video_visual_embeddings(self, video_id: int) -> List[str]:
        """
        Process all frames for a video and generate visual embeddings.
        
        Args:
            video_id: Video ID to process
            
        Returns:
            List of point IDs created in Qdrant
        """
        try:
            point_ids = []
            
            # Get video frames
            frames = self.db.query(Frame).filter(Frame.video_id == video_id).all()
            
            for frame in frames:
                if os.path.exists(frame.path):
                    point_id = self.store_visual_embedding(
                        image_path=frame.path,
                        video_id=video_id,
                        frame_id=frame.id,
                        timestamp=frame.timestamp,
                        metadata={
                            "content_type": "video_frame"
                        }
                    )
                    point_ids.append(point_id)
            
            return point_ids
            
        except Exception as e:
            raise Exception(f"Error processing video visual embeddings: {str(e)}")

    def search_text_embeddings(self, 
                             query: str, 
                             video_id: Optional[int] = None,
                             limit: int = 10) -> List[Dict]:
        """
        Search for similar text embeddings.
        
        Args:
            query: Search query
            video_id: Filter by video ID (optional)
            limit: Number of results to return
            
        Returns:
            List of similar text results
        """
        try:
            # Generate query embedding
            query_embedding = self.generate_text_embedding(query)
            
            # Prepare filter
            query_filter = None
            if video_id:
                query_filter = Filter(
                    must=[FieldCondition(key="video_id", match=MatchValue(value=video_id))]
                )
            
            # Search
            results = self.qdrant_client.search(
                collection_name=self.text_collection,
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
            raise Exception(f"Error searching text embeddings: {str(e)}")

    def search_visual_embeddings(self,
                                image_path: str,
                                video_id: Optional[int] = None,
                                limit: int = 10) -> List[Dict]:
        """
        Search for similar visual embeddings.
        
        Args:
            image_path: Path to query image
            video_id: Filter by video ID (optional)
            limit: Number of results to return
            
        Returns:
            List of similar visual results
        """
        try:
            # Generate query embedding
            query_embedding = self.generate_visual_embedding(image_path)
            
            # Prepare filter
            query_filter = None
            if video_id:
                query_filter = Filter(
                    must=[FieldCondition(key="video_id", match=MatchValue(value=video_id))]
                )
            
            # Search
            results = self.qdrant_client.search(
                collection_name=self.visual_collection,
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
            raise Exception(f"Error searching visual embeddings: {str(e)}")

    def delete_video_embeddings(self, video_id: int):
        """Delete all embeddings for a specific video."""
        try:
            # Delete text embeddings
            self.qdrant_client.delete(
                collection_name=self.text_collection,
                points_selector=Filter(
                    must=[FieldCondition(key="video_id", match=MatchValue(value=video_id))]
                )
            )
            
            # Delete visual embeddings
            self.qdrant_client.delete(
                collection_name=self.visual_collection,
                points_selector=Filter(
                    must=[FieldCondition(key="video_id", match=MatchValue(value=video_id))]
                )
            )
            
        except Exception as e:
            raise Exception(f"Error deleting video embeddings: {str(e)}") 