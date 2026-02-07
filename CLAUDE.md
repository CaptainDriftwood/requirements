# Claude Code Project Rules

## Testing Guidelines

- **Prefer test functions over test classes**: When a test module would contain only one test class, use standalone test functions instead. Only use test classes when grouping multiple related test scenarios with shared fixtures or setup.
- **Use pytest.parametrize for multiple test cases**: When testing multiple inputs or scenarios for the same behavior, use `@pytest.mark.parametrize` instead of multiple assertions in a single test or separate test functions for each case.

## Code Style

- Follow existing patterns in the codebase
- Use type hints for all function signatures
- Keep functions focused and single-purpose