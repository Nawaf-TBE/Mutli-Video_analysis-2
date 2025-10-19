"""
Q&A management for video content using LangChain.

This module provides a comprehensive Q&A system for video content analysis,
including transcript-based question answering with source citations and
configurable retrieval parameters.
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from functools import lru_cache

from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.schema import Document

from .vector_store_manager import VectorStoreManager

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class QAConfig:
    """Configuration for Q&A operations."""
    model_name: str = "gpt-4"
    temperature: float = 0.1
    max_tokens: Optional[int] = None
    retrieval_k: int = 3
    max_source_docs: int = 3
    chunk_size: int = 200


@dataclass
class QAResponse:
    """Structured response from Q&A operations."""
    success: bool
    answer: str
    sources: List[Dict[str, Any]]
    processing_time: Optional[float] = None
    error_message: Optional[str] = None


class QAManager:
    """
    Manages Q&A operations for video content.
    
    This class provides a comprehensive interface for asking questions about
    video content using LangChain's retrieval-augmented generation (RAG) approach.
    It handles vector store management, prompt engineering, and response formatting.
    """
    
    # Default prompt template for video Q&A
    DEFAULT_PROMPT_TEMPLATE = """You are a helpful AI assistant that analyzes video content based on transcripts. 
You have access to a video transcript and should answer questions about the video content.

Use the following pieces of context from the video transcript to answer the question. 
If you don't know the answer based on the transcript, just say you don't have enough information in the transcript to answer that question.

Context from video transcript:
{context}

Question: {question}

Answer based on the video content:"""
    
    def __init__(self, config: Optional[QAConfig] = None):
        """
        Initialize the Q&A manager.
        
        Args:
            config: Optional configuration object. If None, uses default settings.
        """
        self.config = config or QAConfig()
        self.vector_store_manager = VectorStoreManager()
        
        # Initialize LLM with configuration
        self._initialize_llm()
        
        logger.info(f"QAManager initialized with model: {self.config.model_name}")
    
    def _initialize_llm(self) -> None:
        """Initialize the language model with current configuration."""
        try:
            self.llm = ChatOpenAI(
                model_name=self.config.model_name,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            )
            logger.debug("LLM initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            raise RuntimeError(f"Failed to initialize language model: {e}")
    
    def _create_prompt_template(self) -> PromptTemplate:
        """Create the prompt template for video Q&A."""
        return PromptTemplate(
            template=self.DEFAULT_PROMPT_TEMPLATE,
            input_variables=["context", "question"]
        )
    
    @lru_cache(maxsize=32)
    def get_qa_chain(self, video_id: int) -> Optional[RetrievalQA]:
        """
        Get QA chain for a video with caching for performance.
        
        Args:
            video_id: The ID of the video to create a QA chain for.
            
        Returns:
            RetrievalQA chain if successful, None otherwise.
        """
        logger.debug(f"Creating QA chain for video {video_id}")
        
        try:
            vectorstore = self.vector_store_manager.load_vector_store(video_id)
            
            if not vectorstore:
                logger.warning(f"No vector store found for video {video_id}")
                return None
            
            # Create retriever with configured parameters
            retriever = vectorstore.as_retriever(
                search_kwargs={"k": self.config.retrieval_k}
            )
            
            # Create prompt template
            prompt_template = self._create_prompt_template()
            
            # Build QA chain with custom prompt
            qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=retriever,
                return_source_documents=True,
                chain_type_kwargs={"prompt": prompt_template}
            )
            
            logger.info(f"Successfully created QA chain for video {video_id}")
            return qa_chain
            
        except Exception as e:
            logger.error(f"Failed to create QA chain for video {video_id}: {e}")
            return None
    
    def ask_question(self, video_id: int, question: str) -> QAResponse:
        """
        Ask a question about a video.
        
        Args:
            video_id: The ID of the video to ask about.
            question: The question to ask.
            
        Returns:
            QAResponse object with the answer and sources.
        """
        import time
        start_time = time.time()
        
        logger.info(f"Processing question for video {video_id}: {question[:50]}...")
        
        # Validate inputs
        if not question or not question.strip():
            return QAResponse(
                success=False,
                answer="Please provide a valid question.",
                sources=[],
                error_message="Empty question provided"
            )
        
        # Get QA chain
        qa_chain = self.get_qa_chain(video_id)
        
        if not qa_chain:
            return QAResponse(
                success=False,
                answer="Sorry, I cannot answer questions about this video. The transcript may not be available or processed yet.",
                sources=[],
                error_message="No QA chain available for this video"
            )
        
        try:
            # Execute the question
            result = qa_chain({"query": question.strip()})
            
            answer = result["result"]
            source_documents = result.get("source_documents", [])
            
            logger.info(f"Found {len(source_documents)} source documents")
            
            # Format sources
            formatted_sources = self._format_sources(source_documents)
            
            processing_time = time.time() - start_time
            
            return QAResponse(
                success=True,
                answer=answer,
                sources=formatted_sources,
                processing_time=processing_time
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"Error answering question: {str(e)}"
            logger.error(error_msg)
            
            return QAResponse(
                success=False,
                answer=f"Sorry, I encountered an error: {str(e)}",
                sources=[],
                processing_time=processing_time,
                error_message=error_msg
            )
    
    def _format_sources(self, source_documents: List[Document]) -> List[Dict[str, Any]]:
        """
        Format source documents for response.
        
        Args:
            source_documents: List of source documents from retrieval.
            
        Returns:
            List of formatted source dictionaries.
        """
        formatted_sources = []
        
        for doc in source_documents[:self.config.max_source_docs]:
            metadata = doc.metadata
            content = doc.page_content
            
            # Truncate content if too long
            if len(content) > self.config.chunk_size:
                content = content[:self.config.chunk_size] + "..."
            
            # Extract timestamp information
            timestamp = metadata.get("timestamp", "00:00")
            start_time = metadata.get("start_time", metadata.get("approximate_start_time", 0))
            
            formatted_sources.append({
                "content": content,
                "timestamp": timestamp,
                "start_time": start_time,
                "video_id": metadata.get("video_id"),
                "source": metadata.get("source", "transcript")
            })
        
        return formatted_sources
    
    def ask_question_legacy(self, video_id: int, question: str) -> Dict[str, Any]:
        """
        Legacy method for backward compatibility.
        
        Args:
            video_id: The ID of the video to ask about.
            question: The question to ask.
            
        Returns:
            Dictionary with the response (legacy format).
        """
        response = self.ask_question(video_id, question)
        
        return {
            "success": response.success,
            "answer": response.answer,
            "sources": response.sources
        }
    
    def clear_cache(self) -> None:
        """Clear the QA chain cache."""
        self.get_qa_chain.cache_clear()
        logger.info("QA chain cache cleared")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about the QA chain cache."""
        cache_info = self.get_qa_chain.cache_info()
        return {
            "hits": cache_info.hits,
            "misses": cache_info.misses,
            "current_size": cache_info.currsize,
            "max_size": cache_info.maxsize
        }
    
    def update_config(self, new_config: QAConfig) -> None:
        """
        Update the configuration and reinitialize components.
        
        Args:
            new_config: New configuration object.
        """
        self.config = new_config
        self._initialize_llm()
        self.clear_cache()  # Clear cache when config changes
        logger.info("Configuration updated and cache cleared")
    
    def validate_video_availability(self, video_id: int) -> bool:
        """
        Check if a video is available for Q&A operations.
        
        Args:
            video_id: The ID of the video to check.
            
        Returns:
            True if video is available, False otherwise.
        """
        try:
            vectorstore = self.vector_store_manager.load_vector_store(video_id)
            return vectorstore is not None
        except Exception as e:
            logger.error(f"Error validating video {video_id}: {e}")
            return False 