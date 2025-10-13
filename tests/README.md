# Testing Guide

This directory contains tests for the Agentic Morning Digest application.

## Test Structure

```
tests/
├── __init__.py
├── test_services.py      # Unit tests for backend services
├── test_app.py           # Streamlit AppTest tests for UI
└── README.md            # This file
```

## Running Tests

### Install Test Dependencies

```bash
pip install -r requirements.txt
```

### Run All Tests

```bash
# From project root
pytest

# Or with verbose output
pytest -v
```

### Run Specific Test Files

```bash
# Run only service tests
pytest tests/test_services.py

# Run only app tests
pytest tests/test_app.py
```

### Run Specific Test Classes or Functions

```bash
# Run a specific test class
pytest tests/test_services.py::TestDigestService

# Run a specific test function
pytest tests/test_services.py::TestDigestService::test_load_static_samples
```

### Run with Coverage

```bash
# Generate coverage report
pytest --cov=app --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Run Tests with Output

```bash
# Show print statements
pytest -s

# Show detailed output
pytest -vv
```

## Test Categories

### 1. Unit Tests (`test_services.py`)

Tests for backend business logic in `app/services.py`:

- **DigestService Tests**
  - Static sample loading
  - Digest generation with live/mock data
  - Mock section creation with various preferences
  - Fallback behavior

- **VoiceoverService Tests**
  - Script generation
  - Audio generation
  - Audio cleanup

- **Integration Tests**
  - End-to-end workflows
  - Service coordination

### 2. Streamlit AppTest (`test_app.py`)

Tests for Streamlit UI in `app/app.py`:

- **App Initialization**
  - Page config
  - Session state setup
  - Initial empty state

- **UI Components**
  - Sidebar preferences
  - Generate buttons
  - Agent log display

- **User Workflows**
  - Digest generation
  - Voiceover generation
  - Regenerate functionality

- **Error Handling**
  - Graceful fallback
  - Error messages

## Writing New Tests

### Unit Test Example

```python
import pytest
from services import DigestService

class TestNewFeature:
    """Tests for new feature."""

    @pytest.fixture
    def service(self):
        """Create service instance."""
        return DigestService()

    def test_feature_works(self, service):
        """Test that feature works correctly."""
        result = service.new_feature()
        assert result is not None
```

### Streamlit AppTest Example

```python
from streamlit.testing.v1 import AppTest

def test_new_ui_element():
    """Test that new UI element appears."""
    at = AppTest.from_file("../app/app.py")
    at.run()

    # Check for your element
    assert not at.exception
```

## Mocking

Tests use `unittest.mock` for external dependencies:

```python
from unittest.mock import Mock, patch

@patch('services.generate_digest_with_agent')
def test_with_mock(mock_generate):
    """Test with mocked function."""
    mock_generate.return_value = [{'id': 'test'}]
    # Your test code here
```

## Continuous Integration

Tests should pass before committing:

```bash
# Run all tests
pytest

# Run with coverage check
pytest --cov=app --cov-report=term-missing
```

## Troubleshooting

### Import Errors

If you get import errors, make sure you're running from the project root:

```bash
cd /path/to/news_push_with_a_twist
pytest
```

### Path Issues

Tests add the `app` directory to the Python path automatically. If you still have issues:

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'app'))
```

### Streamlit AppTest Issues

AppTest requires streamlit >= 1.28.0. Update if needed:

```bash
pip install --upgrade streamlit
```

## Best Practices

1. **Keep tests isolated** - Each test should be independent
2. **Use fixtures** - Share setup code with pytest fixtures
3. **Mock external calls** - Don't hit real APIs in tests
4. **Test edge cases** - Include error conditions and boundary cases
5. **Keep tests fast** - Mock slow operations like network calls
6. **Clear naming** - Test names should describe what they test
7. **One assertion focus** - Each test should test one thing

## Coverage Goals

- **Backend Services**: Aim for 80%+ coverage
- **UI Components**: Test critical user workflows
- **Integration**: Test key end-to-end flows

Current coverage can be checked with:

```bash
pytest --cov=app --cov-report=term-missing
```
