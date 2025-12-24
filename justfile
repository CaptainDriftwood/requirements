# Default recipe to run when just is called without arguments
[private]
default: help

# Display this help message
help:
    @echo "Usage: just [recipe] ..."
    @echo ""
    @echo "Recipes:"
    @just --list --unsorted

# Run pytest against all tests
test:
    @uv run pytest

# Run pytest with minimal output for quick verification
test-quick:
    @uv run pytest -q

# Run ruff linter against all files
lint:
    @uv run ruff check ./

# Run ruff formatter against all Python files
format:
    @uv run ruff check --fix ./
    @uv run ruff format ./

# Clean untracked files (use: just clean --dry-run)
clean *ARGS:
    @python clean.py {{ ARGS }}

# Upgrade all Python packages to latest versions using uv
upgrade:
    uv sync --upgrade

# Run mypy against all Python files
type:
    @uv run mypy ./

# Run all quality checks (lint, type, test)
check: lint type test

# Build the package
build:
    uv build

# Install package in development mode
install:
    uv pip install -e .

# Run tests across all supported Python versions
nox *ARGS:
    uvx nox {{ ARGS }}