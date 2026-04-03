#!/bin/bash
# Start both backend API and Telegram bot together
# For Render.com free plan (single web service)

set -e

echo "🚀 Starting Rustam Barber services..."

# Get PORT from environment or use default
PORT=${PORT:-8000}

echo "📡 Starting FastAPI backend on port $PORT..."
# Start uvicorn in background
uvicorn backend.main:app --host 0.0.0.0 --port $PORT &
BACKEND_PID=$!

# Wait a bit for backend to start
sleep 3

echo "🤖 Starting Telegram bot..."
# Start bot in background
python backend/bot.py &
BOT_PID=$!

echo "✅ All services started!"
echo "   - Backend PID: $BACKEND_PID"
echo "   - Bot PID: $BOT_PID"

# Wait for both processes
wait $BACKEND_PID $BOT_PID
