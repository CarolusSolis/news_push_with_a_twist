"""News fetching tools for the AI agent using the multi-source system."""

import logging
from typing import Optional, Dict, Any, List
from langchain.tools import tool

logger = logging.getLogger(__name__)


@tool
def fetch_news(category: str, source: Optional[str] = None, max_items: int = 5) -> dict:
    """Fetch news from available sources with automatic fallback.

    This tool uses the multi-source news system to fetch content from various sources:
    - hackernews: Tech and startup news from Hacker News
    - reddit: Community discussions from relevant subreddits
    - wikipedia: Current events and historical facts
    - tavily: AI-powered intelligent web search

    Args:
        category: Content category to fetch. Options:
            - 'tech': Technology and AI news
            - 'science': Scientific discoveries and research
            - 'news': General news and current events
            - 'fun': Interesting facts and stories
            - 'history': Historical events and "On this day"
            - 'startup': Startup and entrepreneurship news
            - 'ai': Artificial intelligence specific news
        source: Optional specific source name ('hackernews', 'reddit', 'wikipedia', 'tavily')
                If not specified, uses automatic source selection with fallback
        max_items: Maximum number of news items to return (default: 5)

    Returns:
        Dictionary with:
            - items: List of news items with title, url, description
            - source_used: Name of the source that provided the items
            - category: Category that was fetched
            - count: Number of items returned

    Examples:
        fetch_news(category='tech', max_items=3)  # Auto-select best source for tech news
        fetch_news(category='science', source='reddit', max_items=5)  # Specific source
        fetch_news(category='fun', max_items=2)  # Get interesting facts
    """
    logger.info(f"[NewsTools] fetch_news called: category={category}, source={source}, max_items={max_items}")

    try:
        # Import the news source manager
        from ..sources import NewsSourceManager

        # Initialize the manager
        manager = NewsSourceManager()

        # Log available sources
        available_sources = manager.get_available_sources()
        logger.info(f"[NewsTools] Available sources: {available_sources}")

        # Fetch news items
        news_items = manager.fetch_by_category(
            category=category,
            max_items=max_items,
            source_name=source
        )

        if not news_items:
            logger.warning(f"[NewsTools] No items fetched for category '{category}'")
            return {
                'items': [],
                'source_used': 'none',
                'category': category,
                'count': 0,
                'error': 'No items available from any source'
            }

        # Convert NewsItem objects to dictionaries
        items_list = []
        for item in news_items:
            items_list.append({
                'title': item.title,
                'url': item.url,
                'description': item.description,
                'source': item.source_name,
                'metadata': item.metadata
            })

        # Determine which source was actually used
        source_used = news_items[0].source_name if news_items else 'unknown'

        logger.info(f"[NewsTools] Successfully fetched {len(items_list)} items from {source_used}")

        return {
            'items': items_list,
            'source_used': source_used,
            'category': category,
            'count': len(items_list)
        }

    except Exception as e:
        logger.error(f"[NewsTools] Error fetching news: {e}")
        return {
            'items': [],
            'source_used': 'error',
            'category': category,
            'count': 0,
            'error': str(e)
        }


@tool
def get_available_sources() -> dict:
    """Get information about available news sources.

    Returns:
        Dictionary with:
            - available_sources: List of currently available source names
            - total_sources: Total number of registered sources
            - sources_info: Detailed information about each source

    Use this tool to check which news sources are currently available before
    calling fetch_news with a specific source parameter.
    """
    logger.info("[NewsTools] get_available_sources called")

    try:
        from ..sources import NewsSourceManager

        manager = NewsSourceManager()
        info = manager.get_source_info()

        logger.info(f"[NewsTools] {info['available_sources']}/{info['total_sources']} sources available")

        return {
            'available_sources': manager.get_available_sources(),
            'total_sources': info['total_sources'],
            'sources_info': info['sources']
        }

    except Exception as e:
        logger.error(f"[NewsTools] Error getting source info: {e}")
        return {
            'available_sources': [],
            'total_sources': 0,
            'error': str(e)
        }


@tool
def search_news(query: str, max_items: int = 5) -> dict:
    """Search for news using intelligent web search (Tavily).

    This tool performs a custom search query using Tavily's AI-powered search.
    Use this when you need specific information that doesn't fit standard categories.

    Args:
        query: Search query string (e.g., "latest AI regulations", "quantum computing breakthroughs")
        max_items: Maximum number of results to return (default: 5)

    Returns:
        Dictionary with:
            - items: List of search results with title, url, description
            - query: The search query that was used
            - count: Number of results returned

    Note: This tool requires TAVILY_API_KEY to be set in environment.

    Examples:
        search_news("latest developments in fusion energy", max_items=3)
        search_news("most interesting space missions 2025", max_items=5)
    """
    logger.info(f"[NewsTools] search_news called: query='{query}', max_items={max_items}")

    try:
        from ..sources.tavily_source import TavilySource

        # Initialize Tavily source
        tavily = TavilySource()

        if not tavily.is_available():
            logger.warning("[NewsTools] Tavily source is not available")
            return {
                'items': [],
                'query': query,
                'count': 0,
                'error': 'Tavily search is not available (missing API key)'
            }

        # Perform custom search
        news_items = tavily.search_custom(query, max_results=max_items)

        # Convert to dictionaries
        items_list = []
        for item in news_items:
            items_list.append({
                'title': item.title,
                'url': item.url,
                'description': item.description,
                'source': item.source_name,
                'metadata': item.metadata
            })

        logger.info(f"[NewsTools] Search returned {len(items_list)} results")

        return {
            'items': items_list,
            'query': query,
            'count': len(items_list)
        }

    except Exception as e:
        logger.error(f"[NewsTools] Error searching news: {e}")
        return {
            'items': [],
            'query': query,
            'count': 0,
            'error': str(e)
        }
