#!/usr/bin/env bash
# Launch Senthium Web Dashboard
# Starts both Go backend and Next.js frontend

set -e

echo "🚀 Starting Senthium Web Dashboard"
echo "===================================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if Go is installed
if ! command -v go &> /dev/null; then
    echo "❌ Go is not installed. Please install Go 1.21 or later."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18 or later."
    exit 1
fi

# Build and start Go server
echo -e "${BLUE}[1/2]${NC} Starting Go backend server..."
cd server
go mod download
go build -o senthium-server main.go
./senthium-server &
GO_PID=$!
cd ..

echo -e "${GREEN}✓${NC} Go server started (PID: $GO_PID)"
echo ""

# Wait a moment for Go server to start
sleep 2

# Start Next.js frontend
echo -e "${BLUE}[2/2]${NC} Starting Next.js frontend..."
cd dashboard
npm install
npm run dev &
NEXT_PID=$!
cd ..

echo -e "${GREEN}✓${NC} Next.js frontend started (PID: $NEXT_PID)"
echo ""

echo "===================================="
echo -e "${GREEN}✨ Dashboard is ready!${NC}"
echo ""
echo "📊 Frontend: http://localhost:3000"
echo "🔌 Backend:  http://localhost:8080"
echo ""
echo "Press Ctrl+C to stop both servers"

# Cleanup function
cleanup() {
    echo ""
    echo "🛑 Stopping servers..."
    kill $GO_PID $NEXT_PID 2>/dev/null
    echo "✓ Servers stopped"
    exit 0
}

trap cleanup INT TERM

# Wait for both processes
wait
