.PHONY: lint format type test clean upgrade help

help:  ## Display this help message
	@echo "Usage: make [target] ..."
	@echo ""
	@echo "Targets:"
	@echo "  test    Run pytest against all tests"
	@echo "  lint    Run ruff linter against all files"
	@echo "  format  Run black and isort against all Python files"
	@echo "  clean   Remove all .pytest_cache and __pycache__ directories"
	@echo "  upgrade Upgrade all Python packages to latest versions using pdm"
	@echo "  type    Run mypy against all Python files"
	@echo "  help    Display this help message"

test:  ## Run pytest against all tests
	@pytest -v

lint:  ## Run ruff linter against all files
	@ruff check ./

format:  ## Run black and isort against all Python files
	@black ./
	@isort --profile black ./

clean: ## Remove all .pytest_cache and __pycache__ directories
	@find . -type d -name .pytest_cache -exec rm -rf {} +
	@find . -type d -name __pycache__ -exec rm -rf {} +
	@find . -type d -name build -exec rm -rf {} +
	@find . -type d -name "requirements.egg-info" -exec rm -rf {} +

upgrade:  ## Upgrade all Python packages to latest versions using pdm
	pdm update

type:  ## Run mypy against all Python files
	@mypy --config-file ./mypy.ini ./
