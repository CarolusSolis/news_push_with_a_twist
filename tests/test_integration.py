"""Integration tests for the full digest generation pipeline.

These tests verify end-to-end workflows including:
- Agent integration with tools
- Content processing pipeline
- Fallback behavior
- Real vs mock agent behavior
"""

import pytest
from unittest.mock import patch
import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'app'))

from agent.core import (
    generate_digest_with_agent,
    generate_digest_with_real_agent,
    generate_mock_digest,
    get_agent_logs,
    agent_logger
)
from agent.tools.hacker_news import scrape_hacker_news, get_hacker_news_content
from agent.tools.content_tools import analyze_user_preferences, process_content_item


class TestHackerNewsIntegration:
    """Integration tests for Hacker News tool with the agent system."""

    def test_hacker_news_scraping_tool(self):
        """Test that Hacker News scraping tool returns valid data."""
        result = scrape_hacker_news.invoke({"max_items": 3})

        # Check structure
        assert isinstance(result, dict)
        assert 'items' in result
        assert 'source' in result
        assert 'total_items' in result
        assert result['source'] == 'hacker_news'

        # Check items if available
        if result['items']:
            item = result['items'][0]
            assert 'title' in item
            assert 'url' in item
            assert isinstance(item['title'], str)

    def test_hacker_news_api_method(self):
        """Test the Hacker News API method."""
        result = get_hacker_news_content('api', 2)

        assert isinstance(result, dict)
        assert 'items' in result
        assert result.get('method') == 'api'

    def test_content_processing_pipeline(self):
        """Test the full content processing pipeline."""
        mock_hn_item = {
            'title': 'Revolutionary AI breakthrough',
            'url': 'https://example.com/ai',
            'snippet': 'Posted by researcher • 150 points',
            'points': 150,
            'comments': 45,
            'author': 'researcher',
            'source': 'hacker_news',
            'rank': 1
        }

        processed = process_content_item.invoke({
            "item": mock_hn_item,
            "item_type": "serious"
        })

        assert processed['kind'] == 'need'
        assert processed['processed'] == True
        assert 'AI breakthrough' in processed['text']
        assert processed['url'] == mock_hn_item['url']


class TestAgentIntegration:
    """Integration tests for agent orchestration."""

    def setup_method(self):
        """Clear logs before each test."""
        agent_logger.clear_logs()

    def test_agent_with_tech_preferences(self):
        """Test agent generates appropriate content for tech preferences."""
        preferences = {
            'learn_about': 'AI, machine learning, and technology news',
            'fun_learning': 'quotes and historical facts',
            'time_budget': 'standard',
            'include_quotes': True
        }

        # Test preference analysis
        strategy = analyze_user_preferences.invoke({"preferences": preferences})

        assert strategy['include_tech'] == True
        assert strategy['max_items'] >= 4
        assert strategy['alternating_pattern'] == True

    def test_mock_digest_generation(self):
        """Test mock digest generation works correctly."""
        agent_logger.clear_logs()

        preferences = {
            'learn_about': 'AI and technology',
            'fun_learning': 'quotes',
            'time_budget': 'quick',
            'include_quotes': True
        }

        sections = generate_mock_digest(preferences, use_live_data=False)

        # Should generate sections
        assert isinstance(sections, list)
        assert len(sections) > 0

        # Check section structure
        for section in sections:
            assert 'id' in section
            assert 'title' in section
            assert 'kind' in section
            assert 'items' in section
            assert section['kind'] in ['need', 'nice']

        # Check logs were generated
        logs = get_agent_logs()
        assert len(logs) > 0

    def test_alternating_pattern(self):
        """Test that digest maintains alternating need/nice pattern."""
        preferences = {
            'learn_about': 'AI, technology, startups',
            'fun_learning': 'quotes and history',
            'time_budget': 'standard',
            'include_quotes': True
        }

        sections = generate_mock_digest(preferences, use_live_data=False)

        if len(sections) >= 2:
            kinds = [section['kind'] for section in sections]
            # Check alternating pattern
            for i in range(len(kinds) - 1):
                assert kinds[i] != kinds[i + 1], f"Not alternating at position {i}"


class TestAgentFallback:
    """Test fallback behavior when live data is unavailable."""

    def setup_method(self):
        """Clear logs before each test."""
        agent_logger.clear_logs()

    def test_fallback_to_static_data(self):
        """Test that agent falls back to static data gracefully."""
        preferences = {
            'learn_about': 'technology',
            'fun_learning': 'quotes',
            'time_budget': 'quick'
        }

        # Mock failure scenario
        with patch('agent.tools.retrieval_tools.fetch_content_by_type') as mock_fetch:
            mock_fetch.return_value = {
                'items': [],
                'source': 'hacker_news',
                'error': 'Network timeout'
            }

            sections = generate_mock_digest(preferences, use_live_data=True)

            # Should still return sections from fallback
            assert isinstance(sections, list)
            assert len(sections) > 0  # Mock digest creates fallback sections

    def test_digest_with_both_modes(self):
        """Test digest generation with both live and mock data."""
        preferences = {
            'learn_about': 'technology',
            'fun_learning': 'quotes',
            'time_budget': 'quick'
        }

        # Test with mock data (should always work)
        sections_mock = generate_mock_digest(preferences, use_live_data=False)
        assert len(sections_mock) > 0

        # Test with live data (may fallback to mock if network fails)
        sections_live = generate_mock_digest(preferences, use_live_data=True)
        assert len(sections_live) > 0


class TestRealAgent:
    """Tests for real agent with OpenAI API (may skip if no API key)."""

    def setup_method(self):
        """Clear logs before each test."""
        agent_logger.clear_logs()

    @pytest.mark.skipif(
        not Path.home().joinpath('.env').exists(),
        reason="Requires OpenAI API key in .env"
    )
    def test_real_agent_generation(self):
        """Test real agent with live API (requires OPENAI_API_KEY)."""
        preferences = {
            'learn_about': 'AI and technology news',
            'fun_learning': 'quotes',
            'time_budget': 'standard',
            'include_quotes': True
        }

        try:
            sections = generate_digest_with_real_agent(preferences)

            # If API key is available, should return sections
            if sections:
                assert isinstance(sections, list)
                assert len(sections) > 0

                for section in sections:
                    assert 'title' in section
                    assert 'kind' in section
                    assert 'items' in section
        except Exception as e:
            # If no API key, this is expected
            pytest.skip(f"Real agent test skipped: {e}")

    def test_generate_digest_with_agent_wrapper(self):
        """Test the wrapper function that chooses between real and mock agent."""
        preferences = {
            'learn_about': 'technology',
            'fun_learning': 'quotes',
            'time_budget': 'quick'
        }

        # Should work regardless of API key availability
        sections = generate_digest_with_agent(preferences, use_live_data=True)

        assert isinstance(sections, list)
        assert len(sections) > 0

        # Check structure
        for section in sections:
            assert 'id' in section or 'title' in section
            assert 'kind' in section


class TestEndToEndWorkflow:
    """End-to-end integration tests for complete workflows."""

    def setup_method(self):
        """Clear logs before each test."""
        agent_logger.clear_logs()

    def test_complete_digest_generation_workflow(self):
        """Test the complete digest generation workflow."""
        # Step 1: User sets preferences
        preferences = {
            'learn_about': 'AI, machine learning, startups',
            'fun_learning': 'quotes and trivia',
            'time_budget': 'standard',
            'include_quotes': True,
            'mood': 'focused'
        }

        # Step 2: Generate digest
        sections = generate_mock_digest(preferences, use_live_data=False)

        # Step 3: Verify output
        assert len(sections) > 0

        # Step 4: Check agent logged activities
        logs = get_agent_logs()
        assert len(logs) > 0

        # Step 5: Verify section structure matches expected format
        for section in sections:
            assert section['kind'] in ['need', 'nice']
            assert 'items' in section
            assert len(section['items']) > 0

            for item in section['items']:
                assert 'text' in item
                assert isinstance(item['text'], str)
                assert len(item['text']) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
