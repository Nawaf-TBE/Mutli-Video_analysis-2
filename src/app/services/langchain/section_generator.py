"""
Section generation for video content using AI.
"""

from typing import List, Dict, Any
from .qa_manager import QAManager


class SectionGenerator:
    """Generates intelligent video sections using AI."""
    
    def __init__(self):
        self.qa_manager = QAManager()
    
    def generate_sections(self, video_id: int) -> List[Dict[str, Any]]:
        """Generate intelligent sections using LangChain."""
        qa_chain = self.qa_manager.get_qa_chain(video_id)
        
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