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
└── langchain_service_refactored.py - Main orchestrator

Original monolithic service (667 lines) → Modular architecture (550 lines, 6 focused modules)
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

# Import the refactored service directly
from .langchain_service_refactored import LangChainVideoService as _LangChainVideoService


class LangChainVideoService(_LangChainVideoService):
    """
    Main LangChain video analysis service.
    
    Inherits from the refactored modular service, providing a clean API
    for video transcript processing, Q&A, and intelligent section generation.
    
    Key Features:
    - Multi-source transcript extraction (YouTube API, Gemini, yt-dlp fallback)
    - Vector embeddings with ChromaDB
    - RAG-based question answering
    - AI-powered video sectioning
    """
    
    def __init__(self, db: Session):
        """Initialize the service with database session."""
        super().__init__(db)
    
    # All core methods are inherited from _LangChainVideoService:
    # - extract_video_id(url)
    # - fetch_transcript(video_url)
    # - process_transcript(video_id, video_url)
    # - ask_question(video_id, question)
    # - generate_sections(video_id)
    # - get_qa_chain(video_id)
    # - check_video_processed(video_id)
    
    # Expose component-specific methods for advanced usage
    
    @property
    def transcript_extractor(self):
        """Access to the transcript extraction component."""
        return super().transcript_extractor
    
    @property
    def vector_store_manager(self):
        """Access to the vector store management component."""
        return super().vector_store_manager
    
    @property
    def qa_manager(self):
        """Access to the Q&A management component."""
        return super().qa_manager
    
    @property
    def section_generator(self):
        """Access to the section generation component."""
        return super().section_generator 