.PHONY: help install test run docker-up docker-down docker-test clean

help:
	@echo "DevBud - Development Management Dashboard"
	@echo ""
	@echo "Available commands:"
	@echo "  make install      Install dependencies"
	@echo "  make test         Run tests"
	@echo "  make run          Run development server"
	@echo "  make docker-up    Start all services with Docker"
	@echo "  make docker-down  Stop all Docker services"
	@echo "  make docker-test  Run tests in Docker"
	@echo "  make clean        Clean up temporary files"

install:
	cd backend && python3 -m venv venv
	cd backend && . venv/bin/activate && pip install -r requirements.txt
	cd backend && cp .env.example .env
	@echo "Installation complete. Please edit backend/.env with your configuration."

test:
	cd backend && . venv/bin/activate && pytest -v

test-cov:
	cd backend && . venv/bin/activate && pytest -v --cov=app --cov-report=html --cov-report=term

run:
	cd backend && . venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

run-worker:
	cd backend && . venv/bin/activate && export $$(cat .env.local | xargs) && python -m celery -A app.services.task_queue worker --loglevel=info

run-worker-local:
	@echo "Starting Celery worker with local environment..."
	@echo "Make sure Claude Code CLI is installed and authenticated (claude login)"
	cd backend && export $$(cat .env.local | xargs) && PYTHONPATH=. venv/bin/python -m celery -A app.services.task_queue_sync worker --loglevel=info --pool=solo

run-flower:
	cd backend && . venv/bin/activate && celery -A app.services.task_queue flower --port=5555

docker-up:
	docker-compose up -d
	@echo "DevBud is running!"
	@echo "API: http://localhost:8000"
	@echo "API Docs: http://localhost:8000/docs"
	@echo "Flower (Celery Monitor): http://localhost:5555"

docker-up-hybrid:
	@echo "Starting DevBud in hybrid mode (worker runs locally)..."
	docker compose up -d db redis backend frontend flower
	@echo ""
	@echo "Services running in Docker:"
	@echo "  - API: http://localhost:8000/docs"
	@echo "  - Frontend: http://localhost:3000"
	@echo "  - Flower: http://localhost:5555"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Ensure Claude Code CLI is installed: npm install -g @anthropics/claude-code"
	@echo "  2. Login to Claude: claude login"
	@echo "  3. In a new terminal, run: make run-worker-local"

docker-down:
	docker-compose down

docker-test:
	docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit
	docker-compose -f docker-compose.test.yml down

docker-logs:
	docker-compose logs -f

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +