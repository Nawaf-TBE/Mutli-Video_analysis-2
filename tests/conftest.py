import pytest
import asyncio
from typing import Generator, AsyncGenerator
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from src.app.main import app
from src.app.db.database import Base, get_db
from src.app.db.models import Video, Section, Frame

# Test database configuration
TEST_DATABASE_URL = "sqlite:///./test.db"

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
def test_engine():
    """Create a test database engine."""
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def test_db_session(test_engine):
    """Create a test database session."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture(scope="function")
def test_client(test_db_session):
    """Create a test client with database override."""
    def override_get_db():
        try:
            yield test_db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
async def async_client(test_db_session):
    """Create an async test client."""
    def override_get_db():
        try:
            yield test_db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    
    app.dependency_overrides.clear()

@pytest.fixture
def sample_video(test_db_session):
    """Create a sample video for testing."""
    video = Video(
        url="https://www.youtube.com/watch?v=test123",
        title="Test Video",
        created_at=None,
        updated_at=None
    )
    test_db_session.add(video)
    test_db_session.commit()
    test_db_session.refresh(video)
    return video

@pytest.fixture
def sample_section(test_db_session, sample_video):
    """Create a sample section for testing."""
    section = Section(
        video_id=sample_video.id,
        title="Introduction",
        start_time=0.0,
        end_time=120.5,
        created_at=None,
        updated_at=None
    )
    test_db_session.add(section)
    test_db_session.commit()
    test_db_session.refresh(section)
    return section

@pytest.fixture
def sample_frame(test_db_session, sample_video):
    """Create a sample frame for testing."""
    frame = Frame(
        video_id=sample_video.id,
        timestamp=60.0,
        path="/test/path/frame_60.jpg",
        created_at=None,
        updated_at=None
    )
    test_db_session.add(frame)
    test_db_session.commit()
    test_db_session.refresh(frame)
    return frame

@pytest.fixture
def mock_youtube_url():
    """Sample YouTube URL for testing."""
    return "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

@pytest.fixture
def mock_youtube_metadata():
    """Mock YouTube video metadata."""
    return {
        "title": "Test Video Title",
        "length": 300,
        "description": "Test video description",
        "author": "Test Author"
    }

@pytest.fixture
def mock_transcript():
    """Mock video transcript."""
    return [
        {"text": "Hello everyone", "start": 0.0, "duration": 2.0},
        {"text": "Welcome to this video", "start": 2.0, "duration": 3.0},
        {"text": "Today we'll discuss", "start": 5.0, "duration": 2.5},
        {"text": "Thank you for watching", "start": 295.0, "duration": 2.0}
    ]

@pytest.fixture
def mock_ai_sections():
    """Mock AI-generated sections."""
    return [
        {
            "title": "Introduction",
            "start_time": 0.0,
            "end_time": 60.0
        },
        {
            "title": "Main Content", 
            "start_time": 60.0,
            "end_time": 240.0
        },
        {
            "title": "Conclusion",
            "start_time": 240.0,
            "end_time": 300.0
        }
    ]
