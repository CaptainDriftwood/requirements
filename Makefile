.PHONY: help
help:  ## Display this help message
	@echo "Usage: make [target] ..."
	@echo ""
	@echo "Targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {if ($$1 == "help") printf "  %-10s %s\n", $$1, $$2}' && \
	grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {if ($$1 != "help") printf "  %-10s %s\n", $$1, $$2}' | sort

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
