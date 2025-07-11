.PHONY: help
help:  ## Display this help message
	@echo "Usage: make [target] ..."
	@echo ""
	@echo "Targets:"
	@echo "  test    Run pytest against all tests"
	@echo "  lint    Run ruff linter against all files"
	@echo "  format  Run ruff formatter against all Python files"
	@echo "  clean   Clean untracked files (use clean ARGS=\"--dry-run\" for dry run)"
	@echo "  upgrade Upgrade all Python packages to latest versions using uv"
	@echo "  type    Run mypy against all Python files"
	@echo "  help    Display this help message"

.PHONY: test
test:  ## Run pytest against all tests
	@uv run pytest

.PHONY: lint
lint:  ## Run ruff linter against all files
	@uv run ruff check ./

.PHONY: format
format:  ## Run ruff formatter against all Python files
	@uv run ruff check --fix ./
	@uv run ruff format ./

.PHONY: clean
clean:  ## Clean untracked files (use clean ARGS="--dry-run" for dry run)
	@python clean.py $(ARGS)

.PHONY: upgrade
upgrade:  ## Upgrade all Python packages to latest versions using uv
	uv sync --upgrade

.PHONY: type
type:  ## Run mypy against all Python files
	@uv run mypy ./
