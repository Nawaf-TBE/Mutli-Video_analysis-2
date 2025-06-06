import pytest
from unittest.mock import Mock, patch, MagicMock
from src.app.services.youtube import YouTubeService
from src.app.models.video import Video

class TestYouTubeService:
    """Unit tests for YouTube service."""

    @pytest.fixture
    def youtube_service(self, test_db_session):
        """Create YouTube service instance."""
        return YouTubeService(test_db_session)

    def test_extract_video_id_from_url(self, youtube_service):
        """Test video ID extraction from various YouTube URL formats."""
        test_cases = [
            ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
            ("https://youtu.be/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
            ("https://youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
            ("https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=10s", "dQw4w9WgXcQ"),
        ]
        
        for url, expected_id in test_cases:
            result = youtube_service.extract_video_id(url)
            assert result == expected_id

    def test_extract_video_id_invalid_url(self, youtube_service):
        """Test video ID extraction with invalid URLs."""
        invalid_urls = [
            "https://www.example.com",
            "not-a-url",
            "https://youtube.com/invalid",
            ""
        ]
        
        for url in invalid_urls:
            result = youtube_service.extract_video_id(url)
            assert result is None

    @patch('pytube.YouTube')
    def test_get_video_metadata_success(self, mock_youtube, youtube_service):
        """Test successful video metadata retrieval."""
        # Mock pytube YouTube object
        mock_video = Mock()
        mock_video.title = "Test Video"
        mock_video.length = 300
        mock_video.description = "Test description"
        mock_video.author = "Test Author"
        mock_video.views = 1000
        mock_youtube.return_value = mock_video
        
        metadata = youtube_service.get_video_metadata("dQw4w9WgXcQ")
        
        assert metadata["title"] == "Test Video"
        assert metadata["duration"] == 300
        assert metadata["description"] == "Test description"
        mock_youtube.assert_called_once_with("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

    @patch('pytube.YouTube')
    def test_get_video_metadata_failure(self, mock_youtube, youtube_service):
        """Test video metadata retrieval failure."""
        mock_youtube.side_effect = Exception("Video not found")
        
        with pytest.raises(Exception, match="Error fetching video metadata"):
            youtube_service.get_video_metadata("invalid_id")

    @patch('httpx.post')
    def test_get_transcript_success(self, mock_post, youtube_service):
        """Test successful transcript retrieval."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "transcript": [
                {"text": "Hello", "start": 0.0, "duration": 2.0},
                {"text": "World", "start": 2.0, "duration": 2.0}
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        transcript = youtube_service.get_transcript("dQw4w9WgXcQ")
        
        assert len(transcript) == 2
        assert transcript[0]["text"] == "Hello"
        assert transcript[1]["text"] == "World"

    @patch('httpx.post')
    def test_get_transcript_failure(self, mock_post, youtube_service):
        """Test transcript retrieval failure."""
        mock_post.side_effect = Exception("Transcript not available")
        
        with pytest.raises(Exception, match="Error fetching transcript"):
            youtube_service.get_transcript("invalid_id")

    @patch.object(YouTubeService, 'get_video_metadata')
    @patch.object(YouTubeService, 'get_transcript')  
    @patch('src.app.services.youtube.SectionizerService')
    def test_process_video_success(self, mock_sectionizer_class, mock_get_transcript, 
                                 mock_get_metadata, youtube_service, mock_youtube_metadata, 
                                 mock_transcript, mock_ai_sections):
        """Test successful video processing."""
        # Mock metadata and transcript
        mock_get_metadata.return_value = mock_youtube_metadata
        mock_get_transcript.return_value = mock_transcript
        
        # Mock sectionizer
        mock_sectionizer = Mock()
        mock_sectionizer.process_transcript_sections.return_value = mock_ai_sections
        mock_sectionizer_class.return_value = mock_sectionizer
        
        # Process video
        result = youtube_service.process_video("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        
        # Assertions
        assert isinstance(result, Video)
        assert result.title == mock_youtube_metadata["title"]
        assert result.url == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        
        # Verify method calls
        mock_get_metadata.assert_called_once()
        mock_get_transcript.assert_called_once()
        mock_sectionizer.process_transcript_sections.assert_called_once()

    def test_process_video_invalid_url(self, youtube_service):
        """Test processing with invalid URL."""
        with pytest.raises(ValueError, match="Invalid YouTube URL"):
            youtube_service.process_video("invalid-url")

    @patch.object(YouTubeService, 'get_video_metadata')
    def test_process_video_metadata_failure(self, mock_get_metadata, youtube_service):
        """Test processing when metadata retrieval fails."""
        mock_get_metadata.side_effect = Exception("Metadata error")
        
        with pytest.raises(Exception):
            youtube_service.process_video("https://www.youtube.com/watch?v=dQw4w9WgXcQ") 