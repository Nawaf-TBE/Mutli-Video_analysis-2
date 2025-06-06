import pytest
from unittest.mock import Mock, patch, MagicMock
from src.app.services.visual_search import VisualSearchService
from src.app.models.frame import Frame

class TestVisualSearchService:
    """Unit tests for Visual Search service."""

    @pytest.fixture
    def visual_search_service(self, test_db_session):
        """Create VisualSearchService instance."""
        with patch('src.app.services.visual_search.EmbeddingService'):
            return VisualSearchService(test_db_session)

    def test_get_frame_url_absolute_path(self, visual_search_service):
        """Test frame URL generation from absolute path."""
        test_cases = [
            ("/full/path/storage/frames/1/frame_60.jpg", "/api/frames/storage/frames/1/frame_60.jpg"),
            ("/other/path/frame.jpg", "/api/frames/frame.jpg"),
            ("relative/path.jpg", "/api/frames/relative/path.jpg")
        ]
        
        for input_path, expected_url in test_cases:
            result = visual_search_service._get_frame_url(input_path)
            assert result == expected_url

    def test_deduplicate_results(self, visual_search_service):
        """Test result deduplication keeps highest scores."""
        results = [
            {"frame_id": 1, "score": 0.8, "data": "first"},
            {"frame_id": 2, "score": 0.9, "data": "second"},
            {"frame_id": 1, "score": 0.95, "data": "better_first"},  # Higher score
            {"frame_id": 3, "score": 0.7, "data": "third"}
        ]
        
        deduplicated = visual_search_service._deduplicate_results(results)
        
        assert len(deduplicated) == 3
        
        # Check that frame_id 1 has the higher score
        frame_1_result = next(r for r in deduplicated if r["frame_id"] == 1)
        assert frame_1_result["score"] == 0.95
        assert frame_1_result["data"] == "better_first"

    def test_get_frames_in_time_range(self, visual_search_service, sample_video, test_db_session):
        """Test getting frames within time range."""
        # Create test frames
        frames = [
            Frame(video_id=sample_video.id, timestamp=10.0, path="/path1.jpg"),
            Frame(video_id=sample_video.id, timestamp=25.0, path="/path2.jpg"),
            Frame(video_id=sample_video.id, timestamp=35.0, path="/path3.jpg"),
            Frame(video_id=sample_video.id, timestamp=50.0, path="/path4.jpg"),
        ]
        
        for frame in frames:
            test_db_session.add(frame)
        test_db_session.commit()
        
        # Test range query
        result_frames = visual_search_service._get_frames_in_time_range(
            video_id=sample_video.id,
            start_time=20.0,
            end_time=40.0,
            max_frames=10
        )
        
        assert len(result_frames) == 2
        assert result_frames[0].timestamp == 25.0
        assert result_frames[1].timestamp == 35.0

    def test_get_frames_in_time_range_with_limit(self, visual_search_service, sample_video, test_db_session):
        """Test getting frames with max_frames limit."""
        # Create many test frames
        for i in range(10):
            frame = Frame(video_id=sample_video.id, timestamp=float(i * 5), path=f"/path{i}.jpg")
            test_db_session.add(frame)
        test_db_session.commit()
        
        # Test with limit
        result_frames = visual_search_service._get_frames_in_time_range(
            video_id=sample_video.id,
            start_time=0.0,
            end_time=50.0,
            max_frames=3
        )
        
        assert len(result_frames) == 3

    def test_search_by_timestamp(self, visual_search_service, sample_video, test_db_session):
        """Test timestamp-based search."""
        # Create test frames
        frames = [
            Frame(video_id=sample_video.id, timestamp=55.0, path="/path1.jpg"),
            Frame(video_id=sample_video.id, timestamp=65.0, path="/path2.jpg"),
            Frame(video_id=sample_video.id, timestamp=75.0, path="/path3.jpg"),
        ]
        
        for frame in frames:
            test_db_session.add(frame)
        test_db_session.commit()
        
        # Search around timestamp 60
        result = visual_search_service.search_by_timestamp(
            video_id=sample_video.id,
            timestamp=60.0,
            time_window=20.0,
            limit=10
        )
        
        assert result["video_id"] == sample_video.id
        assert result["search_type"] == "timestamp"
        assert result["target_timestamp"] == 60.0
        assert len(result["results"]) == 3
        
        # Check scores (closer timestamps should have higher scores)
        scores = [r["score"] for r in result["results"]]
        assert all(0 <= s <= 1 for s in scores)

    @patch('src.app.services.visual_search.Image')
    def test_save_temp_image_base64(self, mock_image, visual_search_service):
        """Test saving base64 image data to temporary file."""
        import base64
        import tempfile
        
        # Mock image data
        test_data = b"fake_image_data"
        b64_data = base64.b64encode(test_data).decode()
        
        # Mock tempfile
        mock_temp = Mock()
        mock_temp.name = "/tmp/test_image.jpg"
        
        with patch('src.app.services.visual_search.tempfile.NamedTemporaryFile', return_value=mock_temp):
            result_path = visual_search_service._save_temp_image(b64_data)
            
            assert result_path == "/tmp/test_image.jpg"
            mock_temp.write.assert_called_once_with(test_data)
            mock_temp.close.assert_called_once()

    def test_save_temp_image_data_url(self, visual_search_service):
        """Test saving image from data URL format."""
        import base64
        
        test_data = b"fake_image_data"
        b64_data = base64.b64encode(test_data).decode()
        data_url = f"data:image/jpeg;base64,{b64_data}"
        
        mock_temp = Mock()
        mock_temp.name = "/tmp/test_image.jpg"
        
        with patch('src.app.services.visual_search.tempfile.NamedTemporaryFile', return_value=mock_temp):
            result_path = visual_search_service._save_temp_image(data_url)
            
            assert result_path == "/tmp/test_image.jpg"
            mock_temp.write.assert_called_once_with(test_data)

    def test_get_video_frame_summary_no_frames(self, visual_search_service, sample_video):
        """Test frame summary when no frames exist."""
        result = visual_search_service.get_video_frame_summary(sample_video.id)
        
        assert result["video_id"] == sample_video.id
        assert result["total_frames"] == 0
        assert result["duration_covered"] == 0
        assert result["message"] == "No frames available for this video"

    def test_get_video_frame_summary_with_frames(self, visual_search_service, sample_video, test_db_session):
        """Test frame summary with existing frames."""
        # Create test frames
        frames = [
            Frame(video_id=sample_video.id, timestamp=10.0, path="/path1.jpg"),
            Frame(video_id=sample_video.id, timestamp=30.0, path="/path2.jpg"),
            Frame(video_id=sample_video.id, timestamp=50.0, path="/path3.jpg"),
        ]
        
        for frame in frames:
            test_db_session.add(frame)
        test_db_session.commit()
        
        result = visual_search_service.get_video_frame_summary(sample_video.id)
        
        assert result["video_id"] == sample_video.id
        assert result["total_frames"] == 3
        assert result["duration_covered"] == 40.0  # 50 - 10
        assert result["start_time"] == 10.0
        assert result["end_time"] == 50.0
        assert result["average_interval"] == 20.0  # (20 + 20) / 2
        assert len(result["sample_frames"]) == 3

    @patch.object(VisualSearchService, '_get_frames_in_time_range')
    def test_search_by_text_query_text_mode(self, mock_get_frames, visual_search_service, sample_video):
        """Test text-only search mode."""
        # Mock embedding service
        mock_embedding_service = Mock()
        mock_text_results = [
            {
                "id": "test1",
                "score": 0.9,
                "metadata": {
                    "start_time": 10.0,
                    "end_time": 30.0,
                    "text": "test content",
                    "content_type": "section_title"
                }
            }
        ]
        mock_embedding_service.search_text_embeddings.return_value = mock_text_results
        visual_search_service.embedding_service = mock_embedding_service
        
        # Mock frame retrieval
        mock_frame = Mock()
        mock_frame.id = 1
        mock_frame.timestamp = 20.0
        mock_frame.path = "/test/path.jpg"
        mock_get_frames.return_value = [mock_frame]
        
        result = visual_search_service.search_by_text_query(
            video_id=sample_video.id,
            query="test query",
            search_type="text",
            limit=10
        )
        
        assert result["video_id"] == sample_video.id
        assert result["query"] == "test query"
        assert result["search_type"] == "text"
        assert len(result["results"]) == 1
        assert result["results"][0]["match_type"] == "text" 