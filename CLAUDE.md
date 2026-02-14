# Claude Code Project Rules

## Project Overview

CLI tool for managing `requirements.txt` files in Python monorepos. Entry point is `src/requirements/main.py` using Click.

### Module Responsibilities

- `main.py` - CLI commands and user-facing output (Click command group)
- `files.py` - File discovery, excludes venv/.venv/.aws-sam directories
- `packages.py` - Package name matching (handles extras, URLs, VCS, normalization)
- `sorting.py` - Alphabetical sorting with path references at end
- `config.py` - User config at ~/.requirements/config.toml
- `console.py` - Rich console with color priority chain
- `pypi.py` - PEP 503 Simple API client for version queries

## Development

```bash
just check      # Run all checks (format, lint, type, test)
just test       # Run all tests
just test-unit  # Run unit tests only (fast)
just lint       # Run ruff linter
just format     # Format and fix with ruff
just type       # Run ty type checker
```

## Testing Guidelines

- **Prefer test functions over test classes**: Use standalone test functions unless grouping related scenarios with shared fixtures.
- **Use pytest.parametrize**: For multiple inputs or scenarios, use `@pytest.mark.parametrize` instead of multiple assertions or separate test functions.
- **Use pyfakefs**: For filesystem tests, use fixtures from `conftest.py` (e.g., `single_requirements_file`, `fs`) not `tempfile`.
- **Test organization**: Unit tests in `tests/unit/`, integration tests in `tests/integration/`.
- **Coverage minimum**: 90% required.

## Code Style

- Follow existing patterns in the codebase
- Use type hints for all function signatures
- Keep functions focused and single-purpose

## Code Patterns

- **Error handling**: Use `click.ClickException` for user-facing errors
- **Console output**: Use the shared `console` from Click context, not `print()`
- **Color priority**: CLI flag > NO_COLOR env > config > auto-detect
- **Package matching**: Always normalize names (hyphens/underscores equivalent, case-insensitive)
- **Preview mode**: All modification commands must support `--preview` with unified diff output
- **Sorting**: Alphabetical with path references (`./`, `../`, `-e`) at end

## Avoid

- Don't use `tempfile` for tests—use pyfakefs fixtures
- Don't add commands without `--preview` support
- Don't hardcode colors—use the theme in `console.py`
- Don't break PEP 440 version specifier compatibility
- Never add Co-Authored-By lines to commits