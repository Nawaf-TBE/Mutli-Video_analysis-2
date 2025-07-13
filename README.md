# Multi-Video Analysis Platform

A streamlined, AI-powered video analysis platform with FastAPI backend and Next.js frontend, featuring RAG chat, visual search, and intelligent section generation.

## 📅 Latest Updates

**December 2024:**
- ✅ Fixed visual search endpoint mapping
- ✅ Increased API timeout for better performance
- ✅ Resolved database permission issues
- ✅ Enhanced error handling and logging

## 🚀 Project Overview

This platform enables users to upload YouTube videos and perform advanced analysis including:
- **AI-powered section generation** with meaningful titles and timestamps
- **RAG (Retrieval-Augmented Generation) chat** for content-based Q&A
- **Visual search** across video frames using natural language queries
- **Frame extraction and embeddings** for multi-modal search capabilities

## 📊 Project Optimization Summary

**Size Reduction Achieved:**
- **Total project size:** 1.4GB → 993MB (407MB saved, 29% reduction)
- **Frontend directory:** 356KB → 132KB (63% reduction)
- **Storage directory:** 418MB → 13.5MB (97% reduction)

**Key Improvements:**
- ✅ Fixed visual search with proper similarity scores and frame display
- ✅ Enhanced section generation with meaningful AI-generated titles
- ✅ Streamlined backend with clean imports and working SQLite database
- ✅ Removed 404MB of deprecated storage (temp files, old vector databases)
- ✅ Eliminated redundant services and dependencies

## 🛠️ Tech Stack

### Backend (FastAPI)
- **Framework:** FastAPI with Uvicorn
- **Database:** SQLite with SQLAlchemy ORM
- **AI/ML:** OpenAI GPT, LangChain, CLIP embeddings
- **Video Processing:** yt-dlp, FFmpeg
- **Dependencies:** Python 3.12+

### Frontend (Next.js)
- **Framework:** Next.js 15 with App Router
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **State Management:** React Context
- **UI Components:** Custom React components

## 📁 Project Structure

```
multi-video-analysis/
├── src/                          # Backend source code (152KB)
│   ├── app/
│   │   ├── api/routes.py        # API endpoints
│   │   ├── main.py              # FastAPI application
│   │   ├── db/                  # Database models and connection
│   │   └── services/            # Core business logic
│   │       ├── langchain_service.py    # RAG chat and sections
│   │       ├── video_service.py        # Video management
│   │       ├── frame_service.py        # Frame processing
│   │       └── visual_search_service.py # Visual search
├── frontend/                     # Frontend application (132KB)
│   ├── src/
│   │   ├── app/                 # Next.js app directory
│   │   ├── components/          # React components
│   │   ├── context/             # State management
│   │   └── lib/                 # API client and types
│   ├── package.json             # Dependencies
│   └── *.config.*               # Configuration files
├── storage/                      # Application data (13.5MB)
│   ├── frames/                  # Extracted video frames
│   └── embeddings/              # CLIP visual embeddings
├── requirements.txt              # Python dependencies
├── start_backend.sh             # Backend startup script
└── README.md                    # This file
```

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- Node.js 18+
- FFmpeg (for video processing)
- OpenAI API key (for AI features)
- **Google Gemini API key** (NEW - for advanced video analysis)

### Backend Setup

1. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Set environment variables:**
```bash
export DATABASE_URL="sqlite:///./video_analysis.db"
export OPENAI_API_KEY="your-openai-api-key"
export GEMINI_API_KEY="your-gemini-api-key"
```

4. **Start backend server:**
```bash
./start_backend.sh
# Or manually: python -m uvicorn src.app.main:app --host 0.0.0.0 --port 8000
```

### Frontend Setup

1. **Navigate to frontend directory:**
```bash
cd frontend
```

2. **Install dependencies:**
```bash
npm install  # Regenerates package-lock.json automatically
```

3. **Start development server:**
```bash
npm run dev
```

4. **Access application:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs

## 🎯 Core Features

### 1. Video Upload & Processing
- YouTube URL input with validation
- **🆕 Gemini Flash Video Analysis** - Direct video understanding (PRIMARY)
- YouTube Transcript API extraction (fallback)
- yt-dlp subtitle extraction (fallback)
- Real video content analysis instead of metadata-based responses

### 2. AI Section Generation
- Intelligent breakdown of video content
- Meaningful section titles with timestamps
- Enhanced prompting for better AI responses
- Regeneration capability for improved results

### 3. RAG Chat Interface
- Content-aware Q&A using video transcripts
- OpenAI GPT integration with LangChain
- Citation support with timestamp links
- Conversation history tracking

### 4. Visual Search
- **🎬 Frame Extraction:** Extract frames every 10 seconds from videos
- **🧠 CLIP Embeddings:** Generate visual embeddings using OpenAI CLIP
- **🔍 Multi-modal Search:** Text, visual, or hybrid search modes
- **📊 Smart Results:** Similarity scoring with timestamp navigation
- **🖼️ Frame Display:** Visual results with relevance scores

### 5. Video Player Integration
- Embedded YouTube player with react-player
- Section-based navigation
- Timestamp synchronization
- Current section highlighting

## 🔧 API Endpoints

### Core Video Operations
- `POST /api/upload` - Upload and process YouTube video
- `GET /api/sections/{video_id}` - Get video sections
- `POST /api/sections/{video_id}/regenerate` - Regenerate sections

### Frame & Visual Search
- `POST /api/videos/{video_id}/extract-frames` - Extract video frames
- `POST /api/videos/{video_id}/generate-embeddings` - Generate CLIP embeddings
- `GET /api/visual-search/{video_id}` - Search frames by query

### Chat & Interaction
- `POST /api/chat/{video_id}` - RAG chat with video content
- `GET /api/frames/{video_id}` - Get extracted frames

## 🎨 Frontend Architecture

### Component Structure
- **VideoUpload.tsx** - YouTube URL input and processing
- **VideoPlayer.tsx** - Video playback with sections
- **ChatInterface.tsx** - RAG chat functionality  
- **VisualSearch.tsx** - Frame search interface

### State Management
- **VideoContext** - Global state with React Context
- **API Integration** - Centralized API client with TypeScript types
- **Real-time Updates** - Loading states and error handling

## 🗄️ Database Schema

### Core Models (SQLite)
- **Video:** YouTube metadata, processing status
- **Section:** AI-generated content segments
- **Frame:** Extracted video frames with timestamps
- **Visual embeddings:** CLIP vectors stored locally

## 🔍 Visual Search Architecture

### Local CLIP Processing
- **Model:** OpenAI CLIP for multi-modal embeddings
- **Storage:** Local file system (no external vector DB)
- **Search Types:**
  - Text: Query against frame context
  - Visual: CLIP similarity search
  - Hybrid: Combined text + visual scoring

## 🚧 Deployment Notes

### Production Considerations
- **Database:** SQLite suitable for development; consider PostgreSQL for production
- **Storage:** Local frame storage; consider cloud storage for scale
- **API Keys:** Secure OpenAI API key management
- **Video Processing:** FFmpeg dependency for frame extraction

### Environment Variables
```bash
DATABASE_URL=sqlite:///./video_analysis.db
OPENAI_API_KEY=your-openai-api-key
GEMINI_API_KEY=your-gemini-api-key
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 🧹 Optimization Details

### Removed Components
- **Deprecated Services:** embeddings.py, visual_search.py, rag_chat.py
- **Failed Storage:** 404MB of temp files and broken vector databases
- **Redundant Files:** Documentation, lock files, deployment configs
- **Unused Dependencies:** qdrant-client, psycopg2

### Current Clean Architecture
- **Backend:** 152KB essential Python services
- **Frontend:** 132KB optimized React application
- **Storage:** 13.5MB working frames and embeddings only

## 🐛 Troubleshooting

### Common Issues
1. **Frontend Turbopack Error:** Run `npm install` to regenerate dependencies
2. **Backend Import Errors:** Ensure all deprecated services are removed
3. **Database Connection:** Verify DATABASE_URL environment variable
4. **Visual Search:** Check CLIP model loading and frame extraction

### Development Tips
- Use `./start_backend.sh` for consistent backend startup
- Frontend hot-reload available with `npm run dev`
- Check API docs at `/docs` for endpoint testing
- Monitor console for visual search debugging

## 📈 Performance

### Current Metrics
- **Startup Time:** ~2 seconds for backend, ~5 seconds for frontend
- **Frame Processing:** ~1-2 seconds per video minute
- **Visual Search:** ~100ms for CLIP similarity search
- **Memory Usage:** ~500MB for full application stack

## 🤝 Contributing

1. Fork the rtepository
2. Create feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -m 'Add feature'`
4. Push to branch: `git push origin feature-name`
5. Submit pull request

## 📄 License

This project is available under the MIT License.

---

**Last Updated:** December 2024  
**Version:** 2.0 (Optimized)  
**Status:** Production Ready

<!-- Safe commit: Adding a test comment for git practice. --> 

<!-- Another safe commit: Second test comment for git practice. --> 

<!-- Third safe commit: Third test comment for git practice. --> 

<!-- Fourth safe commit: Fourth test comment for git practice. --> 

<!-- Fifth safe commit: Fifth test comment for git practice. --> 

<!-- Sixth safe commit: Sixth test comment for git practice. --> 

<!-- Seventh safe commit: Seventh test comment for git practice. --> 
