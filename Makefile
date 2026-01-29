# AI-CPaaS Demo Makefile

.PHONY: help install dev test lint format clean run docker-build docker-run

# Default target
help:
	@echo "Available commands:"
	@echo "  install     Install dependencies"
	@echo "  dev         Install development dependencies"
	@echo "  test        Run all tests"
	@echo "  test-unit   Run unit tests only"
	@echo "  test-prop   Run property-based tests only"
	@echo "  lint        Run linting checks"
	@echo "  format      Format code"
	@echo "  clean       Clean up generated files"
	@echo "  run         Run the API server"
	@echo "  run-dev     Run the API server in development mode"

# Installation
install:
	poetry install --no-dev

dev:
	poetry install
	poetry run pre-commit install

# Testing
test:
	poetry run pytest

test-unit:
	poetry run pytest tests/unit/

test-integration:
	poetry run pytest tests/integration/

test-property:
	poetry run pytest tests/property/ -m property

test-coverage:
	poetry run pytest --cov --cov-report=html --cov-report=term

# Code quality
lint:
	poetry run flake8 src/ tests/
	poetry run mypy src/

format:
	poetry run black src/ tests/
	poetry run isort src/ tests/

format-check:
	poetry run black --check src/ tests/
	poetry run isort --check-only src/ tests/

# Development server
run:
	poetry run uvicorn ai_cpaas_demo.api.main:app --host 0.0.0.0 --port 8000

run-dev:
	poetry run uvicorn ai_cpaas_demo.api.main:app --host 0.0.0.0 --port 8000 --reload

# Cleanup
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/

# Docker (for containerized deployment)
docker-build:
	docker build -t ai-cpaas-demo .

docker-run:
	docker run -p 8000:8000 --env-file .env ai-cpaas-demo

# AWS CDK (for infrastructure)
cdk-synth:
	cd infrastructure && cdk synth

cdk-deploy:
	cd infrastructure && cdk deploy

cdk-destroy:
	cd infrastructure && cdk destroy

# Database migrations (for open source variant)
db-upgrade:
	poetry run alembic upgrade head

db-downgrade:
	poetry run alembic downgrade -1

# Demo data
seed-demo-data:
	poetry run python -m ai_cpaas_demo.scripts.seed_demo_data

# Property-based test with specific iterations
test-property-verbose:
	poetry run pytest tests/property/ -v --hypothesis-show-statistics