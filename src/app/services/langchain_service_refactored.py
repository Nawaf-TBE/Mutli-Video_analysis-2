"""
Refactored LangChain-based video analysis service using modular components.
"""

from typing import List, Dict, Any
from sqlalchemy.orm import Session
from .transcript.transcript_extractor import TranscriptExtractor
from .langchain.vector_store_manager import VectorStoreManager
from .langchain.qa_manager import QAManager
from .langchain.section_generator import SectionGenerator


class LangChainVideoService:
    """
    Simplified video analysis using LangChain with modular architecture.
    
    This service orchestrates multiple specialized components:
    - TranscriptExtractor: Handles video transcript extraction from multiple sources
    - VectorStoreManager: Manages LangChain vector stores and document processing  
    - QAManager: Handles question answering and retrieval chains
    - SectionGenerator: Generates intelligent video sections using AI
    """
    
    def __init__(self, db: Session):
        self.db = db
        
        # Initialize modular components
        self.transcript_extractor = TranscriptExtractor()
        self.vector_store_manager = VectorStoreManager()
        self.qa_manager = QAManager()
        self.section_generator = SectionGenerator()
        
        print("✅ LangChain Video Service initialized with modular architecture")
    
    def extract_video_id(self, url: str) -> str:
        """Extract YouTube video ID from URL."""
        return self.transcript_extractor.extract_video_id(url)
    
    def fetch_transcript(self, video_url: str) -> List[Dict[str, Any]]:
        """Fetch transcript using multiple methods with Gemini as primary."""
        return self.transcript_extractor.fetch_transcript(video_url)
    
    def process_transcript(self, video_id: int, video_url: str) -> Dict[str, Any]:
        """Process transcript and create vector store."""
        
        # 1. Fetch transcript using the transcript extractor
        segments = self.transcript_extractor.fetch_transcript(video_url)
        
        # 2. Process transcript and create vector store
        return self.vector_store_manager.process_transcript(video_id, segments)
    
    def ask_question(self, video_id: int, question: str) -> Dict[str, Any]:
        """Ask a question about a video."""
        return self.qa_manager.ask_question(video_id, question)
    
    def generate_sections(self, video_id: int) -> List[Dict[str, Any]]:
        """Generate intelligent sections using LangChain."""
        return self.section_generator.generate_sections(video_id)
    
    def get_qa_chain(self, video_id: int):
        """Get QA chain for a video (for backward compatibility)."""
        return self.qa_manager.get_qa_chain(video_id)
    
    def check_video_processed(self, video_id: int) -> bool:
        """Check if video has been processed and vector store exists."""
        return self.vector_store_manager.check_vector_store_exists(video_id) 