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
    
    def process_transcript(self, video_id: int, segments: List[Dict[str, Any]]) -> ProcessingResult:
        """
        Process transcript and create vector store.
        
        Args:
            video_id: The ID of the video to process.
            segments: List of transcript segments with text and timing information.
            
        Returns:
            ProcessingResult with processing status and metadata.
        """
        import time
        start_time = time.time()
        
        logger.info(f"Processing transcript for video {video_id} with {len(segments)} segments")
        
        # Validate inputs
        if not segments:
            return ProcessingResult(
                success=False,
                message="No transcript available for this video",
                video_id=video_id,
                segments_count=0,
                chunks_count=0,
                processing_time=time.time() - start_time,
                error_message="Empty segments list"
            )
        
        try:
            # Process segments into documents
            documents = self._create_documents_from_segments(video_id, segments)
            if not documents:
                return ProcessingResult(
                    success=False,
                    message="No valid text found in segments",
                    video_id=video_id,
                    segments_count=len(segments),
                    chunks_count=0,
                    processing_time=time.time() - start_time,
                    error_message="No valid text content"
                )
            
            # Create chunks from documents
            chunk_docs = self._create_chunks_from_documents(video_id, documents)
            if not chunk_docs:
                return ProcessingResult(
                    success=False,
                    message="Failed to create chunks from documents",
                    video_id=video_id,
                    segments_count=len(segments),
                    chunks_count=0,
                    processing_time=time.time() - start_time,
                    error_message="Chunking failed"
                )
            
            # Create vector store
            vectorstore_path = self._create_vector_store(video_id, chunk_docs)
            if not vectorstore_path:
                return ProcessingResult(
                    success=False,
                    message="Failed to create vector store",
                    video_id=video_id,
                    segments_count=len(segments),
                    chunks_count=len(chunk_docs),
                    processing_time=time.time() - start_time,
                    error_message="Vector store creation failed"
                )
            
            processing_time = time.time() - start_time
            logger.info(f"Successfully processed video {video_id} in {processing_time:.2f}s")
            
            return ProcessingResult(
                success=True,
                message="Transcript processed successfully",
                video_id=video_id,
                segments_count=len(segments),
                chunks_count=len(chunk_docs),
                vectorstore_path=vectorstore_path,
                processing_time=processing_time
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"Error processing transcript: {str(e)}"
            logger.error(error_msg)
            
            return ProcessingResult(
                success=False,
                message="Failed to process transcript",
                video_id=video_id,
                segments_count=len(segments),
                chunks_count=0,
                processing_time=processing_time,
                error_message=error_msg
            )
    
    def _create_documents_from_segments(self, video_id: int, segments: List[Dict[str, Any]]) -> List[Document]:
        """Create documents from transcript segments."""
        documents = []
        
        for segment in segments:
            text = segment.get("text", "").strip()
            if not text:
                continue
            
            start_time = segment.get("start", 0)
            duration = segment.get("duration", 0)
            
            # Create document with rich metadata
            metadata = DocumentMetadata(
                video_id=video_id,
                start_time=start_time,
                duration=duration,
                timestamp=self._format_timestamp(start_time),
                source="transcript"
            )
            
            doc = Document(
                page_content=text,
                metadata=metadata.__dict__
            )
            documents.append(doc)
        
        logger.debug(f"Created {len(documents)} documents from segments")
        return documents
    
    def _create_chunks_from_documents(self, video_id: int, documents: List[Document]) -> List[Document]:
        """Create chunks from documents using the configured text splitter."""
        if not documents:
            return []
        
        # Extract text content
        full_text_parts = [doc.page_content for doc in documents]
        full_text = " ".join(full_text_parts)
        
        # Split into chunks
        chunks = self.text_splitter.split_text(full_text)
        
        # Create chunk documents with metadata
        chunk_docs = []
        total_segments = len(documents)
        
        for i, chunk in enumerate(chunks):
            # Calculate approximate timestamp for this chunk
            chunk_start = self._calculate_chunk_timestamp(i, len(chunks), documents)
            
            metadata = DocumentMetadata(
                video_id=video_id,
                start_time=chunk_start,
                duration=0,  # Will be calculated if needed
                timestamp=self._format_timestamp(chunk_start),
                source="transcript_chunk",
                chunk_id=i,
                approximate_start_time=chunk_start
            )
            
            chunk_doc = Document(
                page_content=chunk,
                metadata=metadata.__dict__
            )
            chunk_docs.append(chunk_doc)
        
        logger.debug(f"Created {len(chunk_docs)} chunks from {len(documents)} documents")
        return chunk_docs
    
    def _calculate_chunk_timestamp(self, chunk_index: int, total_chunks: int, documents: List[Document]) -> float:
        """Calculate approximate timestamp for a chunk."""
        if not documents:
            return 0.0
        
        # Simple linear interpolation based on chunk position
        total_duration = documents[-1].metadata.get("start_time", 0) + documents[-1].metadata.get("duration", 0)
        return (chunk_index / total_chunks) * total_duration
    
    def _format_timestamp(self, seconds: float) -> str:
        """Format seconds into MM:SS timestamp."""
        minutes = int(seconds // 60)
        seconds_remainder = int(seconds % 60)
        return f"{minutes:02d}:{seconds_remainder:02d}"
    
    def _create_vector_store(self, video_id: int, documents: List[Document]) -> Optional[str]:
        """Create or update vector store for a video."""
        chroma_dir = Path(self.config.storage_base_path) / f"video_{video_id}"
        
        try:
            # Ensure directory exists
            chroma_dir.mkdir(parents=True, exist_ok=True)
            
            # Clear existing directory to avoid conflicts
            if chroma_dir.exists():
                shutil.rmtree(chroma_dir)
                chroma_dir.mkdir(parents=True, exist_ok=True)
            
            # Create vector store
            vectorstore = Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings,
                persist_directory=str(chroma_dir),
                collection_name=self.config.collection_name
            )
            
            logger.info(f"Created vector store with {len(documents)} documents at {chroma_dir}")
            return str(chroma_dir)
            
        except Exception as e:
            logger.error(f"Failed to create vector store: {e}")
            return None
    
    def load_vector_store(self, video_id: int) -> Optional[Chroma]:
        """
        Load existing vector store for a video.
        
        Args:
            video_id: The ID of the video to load vector store for.
            
        Returns:
            Chroma vector store if successful, None otherwise.
        """
        chroma_dir = Path(self.config.storage_base_path) / f"video_{video_id}"
        
        if not chroma_dir.exists():
            logger.warning(f"No vector store found for video {video_id}")
            return None
        
        try:
            # Load existing vector store
            vectorstore = Chroma(
                persist_directory=str(chroma_dir),
                embedding_function=self.embeddings,
                collection_name=self.config.collection_name
            )
            
            logger.info(f"Successfully loaded vector store for video {video_id}")
            return vectorstore
            
        except Exception as e:
            logger.error(f"Failed to load vector store for video {video_id}: {e}")
            return None
    
    def check_vector_store_exists(self, video_id: int) -> bool:
        """
        Check if vector store exists for a video.
        
        Args:
            video_id: The ID of the video to check.
            
        Returns:
            True if vector store exists and is not empty, False otherwise.
        """
        chroma_dir = Path(self.config.storage_base_path) / f"video_{video_id}"
        return chroma_dir.exists() and any(chroma_dir.iterdir())
    
    def get_vector_store_info(self, video_id: int) -> Dict[str, Any]:
        """
        Get information about a vector store.
        
        Args:
            video_id: The ID of the video to get info for.
            
        Returns:
            Dictionary with vector store information.
        """
        chroma_dir = Path(self.config.storage_base_path) / f"video_{video_id}"
        
        if not chroma_dir.exists():
            return {
                "exists": False,
                "path": str(chroma_dir),
                "size": 0,
                "files": []
            }
        
        try:
            # Get directory size and file list
            total_size = sum(f.stat().st_size for f in chroma_dir.rglob('*') if f.is_file())
            files = [f.name for f in chroma_dir.iterdir() if f.is_file()]
            
            return {
                "exists": True,
                "path": str(chroma_dir),
                "size": total_size,
                "files": files,
                "collection_name": self.config.collection_name
            }
            
        except Exception as e:
            logger.error(f"Error getting vector store info for video {video_id}: {e}")
            return {
                "exists": False,
                "path": str(chroma_dir),
                "error": str(e)
            }
    
    def delete_vector_store(self, video_id: int) -> bool:
        """
        Delete vector store for a video.
        
        Args:
            video_id: The ID of the video to delete vector store for.
            
        Returns:
            True if deletion was successful, False otherwise.
        """
        chroma_dir = Path(self.config.storage_base_path) / f"video_{video_id}"
        
        if not chroma_dir.exists():
            logger.warning(f"Vector store for video {video_id} does not exist")
            return True
        
        try:
            shutil.rmtree(chroma_dir)
            logger.info(f"Successfully deleted vector store for video {video_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete vector store for video {video_id}: {e}")
            return False
    
    def list_vector_stores(self) -> List[Dict[str, Any]]:
        """
        List all available vector stores.
        
        Returns:
            List of dictionaries with vector store information.
        """
        storage_path = Path(self.config.storage_base_path)
        
        if not storage_path.exists():
            return []
        
        vector_stores = []
        
        for video_dir in storage_path.iterdir():
            if video_dir.is_dir() and video_dir.name.startswith("video_"):
                try:
                    video_id = int(video_dir.name.split("_")[1])
                    info = self.get_vector_store_info(video_id)
                    info["video_id"] = video_id
                    vector_stores.append(info)
                except (ValueError, IndexError):
                    continue
        
        return vector_stores
    
    def update_config(self, new_config: VectorStoreConfig) -> None:
        """
        Update the configuration and reinitialize components.
        
        Args:
            new_config: New configuration object.
        """
        self.config = new_config
        self._initialize_embeddings()
        self._initialize_text_splitter()
        logger.info("VectorStoreManager configuration updated")
    
    def validate_segments(self, segments: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
        """
        Validate transcript segments for processing.
        
        Args:
            segments: List of segments to validate.
            
        Returns:
            Tuple of (is_valid, list_of_issues).
        """
        issues = []
        
        if not segments:
            issues.append("No segments provided")
            return False, issues
        
        for i, segment in enumerate(segments):
            if not isinstance(segment, dict):
                issues.append(f"Segment {i} is not a dictionary")
                continue
            
            if "text" not in segment:
                issues.append(f"Segment {i} missing 'text' field")
            elif not segment["text"] or not segment["text"].strip():
                issues.append(f"Segment {i} has empty text")
            
            if "start" not in segment:
                issues.append(f"Segment {i} missing 'start' field")
            elif not isinstance(segment["start"], (int, float)):
                issues.append(f"Segment {i} 'start' field is not numeric")
        
        return len(issues) == 0, issues
    
    def process_transcript_legacy(self, video_id: int, segments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Legacy method for backward compatibility.
        
        Args:
            video_id: The ID of the video to process.
            segments: List of transcript segments.
            
        Returns:
            Dictionary with the result (legacy format).
        """
        result = self.process_transcript(video_id, segments)
        
        return {
            "success": result.success,
            "message": result.message,
            "segments_count": result.segments_count,
            "chunks_count": result.chunks_count,
            "vectorstore_path": result.vectorstore_path
        } 