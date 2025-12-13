# Nova Agent CI/CD Workflows

This directory contains GitHub Actions workflows for the Nova Agent project.

## Workflow: ci.yml

The main CI workflow runs on every push and pull request with the following jobs:

### 1. Lint Job
- Runs code quality checks using:
  - **ruff**: Fast Python linter for common issues
  - **black**: Code formatter for consistent style
  - **mypy**: Static type checker

### 2. Test Job
- Depends on lint job passing
- Runs the pytest test suite
- Tests are run with `-q` flag for cleaner output

### 3. Build Job
- Depends on both lint and test jobs
- Currently runs even if previous jobs fail (for debugging)
- Placeholder for actual build/packaging steps

## Local Development

To run the same checks locally before pushing:

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r dev-requirements.txt

# Run linting checks
ruff check .
black --check .
mypy .

# Run tests
pytest -q

# Auto-fix common issues
python fix_lint_issues.py
```

## Common Issues and Solutions

### 1. Import Errors in Tests
- Ensure all dependencies are installed
- Check that conftest.py properly mocks external services

### 2. Many Linting Errors
- Run `ruff check . --fix --unsafe-fixes` to auto-fix common issues
- Run `black .` to format code automatically
- Manually fix remaining issues

### 3. Type Checking Errors
- Add type hints to functions
- Use `# type: ignore` sparingly for third-party libraries
- Configure mypy.ini for project-specific settings

## Debugging CI Failures

The build job has `if: ${{ always() }}` which means it runs even when lint/test fail. This helps with debugging by:
- Showing if the build environment is set up correctly
- Allowing you to add debug commands
- Providing logs even when earlier steps fail

Remember to remove this condition once CI is stable.

## Required Secrets

Currently none required, but you may need to add:
- `PYPI_TOKEN` for package publishing
- `CODECOV_TOKEN` for coverage reporting
- API keys for integration tests

## Next Steps

1. Fix the existing linting issues in the codebase
2. Ensure all tests pass locally
3. Remove the `always()` condition from the build job
4. Add actual build/deployment steps
5. Consider adding:
   - Coverage reporting
   - Security scanning
   - Documentation building
   - Release automation
