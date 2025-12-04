.PHONY: help install dev test lint format db-up db-down seed clean

help:
	@echo "Available commands:"
	@echo "  install    - Install dependencies"
	@echo "  dev        - Run development server"
	@echo "  test       - Run tests"
	@echo "  lint       - Run linter"
	@echo "  format     - Format code"
	@echo "  db-up      - Start PostgreSQL container"
	@echo "  db-down    - Stop PostgreSQL container"
	@echo "  db-reset   - Reset database (destroy and recreate)"
	@echo "  seed       - Seed knowledge base"
	@echo "  clean      - Clean build artifacts"

install:
	pip install -e ".[dev]"

dev:
	uvicorn src.support_agent.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest tests/ -v --cov=src/support_agent --cov-report=term-missing

lint:
	ruff check src/ tests/

format:
	ruff format src/ tests/

db-up:
	docker-compose up -d postgres

db-down:
	docker-compose down

db-reset:
	docker-compose down -v
	docker-compose up -d postgres
	@echo "Waiting for database to be ready..."
	@sleep 3

seed:
	python scripts/seed_knowledge_base.py

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .coverage htmlcov dist build *.egg-info
