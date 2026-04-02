#!/bin/bash
# Start script for Render.com

# Get PORT from environment or use default
PORT=${PORT:-8000}

# Start uvicorn
uvicorn backend.main:app --host 0.0.0.0 --port $PORT
