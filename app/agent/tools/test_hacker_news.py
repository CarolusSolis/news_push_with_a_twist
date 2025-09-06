"""Test suite for Hacker News tool integration with AI agent system."""

import pytest
import json
import time
from unittest.mock import patch, MagicMock
from typing import Dict, Any, List

# Import the tools and core system
from .hacker_news import scrape_hacker_news, get_top_stories, get_hacker_news_content
from ..core import generate_digest_with_agent, generate_mock_digest, get_agent_logs, agent_logger
from .content_tools import analyze_user_preferences, process_content_item
from .retrieval_tools import fetch_content_by_type


class TestHackerNewsTool:
    """Test the Hacker News scraping tool functionality."""
    
    def test_scrape_hacker_news_structure(self):
        """Test that scrape_hacker_news returns the expected structure."""
        result = scrape_hacker_news.invoke({"max_items": 3})
        
        # Check basic structure
        assert isinstance(result, dict)
        assert 'items' in result
        assert 'source' in result
        assert 'scraped_at' in result
        assert 'total_items' in result
        assert result['source'] == 'hacker_news'
        assert isinstance(result['items'], list)
        assert result['total_items'] == len(result['items'])
        
        # If we got items, check their structure
        if result['items']:
            item = result['items'][0]
            required_fields = ['title', 'url', 'snippet', 'points', 'comments', 'author', 'source', 'rank']
            for field in required_fields:
                assert field in item, f"Missing field: {field}"
            
            assert isinstance(item['title'], str)
            assert isinstance(item['url'], str)
            assert isinstance(item['points'], int)
            assert isinstance(item['comments'], int)
            assert item['source'] == 'hacker_news'
    
    def test_scrape_hacker_news_with_network_error(self):
        """Test that scrape_hacker_news handles network errors gracefully."""
        with patch('requests.get') as mock_get:
            mock_get.side_effect = Exception("Network error")
            
            result = scrape_hacker_news.invoke({"max_items": 5})
            
            assert isinstance(result, dict)
            assert 'error' in result
            assert result['items'] == []
            assert result['total_items'] == 0
            assert 'Network error' in result['error']
    
    def test_get_top_stories_api(self):
        """Test the Hacker News API method."""
        result = get_top_stories(3)
        
        assert isinstance(result, list)
        if result:  # If API is accessible
            story = result[0]
            required_fields = ['title', 'url', 'snippet', 'points', 'comments', 'author', 'source', 'id']
            for field in required_fields:
                assert field in story, f"Missing field: {field}"
            
            assert isinstance(story['title'], str)
            assert isinstance(story['url'], str)
            assert isinstance(story['points'], int)
            assert isinstance(story['comments'], int)
            assert story['source'] == 'hacker_news'
    
    def test_get_hacker_news_content_methods(self):
        """Test both scraping and API methods."""
        # Test scraping method
        scrape_result = get_hacker_news_content('scrape', 2)
        assert isinstance(scrape_result, dict)
        assert 'items' in scrape_result
        assert 'source' in scrape_result
        
        # Test API method
        api_result = get_hacker_news_content('api', 2)
        assert isinstance(api_result, dict)
        assert 'items' in api_result
        assert 'source' in api_result
        assert 'method' in api_result
        assert api_result['method'] == 'api'


class TestAgentIntegration:
    """Test the AI agent system's integration with Hacker News tools."""
    
    def setup_method(self):
        """Clear agent logs before each test."""
        agent_logger.clear_logs()
    
    def test_agent_logs_hacker_news_activity(self):
        """Test that the agent logs Hacker News tool usage."""
        preferences = {
            'learn_about': 'AI and technology',
            'fun_learning': 'quotes and history',
            'time_budget': 'quick',
            'include_quotes': True
        }
        
        # Generate digest (this should use Hacker News for tech content)
        sections = generate_mock_digest(preferences, use_live_data=False)
        
        logs = get_agent_logs()
        
        # Check that agent logged its activities
        assert len(logs) > 0
        assert any('[Agent]' in log for log in logs)
        
        # Check for content fetching logs
        content_logs = [log for log in logs if 'content' in log.lower() or 'fetch' in log.lower()]
        assert len(content_logs) > 0, "No content fetching logs found"
    
    def test_agent_handles_hacker_news_in_preferences(self):
        """Test that agent correctly processes tech preferences using Hacker News."""
        preferences = {
            'learn_about': 'AI, machine learning, and startup news',
            'fun_learning': 'historical facts',
            'time_budget': 'standard',
            'include_quotes': True
        }
        
        # Test strategy analysis
        strategy = analyze_user_preferences.invoke({"preferences": preferences})
        
        assert strategy['include_tech'] == True, "Should include tech content for AI/startup interests"
        assert strategy['max_items'] >= 4, "Should have reasonable number of items"
        assert strategy['alternating_pattern'] == True, "Should use alternating pattern"
    
    def test_agent_fallback_behavior(self):
        """Test that agent falls back gracefully when Hacker News is unavailable."""
        preferences = {
            'learn_about': 'technology and AI',
            'fun_learning': 'quotes',
            'time_budget': 'quick'
        }
        
        # Mock the fetch_content_by_type to simulate failure
        with patch('agent.tools.retrieval_tools.fetch_content_by_type') as mock_fetch:
            mock_fetch.return_value = {
                'items': [],
                'source': 'hacker_news',
                'error': 'Network timeout'
            }
            
            sections = generate_mock_digest(preferences, use_live_data=True)
            
            # Should still return some sections (from other sources or fallback)
            assert isinstance(sections, list)
            
            logs = get_agent_logs()
            # Should log the fallback behavior
            assert any('fallback' in log.lower() or 'error' in log.lower() for log in logs)
    
    def test_agent_content_processing_pipeline(self):
        """Test the full pipeline from Hacker News data to processed content."""
        # Mock Hacker News data
        mock_hn_data = {
            'title': 'New AI breakthrough in natural language processing',
            'url': 'https://example.com/ai-breakthrough',
            'snippet': 'Posted by researcher • 150 points • 45 comments',
            'points': 150,
            'comments': 45,
            'author': 'researcher',
            'source': 'hacker_news',
            'rank': 1
        }
        
        # Test content processing
        processed = process_content_item.invoke({
            "item": mock_hn_data,
            "item_type": "serious"
        })
        
        assert processed['kind'] == 'need'
        assert processed['processed'] == True
        assert 'AI breakthrough' in processed['text']
        assert processed['url'] == mock_hn_data['url']
    
    def test_agent_alternating_pattern_with_hn(self):
        """Test that agent maintains alternating pattern when using Hacker News."""
        preferences = {
            'learn_about': 'AI, technology, startups',
            'fun_learning': 'quotes and history',
            'time_budget': 'standard',
            'include_quotes': True
        }
        
        sections = generate_mock_digest(preferences, use_live_data=False)
        
        # Should have alternating pattern
        kinds = [section['kind'] for section in sections]
        
        # Check for alternating pattern (should start with 'need' for tech content)
        if len(kinds) >= 2:
            # Should alternate between need and nice
            for i in range(len(kinds) - 1):
                assert kinds[i] != kinds[i + 1], f"Not alternating at position {i}: {kinds}"
    
    def test_agent_with_live_hacker_news_data(self):
        """Test agent behavior with live Hacker News data (if available)."""
        preferences = {
            'learn_about': 'technology and AI news',
            'fun_learning': 'quotes',
            'time_budget': 'quick'
        }
        
        # Try with live data (this might fail in test environment)
        try:
            sections = generate_mock_digest(preferences, use_live_data=True)
            
            assert isinstance(sections, list)
            
            # Check that we got some content
            if sections:
                # Should have proper section structure
                for section in sections:
                    assert 'id' in section
                    assert 'title' in section
                    assert 'kind' in section
                    assert 'items' in section
                    assert section['kind'] in ['need', 'nice']
                    
                    if section['items']:
                        item = section['items'][0]
                        assert 'text' in item
                        assert isinstance(item['text'], str)
            
            logs = get_agent_logs()
            assert any('live' in log.lower() or 'mock' in log.lower() for log in logs)
            
        except Exception as e:
            # If live data fails, that's okay - we're testing the fallback
            assert "Network" in str(e) or "timeout" in str(e).lower() or "connection" in str(e).lower()


class TestHackerNewsToolIntegration:
    """Test the integration between Hacker News tool and the broader system."""
    
    def test_tool_can_be_imported_by_agent(self):
        """Test that the Hacker News tool can be imported and used by the agent."""
        from ..core import create_digest_agent
        
        # This should not raise an import error
        agent = create_digest_agent()
        
        # If agent is None (no API key), that's expected in test environment
        # The important thing is that the import worked
        assert agent is None or hasattr(agent, 'invoke')
    
    def test_tool_works_with_langchain_tool_decorator(self):
        """Test that the tool works properly with LangChain's tool decorator."""
        # Test that the tool has the expected LangChain tool attributes
        assert hasattr(scrape_hacker_news, 'invoke')
        assert hasattr(scrape_hacker_news, 'name')
        assert hasattr(scrape_hacker_news, 'description')
        
        # Test that we can call it with invoke
        result = scrape_hacker_news.invoke({"max_items": 1})
        assert isinstance(result, dict)
    
    def test_tool_error_handling_in_agent_context(self):
        """Test that tool errors are handled gracefully in agent context."""
        preferences = {
            'learn_about': 'technology',
            'fun_learning': 'quotes',
            'time_budget': 'quick'
        }
        
        # Mock a tool failure
        with patch('agent.tools.hacker_news.scrape_hacker_news') as mock_scrape:
            mock_scrape.invoke.side_effect = Exception("Tool failure")
            
            # Should not crash the entire system
            sections = generate_mock_digest(preferences, use_live_data=True)
            
            assert isinstance(sections, list)
            # Should still produce some output (from other sources or fallback)


if __name__ == "__main__":
    # Run a quick integration test
    print("Running Hacker News tool integration test...")
    
    # Test basic tool functionality
    print("Testing Hacker News scraping...")
    result = scrape_hacker_news.invoke({"max_items": 2})
    print(f"Scraped {result['total_items']} items")
    
    # Test agent integration
    print("Testing agent integration...")
    preferences = {
        'learn_about': 'AI and technology',
        'fun_learning': 'quotes',
        'time_budget': 'quick'
    }
    
    sections = generate_mock_digest(preferences, use_live_data=False)
    print(f"Generated {len(sections)} sections")
    
    logs = get_agent_logs()
    print(f"Agent logged {len(logs)} messages")
    
    print("Integration test completed successfully!")