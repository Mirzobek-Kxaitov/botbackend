#!/bin/bash
# Start FastAPI backend (bot manager runs inside FastAPI via startup event)
# For Render.com free plan (single web service)

echo "🚀 Starting Barbers Platform services..."

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "📌 Working from: $SCRIPT_DIR"

PORT=${PORT:-8000}
echo "📌 Using PORT: $PORT"

# Wait during deployment to avoid bot conflicts
if [ "$RENDER" = "true" ]; then
    echo "⏳ Waiting 45 seconds for old bot instances to shutdown..."
    sleep 45
fi

echo "📡 Starting FastAPI (with integrated bot manager) on port $PORT..."
cd "$SCRIPT_DIR/backend"
exec python3 -m uvicorn main:app --host 0.0.0.0 --port $PORT
