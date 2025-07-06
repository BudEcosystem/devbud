#!/bin/bash
# Setup script for DevBud hybrid mode
# This script helps set up the environment for running the Celery worker locally
# while other services run in Docker

set -e

echo "DevBud Hybrid Mode Setup"
echo "========================"
echo ""

# Check if Claude Code CLI is installed
if ! command -v claude &> /dev/null; then
    echo "❌ Claude Code CLI is not installed."
    echo ""
    echo "Please install it using:"
    echo "  npm install -g @anthropics/claude-code"
    echo ""
    echo "Or visit: https://github.com/anthropics/claude-code"
    exit 1
else
    echo "✅ Claude Code CLI is installed"
fi

# Check if user is logged in to Claude
if ! claude api --help &> /dev/null 2>&1; then
    echo ""
    echo "⚠️  Please login to Claude Code CLI:"
    echo "  claude login"
    echo ""
    read -p "Press Enter after logging in to continue..."
else
    echo "✅ Claude Code CLI is authenticated"
fi

# Create worktree directory
WORKTREE_DIR="$HOME/workspace"
echo ""
echo "Creating worktree directory at: $WORKTREE_DIR"
mkdir -p "$WORKTREE_DIR"
echo "✅ Worktree directory created"

# Check if backend virtual environment exists
if [ ! -d "backend/venv" ]; then
    echo ""
    echo "Creating Python virtual environment..."
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cd ..
    echo "✅ Python environment set up"
else
    echo "✅ Python virtual environment exists"
fi

# Check if .env.local exists
if [ ! -f "backend/.env.local" ]; then
    echo ""
    echo "❌ backend/.env.local not found!"
    echo "This file should have been created. Please check the setup."
    exit 1
else
    echo "✅ Local environment configuration exists"
fi

# Start Docker services (excluding worker)
echo ""
echo "Starting Docker services (excluding worker)..."
docker compose up -d db redis backend frontend flower

# Wait for services to be ready
echo ""
echo "Waiting for services to be ready..."
sleep 10

# Check service health
echo ""
echo "Checking service status:"
echo "  - PostgreSQL: $(docker compose ps -q db &> /dev/null && echo '✅ Running' || echo '❌ Not running')"
echo "  - Redis: $(docker compose ps -q redis &> /dev/null && echo '✅ Running' || echo '❌ Not running')"
echo "  - Backend API: $(docker compose ps -q backend &> /dev/null && echo '✅ Running' || echo '❌ Not running')"
echo "  - Frontend: $(docker compose ps -q frontend &> /dev/null && echo '✅ Running' || echo '❌ Not running')"
echo "  - Flower: $(docker compose ps -q flower &> /dev/null && echo '✅ Running' || echo '❌ Not running')"

echo ""
echo "✅ Setup complete!"
echo ""
echo "Services available at:"
echo "  - Frontend: http://localhost:3000"
echo "  - API Docs: http://localhost:8000/docs"
echo "  - Flower (Celery Monitor): http://localhost:5555"
echo ""
echo "To start the Celery worker locally, run in a new terminal:"
echo "  make run-worker-local"
echo ""
echo "To stop all services:"
echo "  docker compose down"