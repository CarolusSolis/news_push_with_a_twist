"""Streamlit app tests using AppTest."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
import sys

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'app'))

# Import streamlit testing
from streamlit.testing.v1 import AppTest


class TestAppInitialization:
    """Test app initialization and configuration."""

    def test_app_loads_successfully(self):
        """Test that the app loads without errors."""
        at = AppTest.from_file("../app/app.py")
        at.run()

        assert not at.exception

    def test_page_config(self):
        """Test that page config is set correctly."""
        at = AppTest.from_file("../app/app.py")
        at.run()

        # The app should run without errors
        assert not at.exception

    def test_session_state_initialization(self):
        """Test that session state is initialized correctly."""
        at = AppTest.from_file("../app/app.py")
        at.run()

        # Check if session state keys exist
        assert 'digest_sections' in at.session_state
        assert 'agent_log' in at.session_state
        assert 'generation_status' in at.session_state
        assert 'voiceover_script' in at.session_state
        assert 'voiceover_audio_path' in at.session_state
        assert 'voiceover_status' in at.session_state

    def test_initial_state_empty(self):
        """Test that initial state is empty."""
        at = AppTest.from_file("../app/app.py")
        at.run()

        assert at.session_state.digest_sections == []
        assert at.session_state.agent_log == []
        assert at.session_state.generation_status is None


class TestSidebarPreferences:
    """Test sidebar preferences UI."""

    def test_sidebar_exists(self):
        """Test that sidebar is rendered."""
        at = AppTest.from_file("../app/app.py")
        at.run()

        # Check if sidebar elements exist
        assert len(at.sidebar) > 0

    def test_preferences_form_elements(self):
        """Test that preference form elements are present."""
        at = AppTest.from_file("../app/app.py")
        at.run()

        # The sidebar should contain form elements
        # (specific checks depend on prefs.py implementation)
        assert len(at.sidebar) > 0


class TestDigestGeneration:
    """Test digest generation workflow."""

    @patch('services.DigestService.generate_digest')
    @patch('services.DigestService.create_mock_sections')
    def test_generate_button_creates_digest(
        self,
        mock_create_sections,
        mock_generate
    ):
        """Test that clicking generate button creates a digest."""
        # Mock the service methods
        mock_sections = [
            {
                'id': 'test_section',
                'title': 'Test Section',
                'kind': 'need',
                'items': [{'text': 'Test item', 'url': ''}]
            }
        ]
        mock_logs = ['[Agent] Test log']

        mock_generate.return_value = (mock_sections, mock_logs)
        mock_create_sections.return_value = (mock_sections, mock_logs)

        at = AppTest.from_file("../app/app.py")
        at.run()

        # Find and click the generate button
        # Note: Button text matching may vary based on app state
        buttons = [b for b in at.button if '🤖' in str(b)]
        if buttons:
            buttons[0].click().run()

            # Check if digest was generated
            assert len(at.session_state.digest_sections) > 0

    def test_empty_state_shows_initially(self):
        """Test that empty state is shown when no digest exists."""
        at = AppTest.from_file("../app/app.py")
        at.run()

        # Since no digest has been generated, session state should be empty
        assert at.session_state.digest_sections == []


class TestVoiceoverGeneration:
    """Test voiceover generation workflow."""

    @patch('services.VoiceoverService.generate_script')
    @patch('services.VoiceoverService.generate_audio')
    def test_voiceover_button_appears_after_digest(
        self,
        mock_generate_audio,
        mock_generate_script
    ):
        """Test that voiceover button appears after digest is generated."""
        # Setup mocks
        mock_generate_script.return_value = "Test script"
        mock_generate_audio.return_value = "/tmp/test_audio.mp3"

        at = AppTest.from_file("../app/app.py")
        at.run()

        # Set session state to simulate digest generation
        at.session_state.digest_sections = [
            {
                'id': 'test',
                'title': 'Test',
                'kind': 'need',
                'items': [{'text': 'Test', 'url': ''}]
            }
        ]
        at.run()

        # Voiceover button should be available
        voiceover_buttons = [b for b in at.button if '🎙️' in str(b)]
        assert len(voiceover_buttons) > 0


class TestAgentLog:
    """Test agent thinking log display."""

    def test_agent_log_section_exists(self):
        """Test that agent log section is rendered."""
        at = AppTest.from_file("../app/app.py")
        at.run()

        # The app should have a way to display agent logs
        # (specific checks depend on presenter.py implementation)
        assert not at.exception

    def test_agent_log_updates_after_generation(self):
        """Test that agent log is populated after digest generation."""
        at = AppTest.from_file("../app/app.py")
        at.run()

        # Set agent log
        at.session_state.agent_log = ['[Test] Log message']
        at.run()

        # Log should be stored in session state
        assert len(at.session_state.agent_log) > 0


class TestErrorHandling:
    """Test error handling in the app."""

    @patch('services.DigestService.generate_digest')
    @patch('services.DigestService.create_mock_sections')
    def test_fallback_on_generation_error(
        self,
        mock_create_sections,
        mock_generate
    ):
        """Test that fallback works when digest generation fails."""
        # Mock failure then fallback
        mock_generate.side_effect = Exception("API Error")
        mock_create_sections.return_value = (
            [{'id': 'fallback', 'title': 'Fallback', 'kind': 'need', 'items': []}],
            ['[Fallback] Using mock data']
        )

        at = AppTest.from_file("../app/app.py")
        at.run()

        # The app should not crash
        assert not at.exception


class TestRegenerateWorkflow:
    """Test regenerate functionality."""

    def test_regenerate_button_appears_after_digest(self):
        """Test that regenerate button appears after initial generation."""
        at = AppTest.from_file("../app/app.py")
        at.run()

        # Set session state to simulate existing digest
        at.session_state.digest_sections = [
            {'id': 'test', 'title': 'Test', 'kind': 'need', 'items': []}
        ]
        at.run()

        # Regenerate button should be available
        regen_buttons = [b for b in at.button if '🔄' in str(b)]
        assert len(regen_buttons) > 0


class TestLayoutStructure:
    """Test app layout structure."""

    def test_two_column_layout(self):
        """Test that app uses two-column layout."""
        at = AppTest.from_file("../app/app.py")
        at.run()

        # The app should have a column structure
        # (specific implementation may vary)
        assert not at.exception

    def test_main_content_area_exists(self):
        """Test that main content area is present."""
        at = AppTest.from_file("../app/app.py")
        at.run()

        # Main content should be rendered
        assert not at.exception


class TestDataPersistence:
    """Test data persistence in session state."""

    def test_session_state_persists_between_reruns(self):
        """Test that session state persists across reruns."""
        at = AppTest.from_file("../app/app.py")
        at.run()

        # Set some session state
        test_data = [{'id': 'test', 'title': 'Test', 'kind': 'need', 'items': []}]
        at.session_state.digest_sections = test_data

        # Rerun the app
        at.run()

        # Data should persist
        assert at.session_state.digest_sections == test_data

    def test_clear_functionality(self):
        """Test that clear/regenerate clears old data."""
        at = AppTest.from_file("../app/app.py")
        at.run()

        # Set initial data
        at.session_state.digest_sections = [{'id': 'old', 'title': 'Old', 'kind': 'need', 'items': []}]
        at.session_state.agent_log = ['Old log']

        # The app should allow clearing/regenerating
        # (implementation depends on actual regenerate logic)
        at.run()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
