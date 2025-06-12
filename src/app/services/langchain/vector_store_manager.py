"""
Vector store management for LangChain operations.
"""

import os
import shutil
from pathlib import Path
from typing import List, Dict, Any
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.docstore.document import Document


class VectorStoreManager:
    """Manages vector stores for video transcripts."""
    
    def __init__(self):
        # Initialize LangChain components
        self.embeddings = OpenAIEmbeddings()
        
        # Text splitter for better chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
        )
    
    def process_transcript(self, video_id: int, segments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process transcript and create vector store."""
        
        if not segments:
            return {
                "success": False,
                "message": "No transcript available for this video",
                "segments_count": 0,
                "chunks_count": 0
            }
        
        # Create documents with metadata
        documents = []
        full_text_parts = []
        
        for segment in segments:
            text = segment["text"].strip()
            if not text:
                continue
                
            start_time = segment.get("start", 0)
            duration = segment.get("duration", 0)
            
            # Create document with rich metadata
            doc = Document(
                page_content=text,
                metadata={
                    "video_id": video_id,
                    "start_time": start_time,
                    "duration": duration,
                    "timestamp": f"{int(start_time//60):02d}:{int(start_time%60):02d}",
                    "source": "transcript"
                }
            )
            documents.append(doc)
            full_text_parts.append(text)
        
        # Split text for better retrieval
        full_text = " ".join(full_text_parts)
        chunks = self.text_splitter.split_text(full_text)
        
        # Create optimized documents from chunks
        chunk_docs = []
        for i, chunk in enumerate(chunks):
            # Try to find approximate timestamp for this chunk
            chunk_start = (i / len(chunks)) * segments[-1].get("start", 0) if segments else 0
            
            chunk_docs.append(Document(
                page_content=chunk,
                metadata={
                    "video_id": video_id,
                    "chunk_id": i,
                    "approximate_start_time": chunk_start,
                    "timestamp": f"{int(chunk_start//60):02d}:{int(chunk_start%60):02d}",
                    "source": "transcript_chunk"
                }
            ))
        
        # Create or update vector store
        chroma_dir = Path(f"storage/chroma/video_{video_id}")
        chroma_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Clear existing directory to avoid database conflicts
            if chroma_dir.exists():
                shutil.rmtree(chroma_dir)
                chroma_dir.mkdir(parents=True, exist_ok=True)
            
            vectorstore = Chroma.from_documents(
                documents=chunk_docs,
                embedding=self.embeddings,
                persist_directory=str(chroma_dir),
                collection_name="default_collection"
            )
            
            print(f"✅ Created vector store with {len(chunk_docs)} chunks")
            
        except Exception as e:
            print(f"❌ Failed to create vector store: {e}")
            return {
                "success": False,
                "message": f"Failed to create embeddings: {e}",
                "segments_count": len(segments),
                "chunks_count": 0
            }
        
        return {
            "success": True,
            "message": "Transcript processed successfully",
            "segments_count": len(segments),
            "chunks_count": len(chunk_docs),
            "vectorstore_path": str(chroma_dir)
        }
    
    def load_vector_store(self, video_id: int):
        """Load existing vector store for a video."""
        chroma_dir = Path(f"storage/chroma/video_{video_id}")
        
        if not chroma_dir.exists():
            print(f"❌ No vector store found for video {video_id}")
            return None
        
        try:
            # Load existing vector store with proper client settings
            vectorstore = Chroma(
                persist_directory=str(chroma_dir),
                embedding_function=self.embeddings,
                collection_name="default_collection"
            )
            
            return vectorstore
            
        except Exception as e:
            print(f"❌ Failed to load vector store: {e}")
            return None
    
    def check_vector_store_exists(self, video_id: int) -> bool:
        """Check if vector store exists for a video."""
        chroma_dir = Path(f"storage/chroma/video_{video_id}")
        return chroma_dir.exists() and any(chroma_dir.iterdir()) 