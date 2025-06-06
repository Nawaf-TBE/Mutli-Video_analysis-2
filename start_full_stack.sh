#!/bin/bash

# Multi-Video Analysis Platform - Full Stack Startup Script
# This script starts both the FastAPI backend and Next.js frontend

set -e  # Exit on any error

echo "🚀 Starting Multi-Video Analysis Platform..."
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a port is in use
port_in_use() {
    lsof -i :$1 >/dev/null 2>&1
}

# Check dependencies
echo -e "${BLUE}📋 Checking dependencies...${NC}"

if ! command_exists python3; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    exit 1
fi

if ! command_exists node; then
    echo -e "${RED}❌ Node.js is not installed${NC}"
    exit 1
fi

if ! command_exists npm; then
    echo -e "${RED}❌ npm is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ All dependencies are installed${NC}"

# Check if ports are available
if port_in_use 8000; then
    echo -e "${YELLOW}⚠️  Port 8000 is already in use (backend)${NC}"
    read -p "Do you want to continue? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

if port_in_use 3000; then
    echo -e "${YELLOW}⚠️  Port 3000 is already in use (frontend)${NC}"
    read -p "Do you want to continue? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Start backend
echo -e "${BLUE}🖥️  Starting FastAPI Backend (Port 8000)...${NC}"
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Virtual environment not found. Please run setup first.${NC}"
    exit 1
fi

# Activate virtual environment and start backend
source venv/bin/activate
echo -e "${GREEN}✅ Virtual environment activated${NC}"

# Install backend dependencies if needed
if [ ! -f "venv/.installed" ]; then
    echo -e "${YELLOW}📦 Installing backend dependencies...${NC}"
    pip install -r requirements.txt
    touch venv/.installed
fi

# Start backend in background
echo -e "${BLUE}🚀 Starting backend server...${NC}"
uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
echo -e "${GREEN}✅ Backend started with PID: $BACKEND_PID${NC}"

# Wait for backend to start
echo -e "${BLUE}⏳ Waiting for backend to be ready...${NC}"
sleep 5

# Check if backend is running
if ! port_in_use 8000; then
    echo -e "${RED}❌ Backend failed to start${NC}"
    exit 1
fi

# Start frontend
echo -e "${BLUE}🌐 Starting Next.js Frontend (Port 3000)...${NC}"
cd frontend

# Install frontend dependencies if needed
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}📦 Installing frontend dependencies...${NC}"
    npm install
fi

# Start frontend in background
echo -e "${BLUE}🚀 Starting frontend server...${NC}"
npm run dev &
FRONTEND_PID=$!
echo -e "${GREEN}✅ Frontend started with PID: $FRONTEND_PID${NC}"

# Wait for frontend to start
echo -e "${BLUE}⏳ Waiting for frontend to be ready...${NC}"
sleep 8

cd ..

# Final status
echo
echo -e "${GREEN}🎉 Multi-Video Analysis Platform is now running!${NC}"
echo "=============================================="
echo -e "${BLUE}📊 Backend API:${NC} http://localhost:8000"
echo -e "${BLUE}📊 API Docs:${NC} http://localhost:8000/docs"
echo -e "${BLUE}🌐 Frontend:${NC} http://localhost:3000"
echo
echo -e "${YELLOW}📝 Usage:${NC}"
echo "1. Open http://localhost:3000 in your browser"
echo "2. Upload a YouTube video URL"
echo "3. Chat with the video content"
echo "4. Search video frames visually"
echo
echo -e "${YELLOW}⚠️  To stop the services:${NC}"
echo "Press Ctrl+C to stop this script"
echo "Or run: pkill -f uvicorn && pkill -f next"
echo

# Keep script running and handle Ctrl+C
trap 'echo -e "\n${YELLOW}🛑 Stopping services...${NC}"; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0' INT

# Wait for user to stop
while true; do
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        echo -e "${RED}❌ Backend process died${NC}"
        break
    fi
    if ! kill -0 $FRONTEND_PID 2>/dev/null; then
        echo -e "${RED}❌ Frontend process died${NC}"
        break
    fi
    sleep 2
done

echo -e "${YELLOW}🔧 Services stopped${NC}" 