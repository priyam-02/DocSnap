.PHONY: lint format type-check test clean help

help:
	@echo "Available commands:"
	@echo "  make lint        - Run ruff linter"
	@echo "  make format      - Format code with black and ruff"
	@echo "  make type-check  - Run mypy type checker"
	@echo "  make test        - Run pytest with coverage"
	@echo "  make clean       - Remove cache and build files"

lint:
	@echo "Running ruff linter..."
	ruff check api/

format:
	@echo "Formatting with black..."
	black api/
	@echo "Auto-fixing with ruff..."
	ruff check --fix api/

type-check:
	@echo "Running mypy type checker..."
	mypy api/

test:
	@echo "Running tests with coverage..."
	pytest tests/ -v --cov=api --cov-report=term-missing --cov-report=html

clean:
	@echo "Cleaning cache and build files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage
	@echo "Clean complete!"
