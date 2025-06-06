# Section breakdown logic
from openai import OpenAI
from sqlalchemy.orm import Session
from ..models.video import Video
from ..models.section import Section
from typing import List, Dict, Tuple
import os
import math

class SectionizerService:
    def __init__(self, db: Session):
        self.db = db
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def chunk_transcript(self, transcript: List[Dict], chunk_duration: int = 120) -> List[List[Dict]]:
        """
        Split transcript into chunks based on duration (in seconds).
        Default chunk size is 2 minutes (120 seconds).
        """
        chunks = []
        current_chunk = []
        current_duration = 0
        
        for entry in transcript:
            start_time = entry.get('start', 0)
            duration = entry.get('duration', 0)
            
            # If adding this entry would exceed chunk duration, start a new chunk
            if current_duration + duration > chunk_duration and current_chunk:
                chunks.append(current_chunk)
                current_chunk = [entry]
                current_duration = duration
            else:
                current_chunk.append(entry)
                current_duration += duration
        
        # Add the last chunk if it has content
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks

    def generate_section_title(self, transcript_chunk: List[Dict]) -> str:
        """
        Use OpenAI to generate a human-readable section title based on transcript content.
        """
        # Extract text from transcript chunk
        text_content = " ".join([entry.get('text', '') for entry in transcript_chunk])
        
        # Create prompt for OpenAI
        prompt = f"""
        Based on the following transcript segment, generate a concise, descriptive title that captures the main topic or theme discussed. The title should be:
        - 3-8 words long
        - Descriptive and engaging
        - Suitable for a video section title
        
        Transcript segment:
        {text_content[:1000]}...
        
        Section title:
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that creates engaging section titles for video content."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=50,
                temperature=0.7
            )
            
            title = response.choices[0].message.content.strip()
            # Clean up the title (remove quotes if present)
            title = title.strip('"').strip("'")
            return title
            
        except Exception as e:
            # Fallback to a simple title if OpenAI fails
            start_time = transcript_chunk[0].get('start', 0)
            return f"Section at {self.format_time(start_time)}"

    def format_time(self, seconds: float) -> str:
        """Convert seconds to MM:SS format."""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"

    def process_transcript_sections(self, video_id: int, transcript: List[Dict]) -> List[Section]:
        """
        Process transcript into sections with AI-generated titles.
        """
        # Clear existing sections for this video
        self.db.query(Section).filter(Section.video_id == video_id).delete()
        
        # Chunk the transcript
        chunks = self.chunk_transcript(transcript)
        
        sections = []
        for i, chunk in enumerate(chunks):
            if not chunk:
                continue
                
            start_time = chunk[0].get('start', 0)
            end_time = chunk[-1].get('start', 0) + chunk[-1].get('duration', 0)
            
            # Generate AI title
            title = self.generate_section_title(chunk)
            
            # Create section
            section = Section(
                video_id=video_id,
                title=title,
                start_time=start_time,
                end_time=end_time
            )
            
            self.db.add(section)
            sections.append(section)
        
        self.db.commit()
        return sections

    def get_sections_by_video_id(self, video_id: int) -> List[Section]:
        """Get all sections for a specific video."""
        return self.db.query(Section).filter(Section.video_id == video_id).order_by(Section.start_time).all()

    def regenerate_sections(self, video_id: int) -> List[Section]:
        """
        Regenerate sections for a video using stored transcript data.
        This is useful if you want to re-process with different chunking or AI parameters.
        """
        # For now, this would require storing the original transcript
        # You might want to add a transcript field to the Video model
        # or implement transcript retrieval logic
        pass 