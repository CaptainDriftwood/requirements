.PHONY: lint format type test upgrade help

help:  ## Display this help message
	@echo "Usage: make [target] ..."
	@echo ""
	@echo "Targets:"
	@echo "  test    Run pytest against all tests"
	@echo "  lint    Run ruff linter against all files"
	@echo "  format  Run ruff formatter against all Python files"
	@echo "  clean   Remove all .pytest_cache and __pycache__ directories"
	@echo "  upgrade Upgrade all Python packages to latest versions using uv"
	@echo "  type    Run mypy against all Python files"
	@echo "  help    Display this help message"

test:  ## Run pytest against all tests
	@uv run pytest

lint:  ## Run ruff linter against all files
	@uv run ruff check ./

format:  ## Run ruff formatter against all Python files
	@uv run ruff check --fix ./
	@uv run ruff format ./

upgrade:  ## Upgrade all Python packages to latest versions using uv
	uv sync --upgrade

type:  ## Run mypy against all Python files
	@uv run mypy ./
