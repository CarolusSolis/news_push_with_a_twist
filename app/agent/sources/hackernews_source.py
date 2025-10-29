"""HackerNews source implementation."""

import logging
from typing import List
from datetime import datetime

from .base import NewsSource, NewsItem

logger = logging.getLogger(__name__)


class HackerNewsSource(NewsSource):
    """News source for Hacker News content."""

    def __init__(self):
        """Initialize HackerNews source."""
        super().__init__(name='hackernews', categories=['tech', 'startup', 'ai'])
        self._is_initialized = True

    def is_available(self) -> bool:
        """Check if HackerNews is available.

        Returns:
            True (HackerNews is always available via scraping)
        """
        return True

    def fetch(self, category: str, max_items: int = 5, **kwargs) -> List[NewsItem]:
        """Fetch items from Hacker News.

        Args:
            category: Content category ('tech', 'startup', 'ai')
            max_items: Maximum number of items to return
            **kwargs: Additional parameters (method='scrape')

        Returns:
            List of NewsItem objects

        Raises:
            ValueError: If category not supported
            RuntimeError: If scraping fails
        """
        if not self.supports_category(category):
            raise ValueError(f"Category '{category}' not supported by HackerNews source")

        if not self.is_available():
            raise RuntimeError("HackerNews source is not available")

        try:
            # Import the existing HackerNews scraper
            from ..tools.hacker_news import get_hacker_news_content

            logger.info(f"[HackerNews] Fetching {max_items} items")

            # Fetch using the existing scraper
            result = get_hacker_news_content(method='scrape', max_items=max_items)

            if not result or not result.get('items'):
                logger.warning("[HackerNews] No items returned from scraper")
                return []

            # Convert to NewsItem objects
            news_items = []
            for item in result['items'][:max_items]:
                news_item = NewsItem(
                    title=item.get('title', ''),
                    url=item.get('url'),
                    description=None,  # HN doesn't provide descriptions
                    source_name='hackernews',
                    category=category,
                    published_at=None,  # HN scraper doesn't provide timestamps
                    metadata={
                        'points': item.get('points', 0),
                        'comments': item.get('comments', 0),
                        'rank': item.get('rank', 0)
                    }
                )
                news_items.append(news_item)

            logger.info(f"[HackerNews] Successfully fetched {len(news_items)} items")
            return news_items

        except Exception as e:
            logger.error(f"[HackerNews] Error fetching content: {e}")
            raise RuntimeError(f"Failed to fetch from HackerNews: {e}")

    def __repr__(self) -> str:
        """String representation."""
        return f"<HackerNewsSource categories={self.categories}>"
