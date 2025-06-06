# 🎥 Multi-Video Analysis Platform

A comprehensive AI-powered platform for YouTube video analysis featuring RAG-based chat, visual search, and intelligent content processing. Built with FastAPI, Next.js, PostgreSQL, and Qdrant vector database.

## 🌟 Key Features

### 🤖 **AI-Powered Analysis**
- **RAG Chat**: Conversational AI that understands your video content
- **Smart Sections**: Auto-generated video sections with timestamps
- **Visual Search**: Search video frames using natural language
- **Multi-modal Embeddings**: Text and image understanding

### 🎯 **Core Functionality**
- **YouTube Integration**: Direct URL processing and metadata extraction
- **Frame Extraction**: Intelligent frame sampling for visual analysis
- **Real-time Chat**: Context-aware responses with citations
- **Vector Search**: Semantic search across video content
- **Interactive Player**: Seamless navigation with section highlighting

### 🎨 **Modern Interface**
- **Responsive Design**: Works perfectly on desktop and mobile
- **Real-time Updates**: Live processing feedback and status
- **Intuitive Navigation**: Tab-based interface for different features
- **Accessibility**: Screen reader friendly with proper ARIA labels

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   External      │
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│   Services      │
│                 │    │                 │    │                 │
│ • Video Upload  │    │ • YouTube API   │    │ • YouTube       │
│ • Video Player  │    │ • AI Processing │    │ • Hugging Face  │
│ • Chat Interface│    │ • RAG System    │    │ • OpenAI        │
│ • Visual Search │    │ • Vector Search │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                    ┌─────────────────┐    ┌─────────────────┐
                    │   Database      │    │  Vector Store   │
                    │ (PostgreSQL)    │    │   (Qdrant)      │
                    │                 │    │                 │
                    │ • Videos        │    │ • Embeddings    │
                    │ • Sections      │    │ • Similarity    │
                    │ • Frames        │    │ • Search Index  │
                    │ • Chat History  │    │                 │
                    └─────────────────┘    └─────────────────┘
```

## 📁 Project Structure

```
multi-video-analysis/
├── src/                        # Backend source code
│   ├── app/                    # FastAPI application
│   │   ├── main.py            # App entry point
│   │   ├── routes.py          # API endpoints
│   │   └── database.py        # Database config
│   ├── models/                # Database models
│   │   ├── video.py          # Video model
│   │   ├── section.py        # Section model
│   │   └── frame.py          # Frame model
│   └── services/              # Business logic
│       ├── youtube_service.py # YouTube processing
│       ├── ai_service.py      # AI operations
│       ├── chat_service.py    # RAG chat
│       ├── visual_search.py   # Visual search
│       └── embeddings.py      # Vector operations
├── frontend/                   # Next.js frontend
│   ├── src/
│   │   ├── app/               # Next.js app router
│   │   ├── components/        # React components
│   │   ├── context/           # Global state
│   │   └── lib/               # API client
│   └── public/                # Static assets
├── tests/                      # Test suite
│   ├── unit/                  # Unit tests
│   ├── integration/           # Integration tests
│   └── fixtures/              # Test data
├── scripts/                    # Utility scripts
├── requirements.txt            # Python dependencies
├── start_full_stack.sh        # Full stack launcher
└── README.md                  # This file
```

## 🚀 Quick Start

### Prerequisites
- **Python 3.9+** with pip
- **Node.js 18+** with npm
- **PostgreSQL 13+**
- **Docker** (for Qdrant)

### 1. Clone and Setup
```bash
git clone <repository-url>
cd multi-video-analysis

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install backend dependencies
pip install -r requirements.txt
```

### 2. Database Setup
```bash
# Create PostgreSQL database
createdb multi_video_analysis

# Run migrations (tables auto-created on first run)
# Set DATABASE_URL in .env file
```

### 3. Start Qdrant Vector Database
```bash
docker run -p 6333:6333 qdrant/qdrant
```

### 4. Environment Configuration
```bash
# Copy and edit environment file
cp .env.example .env

# Required variables:
# DATABASE_URL=postgresql://username:password@localhost/multi_video_analysis
# OPENAI_API_KEY=your_openai_key
```

### 5. Install Frontend
```bash
cd frontend
npm install
cd ..
```

### 6. Launch Everything
```bash
# Start both backend and frontend
./start_full_stack.sh
```

**Access the application:**
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 📖 Usage Guide

### 1. **Upload Video**
1. Navigate to the Upload tab
2. Paste a YouTube URL
3. Click "Upload & Process"
4. Wait for automatic processing (sections, transcript extraction)

### 2. **Video Analysis**
- **Watch**: Use the integrated player with section navigation
- **Sections**: AI-generated segments with timestamps
- **Regenerate**: Refresh sections with new AI analysis

### 3. **RAG Chat**
1. Switch to Chat tab
2. Ask questions about video content
3. Get contextual responses with citations
4. Click timestamps to verify sources

### 4. **Visual Search**
1. Go to Visual Search tab
2. Extract frames from video
3. Generate embeddings for visual content
4. Search using natural language queries
5. Choose search type: text, visual, or hybrid

## 🔧 API Endpoints

### Core Video Operations
```http
POST   /api/upload                      # Upload YouTube video
GET    /api/videos/{id}                 # Get video details
DELETE /api/videos/{id}                 # Delete video
```

### Section Management
```http
GET    /api/sections/{video_id}         # Get video sections
POST   /api/sections/{video_id}/regenerate  # Regenerate sections
```

### Chat & RAG
```http
POST   /api/chat/{video_id}             # Chat with video
GET    /api/chat/{video_id}/history     # Get chat history
```

### Visual Search
```http
GET    /api/visual-search/{video_id}    # Search frames
GET    /api/visual-search/{video_id}/timestamp/{timestamp}  # Search by time
GET    /api/visual-search/{video_id}/summary  # Get frame summary
POST   /api/visual-search/{video_id}/upload   # Upload image search
```

### Frame Operations
```http
GET    /api/frames/{video_id}           # Get video frames
POST   /api/videos/{video_id}/extract-frames  # Extract frames
POST   /api/videos/{video_id}/generate-embeddings  # Generate embeddings
```

## 🧪 Testing

### Run Test Suite
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test categories
pytest tests/unit/
pytest tests/integration/

# Run and generate coverage report
pytest --cov=src --cov-report=html
```

### Test Coverage
- **Unit Tests**: Service classes and utilities
- **Integration Tests**: API endpoints end-to-end
- **Fixtures**: Sample data for consistent testing

## 🛠️ Development

### Backend Development
```bash
# Start backend only
uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest

# Format code
black src/
isort src/
```

### Frontend Development
```bash
cd frontend

# Start frontend only
npm run dev

# Build for production
npm run build

# Type checking
npm run type-check
```

### Code Quality
- **Backend**: Black formatting, isort imports, pytest testing
- **Frontend**: ESLint, TypeScript strict mode, Tailwind CSS
- **API**: OpenAPI/Swagger documentation
- **Database**: SQLAlchemy ORM with automatic migrations

## 🌊 Tech Stack Deep Dive

### Backend Stack
- **FastAPI**: Modern Python web framework with automatic API docs
- **SQLAlchemy**: Powerful ORM with async support
- **PostgreSQL**: Robust relational database
- **Qdrant**: Vector database for similarity search
- **Pydantic**: Data validation and serialization
- **pytest**: Comprehensive testing framework

### Frontend Stack
- **Next.js 15**: React framework with App Router
- **TypeScript**: Type-safe JavaScript
- **Tailwind CSS**: Utility-first CSS framework
- **React Player**: YouTube video integration
- **Lucide React**: Beautiful icon system
- **Axios**: HTTP client for API communication

### AI & ML Stack
- **OpenAI GPT**: Language model for chat and analysis
- **Hugging Face**: Transformers for embeddings
- **CLIP**: Multi-modal vision-language model
- **Sentence Transformers**: Text embedding models
- **RAG Pipeline**: Retrieval-Augmented Generation

### Infrastructure
- **Docker**: Containerization for Qdrant
- **Git**: Version control
- **Environment Variables**: Configuration management
- **CORS**: Cross-origin resource sharing
- **Async/Await**: Non-blocking operations

## 🚀 Production Deployment

### Backend Deployment
```bash
# Install production dependencies
pip install gunicorn

# Run with Gunicorn
gunicorn src.app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Frontend Deployment
```bash
cd frontend

# Build for production
npm run build

# Start production server
npm start
```

### Environment Variables
```bash
# Production environment
DATABASE_URL=postgresql://user:pass@prod-host/db
OPENAI_API_KEY=prod_key
QDRANT_URL=https://your-qdrant-instance.com
ENVIRONMENT=production
```

## 🔍 Monitoring & Debugging

### Logs
- **Backend**: uvicorn logs with request tracking
- **Frontend**: Next.js development logs
- **Database**: SQL query logging available
- **Vector Database**: Qdrant operation logs

### Health Checks
```http
GET /health          # Backend health
GET /api/health      # API health
```

## 🤝 Contributing

1. **Fork** the repository
2. **Create** a feature branch
3. **Make** your changes
4. **Add** tests for new functionality
5. **Run** the test suite
6. **Submit** a pull request

### Development Workflow
```bash
# Create feature branch
git checkout -b feature/amazing-feature

# Make changes and test
pytest
npm test

# Commit with descriptive message
git commit -m "Add amazing feature"

# Push and create PR
git push origin feature/amazing-feature
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **OpenAI** for GPT models
- **Hugging Face** for transformer models
- **Qdrant** for vector database technology
- **FastAPI** and **Next.js** communities
- **YouTube** for video platform integration

---

**Built with ❤️ for the AI and video analysis community**

For questions, issues, or contributions, please visit our [GitHub repository](https://github.com/your-username/multi-video-analysis).

## 🆘 Troubleshooting

### Common Issues

**Backend won't start:**
```bash
# Check virtual environment
source venv/bin/activate
pip install -r requirements.txt
```

**Frontend won't start:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

**Database connection error:**
```bash
# Check PostgreSQL is running
createuser -s postgres  # If user doesn't exist
createdb multi_video_analysis
```

**Qdrant connection error:**
```bash
# Restart Qdrant container
docker run -p 6333:6333 qdrant/qdrant
```

For more help, check the issue tracker or create a new issue. 