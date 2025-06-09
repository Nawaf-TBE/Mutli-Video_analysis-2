"""
LangChain-based video analysis service - simplified and more reliable.
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from youtube_transcript_api import YouTubeTranscriptApi
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.docstore.document import Document

from ..models.video import Video
from ..models.section import Section

class LangChainVideoService:
    """Simplified video analysis using LangChain."""
    
    def __init__(self, db: Session):
        self.db = db
        
        # Initialize LangChain components
        self.embeddings = OpenAIEmbeddings()
        self.llm = ChatOpenAI(
            model_name="gpt-4",
            temperature=0.1
        )
        
        # Text splitter for better chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
        )
    
    def extract_video_id(self, url: str) -> str:
        """Extract YouTube video ID from URL."""
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([^&\n?#]+)',
            r'youtube\.com/.*[?&]v=([^&\n?#]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        raise ValueError(f"Could not extract video ID from URL: {url}")
    
    def fetch_transcript(self, video_url: str) -> List[Dict[str, Any]]:
        """Fetch transcript using YouTubeTranscriptApi - much more reliable!"""
        try:
            video_id = self.extract_video_id(video_url)
            print(f"📹 Fetching transcript for video: {video_id}")
            
            # Try to get transcript with language preferences
            transcript = YouTubeTranscriptApi.get_transcript(
                video_id,
                languages=['en', 'en-US', 'en-GB']  # Prefer English
            )
            
            print(f"✅ Found {len(transcript)} transcript segments")
            return transcript
            
        except Exception as e:
            print(f"⚠️ No transcript available: {e}")
            # Return empty list instead of dummy data
            return []
    
    def process_transcript(self, video_id: int, video_url: str) -> Dict[str, Any]:
        """Process transcript and create vector store."""
        
        # 1. Fetch transcript
        segments = self.fetch_transcript(video_url)
        
        if not segments:
            return {
                "success": False,
                "message": "No transcript available for this video",
                "segments_count": 0,
                "chunks_count": 0
            }
        
        # 2. Create documents with metadata
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
        
        # 3. Split text for better retrieval
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
        
        # 4. Create or update vector store
        chroma_dir = Path(f"storage/chroma/video_{video_id}")
        chroma_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            vectorstore = Chroma.from_documents(
                documents=chunk_docs,
                embedding=self.embeddings,
                persist_directory=str(chroma_dir)
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
    
    def get_qa_chain(self, video_id: int) -> Optional[RetrievalQA]:
        """Get QA chain for a video."""
        chroma_dir = Path(f"storage/chroma/video_{video_id}")
        
        if not chroma_dir.exists():
            print(f"❌ No vector store found for video {video_id}")
            return None
        
        try:
            # Load existing vector store
            vectorstore = Chroma(
                persist_directory=str(chroma_dir),
                embedding_function=self.embeddings
            )
            
            # Create retriever
            retriever = vectorstore.as_retriever(
                search_kwargs={"k": 3}
            )
            
            # Build QA chain
            qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=retriever,
                return_source_documents=True
            )
            
            return qa_chain
            
        except Exception as e:
            print(f"❌ Failed to load QA chain: {e}")
            return None
    
    def ask_question(self, video_id: int, question: str) -> Dict[str, Any]:
        """Ask a question about a video."""
        qa_chain = self.get_qa_chain(video_id)
        
        if not qa_chain:
            return {
                "success": False,
                "answer": "Sorry, I cannot answer questions about this video. The transcript may not be available or processed yet.",
                "sources": []
            }
        
        try:
            result = qa_chain({"query": question})
            
            answer = result["result"]
            sources = result.get("source_documents", [])
            
            # Format sources with timestamps
            formatted_sources = []
            for doc in sources[:3]:  # Top 3 sources
                metadata = doc.metadata
                formatted_sources.append({
                    "content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                    "timestamp": metadata.get("timestamp", "00:00"),
                    "start_time": metadata.get("start_time", metadata.get("approximate_start_time", 0))
                })
            
            return {
                "success": True,
                "answer": answer,
                "sources": formatted_sources
            }
            
        except Exception as e:
            print(f"❌ Error answering question: {e}")
            return {
                "success": False,
                "answer": f"Sorry, I encountered an error: {str(e)}",
                "sources": []
            }
    
    def generate_sections(self, video_id: int) -> List[Dict[str, Any]]:
        """Generate intelligent sections using LangChain."""
        qa_chain = self.get_qa_chain(video_id)
        
        if not qa_chain:
            # Create meaningful fallback sections when no transcript is available
            return [
                {"title": "Introduction", "start_time": 0, "end_time": 60},
                {"title": "Main Content", "start_time": 60, "end_time": 240},
                {"title": "Conclusion", "start_time": 240, "end_time": 300}
            ]
        
        try:
            # Ask for sections breakdown with better prompting
            sections_query = """
            Analyze this video transcript and create 3-5 main sections that best organize the content.
            For each section, provide a clear, descriptive title (3-8 words) that captures the main topic.
            
            Look for natural breaks in content, topic changes, or different phases of discussion.
            
            Format your response as a numbered list like this:
            1. Introduction and Overview
            2. Main Topic Discussion  
            3. Key Examples and Case Studies
            4. Practical Applications
            5. Summary and Conclusions
            
            Only provide the titles, one per line, numbered.
            """
            
            result = qa_chain({"query": sections_query})
            answer = result["result"]
            
            # Parse the AI response into sections
            sections = []
            lines = answer.split('\n')
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # Remove numbering (1., 2., etc.) and clean up
                cleaned_line = line
                if line[0].isdigit() and '.' in line:
                    cleaned_line = line.split('.', 1)[1].strip()
                elif line.startswith('-') or line.startswith('•'):
                    cleaned_line = line[1:].strip()
                
                # Only add if it looks like a proper title
                if len(cleaned_line) > 5 and len(cleaned_line) < 100:
                    sections.append({"title": cleaned_line})
            
            # Ensure we have at least some sections
            if not sections:
                sections = [
                    {"title": "Video Introduction"},
                    {"title": "Main Discussion"},
                    {"title": "Key Points"},
                    {"title": "Conclusion"}
                ]
            
            # Add timing information (distribute evenly across 5-minute duration)
            total_duration = 300  # Default 5 minutes
            section_duration = total_duration / len(sections)
            
            for i, section in enumerate(sections):
                section["start_time"] = i * section_duration
                section["end_time"] = (i + 1) * section_duration
            
            return sections
            
        except Exception as e:
            print(f"❌ Error generating sections: {e}")
            # Better fallback sections
            return [
                {"title": "Video Introduction", "start_time": 0, "end_time": 75},
                {"title": "Main Content", "start_time": 75, "end_time": 225},
                {"title": "Summary", "start_time": 225, "end_time": 300}
            ] 