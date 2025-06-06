# Chat with video logic
import os
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime

# LLM integration
from openai import OpenAI

# Database and services
from sqlalchemy.orm import Session
from ..models.video import Video
from ..models.section import Section
from ..models.frame import Frame
from .embeddings import EmbeddingService

@dataclass
class ChatMessage:
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime
    metadata: Optional[Dict] = None

@dataclass
class RetrievalContext:
    text_results: List[Dict]
    visual_results: List[Dict]
    combined_score: float
    video_info: Dict

@dataclass
class ChatResponse:
    response: str
    citations: List[Dict]
    context_used: RetrievalContext
    conversation_id: str

class RAGChatService:
    def __init__(self, db: Session):
        self.db = db
        self.embedding_service = EmbeddingService(db)
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Chat configuration
        self.max_context_length = 8000
        self.text_search_limit = 5
        self.visual_search_limit = 3
        self.relevance_threshold = 0.7
        
        # Conversation memory (in-memory for now)
        self.conversations: Dict[str, List[ChatMessage]] = {}

    def format_timestamp(self, seconds: float) -> str:
        """Convert seconds to MM:SS format."""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"

    def get_video_info(self, video_id: int) -> Dict:
        """Get basic video information."""
        video = self.db.query(Video).filter(Video.id == video_id).first()
        if not video:
            raise ValueError(f"Video {video_id} not found")
        
        return {
            "id": video.id,
            "title": video.title,
            "url": video.url,
            "created_at": video.created_at.isoformat() if video.created_at else None
        }

    def retrieve_relevant_context(self, 
                                 query: str, 
                                 video_id: int,
                                 include_visual: bool = True) -> RetrievalContext:
        """
        Retrieve relevant context from both text and visual embeddings.
        """
        try:
            # Search text embeddings
            text_results = self.embedding_service.search_text_embeddings(
                query=query,
                video_id=video_id,
                limit=self.text_search_limit
            )
            
            # Filter by relevance threshold
            text_results = [
                result for result in text_results 
                if result['score'] >= self.relevance_threshold
            ]
            
            visual_results = []
            if include_visual:
                # For text queries on visual content, we could use CLIP's text encoder
                # For now, we'll skip visual search unless specifically requested
                pass
            
            # Get video info
            video_info = self.get_video_info(video_id)
            
            # Calculate combined relevance score
            combined_score = 0.0
            if text_results:
                combined_score = sum(r['score'] for r in text_results) / len(text_results)
            
            return RetrievalContext(
                text_results=text_results,
                visual_results=visual_results,
                combined_score=combined_score,
                video_info=video_info
            )
            
        except Exception as e:
            raise Exception(f"Error retrieving context: {str(e)}")

    def build_context_prompt(self, 
                            query: str, 
                            context: RetrievalContext,
                            conversation_history: List[ChatMessage] = None) -> str:
        """
        Build a comprehensive prompt with retrieved context.
        """
        # Start with system prompt
        system_prompt = f"""You are an AI assistant that helps users understand and explore video content. 
You have access to information from the video titled "{context.video_info['title']}".

Your responses should be:
1. Accurate and based on the provided context
2. Include specific timestamps when referencing content
3. Conversational and helpful
4. Cite sources when making claims

When providing timestamps, use the format [MM:SS] and always include them when referencing specific content.
"""

        # Add conversation history if available
        history_context = ""
        if conversation_history:
            recent_history = conversation_history[-3:]  # Last 3 exchanges
            for msg in recent_history:
                history_context += f"{msg.role.capitalize()}: {msg.content}\n"
            
            if history_context:
                system_prompt += f"\nRecent conversation:\n{history_context}\n"

        # Add retrieved context
        context_sections = []
        
        # Text context
        if context.text_results:
            context_sections.append("RELEVANT VIDEO CONTENT:")
            for i, result in enumerate(context.text_results, 1):
                metadata = result['metadata']
                
                # Format timestamp if available
                timestamp_info = ""
                if 'start_time' in metadata:
                    start_time = self.format_timestamp(metadata['start_time'])
                    end_time = ""
                    if 'end_time' in metadata:
                        end_time = f"-{self.format_timestamp(metadata['end_time'])}"
                    timestamp_info = f" [{start_time}{end_time}]"
                
                content_type = metadata.get('content_type', 'content')
                text_content = metadata.get('text', '')
                
                context_sections.append(
                    f"{i}. {content_type.replace('_', ' ').title()}{timestamp_info}: {text_content}"
                )
        
        # Visual context (if any)
        if context.visual_results:
            context_sections.append("\nRELEVANT VISUAL CONTENT:")
            for i, result in enumerate(context.visual_results, 1):
                metadata = result['metadata']
                timestamp = metadata.get('timestamp', 0)
                timestamp_str = self.format_timestamp(timestamp)
                context_sections.append(
                    f"{i}. Frame at [{timestamp_str}]: Visual content from video"
                )

        # Combine everything
        full_context = "\n".join(context_sections)
        
        prompt = f"""{system_prompt}

{full_context}

User Query: {query}

Please provide a helpful response based on the video content above. Include timestamps when referencing specific parts of the video."""

        return prompt

    def generate_response(self, prompt: str) -> str:
        """
        Generate response using OpenAI GPT.
        """
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            # Fallback response
            return f"I apologize, but I'm having trouble generating a response right now. Error: {str(e)}"

    def extract_citations(self, response: str, context: RetrievalContext) -> List[Dict]:
        """
        Extract and format citations from the response and context.
        """
        citations = []
        
        # Add citations for text results used
        for i, result in enumerate(context.text_results, 1):
            metadata = result['metadata']
            
            # Format timestamp
            timestamp_info = "Unknown time"
            if 'start_time' in metadata:
                start_time = self.format_timestamp(metadata['start_time'])
                end_time = ""
                if 'end_time' in metadata:
                    end_time = f"-{self.format_timestamp(metadata['end_time'])}"
                timestamp_info = f"{start_time}{end_time}"
            
            citation = {
                "id": i,
                "type": "text",
                "content": metadata.get('text', ''),
                "timestamp": timestamp_info,
                "relevance_score": result['score'],
                "section_id": metadata.get('section_id'),
                "content_type": metadata.get('content_type', 'content')
            }
            citations.append(citation)
        
        # Add citations for visual results
        for i, result in enumerate(context.visual_results, len(context.text_results) + 1):
            metadata = result['metadata']
            timestamp = metadata.get('timestamp', 0)
            
            citation = {
                "id": i,
                "type": "visual",
                "timestamp": self.format_timestamp(timestamp),
                "relevance_score": result['score'],
                "frame_id": metadata.get('frame_id'),
                "image_path": metadata.get('image_path')
            }
            citations.append(citation)
        
        return citations

    def chat(self, 
             query: str, 
             video_id: int,
             conversation_id: Optional[str] = None,
             include_visual: bool = False) -> ChatResponse:
        """
        Main chat function that handles the complete RAG pipeline.
        """
        try:
            # Generate conversation ID if not provided
            if not conversation_id:
                conversation_id = f"chat_{video_id}_{datetime.now().timestamp()}"
            
            # Get conversation history
            conversation_history = self.conversations.get(conversation_id, [])
            
            # Retrieve relevant context
            context = self.retrieve_relevant_context(
                query=query,
                video_id=video_id,
                include_visual=include_visual
            )
            
            # Check if we found relevant context
            if not context.text_results and not context.visual_results:
                response_text = f"""I couldn't find specific information about "{query}" in this video. 
                
The video "{context.video_info['title']}" might not contain content directly related to your question. 
Try asking about different topics or being more specific about what you're looking for."""
                
                citations = []
            else:
                # Build prompt with context
                prompt = self.build_context_prompt(
                    query=query,
                    context=context,
                    conversation_history=conversation_history
                )
                
                # Generate response
                response_text = self.generate_response(prompt)
                
                # Extract citations
                citations = self.extract_citations(response_text, context)
            
            # Store conversation
            user_message = ChatMessage(
                role="user",
                content=query,
                timestamp=datetime.now()
            )
            
            assistant_message = ChatMessage(
                role="assistant",
                content=response_text,
                timestamp=datetime.now(),
                metadata={"citations": citations}
            )
            
            if conversation_id not in self.conversations:
                self.conversations[conversation_id] = []
            
            self.conversations[conversation_id].extend([user_message, assistant_message])
            
            # Keep only last 10 messages to manage memory
            if len(self.conversations[conversation_id]) > 10:
                self.conversations[conversation_id] = self.conversations[conversation_id][-10:]
            
            return ChatResponse(
                response=response_text,
                citations=citations,
                context_used=context,
                conversation_id=conversation_id
            )
            
        except Exception as e:
            # Error handling
            error_response = f"I encountered an error while processing your question: {str(e)}"
            
            return ChatResponse(
                response=error_response,
                citations=[],
                context_used=RetrievalContext([], [], 0.0, self.get_video_info(video_id)),
                conversation_id=conversation_id or f"error_{datetime.now().timestamp()}"
            )

    def get_conversation_history(self, conversation_id: str) -> List[Dict]:
        """
        Get conversation history for a given conversation ID.
        """
        if conversation_id not in self.conversations:
            return []
        
        return [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
                "metadata": msg.metadata
            }
            for msg in self.conversations[conversation_id]
        ]

    def clear_conversation(self, conversation_id: str) -> bool:
        """
        Clear conversation history for a given conversation ID.
        """
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            return True
        return False

    def get_suggested_questions(self, video_id: int) -> List[str]:
        """
        Generate suggested questions based on video content.
        """
        try:
            # Get some sections to understand video content
            sections = self.db.query(Section).filter(Section.video_id == video_id).limit(3).all()
            
            if not sections:
                return [
                    "What is this video about?",
                    "Can you summarize the main points?",
                    "What are the key topics covered?"
                ]
            
            # Generate suggestions based on section titles
            suggestions = []
            for section in sections:
                if section.title and len(section.title) > 10:
                    suggestions.append(f"Tell me more about {section.title.lower()}")
            
            # Add general questions
            suggestions.extend([
                "What are the main points of this video?",
                "Can you provide a summary?",
                "What happens at the beginning?"
            ])
            
            return suggestions[:5]  # Return top 5 suggestions
            
        except Exception:
            return [
                "What is this video about?",
                "Can you summarize the main points?",
                "What are the key topics covered?"
            ] 