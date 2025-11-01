.PHONY: install test lint format clean build publish dev-install help coverage

# Default target
help:
	@echo "Available targets:"
	@echo "  install      - Install package in development mode"
	@echo "  dev-install  - Install with all development dependencies"
	@echo "  test         - Run tests"
	@echo "  coverage     - Run tests with coverage report"
	@echo "  coverage-html - Run tests with coverage and open HTML report"
	@echo "  lint         - Run linting (black, isort, mypy, flake8)"
	@echo "  format       - Format code (black, isort)"
	@echo "  clean        - Clean build artifacts"
	@echo "  build        - Build package"
	@echo "  publish      - Publish to PyPI (requires PYPI_TOKEN)"
	@echo "  examples     - Run example scripts"
	@echo "  pre-commit   - Install and run pre-commit hooks"
	@echo "  setup        - Complete development environment setup"
	@echo "  check        - Run all checks (lint + test + examples)"

# Install package in development mode
install:
	pip install -e .

# Install with all development dependencies
dev-install:
	pip install -e ".[dev,all]"

# Run tests (coverage is now automatic via pyproject.toml)
test:
	pytest tests/

# Run tests with detailed coverage report
coverage:
	./scripts/coverage_report.sh

# Run tests with coverage and open HTML report
coverage-html:
	./scripts/coverage_report.sh --open

# Run linting
lint:
	black --check dataclass_config/ tests/ examples/
	isort --check-only dataclass_config/ tests/ examples/
	mypy dataclass_config/
	flake8 dataclass_config/

# Format code
format:
	black dataclass_config/ tests/ examples/
	isort dataclass_config/ tests/ examples/

# Clean build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf coverage.xml
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Build package
build: clean
	python -m build

# Publish to PyPI
publish: build
	twine check dist/*
	twine upload dist/*

# Run examples
examples:
	cd examples && python basic_example.py --name "MakeTest" --count 2 --debug true
	cd examples && python advanced_example.py --name "MakeTestServer" --debug false

# Install and run pre-commit hooks
pre-commit:
	pre-commit install
	pre-commit run --all-files

# Development setup
setup: dev-install pre-commit
	@echo "Development environment setup complete!"

# Full check (like CI)
check: lint test examples
	@echo "All checks passed!"
