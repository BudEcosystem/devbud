# DevBud - Development Management Dashboard

DevBud is a comprehensive development management platform that enables developers to run code generation tasks using Claude Code CLI while monitoring progress in real-time. It features a modern web interface and supports multiple repository development with parallel task execution.

## Features

- **📊 Modern Web Dashboard**: React/Next.js frontend with real-time updates
- **🔄 Multi-Repository Support**: Manage multiple repositories simultaneously
- **⚡ Parallel Task Execution**: Run multiple tasks per repository in parallel
- **🌿 Git Worktree Isolation**: Each task runs in an isolated git worktree
- **📡 Real-time Monitoring**: Stream Claude Code output via WebSockets
- **📦 Automatic Dependencies**: Detects and installs project dependencies
- **📝 Task History**: Track completed, failed, and cancelled tasks
- **🚀 RESTful API**: Full API for repository and task management
- **🐳 Docker Support**: Complete containerized deployment

## Architecture

### Backend (Python/FastAPI)
- FastAPI for high-performance async API
- SQLAlchemy with PostgreSQL for data persistence  
- Celery for background task processing
- Redis for task queue and caching
- WebSockets for real-time updates
- Git worktree management for isolated environments

### Frontend (React/Next.js)
- Next.js 14 with TypeScript and App Router
- Tailwind CSS for modern styling
- React Query for server state management
- WebSocket client for real-time updates
- Responsive design for desktop and mobile

### Key Components
1. **Repository Manager**: Add, update, and manage git repositories
2. **Task Queue**: Celery-based task execution with Redis broker
3. **Worktree Manager**: Creates isolated git worktrees for each task
4. **Claude Runner**: Manages Claude Code CLI processes
5. **WebSocket Server**: Streams real-time output to clients

## Quick Start with Docker (Recommended)

### Prerequisites
- Docker and Docker Compose
- Git 2.5+
- Claude Code CLI installed and in PATH

### 1. Clone and start
```bash
git clone <repository-url>
cd devbud

# Start all services
docker compose up -d

# View logs (optional)
docker compose logs -f
```

### 2. Access the application
- **Frontend Dashboard**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### 3. Add your first repository
1. Open http://localhost:3000 in your browser
2. Click "Add Repository" 
3. Enter repository details:
   - **Name**: Your repository name
   - **Path**: Full path to your git repository (e.g., `/home/username/my-project`)
   - **Default Branch**: `main` or `master`
   - **Description**: Optional description

## Manual Installation

### Prerequisites
- Python 3.8+
- Node.js 18+
- PostgreSQL
- Redis
- Git 2.5+
- Claude Code CLI

### Backend Setup
```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your database credentials

# Setup database
createdb devbud_db
alembic upgrade head

# Start backend services
redis-server &
celery -A app.services.task_queue worker --loglevel=info &
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env.local
# Edit .env.local with API URLs

# Start development server
npm run dev
```

## API Documentation

Once the server is running, visit:
- API Documentation: http://localhost:8000/docs
- Alternative API Documentation: http://localhost:8000/redoc

## Usage

### 1. Add a Repository

```bash
curl -X POST http://localhost:8000/api/v1/repositories/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-project",
    "path": "/path/to/my-project",
    "default_branch": "main",
    "description": "My awesome project"
  }'
```

### 2. Create a Task

```bash
curl -X POST http://localhost:8000/api/v1/tasks/ \
  -H "Content-Type: application/json" \
  -d '{
    "repository_id": "<repository-uuid>",
    "branch_name": "feature-awesome",
    "instructions": "Implement a new authentication system with JWT tokens"
  }'
```

### 3. Monitor Task Progress

Connect to the WebSocket endpoint to receive real-time updates:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/task/<task-id>');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Task output:', data.output);
};
```

## Testing

The project follows Test-Driven Development (TDD) practices.

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test categories
pytest -m unit        # Unit tests only
pytest -m integration # Integration tests only
```

## Docker Commands

```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f

# Stop all services
docker compose down

# Rebuild and restart
docker compose up --build -d

# Access containers
docker compose exec backend bash
docker compose exec frontend sh
```

## Project Structure

```
devbud/
├── backend/                 # Python FastAPI backend
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Core configuration
│   │   ├── models/         # Database models
│   │   ├── schemas/        # Pydantic schemas
│   │   └── services/       # Business logic services
│   ├── tests/              # Backend tests
│   ├── alembic/            # Database migrations
│   └── requirements.txt    # Python dependencies
├── frontend/               # React/Next.js frontend
│   ├── src/
│   │   ├── app/           # Next.js app directory
│   │   ├── components/    # React components
│   │   ├── lib/          # Utility libraries
│   │   └── types/        # TypeScript types
│   └── package.json      # Node.js dependencies
├── docker-compose.yml     # Docker orchestration
├── .env                   # Environment configuration
└── README.md             # This file
```

## Environment Variables

See `.env` file for all configuration options:

- `SECRET_KEY`: JWT secret key for authentication
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `CLAUDE_MODEL`: Claude model to use (default: opus-4)
- `WORKTREE_BASE_PATH`: Base path for git worktrees
- `MAX_CONCURRENT_TASKS_PER_REPO`: Task concurrency limit

## API Endpoints

### Repositories
- `POST /api/v1/repositories/` - Create repository
- `GET /api/v1/repositories/` - List repositories
- `GET /api/v1/repositories/{id}` - Get repository details
- `PATCH /api/v1/repositories/{id}` - Update repository
- `DELETE /api/v1/repositories/{id}` - Delete repository
- `GET /api/v1/repositories/{id}/tasks` - Get repository tasks

### Tasks
- `POST /api/v1/tasks/` - Create task
- `GET /api/v1/tasks/` - List tasks
- `GET /api/v1/tasks/{id}` - Get task details
- `POST /api/v1/tasks/{id}/cancel` - Cancel task
- `GET /api/v1/tasks/{id}/output` - Get task output

### WebSocket
- `WS /ws/task/{id}` - Stream task output
- `WS /ws/tasks` - Monitor all tasks

## Development Workflow

1. Each task creates a new git worktree
2. Dependencies are automatically installed
3. Claude Code CLI is spawned with the provided instructions
4. Output is streamed in real-time via WebSockets
5. Worktrees can be cleaned up after task completion

## Troubleshooting

### Claude Code not found
Ensure Claude Code CLI is installed and available in your PATH:
```bash
which claude
```

### Database connection errors
Check your PostgreSQL service is running and credentials in `.env` are correct:
```bash
psql -U devbud -d devbud_db -h localhost
```

### Redis connection errors
Ensure Redis is running:
```bash
redis-cli ping
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Write tests for your changes
4. Implement the feature
5. Ensure all tests pass
6. Submit a pull request

## License

[Add your license here]

## Acknowledgments

- Inspired by [Talkito](https://github.com/robdmac/talkito) for Claude communication patterns
- Worktree management inspired by [wt](https://github.com/roderik/wt/)