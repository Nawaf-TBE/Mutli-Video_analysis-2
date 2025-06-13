"""
REFACTORED: LangChain-based video analysis service now uses modular architecture.

This file now imports from the refactored service for backward compatibility.
The original 667-line monolithic service has been broken down into:

Modular Components:
- transcript/transcript_extractor.py (140 lines) - Video transcript extraction
- transcript/transcript_parser.py (90 lines) - Text parsing utilities  
- langchain/vector_store_manager.py (120 lines) - Vector store operations
- langchain/qa_manager.py (80 lines) - Q&A chain management
- langchain/section_generator.py (70 lines) - AI section generation
- langchain_service_refactored.py (50 lines) - Main orchestrator

Total: 550 lines across 6 focused modules (vs 667 lines in 1 file)
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from .langchain_service_refactored import LangChainVideoService as RefactoredLangChainVideoService

# For backward compatibility, export the refactored service with the same class name

class LangChainVideoService:
    """
    Backward-compatible wrapper for the refactored modular LangChain service.
    
    This maintains the same API as the original monolithic service while 
    using the new modular architecture underneath.
    """
    
    def __init__(self, db: Session):
        self.db = db
        # Use the refactored service internally
        self._service = RefactoredLangChainVideoService(db)
    
    def extract_video_id(self, url: str) -> str:
        """Extract YouTube video ID from URL."""
        return self._service.extract_video_id(url)
    
    def fetch_transcript(self, video_url: str) -> List[Dict[str, Any]]:
        """Fetch transcript using multiple methods with Gemini as primary."""
        return self._service.fetch_transcript(video_url)
    
    def process_transcript(self, video_id: int, video_url: str) -> Dict[str, Any]:
        """Process transcript and create vector store."""
        return self._service.process_transcript(video_id, video_url)
    
    def get_qa_chain(self, video_id: int) -> Optional[Any]:
        """Get QA chain for a video."""
        return self._service.get_qa_chain(video_id)
    
    def ask_question(self, video_id: int, question: str) -> Dict[str, Any]:
        """Ask a question about a video."""
        return self._service.ask_question(video_id, question)
    
    def generate_sections(self, video_id: int) -> List[Dict[str, Any]]:
        """Generate intelligent sections using LangChain."""
        return self._service.generate_sections(video_id)
    
    # Additional methods for backward compatibility with any specific implementations
    def analyze_video_with_gemini(self, video_url: str, video_id: str) -> List[Dict[str, Any]]:
        """Analyze video with Gemini (delegated to transcript extractor)."""
        return self._service.transcript_extractor.analyze_video_with_gemini(video_url, video_id)
    
    def parse_gemini_response(self, response_text: str) -> List[Dict[str, Any]]:
        """Parse Gemini response (delegated to transcript parser)."""
        from .transcript.transcript_parser import TranscriptParser
        parser = TranscriptParser()
        return parser.parse_gemini_response(response_text)
    
    def parse_timestamp_to_seconds(self, timestamp_str: str) -> float:
        """Convert timestamp to seconds (delegated to transcript parser)."""
        from .transcript.transcript_parser import TranscriptParser
        parser = TranscriptParser()
        return parser.parse_timestamp_to_seconds(timestamp_str)
    
    def extract_subtitles_with_ytdlp(self, video_url: str, video_id: str) -> List[Dict[str, Any]]:
        """Extract subtitles with yt-dlp (delegated to transcript extractor)."""
        return self._service.transcript_extractor.extract_subtitles_with_ytdlp(video_url, video_id)

    def parse_vtt_file(self, vtt_path: str) -> List[Dict[str, Any]]:
        """Parse VTT file (delegated to transcript parser)."""
        from .transcript.transcript_parser import TranscriptParser
        parser = TranscriptParser()
        return parser.parse_vtt_file(vtt_path)
    
    def parse_vtt_timestamp(self, timestamp: str) -> float:
        """Parse VTT timestamp (delegated to transcript parser)."""
        from .transcript.transcript_parser import TranscriptParser
        parser = TranscriptParser()
        return parser.parse_vtt_timestamp(timestamp)
    
    def generate_contextual_transcript(self, video_url: str, video_id: str) -> List[Dict[str, Any]]:
        """Generate contextual transcript (delegated to transcript extractor)."""
        return self._service.transcript_extractor.generate_contextual_transcript(video_url, video_id) 