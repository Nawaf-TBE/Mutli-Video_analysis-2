#!/bin/bash

# Start the backend with SQLite database
export DATABASE_URL="sqlite:///./video_analysis.db"
python -m uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000 