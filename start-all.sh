#!/bin/bash
# Start both backend API and Multi-Bot Manager together
# For Render.com free plan (single web service)

echo "🚀 Starting Barbers Platform services..."

# Get current script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "📌 Working from: $SCRIPT_DIR"

# Get PORT from environment or use default
PORT=${PORT:-8000}
echo "📌 Using PORT: $PORT"

echo "📡 Starting FastAPI backend on port $PORT..."
# Start uvicorn from backend directory
cd "$SCRIPT_DIR/backend"
python3 -m uvicorn main:app --host 0.0.0.0 --port $PORT 2>&1 &
BACKEND_PID=$!
echo "📌 Backend PID: $BACKEND_PID"

# Wait a bit for backend to start
sleep 5

# Wait extra time during deployment to avoid bot conflicts
# This allows old instance to fully shutdown
if [ "$RENDER" = "true" ]; then
    echo "⏳ Waiting 45 seconds for old bot instances to shutdown..."
    sleep 45
fi

echo "🤖 Starting Multi-Bot Manager..."
# Start bot manager from backend directory (already in backend dir)
python3 bot_manager.py 2>&1 &
BOT_PID=$!
echo "📌 Bot Manager PID: $BOT_PID"

echo "✅ All services started!"
echo "   - Backend PID: $BACKEND_PID"
echo "   - Bot Manager PID: $BOT_PID"

# Keep script running and wait for both processes
wait -n $BACKEND_PID $BOT_PID
