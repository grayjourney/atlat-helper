# =============================================================================
# Project Management Agent - Makefile
# =============================================================================
# Developer convenience commands for common tasks.
#
# Usage:
#   make help      # Show all available commands
#   make dev       # Start development environment
#   make test      # Run tests
#   make lint      # Run linter
# =============================================================================

.PHONY: help dev up down logs test lint format clean build push

# Default target
help:
	@echo "🚀 Project Management Agent - Available Commands"
	@echo "================================================"
	@echo ""
	@echo "Development:"
	@echo "  make dev        Start development environment (docker compose up)"
	@echo "  make up         Start containers in background"
	@echo "  make down       Stop all containers"
	@echo "  make logs       Follow container logs"
	@echo "  make shell      Open shell in API container"
	@echo ""
	@echo "Testing:"
	@echo "  make test       Run all tests"
	@echo "  make test-cov   Run tests with coverage report"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint       Run linter (ruff)"
	@echo "  make format     Format code (black)"
	@echo "  make typecheck  Run type checker (mypy)"
	@echo ""
	@echo "Docker:"
	@echo "  make build      Build production Docker image"
	@echo "  make push       Push image to registry"
	@echo "  make clean      Remove containers, volumes, and cache"

# =============================================================================
# Development
# =============================================================================

dev:
	docker compose up

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

shell:
	docker compose exec api bash

# =============================================================================
# Testing
# =============================================================================

test:
	docker compose exec api pytest tests/ -v

test-cov:
	docker compose exec api pytest tests/ -v --cov=src --cov-report=html
	@echo "Coverage report: htmlcov/index.html"

# Local testing (without Docker)
test-local:
	pytest tests/ -v

# =============================================================================
# Code Quality
# =============================================================================

lint:
	ruff check src/ tests/

format:
	black src/ tests/
	ruff check --fix src/ tests/

typecheck:
	mypy src/

# =============================================================================
# Docker Build & Push
# =============================================================================

IMAGE_NAME ?= atlat-helper
IMAGE_TAG ?= latest
REGISTRY ?= ghcr.io/$(shell git config user.name)

build:
	docker build -t $(IMAGE_NAME):$(IMAGE_TAG) .

push: build
	docker tag $(IMAGE_NAME):$(IMAGE_TAG) $(REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG)
	docker push $(REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG)

# =============================================================================
# Cleanup
# =============================================================================

clean:
	docker compose down -v --rmi local
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .coverage htmlcov/ .mypy_cache/ .ruff_cache/
