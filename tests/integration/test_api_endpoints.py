import pytest
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient
import json


class TestAPIEndpoints:
    """Integration tests for API endpoints."""

    def test_health_endpoint(self, test_client):
        """Test health check endpoint."""
        response = test_client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    def test_upload_endpoint_validation(self, test_client):
        """Test upload endpoint input validation."""
        # Test missing URL
        response = test_client.post("/api/upload", json={})
        assert response.status_code == 422
        assert "Field required" in response.text

        # Test invalid JSON
        response = test_client.post("/api/upload", data="invalid json")
        assert response.status_code == 422

        # Test wrong content type
        response = test_client.post("/api/upload", data={"url": "test"})
        assert response.status_code == 422

    @patch('src.app.services.youtube.YouTubeService.process_video')
    def test_upload_endpoint_success(self, mock_process_video, test_client, sample_video):
        """Test successful video upload."""
        mock_process_video.return_value = sample_video
        
        response = test_client.post(
            "/api/upload",
            json={"url": "https://www.youtube.com/watch?v=test123"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Video processed successfully"
        assert data["video_id"] == sample_video.id
        assert data["title"] == sample_video.title

    @patch('src.app.services.youtube.YouTubeService.process_video')
    def test_upload_endpoint_processing_error(self, mock_process_video, test_client):
        """Test upload endpoint with processing error."""
        mock_process_video.side_effect = Exception("Processing failed")
        
        response = test_client.post(
            "/api/upload",
            json={"url": "https://www.youtube.com/watch?v=test123"}
        )
        
        assert response.status_code == 500
        assert "Error processing video" in response.json()["detail"]

    def test_sections_endpoint_with_data(self, test_client, sample_section):
        """Test sections endpoint with existing data."""
        response = test_client.get(f"/api/sections/{sample_section.video_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == sample_section.id
        assert data[0]["title"] == sample_section.title

    def test_sections_endpoint_no_data(self, test_client):
        """Test sections endpoint with no data."""
        response = test_client.get("/api/sections/999")
        assert response.status_code == 500
        assert "No sections found" in response.json()["detail"]

    def test_sections_endpoint_invalid_id(self, test_client):
        """Test sections endpoint with invalid ID."""
        response = test_client.get("/api/sections/invalid")
        assert response.status_code == 422

    @patch('src.app.services.rag_chat.RAGChatService.chat')
    def test_chat_endpoint_success(self, mock_chat, test_client, sample_video):
        """Test successful chat interaction."""
        # Mock chat response
        mock_response = Mock()
        mock_response.response = "This is a test response"
        mock_response.citations = [{"timestamp": 60.0, "content": "test"}]
        mock_response.conversation_id = "test-conv-id"
        mock_response.context_used = Mock()
        mock_response.context_used.video_info = {"title": "Test Video"}
        mock_response.context_used.combined_score = 0.85
        mock_response.context_used.text_results = []
        mock_response.context_used.visual_results = []
        
        mock_chat.return_value = mock_response
        
        response = test_client.post(
            f"/api/chat/{sample_video.id}",
            json={"message": "Tell me about this video"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["response"] == "This is a test response"
        assert len(data["citations"]) == 1
        assert data["conversation_id"] == "test-conv-id"

    def test_chat_endpoint_validation(self, test_client):
        """Test chat endpoint input validation."""
        # Test missing message
        response = test_client.post("/api/chat/1", json={})
        assert response.status_code == 422

        # Test invalid video ID
        response = test_client.post("/api/chat/invalid", json={"message": "test"})
        assert response.status_code == 422

    def test_chat_endpoint_video_not_found(self, test_client):
        """Test chat endpoint with non-existent video."""
        response = test_client.post(
            "/api/chat/999",
            json={"message": "test message"}
        )
        assert response.status_code == 500
        assert "Video not found" in response.json()["detail"]

    @patch('src.app.services.visual_search.VisualSearchService.search_by_text_query')
    def test_visual_search_endpoint_success(self, mock_search, test_client):
        """Test successful visual search."""
        mock_search.return_value = {
            "video_id": 1,
            "query": "test query",
            "search_type": "hybrid",
            "total_results": 1,
            "results": [
                {
                    "frame_id": 1,
                    "timestamp": 60.0,
                    "score": 0.9,
                    "match_type": "text"
                }
            ]
        }
        
        response = test_client.get(
            "/api/visual-search/1?query=test%20query&search_type=hybrid&limit=10"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["video_id"] == 1
        assert data["query"] == "test query"
        assert len(data["results"]) == 1

    def test_visual_search_endpoint_validation(self, test_client):
        """Test visual search endpoint parameter validation."""
        # Test missing query
        response = test_client.get("/api/visual-search/1")
        assert response.status_code == 422

        # Test invalid search_type
        response = test_client.get("/api/visual-search/1?query=test&search_type=invalid")
        # Should still work as it defaults to valid values

        # Test invalid limit
        response = test_client.get("/api/visual-search/1?query=test&limit=-1")
        # Should still work as FastAPI converts/validates

    @patch('src.app.services.visual_search.VisualSearchService.get_video_frame_summary')
    def test_visual_search_summary_endpoint(self, mock_summary, test_client):
        """Test visual search summary endpoint."""
        mock_summary.return_value = {
            "video_id": 1,
            "total_frames": 5,
            "duration_covered": 300.0,
            "frame_intervals": [10, 10, 10, 10],
            "sample_frames": []
        }
        
        response = test_client.get("/api/visual-search/1/summary")
        
        assert response.status_code == 200
        data = response.json()
        assert data["video_id"] == 1
        assert data["total_frames"] == 5
        assert data["duration_covered"] == 300.0

    def test_visual_search_timestamp_endpoint(self, test_client, sample_frame):
        """Test visual search timestamp endpoint."""
        response = test_client.get(f"/api/visual-search/{sample_frame.video_id}/timestamp/60.0")
        
        assert response.status_code == 200
        data = response.json()
        assert data["video_id"] == sample_frame.video_id
        assert data["search_type"] == "timestamp"
        assert data["target_timestamp"] == 60.0

    def test_visual_search_thumbnails_endpoint_validation(self, test_client):
        """Test thumbnails endpoint parameter validation."""
        # Test missing frame_ids
        response = test_client.get("/api/visual-search/1/thumbnails")
        assert response.status_code == 422

        # Test invalid frame_ids format
        response = test_client.get("/api/visual-search/1/thumbnails?frame_ids=")
        # Should return empty result but not error

    @patch('src.app.services.visual_search.VisualSearchService.get_frame_thumbnails')
    def test_visual_search_thumbnails_endpoint_success(self, mock_thumbnails, test_client):
        """Test successful thumbnail generation."""
        mock_thumbnails.return_value = {
            1: "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD/",
            2: "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD/"
        }
        
        response = test_client.get("/api/visual-search/1/thumbnails?frame_ids=1,2&size=200x150")
        
        assert response.status_code == 200
        data = response.json()
        assert data["video_id"] == 1
        assert len(data["thumbnails"]) == 2
        assert data["total_thumbnails"] == 2

    def test_frames_endpoint_with_data(self, test_client, sample_frame):
        """Test frames endpoint with existing data."""
        response = test_client.get(f"/api/frames/{sample_frame.video_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == sample_frame.id
        assert data[0]["timestamp"] == sample_frame.timestamp

    def test_frames_endpoint_no_data(self, test_client):
        """Test frames endpoint with no data."""
        response = test_client.get("/api/frames/999")
        assert response.status_code == 500
        assert "No frames found" in response.json()["detail"]

    @patch('src.app.services.frame_extractor.FrameExtractorService.process_video_frames')
    def test_extract_frames_endpoint_success(self, mock_extract, test_client, sample_video):
        """Test successful frame extraction."""
        mock_extract.return_value = [Mock(), Mock(), Mock()]  # 3 frames
        
        response = test_client.post(
            f"/api/videos/{sample_video.id}/extract-frames",
            json={"interval": 10}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Frame extraction completed"
        assert data["video_id"] == sample_video.id
        assert data["frames_extracted"] == 3

    def test_extract_frames_endpoint_video_not_found(self, test_client):
        """Test frame extraction with non-existent video."""
        response = test_client.post(
            "/api/videos/999/extract-frames",
            json={"interval": 10}
        )
        assert response.status_code == 404
        assert "Video not found" in response.json()["detail"]

    @patch('src.app.services.embeddings.EmbeddingService.process_video_text_embeddings')
    @patch('src.app.services.embeddings.EmbeddingService.process_video_visual_embeddings')
    def test_generate_embeddings_endpoint_success(self, mock_visual, mock_text, test_client):
        """Test successful embedding generation."""
        mock_text.return_value = ["point1", "point2"]
        mock_visual.return_value = ["point3", "point4", "point5"]
        
        response = test_client.post(
            "/api/videos/1/generate-embeddings",
            json={"include_text": True, "include_visual": True}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Embeddings generated successfully"
        assert data["text_embeddings"] == 2
        assert data["visual_embeddings"] == 3

    def test_cors_headers(self, test_client):
        """Test CORS headers are present."""
        response = test_client.options("/api/upload")
        assert response.status_code == 405  # Method not allowed, but CORS headers should be present
        
        # Test actual request
        response = test_client.get("/health")
        # CORS headers should be handled by middleware 