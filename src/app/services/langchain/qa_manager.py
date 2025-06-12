"""
Q&A management for video content using LangChain.
"""

from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from .vector_store_manager import VectorStoreManager


class QAManager:
    """Manages Q&A operations for video content."""
    
    def __init__(self):
        # Initialize LangChain components
        self.llm = ChatOpenAI(
            model_name="gpt-4",
            temperature=0.1
        )
        
        self.vector_store_manager = VectorStoreManager()
    
    def get_qa_chain(self, video_id: int) -> Optional[RetrievalQA]:
        """Get QA chain for a video."""
        vectorstore = self.vector_store_manager.load_vector_store(video_id)
        
        if not vectorstore:
            return None
        
        try:
            # Create retriever
            retriever = vectorstore.as_retriever(
                search_kwargs={"k": 3}
            )
            
            # Create custom prompt for video analysis
            video_qa_prompt = PromptTemplate(
                template="""You are a helpful AI assistant that analyzes video content based on transcripts. 
                You have access to a video transcript and should answer questions about the video content.

                Use the following pieces of context from the video transcript to answer the question. 
                If you don't know the answer based on the transcript, just say you don't have enough information in the transcript to answer that question.

                Context from video transcript:
                {context}

                Question: {question}

                Answer based on the video content:""",
                input_variables=["context", "question"]
            )
            
            # Build QA chain with custom prompt
            qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=retriever,
                return_source_documents=True,
                chain_type_kwargs={"prompt": video_qa_prompt}
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
            print(f"🤖 Asking question: {question}")
            result = qa_chain({"query": question})
            
            answer = result["result"]
            sources = result.get("source_documents", [])
            print(f"📄 Found {len(sources)} source documents")
            
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