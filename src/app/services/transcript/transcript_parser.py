"""
Transcript parsing utilities for different formats and sources.
"""

from typing import List, Dict, Any


class TranscriptParser:
    """Handles parsing of different transcript formats."""
    
    def parse_gemini_response(self, response_text: str) -> List[Dict[str, Any]]:
        """Parse Gemini's video analysis into transcript format."""
        try:
            transcript = []
            lines = response_text.split('\n')
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # Look for timestamp patterns [0:00-0:30]
                if '[' in line and ']' in line and '-' in line:
                    try:
                        # Extract timestamp and content
                        timestamp_part = line[line.find('[')+1:line.find(']')]
                        content = line[line.find(']')+1:].strip()
                        
                        if '-' in timestamp_part and content:
                            start_time_str = timestamp_part.split('-')[0]
                            start_time = self.parse_timestamp_to_seconds(start_time_str)
                            
                            transcript.append({
                                "text": content,
                                "start": start_time,
                                "duration": 30.0  # Default 30 second segments
                            })
                    except:
                        continue
                elif line and len(line) > 20:  # Other content lines
                    transcript.append({
                        "text": line,
                        "start": len(transcript) * 30.0,
                        "duration": 30.0
                    })
            
            return transcript if transcript else []
            
        except Exception as e:
            print(f"⚠️ Error parsing Gemini response: {e}")
            return []
    
    def parse_timestamp_to_seconds(self, timestamp_str: str) -> float:
        """Convert timestamp like '1:30' to seconds."""
        try:
            parts = timestamp_str.split(':')
            if len(parts) == 2:
                minutes, seconds = map(int, parts)
                return minutes * 60 + seconds
            elif len(parts) == 1:
                return int(parts[0])
        except:
            pass
        return 0.0
    
    def parse_vtt_file(self, vtt_path: str) -> List[Dict[str, Any]]:
        """Parse VTT subtitle file into transcript format."""
        try:
            transcript = []
            with open(vtt_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Simple VTT parsing
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if '-->' in line:  # Timestamp line
                    if i + 1 < len(lines):
                        text = lines[i + 1].strip()
                        if text and not text.startswith('<'):
                            # Parse timestamp
                            start_str = line.split(' --> ')[0].strip()
                            start_time = self.parse_vtt_timestamp(start_str)
                            
                            transcript.append({
                                "text": text,
                                "start": start_time,
                                "duration": 3.0  # Default duration
                            })
            
            return transcript
            
        except Exception as e:
            print(f"⚠️ VTT parsing failed: {e}")
            return []
    
    def parse_vtt_timestamp(self, timestamp: str) -> float:
        """Convert VTT timestamp to seconds."""
        try:
            if '.' in timestamp:
                time_part, ms_part = timestamp.split('.')
                ms = int(ms_part[:3])  # Take first 3 digits
            else:
                time_part = timestamp
                ms = 0
                
            time_components = time_part.split(':')
            if len(time_components) == 3:  # HH:MM:SS
                hours, minutes, seconds = map(int, time_components)
                return hours * 3600 + minutes * 60 + seconds + ms / 1000
            elif len(time_components) == 2:  # MM:SS
                minutes, seconds = map(int, time_components)
                return minutes * 60 + seconds + ms / 1000
                
        except:
            pass
        return 0.0 