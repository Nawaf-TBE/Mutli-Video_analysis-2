"""
Vector store management for LangChain operations.

This module provides comprehensive vector store management for video transcripts,
including document processing, chunking strategies, and ChromaDB integration.
"""

import os
import shutil
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.docstore.document import Document

# Configure logging
logger = logging.getLogger(__name__)


class ChunkingStrategy(Enum):
    """Strategies for text chunking."""
    RECURSIVE = "recursive"
    SENTENCE = "sentence"
    PARAGRAPH = "paragraph"


@dataclass
class VectorStoreConfig:
    """Configuration for vector store operations."""
    chunk_size: int = 1000
    chunk_overlap: int = 100
    chunking_strategy: ChunkingStrategy = ChunkingStrategy.RECURSIVE
    collection_name: str = "default_collection"
    storage_base_path: str = "storage/chroma"
    separators: List[str] = None
    min_chunk_size: int = 50
    max_chunk_size: int = 2000
    
    def __post_init__(self):
        if self.separators is None:
            self.separators = ["\n\n", "\n", ".", "!", "?", ",", " ", ""]


@dataclass
class ProcessingResult:
    """Result of transcript processing."""
    success: bool
    message: str
    video_id: int
    segments_count: int
    chunks_count: int
    vectorstore_path: Optional[str] = None
    processing_time: Optional[float] = None
    error_message: Optional[str] = None


@dataclass
class DocumentMetadata:
    """Standardized document metadata."""
    video_id: int
    start_time: float
    duration: float
    timestamp: str
    source: str
    chunk_id: Optional[int] = None
    approximate_start_time: Optional[float] = None


class VectorStoreManager:
    """
    Manages vector stores for video transcripts.
    
    This class provides comprehensive vector store management including
    document processing, chunking strategies, and ChromaDB integration.
    """
    
    def __init__(self, config: Optional[VectorStoreConfig] = None):
        """
        Initialize the vector store manager.
        
        Args:
            config: Optional configuration object. If None, uses default settings.
        """
        self.config = config or VectorStoreConfig()
        
        # Initialize components
        self._initialize_embeddings()
        self._initialize_text_splitter()
        
        logger.info(f"VectorStoreManager initialized with strategy: {self.config.chunking_strategy.value}")
    
    def _initialize_embeddings(self) -> None:
        """Initialize the embeddings model."""
        try:
            self.embeddings = OpenAIEmbeddings()
            logger.debug("Embeddings initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize embeddings: {e}")
            raise RuntimeError(f"Failed to initialize embeddings: {e}")
    
    def _initialize_text_splitter(self) -> None:
        """Initialize the text splitter based on configuration."""
        try:
            if self.config.chunking_strategy == ChunkingStrategy.RECURSIVE:
                self.text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=self.config.chunk_size,
                    chunk_overlap=self.config.chunk_overlap,
                    separators=self.config.separators
                )
            else:
                # Default to recursive for now, can be extended
                self.text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=self.config.chunk_size,
                    chunk_overlap=self.config.chunk_overlap,
                    separators=self.config.separators
                )
            
            logger.debug("Text splitter initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize text splitter: {e}")
            raise RuntimeError(f"Failed to initialize text splitter: {e}")
    
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