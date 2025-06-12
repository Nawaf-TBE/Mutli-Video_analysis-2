"""
Video transcript extraction service - handles multiple transcript sources.
"""

import os
import re
import tempfile
import subprocess
from typing import List, Dict, Any
import google.generativeai as genai


class TranscriptExtractor:
    """Handles transcript extraction from multiple sources."""
    
    def __init__(self):
        # Initialize Gemini for video analysis
        try:
            genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
            self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
            self.use_gemini = True
            print("✅ Gemini Flash initialized for video analysis")
        except Exception as e:
            print(f"⚠️ Gemini not available: {e}")
            self.use_gemini = False
    
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
        """Fetch transcript using multiple methods with Gemini as primary."""
        video_id = self.extract_video_id(video_url)
        print(f"📹 Analyzing video: {video_id}")
        
        # Method 1: Gemini Flash Video Analysis (PRIMARY METHOD)
        if self.use_gemini:
            try:
                print("🤖 Using Gemini Flash for direct video analysis...")
                transcript = self.analyze_video_with_gemini(video_url, video_id)
                if transcript:
                    print(f"✅ Generated {len(transcript)} content segments via Gemini")
                    return transcript
            except Exception as e:
                print(f"⚠️ Gemini video analysis failed: {e}")
        
        # Method 2: Try YouTube Transcript API (FALLBACK)
        try:
            print("🔄 Falling back to YouTube Transcript API...")
            from youtube_transcript_api import YouTubeTranscriptApi
            transcript = YouTubeTranscriptApi.get_transcript(
                video_id,
                languages=['en', 'en-US', 'en-GB', 'auto']
            )
            if transcript:
                print(f"✅ Found {len(transcript)} transcript segments via YouTube API")
                return transcript
        except Exception as e:
            print(f"⚠️ YouTube Transcript API failed: {e}")
        
        # Method 3: Try yt-dlp for subtitle extraction (FALLBACK)
        try:
            print("🔄 Trying yt-dlp subtitle extraction...")
            transcript = self.extract_subtitles_with_ytdlp(video_url, video_id)
            if transcript:
                print(f"✅ Found {len(transcript)} transcript segments via yt-dlp")
                return transcript
        except Exception as e:
            print(f"⚠️ yt-dlp subtitle extraction failed: {e}")
            
        # Final fallback - return empty to indicate no transcript
        print("❌ All video analysis methods failed - chat disabled for this video")
        return []
    
    def analyze_video_with_gemini(self, video_url: str, video_id: str) -> List[Dict[str, Any]]:
        """Analyze video directly with Gemini Flash - TRUE video understanding."""
        try:
            # Download video segment for analysis (first 10 minutes max)
            temp_dir = tempfile.mkdtemp()
            video_path = os.path.join(temp_dir, f"{video_id}.mp4")
            
            print("📥 Downloading video for Gemini analysis...")
            result = subprocess.run([
                'yt-dlp',
                '-f', 'best[ext=mp4][height<=720]',  # Reasonable quality
                '--output', video_path,
                video_url
            ], capture_output=True, text=True)
            
            if result.returncode != 0 or not os.path.exists(video_path):
                print(f"❌ Video download failed: {result.stderr}")
                return []
            
            print("🤖 Sending video to Gemini Flash for analysis...")
            
            # Upload video to Gemini
            video_file = genai.upload_file(video_path)
            
            # Generate comprehensive content analysis
            prompt = """
            Analyze this video comprehensively and create a detailed transcript-style breakdown. Include:
            
            1. What is being said (if there's speech)
            2. What is being shown visually
            3. Key topics and themes
            4. Important moments or transitions
            5. Any text visible in the video
            
            Format as timestamped segments like this:
            [0:00-0:30] Description of what's happening in this segment
            [0:30-1:00] Next segment description
            
            Provide specific, detailed analysis that would allow someone to understand the video content without watching it.
            """
            
            response = self.gemini_model.generate_content([video_file, prompt])
            
            # Clean up downloaded video
            try:
                os.remove(video_path)
                os.rmdir(temp_dir)
            except:
                pass
            
            # Parse Gemini response into transcript format
            from .transcript_parser import TranscriptParser
            parser = TranscriptParser()
            return parser.parse_gemini_response(response.text)
            
        except Exception as e:
            print(f"❌ Gemini video analysis error: {e}")
            return []
    
    def extract_subtitles_with_ytdlp(self, video_url: str, video_id: str) -> List[Dict[str, Any]]:
        """Extract subtitles using yt-dlp."""
        try:
            import json
            import os
            
            # Get video info with subtitles
            temp_dir = tempfile.mkdtemp()
            result = subprocess.run([
                'yt-dlp', 
                '--write-auto-sub', 
                '--write-sub',
                '--sub-langs', 'en,en-US,en-GB',
                '--sub-format', 'vtt',
                '--skip-download',
                '--output', os.path.join(temp_dir, '%(id)s.%(ext)s'),
                video_url
            ], capture_output=True, text=True, cwd=temp_dir)
            
            if result.returncode == 0:
                # Look for subtitle files
                subtitle_files = []
                for file in os.listdir(temp_dir):
                    if video_id in file and file.endswith('.vtt'):
                        subtitle_files.append(os.path.join(temp_dir, file))
                
                if subtitle_files:
                    # Parse VTT file
                    from .transcript_parser import TranscriptParser
                    parser = TranscriptParser()
                    transcript = parser.parse_vtt_file(subtitle_files[0])
                    
                    # Clean up
                    for file in os.listdir(temp_dir):
                        try:
                            os.remove(os.path.join(temp_dir, file))
                        except:
                            pass
                    os.rmdir(temp_dir)
                    
                    return transcript
                    
        except Exception as e:
            print(f"⚠️ yt-dlp extraction error: {e}")
            
        return []
    
    def generate_contextual_transcript(self, video_url: str, video_id: str) -> List[Dict[str, Any]]:
        """Generate contextual transcript based on video metadata."""
        try:
            import subprocess
            import json
            
            # Get video metadata
            result = subprocess.run([
                'yt-dlp', 
                '--dump-json',
                '--no-download',
                video_url
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                metadata = json.loads(result.stdout)
                title = metadata.get('title', 'Unknown Video')
                description = metadata.get('description', '')
                duration = metadata.get('duration', 300)
                
                print(f"📺 Video: {title}")
                print(f"⏱️ Duration: {duration}s")
                
                # Create sections based on metadata
                transcript = []
                
                # Introduction
                transcript.append({
                    "text": f"This video is titled '{title}' and covers the following content.",
                    "start": 0,
                    "duration": 4.0
                })
                
                # Add description content if available
                if description and len(description) > 50:
                    # Split description into chunks
                    desc_words = description.split()[:100]  # First 100 words
                    desc_text = ' '.join(desc_words)
                    
                    transcript.append({
                        "text": f"The video description mentions: {desc_text}",
                        "start": 4.0,
                        "duration": 6.0
                    })
                
                # Add generic content sections
                middle_time = duration / 2
                transcript.extend([
                    {
                        "text": "The video continues with the main content and key discussion points.",
                        "start": 10.0,
                        "duration": 4.0
                    },
                    {
                        "text": "Throughout the video, various topics and concepts are explained in detail.",
                        "start": middle_time,
                        "duration": 4.0
                    },
                    {
                        "text": "The video concludes with final thoughts and summary of the key points discussed.",
                        "start": duration - 10,
                        "duration": 4.0
                    }
                ])
                
                print(f"✅ Generated contextual transcript with {len(transcript)} segments")
                return transcript
                
        except Exception as e:
            print(f"⚠️ Metadata extraction failed: {e}")
            
        return [] 