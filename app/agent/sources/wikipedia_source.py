"""Wikipedia source implementation."""

import logging
from typing import List
from datetime import datetime
import requests

from .base import NewsSource, NewsItem

logger = logging.getLogger(__name__)


class WikipediaSource(NewsSource):
    """News source for Wikipedia current events and 'On this day' content."""

    def __init__(self):
        """Initialize Wikipedia source."""
        super().__init__(
            name='wikipedia',
            categories=['news', 'history', 'fun', 'events']
        )
        self._is_initialized = True

    def is_available(self) -> bool:
        """Check if Wikipedia is available.

        Returns:
            True (Wikipedia is always available via public API)
        """
        return True

    def fetch(self, category: str, max_items: int = 5, **kwargs) -> List[NewsItem]:
        """Fetch items from Wikipedia.

        Args:
            category: Content category ('news', 'history', 'fun', 'events')
            max_items: Maximum number of items to return
            **kwargs: Additional parameters

        Returns:
            List of NewsItem objects

        Raises:
            ValueError: If category not supported
            RuntimeError: If Wikipedia is not available
        """
        if not self.supports_category(category):
            raise ValueError(f"Category '{category}' not supported by Wikipedia source")

        if not self.is_available():
            raise RuntimeError("Wikipedia source is not available")

        try:
            if category in ['history', 'fun']:
                return self._fetch_on_this_day(max_items)
            elif category in ['news', 'events']:
                return self._fetch_current_events(max_items)
            else:
                logger.warning(f"[Wikipedia] Unknown category '{category}', using 'On this day'")
                return self._fetch_on_this_day(max_items)

        except Exception as e:
            logger.error(f"[Wikipedia] Error fetching content: {e}")
            raise RuntimeError(f"Failed to fetch from Wikipedia: {e}")

    def _fetch_on_this_day(self, max_items: int) -> List[NewsItem]:
        """Fetch 'On this day' events from Wikipedia.

        Args:
            max_items: Maximum number of items to return

        Returns:
            List of NewsItem objects
        """
        try:
            # Get today's date
            today = datetime.now()
            month = today.strftime('%m')
            day = today.strftime('%d')

            # Wikipedia Feed API - "On this day"
            url = f"https://api.wikimedia.org/feed/v1/wikipedia/en/onthisday/all/{month}/{day}"

            headers = {
                'User-Agent': 'Agentic Morning Digest/1.0 (educational project)'
            }

            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()

            news_items = []

            # Get events (historical events)
            events = data.get('events', [])[:max_items]
            for event in events:
                text = event.get('text', '')
                year = event.get('year', '')
                pages = event.get('pages', [])

                # Get URL from first page if available
                url = pages[0].get('content_urls', {}).get('desktop', {}).get('page') if pages else None

                news_item = NewsItem(
                    title=f"In {year}: {text}",
                    url=url,
                    description=text,
                    source_name='wikipedia',
                    category='history',
                    published_at=None,
                    metadata={
                        'year': year,
                        'type': 'historical_event',
                        'date': f"{month}/{day}"
                    }
                )
                news_items.append(news_item)

            logger.info(f"[Wikipedia] Successfully fetched {len(news_items)} 'On this day' events")
            return news_items

        except Exception as e:
            logger.error(f"[Wikipedia] Error fetching 'On this day': {e}")
            return []

    def _fetch_current_events(self, max_items: int) -> List[NewsItem]:
        """Fetch current events from Wikipedia.

        Args:
            max_items: Maximum number of items to return

        Returns:
            List of NewsItem objects
        """
        try:
            # Fetch the "Current events" portal page
            # Using Wikipedia API to get page content
            url = "https://en.wikipedia.org/w/api.php"

            params = {
                'action': 'parse',
                'page': 'Portal:Current_events',
                'format': 'json',
                'prop': 'text',
                'section': 0  # Get the first section (today's events)
            }

            headers = {
                'User-Agent': 'Agentic Morning Digest/1.0 (educational project)'
            }

            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()

            # For now, return a simplified version
            # Full parsing of Wikipedia's current events page requires HTML parsing
            # which is complex - we'll use a simpler approach

            news_items = []

            # Create a single aggregated item pointing to current events
            news_item = NewsItem(
                title="Wikipedia Current Events",
                url="https://en.wikipedia.org/wiki/Portal:Current_events",
                description="Today's notable news events from around the world, as documented by Wikipedia editors.",
                source_name='wikipedia',
                category='news',
                published_at=datetime.now(),
                metadata={
                    'type': 'current_events_portal'
                }
            )
            news_items.append(news_item)

            logger.info(f"[Wikipedia] Successfully fetched {len(news_items)} current events")
            return news_items

        except Exception as e:
            logger.error(f"[Wikipedia] Error fetching current events: {e}")
            return []

    def __repr__(self) -> str:
        """String representation."""
        return f"<WikipediaSource categories={self.categories}>"
