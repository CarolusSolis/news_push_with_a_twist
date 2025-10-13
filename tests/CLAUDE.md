# tests/CLAUDE.md

Testing context for the Agentic Morning Digest test suite.

## Testing Philosophy

- **Backend tests are unit tests**: Fast, isolated, no Streamlit dependencies
- **Frontend tests use Streamlit AppTest**: Test actual UI behavior
- **Mock external dependencies**: No real API calls in tests
- **Test behavior, not implementation**: Focus on what, not how

## Running Tests

### Environment Setup
```bash
# Activate conda environment
conda activate news_push

# Install test dependencies (if not already installed)
pip install -r requirements.txt
```

### Basic Commands
```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_services.py
pytest tests/test_app.py

# Run specific test class
pytest tests/test_services.py::TestDigestService -v

# Run with coverage
pytest --cov=app --cov-report=html
open htmlcov/index.html

# Show print statements (useful for debugging)
pytest -s

# Stop on first failure
pytest -x
```

## Test Structure

```
tests/
├── CLAUDE.md           # This file - testing context
├── __init__.py         # Package marker
├── test_services.py    # Backend unit tests (DigestService, VoiceoverService)
├── test_app.py         # Frontend AppTest tests (Streamlit UI)
└── test_integration.py # Integration tests (agent workflows, HN integration, E2E)
```

**Note:** Old standalone test scripts (`test_hacker_news_integration.py`, `test_real_agent.py`) have been consolidated into `test_integration.py` for better organization.

## Writing Tests

### Backend Unit Tests (test_services.py)

Test pure Python functions in `app/services.py`:

```python
import pytest
from services import DigestService

class TestNewFeature:
    @pytest.fixture
    def digest_service(self, tmp_path):
        """Create service with temp data dir."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        return DigestService(data_dir=data_dir)

    def test_feature_works(self, digest_service):
        """Test that feature works correctly."""
        result = digest_service.new_method()
        assert result is not None
```

**Key patterns:**
- Use fixtures for setup (`@pytest.fixture`)
- Use `tmp_path` for file operations
- Mock external dependencies with `@patch`
- Test edge cases and error conditions

### Frontend AppTest (test_app.py)

Test Streamlit UI in `app/app.py`:

```python
from streamlit.testing.v1 import AppTest

def test_ui_element():
    """Test that UI element appears."""
    at = AppTest.from_file("../app/app.py")
    at.run()

    # Check session state
    assert 'digest_sections' in at.session_state

    # Check for buttons
    assert len([b for b in at.button if '🤖' in str(b)]) > 0
```

**Key patterns:**
- `AppTest.from_file()` loads the app
- `.run()` executes the app
- `.session_state` accesses Streamlit state
- `.button`, `.sidebar` access UI elements

## Mocking External Dependencies

```python
from unittest.mock import Mock, patch

@patch('services.generate_digest_with_agent')
@patch('services.get_agent_logs')
def test_with_mocks(mock_logs, mock_generate):
    """Test with mocked agent calls."""
    mock_generate.return_value = [{'id': 'test'}]
    mock_logs.return_value = ['[Agent] Test log']

    # Your test code here
```

## Coverage Goals

- **Backend Services** (`app/services.py`): Aim for 80%+ coverage
- **UI Critical Paths** (`app/app.py`): Test key user workflows
- **Integration**: Test service coordination

Check coverage:
```bash
pytest --cov=app --cov-report=term-missing
```

## Test Organization

### test_services.py (16 tests)
- `TestDigestService`: Tests for DigestService
  - Static sample loading
  - Digest generation (live/mock)
  - Mock section creation
  - Preference handling
- `TestVoiceoverService`: Tests for VoiceoverService
  - Script generation
  - Audio generation
  - Cleanup
- `TestIntegration`: Service coordination

### test_app.py (17 tests)
- `TestAppInitialization`: App setup and config
- `TestSidebarPreferences`: Preferences UI
- `TestDigestGeneration`: Digest workflow
- `TestVoiceoverGeneration`: Voiceover workflow
- `TestAgentLog`: Log display
- `TestErrorHandling`: Fallback behavior
- `TestRegenerateWorkflow`: Regenerate functionality
- `TestDataPersistence`: Session state

### test_integration.py (11 tests)
- `TestHackerNewsIntegration`: HN scraping and API tests
- `TestAgentIntegration`: Agent orchestration with tools
- `TestAgentFallback`: Fallback behavior for failed requests
- `TestRealAgent`: Real agent with OpenAI API (may skip)
- `TestEndToEndWorkflow`: Complete digest generation pipeline

## Debugging Tests

### Failed Test
```bash
# Run specific failing test with verbose output
pytest tests/test_services.py::TestDigestService::test_name -vv

# Show print statements and full traceback
pytest tests/test_services.py::TestDigestService::test_name -vvs --tb=long
```

### Import Errors
```bash
# Check Python path from project root
cd /path/to/news_push_with_a_twist
python -c "import sys; print(sys.path)"

# Tests add app/ to path automatically - verify it works
python -c "import sys; sys.path.insert(0, 'app'); from services import DigestService; print('OK')"
```

### Streamlit AppTest Issues
- Requires streamlit >= 1.28.0: `pip install --upgrade streamlit`
- Use relative paths: `AppTest.from_file("../app/app.py")`
- Check for `at.exception` to debug errors

## Best Practices

✅ **DO:**
- Keep tests fast (mock slow operations)
- Test one thing per test
- Use descriptive test names (`test_feature_handles_empty_input`)
- Test edge cases and error conditions
- Use fixtures for shared setup

❌ **DON'T:**
- Test implementation details
- Make tests depend on each other
- Hit real APIs (HackerNews, OpenAI, Tavily)
- Write tests that are too slow
- Skip error case testing

## CI Integration (Optional)

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pytest --cov=app --cov-report=xml
      - uses: codecov/codecov-action@v2
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'langgraph'"
Install dependencies:
```bash
conda activate news_push
pip install -r requirements.txt
```

### "No tests collected"
Make sure you're in the project root:
```bash
cd /path/to/news_push_with_a_twist
pytest
```

### Tests pass locally but fail in CI
- Check Python version matches
- Verify all dependencies in requirements.txt
- Check for hardcoded paths

## Quick Validation

```bash
# Verify setup is working
conda activate news_push
python validate_setup.py

# Run a quick test
pytest tests/test_services.py::TestDigestService::test_load_static_samples -v
```
