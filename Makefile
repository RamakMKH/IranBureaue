# ============================================
# Makefile (Development Commands)
# ============================================

.PHONY: help install run test format lint clean docker-build docker-up docker-down

help:
	@echo "News Management System - Make Commands"
	@echo ""
	@echo "install       Install dependencies"
	@echo "run           Run development server"
	@echo "setup         Run setup utility"
	@echo "test          Run tests"
	@echo "format        Format code with black"
	@echo "lint          Lint code with flake8"
	@echo "clean         Clean temporary files"
	@echo "docker-build  Build Docker image"
	@echo "docker-up     Start Docker containers"
	@echo "docker-down   Stop Docker containers"
	@echo "migrate       Run database migrations"

install:
	pip install -r requirements.txt

run:
	python main.py

setup:
	python setup.py

test:
	pytest tests/ -v

format:
	black app/ tests/
	isort app/ tests/

lint:
	flake8 app/ tests/
	mypy app/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.log" -delete
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf htmlcov
	rm -rf dist
	rm -rf build
	rm -rf *.egg-info

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

migrate:
	alembic upgrade head
