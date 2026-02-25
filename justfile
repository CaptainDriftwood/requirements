# Default recipe to run when just is called without arguments
[private]
default: help

# Display this help message
help:
    @echo "Usage: just [recipe] ..."
    @echo ""
    @echo "Recipes:"
    @just --list --unsorted

# Run pytest against all tests (parallel)
test:
    @uv run pytest -n auto

# Run pytest with minimal output for quick verification
test-quick:
    @uv run pytest -n auto -q

# Run only unit tests (fast, no I/O)
test-unit:
    @uv run pytest tests/unit -n auto -q

# Run only integration tests (CLI, file system)
test-integration:
    @uv run pytest tests/integration -n auto -q

# Run ruff linter against all files
lint:
    @uv run ruff check ./

# Run ruff formatter against all Python files
format:
    @uv run ruff check --fix ./
    @uv run ruff format ./

# Clean untracked files, preserving .claude, .venv, .idea, .run
clean:
    git clean -fdx -e .claude -e .venv -e .idea -e .run

# Show what clean would remove (dry-run)
clean-dry:
    git clean -ndx -e .claude -e .venv -e .idea -e .run

# Clean interactively, prompting for each file
clean-i:
    git clean -idx -e .claude -e .venv -e .idea -e .run

# Upgrade all Python packages to latest versions using uv
upgrade:
    uv sync --upgrade

# Run ty type checker against all Python files
type:
    @uv run --with ty ty check src tests

# Run all quality checks (format, lint, type, test)
check: format lint type test

# Build the package
build:
    uv build

# Install package in development mode
install:
    uv pip install -e .

# Run tests across all supported Python versions
nox *ARGS:
    uvx nox {{ ARGS }}