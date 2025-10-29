"""Tests for the multi-source news system."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from pathlib import Path

# Add app directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'app'))

from agent.sources.base import NewsSource, NewsItem
from agent.sources.manager import NewsSourceManager
from agent.sources.hackernews_source import HackerNewsSource
from agent.sources.reddit_source import RedditSource
from agent.sources.wikipedia_source import WikipediaSource
from agent.sources.tavily_source import TavilySource


class TestNewsItem:
    """Tests for NewsItem dataclass."""

    def test_news_item_creation(self):
        """Test creating a NewsItem."""
        item = NewsItem(
            title="Test Title",
            url="https://example.com",
            description="Test description",
            source_name="test_source",
            category="tech"
        )

        assert item.title == "Test Title"
        assert item.url == "https://example.com"
        assert item.description == "Test description"
        assert item.source_name == "test_source"
        assert item.category == "tech"
        assert item.metadata == {}

    def test_news_item_to_dict(self):
        """Test converting NewsItem to dictionary."""
        item = NewsItem(
            title="Test",
            url="https://example.com",
            source_name="test",
            category="tech",
            metadata={"score": 100}
        )

        result = item.to_dict()

        assert result['title'] == "Test"
        assert result['url'] == "https://example.com"
        assert result['source_name'] == "test"
        assert result['metadata']['score'] == 100


class TestHackerNewsSource:
    """Tests for HackerNews source."""

    def test_hackernews_source_initialization(self):
        """Test HackerNews source initializes correctly."""
        source = HackerNewsSource()

        assert source.name == 'hackernews'
        assert 'tech' in source.categories
        assert source.is_available() is True

    def test_hackernews_supports_category(self):
        """Test category support checking."""
        source = HackerNewsSource()

        assert source.supports_category('tech') is True
        assert source.supports_category('startup') is True
        assert source.supports_category('history') is False

    @patch('agent.tools.hacker_news.get_hacker_news_content')
    def test_hackernews_fetch_success(self, mock_get_content):
        """Test fetching from HackerNews successfully."""
        mock_get_content.return_value = {
            'items': [
                {
                    'title': 'Test Article',
                    'url': 'https://example.com',
                    'points': 100,
                    'comments': 50,
                    'rank': 1
                }
            ]
        }

        source = HackerNewsSource()
        items = source.fetch('tech', max_items=1)

        assert len(items) == 1
        assert items[0].title == 'Test Article'
        assert items[0].source_name == 'hackernews'
        assert items[0].metadata['points'] == 100

    @patch('agent.tools.hacker_news.get_hacker_news_content')
    def test_hackernews_fetch_empty(self, mock_get_content):
        """Test fetching when no items are available."""
        mock_get_content.return_value = {'items': []}

        source = HackerNewsSource()
        items = source.fetch('tech', max_items=5)

        assert len(items) == 0

    def test_hackernews_fetch_unsupported_category(self):
        """Test fetching with unsupported category raises error."""
        source = HackerNewsSource()

        with pytest.raises(ValueError, match="Category 'unsupported' not supported"):
            source.fetch('unsupported', max_items=5)


class TestRedditSource:
    """Tests for Reddit source."""

    def test_reddit_source_initialization(self):
        """Test Reddit source initializes."""
        source = RedditSource()

        assert source.name == 'reddit'
        assert 'tech' in source.categories
        assert 'science' in source.categories
        assert 'fun' in source.categories

    def test_reddit_supports_category(self):
        """Test category support checking."""
        source = RedditSource()

        assert source.supports_category('tech') is True
        assert source.supports_category('science') is True
        assert source.supports_category('unsupported') is False

    @patch('praw.Reddit')
    def test_reddit_fetch_success(self, mock_reddit_class):
        """Test fetching from Reddit successfully."""
        # Mock Reddit client and submission
        mock_submission = MagicMock()
        mock_submission.title = "Test Post"
        mock_submission.url = "https://reddit.com/test"
        mock_submission.selftext = ""
        mock_submission.is_self = False
        mock_submission.stickied = False
        mock_submission.score = 500
        mock_submission.num_comments = 100
        mock_submission.created_utc = 1609459200  # 2021-01-01
        mock_submission.author = MagicMock()
        mock_submission.author.__str__ = lambda _: "testuser"

        mock_subreddit = MagicMock()
        mock_subreddit.hot.return_value = [mock_submission]

        mock_reddit_instance = MagicMock()
        mock_reddit_instance.subreddit.return_value = mock_subreddit

        mock_reddit_class.return_value = mock_reddit_instance

        source = RedditSource()

        items = source.fetch('tech', max_items=1)

        assert len(items) == 1
        assert items[0].title == "Test Post"
        assert items[0].source_name == 'reddit'
        assert items[0].metadata['score'] == 500


class TestWikipediaSource:
    """Tests for Wikipedia source."""

    def test_wikipedia_source_initialization(self):
        """Test Wikipedia source initializes correctly."""
        source = WikipediaSource()

        assert source.name == 'wikipedia'
        assert 'news' in source.categories
        assert 'history' in source.categories
        assert source.is_available() is True

    @patch('agent.sources.wikipedia_source.requests.get')
    def test_wikipedia_fetch_on_this_day(self, mock_get):
        """Test fetching 'On this day' events."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'events': [
                {
                    'text': 'Test historical event',
                    'year': 1776,
                    'pages': [{
                        'content_urls': {
                            'desktop': {'page': 'https://en.wikipedia.org/test'}
                        }
                    }]
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        source = WikipediaSource()
        items = source.fetch('history', max_items=1)

        assert len(items) == 1
        assert '1776' in items[0].title
        assert items[0].source_name == 'wikipedia'


class TestTavilySource:
    """Tests for Tavily source."""

    @patch.dict('os.environ', {}, clear=True)
    def test_tavily_source_unavailable_without_key(self):
        """Test Tavily is unavailable without API key."""
        source = TavilySource()

        assert source.is_available() is False

    @patch.dict('os.environ', {'TAVILY_API_KEY': 'test_key'})
    @patch('langchain_tavily.TavilySearch')
    def test_tavily_source_initialization_with_key(self, mock_tavily_search):
        """Test Tavily initializes with API key."""
        source = TavilySource()

        # Even with key, we need the actual client to be initialized
        # This test just verifies the attempt was made
        assert source.name == 'tavily'
        assert 'tech' in source.categories


class TestNewsSourceManager:
    """Tests for NewsSourceManager."""

    @patch('agent.sources.manager.NewsSourceManager._load_sources')
    def test_manager_initialization(self, mock_load_sources):
        """Test manager initializes correctly."""
        manager = NewsSourceManager()

        assert manager.sources == {}
        assert isinstance(manager.source_priority, list)

    @patch('agent.sources.manager.NewsSourceManager._load_sources')
    def test_register_source(self, mock_load_sources):
        """Test registering a source."""
        manager = NewsSourceManager()

        mock_source = Mock(spec=NewsSource)
        mock_source.name = 'test_source'
        mock_source.is_available.return_value = True

        manager.register_source(mock_source)

        assert 'test_source' in manager.sources
        assert manager.sources['test_source'] == mock_source

    @patch('agent.sources.manager.NewsSourceManager._load_sources')
    def test_get_available_sources(self, mock_load_sources):
        """Test getting available sources."""
        manager = NewsSourceManager()

        # Add available source
        available_source = Mock(spec=NewsSource)
        available_source.name = 'available'
        available_source.is_available.return_value = True
        manager.sources['available'] = available_source

        # Add unavailable source
        unavailable_source = Mock(spec=NewsSource)
        unavailable_source.name = 'unavailable'
        unavailable_source.is_available.return_value = False
        manager.sources['unavailable'] = unavailable_source

        available = manager.get_available_sources()

        assert 'available' in available
        assert 'unavailable' not in available

    @patch('agent.sources.manager.NewsSourceManager._load_sources')
    def test_get_sources_for_category(self, mock_load_sources):
        """Test getting sources for a category."""
        manager = NewsSourceManager()

        # Add source that supports 'tech'
        tech_source = Mock(spec=NewsSource)
        tech_source.name = 'tech_source'
        tech_source.is_available.return_value = True
        tech_source.supports_category.return_value = True
        manager.sources['tech_source'] = tech_source

        # Add source that doesn't support 'tech'
        other_source = Mock(spec=NewsSource)
        other_source.name = 'other_source'
        other_source.is_available.return_value = True
        other_source.supports_category.return_value = False
        manager.sources['other_source'] = other_source

        sources = manager.get_sources_for_category('tech')

        assert 'tech_source' in sources
        assert 'other_source' not in sources

    @patch('agent.sources.manager.NewsSourceManager._load_sources')
    def test_fetch_by_category_success(self, mock_load_sources):
        """Test fetching by category successfully."""
        manager = NewsSourceManager()

        # Create mock source
        mock_source = Mock(spec=NewsSource)
        mock_source.name = 'test_source'
        mock_source.is_available.return_value = True
        mock_source.supports_category.return_value = True
        mock_source.fetch.return_value = [
            NewsItem(title="Test", source_name="test_source", category="tech")
        ]

        manager.sources['test_source'] = mock_source
        manager.source_priority = ['test_source']

        items = manager.fetch_by_category('tech', max_items=5)

        assert len(items) == 1
        assert items[0].title == "Test"
        mock_source.fetch.assert_called_once()

    @patch('agent.sources.manager.NewsSourceManager._load_sources')
    def test_fetch_by_category_specific_source(self, mock_load_sources):
        """Test fetching from a specific source."""
        manager = NewsSourceManager()

        # Create mock source
        mock_source = Mock(spec=NewsSource)
        mock_source.name = 'specific_source'
        mock_source.is_available.return_value = True
        mock_source.supports_category.return_value = True
        mock_source.fetch.return_value = [
            NewsItem(title="Specific", source_name="specific_source", category="tech")
        ]

        manager.sources['specific_source'] = mock_source

        items = manager.fetch_by_category('tech', source_name='specific_source')

        assert len(items) == 1
        assert items[0].title == "Specific"

    @patch('agent.sources.manager.NewsSourceManager._load_sources')
    def test_fetch_by_category_fallback(self, mock_load_sources):
        """Test fallback when first source fails."""
        manager = NewsSourceManager()

        # First source fails
        failing_source = Mock(spec=NewsSource)
        failing_source.name = 'failing'
        failing_source.is_available.return_value = True
        failing_source.supports_category.return_value = True
        failing_source.fetch.side_effect = Exception("Fetch failed")

        # Second source succeeds
        working_source = Mock(spec=NewsSource)
        working_source.name = 'working'
        working_source.is_available.return_value = True
        working_source.supports_category.return_value = True
        working_source.fetch.return_value = [
            NewsItem(title="Fallback", source_name="working", category="tech")
        ]

        manager.sources['failing'] = failing_source
        manager.sources['working'] = working_source
        manager.source_priority = ['failing', 'working']

        items = manager.fetch_by_category('tech')

        assert len(items) == 1
        assert items[0].title == "Fallback"
        assert items[0].source_name == "working"

    @patch('agent.sources.manager.NewsSourceManager._load_sources')
    def test_fetch_by_category_no_sources_available(self, mock_load_sources):
        """Test fetching when no sources are available."""
        manager = NewsSourceManager()

        items = manager.fetch_by_category('tech')

        assert len(items) == 0


class TestNewsTools:
    """Tests for news tools."""

    def test_fetch_news_tool_success(self):
        """Test fetch_news tool successfully."""
        from agent.tools.news_tools import fetch_news

        # Create a mock manager instance
        mock_manager = Mock()
        mock_manager.get_available_sources.return_value = ['hackernews']
        mock_manager.fetch_by_category.return_value = [
            NewsItem(
                title="Test News",
                url="https://example.com",
                description="Test description",
                source_name="hackernews",
                category="tech",
                metadata={"points": 100}
            )
        ]

        # Patch where NewsSourceManager is imported in news_tools.py
        with patch('agent.sources.NewsSourceManager', return_value=mock_manager):
            result = fetch_news.invoke({"category": "tech", "max_items": 5})

        assert result['count'] == 1
        assert result['category'] == 'tech'
        assert result['source_used'] == 'hackernews'
        assert len(result['items']) == 1
        assert result['items'][0]['title'] == "Test News"

    @patch('agent.sources.manager.NewsSourceManager')
    def test_get_available_sources_tool(self, mock_manager_class):
        """Test get_available_sources tool."""
        from agent.tools.news_tools import get_available_sources

        # Create a mock manager instance
        mock_manager = Mock()
        mock_manager.get_available_sources.return_value = ['hackernews', 'reddit']
        mock_manager.get_source_info.return_value = {
            'total_sources': 4,
            'available_sources': 2,
            'sources': {}
        }

        # Make the mock class return our mock manager instance
        mock_manager_class.return_value = mock_manager

        result = get_available_sources.invoke({})

        assert result['total_sources'] == 4
        assert 'hackernews' in result['available_sources']
        assert 'reddit' in result['available_sources']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
