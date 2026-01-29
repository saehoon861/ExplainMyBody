#!/bin/bash

# 터미널 1: Flask 서버
echo "🚀 Starting Flask backend..."
uv run python app.py &
BACKEND_PID=$!

# 잠시 대기
sleep 3

# 터미널 2: 프론트엔드 서버
echo "🌐 Starting frontend server..."
uv run python -m http.server 8000 &
FRONTEND_PID=$!

echo ""
echo "✅ Servers started!"
echo "📱 Frontend: http://localhost:8000"
echo "🔌 Backend: http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop all servers"

# Ctrl+C 처리
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT

# 대기
wait