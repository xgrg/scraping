# CI/CD and Testing Guide

This project uses GitHub Actions for continuous integration with automated testing and coverage requirements.

## Requirements

- **Backend Coverage:** Minimum 80% code coverage for Python tests
- **Frontend Coverage:** Minimum 80% code coverage for JavaScript tests

## Backend Testing

### Setup

```bash
# Install dev dependencies
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests with coverage
pytest tests/ --cov=src/scraping --cov-report=term-missing

# Run specific test file
pytest tests/test_main.py -v

# Run with HTML coverage report
pytest tests/ --cov=src/scraping --cov-report=html
# Open htmlcov/index.html in browser
```

### Coverage Check

```bash
# Check coverage meets 80% threshold
coverage report --fail-under=80

# Generate detailed coverage report
coverage html
```

## Frontend Testing

### Setup

```bash
cd app
npm install
```

### Running Tests

```bash
# Run all tests
npm run test

# Run tests in watch mode
npm run test -- --watch

# Run tests with coverage
npm run test:coverage

# Run tests with UI
npm run test:ui
```

### Coverage Check

Coverage is automatically checked as part of the test run. Minimum 80% coverage required for:
- Lines
- Functions
- Branches
- Statements

## GitHub Actions Workflows

### Workflow Files

- **`.github/workflows/backend-ci.yml`** - Python tests on multiple versions (3.8, 3.9, 3.10, 3.11)
- **`.github/workflows/frontend-ci.yml`** - Node.js tests and build
- **`.github/workflows/ci.yml`** - Main CI workflow orchestrating both

### Triggers

Workflows run on:
- Push to `main` or `develop` branches
- Pull requests targeting `main` or `develop`
- File path changes (optimized for changed files only)

### CI Steps

#### Backend
1. Setup Python environment
2. Install dependencies
3. Lint code with ruff
4. Run pytest with coverage (fail if < 80%)
5. Upload coverage to Codecov
6. Archive HTML coverage report

#### Frontend
1. Setup Node.js environment
2. Install dependencies
3. Run formatter check
4. Run tests with coverage (fail if < 80%)
5. Build application
6. Upload coverage to Codecov
7. Archive coverage report

## Local Development

### Pre-commit Checks

Before pushing, run locally:

```bash
# Backend
pytest tests/ --cov=src/scraping --cov-fail-under=80

# Frontend
cd app && npm run test:coverage
```

### Coverage Reports

- **Backend:** Open `htmlcov/index.html`
- **Frontend:** Open `app/coverage/index.html`

## Codecov Integration

Coverage reports are automatically uploaded to Codecov on successful CI runs. View at:
- https://codecov.io/gh/[your-org]/scraping

## Troubleshooting

### Backend Coverage Below 80%

1. Identify uncovered lines: `coverage report --skip-covered`
2. Add tests for uncovered code in `tests/`
3. Ensure new code includes corresponding tests

### Frontend Coverage Below 80%

1. Check coverage report: `npm run test:coverage`
2. Add tests in `app/src/__tests__/`
3. Run `npm run test:ui` for visual coverage analysis

### Test Failures on CI

1. Reproduce locally with same Python/Node version
2. Check test output in GitHub Actions logs
3. Ensure all dependencies are up to date: `pip install -e ".[dev]"` or `npm ci`

## Configuration Files

- **`pyproject.toml`** - Python project config, pytest settings, coverage settings
- **`app/vitest.config.js`** - Frontend test configuration
- **`.coveragerc`** - Coverage measurement settings
- **`.github/workflows/*.yml`** - GitHub Actions workflows
