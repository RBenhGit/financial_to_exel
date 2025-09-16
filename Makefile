# Makefile for Financial Analysis Toolkit
# Provides common development tasks including test coverage analysis

.PHONY: help test test-unit test-integration test-coverage coverage-report coverage-analysis clean install lint format check-all

# Default target
help:
	@echo "Financial Analysis Toolkit - Development Commands"
	@echo ""
	@echo "Testing & Coverage:"
	@echo "  test                Run basic tests"
	@echo "  test-unit           Run unit tests"
	@echo "  test-integration    Run integration tests"
	@echo "  test-coverage       Run tests with coverage reporting"
	@echo "  coverage-report     Generate HTML coverage report"
	@echo "  coverage-analysis   Full coverage analysis with recommendations"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint                Run code linting (ruff, flake8)"
	@echo "  format              Format code (black, isort)"
	@echo "  check-all           Run all quality checks"
	@echo ""
	@echo "Environment:"
	@echo "  install             Install dependencies"
	@echo "  clean               Clean build artifacts and cache"
	@echo ""
	@echo "Application:"
	@echo "  run-app             Start Streamlit application"
	@echo "  run-app-dev         Start Streamlit in development mode"

# Testing targets
test:
	pytest tests/test_basic.py -v

test-unit:
	pytest tests/unit/ -v --tb=short

test-integration:
	pytest tests/integration/ -v --tb=short

test-coverage:
	pytest tests/test_basic.py --cov=core --cov=config --cov=utils --cov-report=html --cov-report=term-missing

coverage-report: test-coverage
	@echo "Coverage report generated in htmlcov/index.html"
	@if command -v start >/dev/null 2>&1; then start htmlcov/index.html; \
	elif command -v open >/dev/null 2>&1; then open htmlcov/index.html; \
	elif command -v xdg-open >/dev/null 2>&1; then xdg-open htmlcov/index.html; fi

coverage-analysis:
	python tools/scripts/run_coverage_analysis.py

# Code quality targets
lint:
	@echo "Running code linting..."
	ruff check .
	flake8 .

format:
	@echo "Formatting code..."
	black --line-length 100 .
	isort .

check-all: lint
	@echo "Running comprehensive code quality checks..."
	pytest --collect-only >/dev/null
	@echo "All quality checks passed!"

# Environment targets
install:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

clean:
	@echo "Cleaning build artifacts and cache..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf coverage.json
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Application targets
run-app:
	python run_streamlit_app.py

run-app-dev:
	streamlit run fcf_analysis_streamlit.py --server.runOnSave true