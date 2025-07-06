# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DevBud is a development management dashboard that allows developers to run code generation tasks using Claude Code CLI while monitoring progress in real-time. It consists of a Python/FastAPI backend and React/Next.js frontend, using Docker Compose for orchestration.

## Essential Commands

### Quick Start
```bash
# Start all services with Docker (recommended)
make docker-up
# OR
docker compose up -d

# Access points:
# - Frontend: http://localhost:3000
# - API: http://localhost:8000/docs
# - Flower (Celery monitor): http://localhost:5555
```

### Hybrid Mode Setup (Recommended for Claude Code CLI)
```bash
# Run this setup script to configure hybrid mode
./setup-hybrid.sh

# OR manually:
# 1. Start Docker services (excluding worker)
make docker-up-hybrid

# 2. In a new terminal, run the worker locally
make run-worker-local

# This allows Claude Code CLI to use browser authentication
# while other services run in Docker containers
```

### Backend Development
```bash
# From /backend directory
make install          # Install dependencies in virtual environment
make run             # Run API server (port 8000)
make run-worker      # Run Celery worker for background tasks
make test            # Run all tests
make test-cov        # Run tests with coverage report
pytest -m unit       # Run only unit tests
pytest -m integration # Run only integration tests
```

### Frontend Development
```bash
# From /frontend directory
npm run dev          # Start development server with hot reload (port 3000)
npm run lint         # Run ESLint for code quality
npm run build        # Create production build
npm start            # Serve production build
```

### Docker Operations
```bash
make docker-up       # Start all services
make docker-down     # Stop all services
make docker-test     # Run tests in Docker
make docker-logs     # View logs from all services
```

## Architecture Overview

### Backend Architecture
- **FastAPI** serves RESTful APIs with automatic documentation at `/docs`
- **PostgreSQL** for persistent data storage (models in `backend/app/models/`)
- **Redis + Celery** for task queue and background job processing
- **WebSockets** for real-time streaming of Claude Code output
- **Git Worktrees** provide isolated environments for each task execution
- **SQLAlchemy** ORM with async support for database operations
- **Alembic** manages database schema migrations

### Frontend Architecture
- **Next.js 14** with App Router for server-side rendering and routing
- **TypeScript** for type safety across the application
- **React Query** manages server state and caching
- **Zustand** for client-side state management
- **Socket.io Client** handles WebSocket connections for real-time updates
- **Tailwind CSS v4** for styling with utility classes
- **Radix UI** provides accessible component primitives

### Key Service Interactions
1. Frontend makes API calls to backend endpoints (`/api/repositories`, `/api/tasks`)
2. Backend creates Celery tasks for long-running operations
3. Celery workers execute Claude Code CLI in isolated git worktrees
4. Output streams via WebSocket to frontend in real-time
5. PostgreSQL stores repository and task metadata
6. Redis acts as message broker between API and workers

## Development Patterns

### API Endpoints
- All API routes are defined in `backend/app/api/endpoints/`
- Pydantic schemas in `backend/app/schemas/` handle validation
- Business logic lives in `backend/app/services/`

### Frontend Components
- Page components in `frontend/src/app/` follow Next.js App Router conventions
- Reusable components in `frontend/src/components/`
- API client and types in `frontend/src/lib/` and `frontend/src/types/`

### Database Changes
```bash
# Create new migration after model changes
cd backend
alembic revision --autogenerate -m "Description of changes"
alembic upgrade head  # Apply migrations
```

### Testing Strategy
- Backend uses pytest with unit/integration test markers
- Tests require PostgreSQL and Redis running (use Docker)
- Frontend testing can be added using Jest/React Testing Library

## Common Tasks

### Adding New API Endpoint
1. Create endpoint in `backend/app/api/endpoints/`
2. Define Pydantic schemas in `backend/app/schemas/`
3. Add business logic to `backend/app/services/`
4. Update frontend API client in `frontend/src/lib/api.ts`
5. Add TypeScript types in `frontend/src/types/`

### Working with Git Worktrees
- In Docker mode: Worktrees are created in `backend/data/worktrees/`
- In Hybrid mode: Worktrees are created in `~/workspace/`
- Each task gets a unique worktree for isolation
- Cleanup happens automatically or via API endpoint

### Debugging WebSocket Issues
- Check browser console for connection errors
- Verify Redis is running for message broker
- Check Celery worker logs: `make docker-logs`
- Frontend WebSocket client: `frontend/src/lib/websocket.ts`

## Hybrid Mode Details

When running in hybrid mode (recommended for Claude Code CLI):

1. **Why Hybrid Mode?**
   - Claude Code CLI requires browser authentication
   - Running inside Docker prevents access to browser login
   - Hybrid mode runs the worker locally with Claude access

2. **Configuration**
   - Docker services use internal networking
   - Worker connects to exposed ports on localhost
   - Environment configured in `backend/.env.local`

3. **File Locations**
   - Worktrees: `~/workspace/` (on host)
   - Repositories: `/home/budadmin/` (mounted in containers)
   - SSH keys: `~/.ssh/` (available to worker)

4. **Prerequisites**
   - Claude Code CLI installed: `npm install -g @anthropics/claude-code`
   - Authenticated: `claude login`
   - Python 3.8+ with venv support