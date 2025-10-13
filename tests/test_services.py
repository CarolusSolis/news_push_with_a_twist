"""Unit tests for backend services."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import json
import tempfile
import os

# Add app directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'app'))

from services import DigestService, VoiceoverService


class TestDigestService:
    """Tests for DigestService."""

    @pytest.fixture
    def digest_service(self, tmp_path):
        """Create a DigestService with a temporary data directory."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()

        # Create a mock static_samples.json
        static_samples = {
            "hacker_news": [
                {
                    "title": "Test HN Article 1",
                    "url": "https://example.com/1",
                    "snippet": "Test snippet 1",
                    "points": 100,
                    "comments": 50
                },
                {
                    "title": "Test HN Article 2",
                    "url": "https://example.com/2",
                    "snippet": "Test snippet 2",
                    "points": 200,
                    "comments": 75
                }
            ],
            "quotes": [
                {
                    "text": "Test quote 1",
                    "author": "Test Author 1"
                },
                {
                    "text": "Test quote 2",
                    "author": "Test Author 2"
                }
            ],
            "wikipedia_today": [
                {
                    "title": "1969 – Apollo 11 Moon Landing",
                    "snippet": "Neil Armstrong and Buzz Aldrin became the first humans to land on the Moon."
                }
            ]
        }

        with open(data_dir / "static_samples.json", 'w') as f:
            json.dump(static_samples, f)

        return DigestService(data_dir=data_dir)

    def test_load_static_samples(self, digest_service):
        """Test loading static samples from JSON file."""
        samples = digest_service.load_static_samples()

        assert isinstance(samples, dict)
        assert "hacker_news" in samples
        assert "quotes" in samples
        assert len(samples["hacker_news"]) == 2
        assert samples["hacker_news"][0]["title"] == "Test HN Article 1"

    def test_load_static_samples_missing_file(self, tmp_path):
        """Test loading static samples when file doesn't exist."""
        service = DigestService(data_dir=tmp_path / "nonexistent")
        samples = service.load_static_samples()

        assert samples == {}

    @patch('services.generate_digest_with_agent')
    @patch('services.get_agent_logs')
    def test_generate_digest_success(
        self,
        mock_get_logs,
        mock_generate,
        digest_service
    ):
        """Test successful digest generation."""
        # Mock the agent functions
        mock_sections = [
            {
                'id': 'quick_hits',
                'title': 'Quick Hits',
                'kind': 'need',
                'items': [{'text': 'Test item', 'url': 'https://example.com'}]
            }
        ]
        mock_logs = ['[Agent] Starting...', '[Agent] Complete']

        mock_generate.return_value = mock_sections
        mock_get_logs.return_value = mock_logs

        prefs = {
            'learn_about': 'AI and technology',
            'fun_learning': 'quotes',
            'time_budget': 'standard'
        }

        sections, logs = digest_service.generate_digest(prefs, use_live_data=True)

        assert sections == mock_sections
        assert logs == mock_logs
        mock_generate.assert_called_once_with(prefs, use_live_data=True)
        mock_get_logs.assert_called_once()

    @patch('services.generate_digest_with_agent')
    def test_generate_digest_failure(self, mock_generate, digest_service):
        """Test digest generation failure."""
        mock_generate.side_effect = Exception("API error")

        prefs = {'learn_about': 'AI', 'fun_learning': 'quotes', 'time_budget': 'standard'}

        with pytest.raises(Exception, match="API error"):
            digest_service.generate_digest(prefs, use_live_data=True)

    def test_create_mock_sections_basic(self, digest_service):
        """Test creating mock sections with basic preferences."""
        prefs = {
            'learn_about': 'AI and technology',
            'fun_learning': 'history',
            'mood': 'focused',
            'time_budget': 'quick',
            'include_quotes': True
        }

        sections, logs = digest_service.create_mock_sections(prefs)

        # Should have at least 2 sections (tech + quote)
        assert len(sections) >= 2
        assert len(logs) > 0

        # Check log messages
        assert any('[Planner]' in log for log in logs)

        # Check sections structure
        for section in sections:
            assert 'id' in section
            assert 'title' in section
            assert 'kind' in section
            assert 'items' in section
            assert section['kind'] in ['need', 'nice']

    def test_create_mock_sections_tech_focus(self, digest_service):
        """Test mock sections with tech focus."""
        prefs = {
            'learn_about': 'AI, machine learning, startups',
            'fun_learning': 'quotes',
            'mood': 'focused',
            'time_budget': 'standard',
            'include_quotes': True
        }

        sections, logs = digest_service.create_mock_sections(prefs)

        # Should have tech items
        need_sections = [s for s in sections if s['kind'] == 'need']
        assert len(need_sections) > 0

        # Should have nice items if quotes enabled
        nice_sections = [s for s in sections if s['kind'] == 'nice']
        assert len(nice_sections) > 0

    def test_create_mock_sections_deep_time_budget(self, digest_service):
        """Test mock sections with deep time budget."""
        prefs = {
            'learn_about': 'technology',
            'fun_learning': 'history',
            'mood': 'focused',
            'time_budget': 'deep',
            'include_quotes': True
        }

        sections, logs = digest_service.create_mock_sections(prefs)

        # Should have more sections with deep time budget
        assert len(sections) >= 3

    def test_create_mock_sections_no_quotes(self, digest_service):
        """Test mock sections without quotes."""
        prefs = {
            'learn_about': 'technology',
            'fun_learning': 'history',
            'mood': 'focused',
            'time_budget': 'quick',
            'include_quotes': False
        }

        sections, logs = digest_service.create_mock_sections(prefs)

        # Should still create sections even without quotes
        assert len(sections) > 0

    def test_create_mock_sections_with_custom_mock_data(self, digest_service):
        """Test creating mock sections with custom mock data."""
        custom_data = {
            'hacker_news': [
                {'title': 'Custom Title', 'snippet': 'Custom snippet', 'url': 'https://custom.com'}
            ],
            'quotes': [
                {'text': 'Custom quote', 'author': 'Custom Author'}
            ],
            'wikipedia_today': []
        }

        prefs = {
            'learn_about': 'technology',
            'fun_learning': 'quotes',
            'mood': 'focused',
            'time_budget': 'quick',
            'include_quotes': True
        }

        sections, logs = digest_service.create_mock_sections(prefs, mock_data=custom_data)

        # Should use custom data
        assert len(sections) > 0
        # Check if custom title appears in any section
        all_text = ' '.join([item['text'] for s in sections for item in s['items']])
        assert 'Custom' in all_text


class TestVoiceoverService:
    """Tests for VoiceoverService."""

    @pytest.fixture
    def voiceover_service(self):
        """Create a VoiceoverService."""
        return VoiceoverService()

    @pytest.fixture
    def sample_sections(self):
        """Sample digest sections for testing."""
        return [
            {
                'id': 'quick_hits',
                'title': '📌 Quick Hits',
                'kind': 'need',
                'items': [
                    {'text': 'AI breakthrough in reasoning', 'url': 'https://example.com'}
                ]
            },
            {
                'id': 'quote',
                'title': '💭 Quote of the Day',
                'kind': 'nice',
                'items': [
                    {'text': '"Innovation distinguishes between a leader and a follower." - Steve Jobs'}
                ]
            }
        ]

    @patch('services.generate_voiceover_script')
    def test_generate_script(self, mock_generate_script, voiceover_service, sample_sections):
        """Test generating voiceover script."""
        mock_script = "This is a test voiceover script."
        mock_generate_script.return_value = mock_script

        prefs = {'mood': 'focused', 'time_budget': 'standard'}

        script = voiceover_service.generate_script(sample_sections, prefs)

        assert script == mock_script
        mock_generate_script.assert_called_once_with(sample_sections, prefs)

    @patch('services.generate_audio_from_script')
    def test_generate_audio_success(self, mock_generate_audio, voiceover_service):
        """Test generating audio from script."""
        mock_path = "/tmp/test_audio.mp3"
        mock_generate_audio.return_value = mock_path

        script = "Test script"
        audio_path = voiceover_service.generate_audio(script, voice='alloy')

        assert audio_path == mock_path
        mock_generate_audio.assert_called_once_with(script, voice='alloy')

    @patch('services.generate_audio_from_script')
    def test_generate_audio_failure(self, mock_generate_audio, voiceover_service):
        """Test audio generation failure."""
        mock_generate_audio.return_value = None

        script = "Test script"
        audio_path = voiceover_service.generate_audio(script)

        assert audio_path is None

    def test_cleanup_audio_success(self, voiceover_service, tmp_path):
        """Test cleaning up audio file."""
        # Create a temporary audio file
        audio_file = tmp_path / "test_audio.mp3"
        audio_file.write_text("test audio content")

        assert audio_file.exists()

        success = voiceover_service.cleanup_audio(str(audio_file))

        assert success is True
        assert not audio_file.exists()

    def test_cleanup_audio_nonexistent_file(self, voiceover_service):
        """Test cleaning up non-existent audio file."""
        success = voiceover_service.cleanup_audio("/nonexistent/path/audio.mp3")

        assert success is False

    def test_cleanup_audio_empty_path(self, voiceover_service):
        """Test cleaning up with empty path."""
        success = voiceover_service.cleanup_audio("")

        assert success is False


class TestIntegration:
    """Integration tests for services working together."""

    @pytest.fixture
    def services(self, tmp_path):
        """Create both services."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()

        # Create mock data
        static_samples = {
            "hacker_news": [{"title": "Test", "url": "https://example.com", "snippet": "Test"}],
            "quotes": [{"text": "Test quote", "author": "Test Author"}],
            "wikipedia_today": []
        }

        with open(data_dir / "static_samples.json", 'w') as f:
            json.dump(static_samples, f)

        return {
            'digest': DigestService(data_dir=data_dir),
            'voiceover': VoiceoverService()
        }

    @patch('services.generate_voiceover_script')
    def test_digest_to_voiceover_workflow(
        self,
        mock_generate_script,
        services
    ):
        """Test the workflow from digest generation to voiceover."""
        # Generate digest
        prefs = {
            'learn_about': 'technology',
            'fun_learning': 'quotes',
            'mood': 'focused',
            'time_budget': 'quick',
            'include_quotes': True
        }

        sections, logs = services['digest'].create_mock_sections(prefs)
        assert len(sections) > 0

        # Generate voiceover script
        mock_generate_script.return_value = "Test voiceover"
        script = services['voiceover'].generate_script(sections, prefs)
        assert script == "Test voiceover"

        mock_generate_script.assert_called_once_with(sections, prefs)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
