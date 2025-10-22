"""
LangChain-based video analysis service with modular architecture.

This service orchestrates specialized components for:
- Video transcript extraction (YouTube, Gemini, yt-dlp)
- Vector store management (ChromaDB + LangChain)
- Question answering (RAG with GPT)
- Intelligent section generation

Architecture:
├── transcript/
│   ├── transcript_extractor.py - Multi-source transcript extraction
│   └── transcript_parser.py - Text parsing utilities
├── langchain/
│   ├── vector_store_manager.py - Vector store operations
│   ├── qa_manager.py - Q&A chain management
│   └── section_generator.py - AI section generation
└── langchain_service.py - Main orchestrator (this file)

Refactored from monolithic service (667 lines) → Modular architecture (6 focused modules)
"""

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from .transcript.transcript_extractor import TranscriptExtractor
from .langchain.vector_store_manager import VectorStoreManager
from .langchain.qa_manager import QAManager
from .langchain.section_generator import SectionGenerator

# Configure logging
logger = logging.getLogger(__name__)


class LangChainVideoService:
    """
    Main LangChain video analysis service with modular architecture.
    
    This service orchestrates multiple specialized components:
    - TranscriptExtractor: Handles video transcript extraction from multiple sources
    - VectorStoreManager: Manages LangChain vector stores and document processing  
    - QAManager: Handles question answering and retrieval chains
    - SectionGenerator: Generates intelligent video sections using AI
    
    Key Features:
    - Multi-source transcript extraction (YouTube API, Gemini, yt-dlp fallback)
    - Vector embeddings with ChromaDB
    - RAG-based question answering
    - AI-powered video sectioning
    """
    
    def __init__(self, db: Session):
        """
        Initialize the service with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        
        # Initialize modular components
        try:
            self.transcript_extractor = TranscriptExtractor()
            self.vector_store_manager = VectorStoreManager()
            self.qa_manager = QAManager()
            self.section_generator = SectionGenerator()
            
            logger.info("✅ LangChain Video Service initialized with modular architecture")
        except Exception as e:
            logger.error(f"❌ Failed to initialize LangChain Video Service: {e}")
            raise RuntimeError(f"Failed to initialize LangChain Video Service: {e}")
    
    def extract_video_id(self, url: str) -> str:
        """
        Extract YouTube video ID from URL.
        
        Args:
            url: YouTube video URL
            
        Returns:
            Video ID string
            
        Raises:
            ValueError: If video ID cannot be extracted
        """
        try:
            return self.transcript_extractor.extract_video_id(url)
        except Exception as e:
            logger.error(f"Failed to extract video ID from URL {url}: {e}")
            raise
    
    def fetch_transcript(self, video_url: str) -> List[Dict[str, Any]]:
        """
        Fetch transcript using multiple methods with Gemini as primary.
        
        Args:
            video_url: YouTube video URL
            
        Returns:
            List of transcript segments
            
        Raises:
            RuntimeError: If transcript extraction fails
        """
        try:
            logger.info(f"Fetching transcript for video: {video_url}")
            return self.transcript_extractor.fetch_transcript(video_url)
        except Exception as e:
            logger.error(f"Failed to fetch transcript for {video_url}: {e}")
            raise RuntimeError(f"Failed to fetch transcript: {e}")
    
    def process_transcript(self, video_id: int, video_url: str) -> Dict[str, Any]:
        """
        Process transcript and create vector store.
        
        Args:
            video_id: Database video ID
            video_url: YouTube video URL
            
        Returns:
            Processing result dictionary
            
        Raises:
            RuntimeError: If processing fails
        """
        try:
            logger.info(f"Processing transcript for video {video_id}")
            
            # 1. Fetch transcript using the transcript extractor
            segments = self.transcript_extractor.fetch_transcript(video_url)
            
            # 2. Process transcript and create vector store
            result = self.vector_store_manager.process_transcript(video_id, segments)
            
            logger.info(f"Successfully processed transcript for video {video_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to process transcript for video {video_id}: {e}")
            raise RuntimeError(f"Failed to process transcript: {e}")
    
    def ask_question(self, video_id: int, question: str) -> Dict[str, Any]:
        """
        Ask a question about a video.
        
        Args:
            video_id: Database video ID
            question: Question to ask about the video
            
        Returns:
            Q&A response dictionary
            
        Raises:
            RuntimeError: If question answering fails
        """
        try:
            logger.info(f"Processing question for video {video_id}: {question[:50]}...")
            return self.qa_manager.ask_question(video_id, question)
        except Exception as e:
            logger.error(f"Failed to answer question for video {video_id}: {e}")
            raise RuntimeError(f"Failed to answer question: {e}")
    
    def generate_sections(self, video_id: int) -> List[Dict[str, Any]]:
        """
        Generate intelligent sections using LangChain.
        
        Args:
            video_id: Database video ID
            
        Returns:
            List of generated sections
            
        Raises:
            RuntimeError: If section generation fails
        """
        try:
            logger.info(f"Generating sections for video {video_id}")
            return self.section_generator.generate_sections(video_id)
        except Exception as e:
            logger.error(f"Failed to generate sections for video {video_id}: {e}")
            raise RuntimeError(f"Failed to generate sections: {e}")
    
    def get_qa_chain(self, video_id: int):
        """
        Get QA chain for a video (for backward compatibility).
        
        Args:
            video_id: Database video ID
            
        Returns:
            QA chain object
            
        Raises:
            RuntimeError: If QA chain creation fails
        """
        try:
            return self.qa_manager.get_qa_chain(video_id)
        except Exception as e:
            logger.error(f"Failed to get QA chain for video {video_id}: {e}")
            raise RuntimeError(f"Failed to get QA chain: {e}")
    
    def check_video_processed(self, video_id: int) -> bool:
        """
        Check if video has been processed and vector store exists.
        
        Args:
            video_id: Database video ID
            
        Returns:
            True if video is processed, False otherwise
        """
        try:
            return self.vector_store_manager.check_vector_store_exists(video_id)
        except Exception as e:
            logger.error(f"Failed to check processing status for video {video_id}: {e}")
            return False
    