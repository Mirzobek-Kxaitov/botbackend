#!/bin/bash
# Start both backend API and Telegram bot together
# For Render.com free plan (single web service)

echo "🚀 Starting Rustam Barber services..."

# Get PORT from environment or use default
PORT=${PORT:-8000}
echo "📌 Using PORT: $PORT"

echo "📡 Starting FastAPI backend on port $PORT..."
# Start uvicorn in foreground briefly to see if it starts, then background
uvicorn backend.main:app --host 0.0.0.0 --port $PORT 2>&1 &
BACKEND_PID=$!
echo "📌 Backend PID: $BACKEND_PID"

# Wait a bit for backend to start
sleep 5

# Wait extra time during deployment to avoid bot conflicts
# This allows old instance to fully shutdown
if [ "$RENDER" = "true" ]; then
    echo "⏳ Waiting 30 seconds for old bot instance to shutdown..."
    sleep 30
fi

echo "🤖 Starting Telegram bot..."
# Start bot in background
python backend/bot.py 2>&1 &
BOT_PID=$!
echo "📌 Bot PID: $BOT_PID"

echo "✅ All services started!"
echo "   - Backend PID: $BACKEND_PID"
echo "   - Bot PID: $BOT_PID"

# Keep script running and wait for both processes
wait -n $BACKEND_PID $BOT_PID
