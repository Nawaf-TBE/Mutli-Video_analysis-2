# Multi-Video Analysis Frontend

A modern, responsive Next.js frontend for the Multi-Video Analysis Platform with AI-powered video processing, RAG chat, and visual search capabilities.

## 🚀 Features

- **📱 Modern UI**: Clean, responsive design built with Tailwind CSS
- **🎥 Video Upload**: YouTube video URL upload with real-time processing feedback
- **▶️ Video Player**: Integrated video player with section navigation using react-player
- **💬 RAG Chat**: AI-powered chat interface with video content using citations and timestamps
- **🔍 Visual Search**: Search video frames by natural language queries
- **📊 Frame Processing**: Extract and generate embeddings for video frames
- **⚡ Real-time Updates**: Live processing status and instant feedback

## 🛠️ Tech Stack

- **Framework**: Next.js 15 with App Router
- **Language**: TypeScript for type safety
- **Styling**: Tailwind CSS for responsive design
- **Icons**: Lucide React for beautiful icons
- **Video Player**: react-player for YouTube video playback
- **HTTP Client**: Axios for API communication
- **State Management**: React Context + useReducer

## 📁 Project Structure

```
frontend/
├── src/
│   ├── app/                    # Next.js app directory
│   │   ├── layout.tsx         # Root layout with VideoProvider
│   │   ├── page.tsx           # Main page with tab interface
│   │   └── globals.css        # Global styles
│   ├── components/            # React components
│   │   ├── VideoUpload.tsx    # YouTube URL upload form
│   │   ├── VideoPlayer.tsx    # Video player with sections
│   │   ├── ChatInterface.tsx  # RAG chat interface
│   │   └── VisualSearch.tsx   # Visual search functionality
│   ├── context/               # React context
│   │   └── VideoContext.tsx   # Global video state management
│   └── lib/                   # Utilities
│       └── api.ts             # API client and TypeScript types
├── .env.local                 # Environment variables
├── package.json               # Dependencies and scripts
└── README.md                  # This file
```

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ 
- npm or yarn
- Backend API running on http://localhost:8000

### Installation

1. **Install dependencies**:
```bash
npm install
```

2. **Set up environment variables**:
```bash
# .env.local (already created)
NEXT_PUBLIC_API_URL=http://localhost:8000
```

3. **Start development server**:
```bash
npm run dev
```

4. **Open browser**:
Navigate to http://localhost:3000

## 📖 Usage Guide

### 1. Upload Video
- Go to the **Upload** tab
- Paste a YouTube URL
- Click "Upload & Process"
- Wait for processing to complete

### 2. Watch & Navigate
- Switch to **Player** tab
- Use the integrated video player
- Click on sections to jump to specific timestamps
- View current section highlight

### 3. Chat with Video
- Go to **Chat** tab
- Type questions about the video content
- Get AI-powered responses with citations
- Click timestamps to verify information

### 4. Visual Search
- Switch to **Visual Search** tab
- First extract frames from the video
- Generate embeddings for the frames
- Search using natural language queries
- Choose between text, visual, or hybrid search
- View results with timestamps and relevance scores

## 🎯 Key Components

### VideoContext
Global state management for:
- Current video information
- Sections and frames data
- Chat history and conversation ID
- Loading states and error handling

### API Integration
Complete integration with backend features:
- Video upload and processing
- Section generation and regeneration
- Frame extraction and embedding generation
- RAG chat with conversation history
- Visual search with multiple search types

### Responsive Design
- Mobile-first approach
- Adaptive layouts for different screen sizes
- Touch-friendly interface
- Optimized for both desktop and mobile

## 🔧 Development

### Build for Production
```bash
npm run build
```

### Type Checking
```bash
npm run build  # Includes type checking
```

### Code Quality
The project follows:
- TypeScript strict mode
- ESLint configuration
- Accessibility best practices
- Modern React patterns

## 🌐 API Integration

The frontend communicates with the backend API running on `http://localhost:8000`:

- **Upload**: `POST /api/upload`
- **Sections**: `GET /api/sections/{video_id}`
- **Chat**: `POST /api/chat/{video_id}`
- **Visual Search**: `GET /api/visual-search/{video_id}`
- **Frame Extraction**: `POST /api/videos/{video_id}/extract-frames`
- **Embeddings**: `POST /api/videos/{video_id}/generate-embeddings`

## 🎨 UI/UX Features

### Tab-based Navigation
- Clean tab interface for different features
- Disabled states for unavailable features
- Progressive disclosure of functionality

### Real-time Feedback
- Loading states for all operations
- Progress indicators for long-running tasks
- Error handling with user-friendly messages

### Accessibility
- Proper ARIA labels
- Keyboard navigation support
- Screen reader friendly
- High contrast colors

## 🔄 State Management

### VideoContext Pattern
```typescript
interface VideoState {
  currentVideo: Video | null
  sections: Section[]
  frames: Frame[]
  chatHistory: ChatResponse[]
  isLoading: boolean
  error: string | null
  conversationId: string | null
}
```

### Actions
- `SET_VIDEO`: Update current video
- `SET_SECTIONS`: Update video sections
- `SET_FRAMES`: Update extracted frames
- `ADD_CHAT_MESSAGE`: Add new chat response
- `SET_LOADING`: Update loading state
- `SET_ERROR`: Handle errors

## 🚀 Production Deployment

### Environment Variables
```bash
NEXT_PUBLIC_API_URL=https://your-api-domain.com
```

### Build & Deploy
```bash
npm run build
npm start  # or deploy to Vercel/Netlify
```

## 🎯 Key Features Walkthrough

1. **Smart Upload**: Validates YouTube URLs and provides processing feedback
2. **Interactive Player**: Synchronized video playback with AI-generated sections
3. **Intelligent Chat**: Context-aware responses with source citations
4. **Advanced Search**: Multi-modal search across video content
5. **Responsive Design**: Works seamlessly on all devices

Built with ❤️ using Next.js, TypeScript, and Tailwind CSS
