"""Tavily search source implementation."""

import logging
import os
from typing import List, Optional
from datetime import datetime

from .base import NewsSource, NewsItem

logger = logging.getLogger(__name__)


class TavilySource(NewsSource):
    """News source using Tavily search API."""

    # Category to search query mapping
    CATEGORY_QUERIES = {
        'tech': ['latest technology news', 'AI breakthroughs', 'new tech products'],
        'science': ['recent scientific discoveries', 'space exploration news', 'medical breakthroughs'],
        'news': ['breaking news today', 'world news', 'current events'],
        'fun': ['interesting facts', 'unusual discoveries', 'amazing stories'],
        'ai': ['artificial intelligence news', 'machine learning advances', 'AI research']
    }

    def __init__(self):
        """Initialize Tavily source."""
        super().__init__(
            name='tavily',
            categories=['tech', 'science', 'news', 'fun', 'ai']
        )

        self.tavily_client = None
        self._initialize()

    def _initialize(self):
        """Initialize Tavily client."""
        try:
            from langchain_tavily import TavilySearch

            api_key = os.getenv('TAVILY_API_KEY')
            if not api_key:
                logger.warning("[Tavily] TAVILY_API_KEY not found in environment")
                self._is_initialized = False
                return

            self.tavily_client = TavilySearch(
                max_results=5,
                topic="general"  # Can be overridden per request
            )

            self._is_initialized = True
            logger.info("[Tavily] Initialized Tavily search source")

        except ImportError:
            logger.warning("[Tavily] langchain-tavily library not installed")
            self._is_initialized = False
        except Exception as e:
            logger.error(f"[Tavily] Failed to initialize: {e}")
            self._is_initialized = False

    def is_available(self) -> bool:
        """Check if Tavily source is available.

        Returns:
            True if TAVILY_API_KEY is set and client is initialized
        """
        return self._is_initialized and self.tavily_client is not None

    def fetch(
        self,
        category: str,
        max_items: int = 5,
        topic: str = "general",
        days: Optional[int] = None,
        **kwargs
    ) -> List[NewsItem]:
        """Fetch items from Tavily search.

        Args:
            category: Content category ('tech', 'science', 'news', 'fun', 'ai')
            max_items: Maximum number of items to return
            topic: Search topic ('general' or 'news')
            days: Number of days back to search (only for topic='news')
            **kwargs: Additional parameters

        Returns:
            List of NewsItem objects

        Raises:
            ValueError: If category not supported
            RuntimeError: If Tavily is not available
        """
        if not self.supports_category(category):
            raise ValueError(f"Category '{category}' not supported by Tavily source")

        if not self.is_available():
            raise RuntimeError("Tavily source is not available")

        try:
            # Get search queries for this category
            queries = self.CATEGORY_QUERIES.get(category, [category])

            news_items = []

            # Perform searches for each query
            items_per_query = max(1, max_items // len(queries))

            for query in queries:
                try:
                    logger.info(f"[Tavily] Searching for: {query}")

                    # Perform search
                    results = self.tavily_client.invoke(query)

                    # Parse results - results is usually a string or list
                    if isinstance(results, str):
                        # Single result as string
                        news_item = NewsItem(
                            title=query,
                            url=None,
                            description=results[:300],  # Limit description length
                            source_name='tavily',
                            category=category,
                            published_at=datetime.now(),
                            metadata={
                                'query': query,
                                'topic': topic
                            }
                        )
                        news_items.append(news_item)

                    elif isinstance(results, list):
                        # Multiple results
                        for result in results[:items_per_query]:
                            if isinstance(result, dict):
                                news_item = NewsItem(
                                    title=result.get('title', query),
                                    url=result.get('url'),
                                    description=result.get('content', result.get('snippet', ''))[:300],
                                    source_name='tavily',
                                    category=category,
                                    published_at=None,
                                    metadata={
                                        'query': query,
                                        'topic': topic,
                                        'score': result.get('score', 0)
                                    }
                                )
                                news_items.append(news_item)

                except Exception as e:
                    logger.warning(f"[Tavily] Error searching for '{query}': {e}")
                    continue

                if len(news_items) >= max_items:
                    break

            logger.info(f"[Tavily] Successfully fetched {len(news_items)} items for category '{category}'")
            return news_items[:max_items]

        except Exception as e:
            logger.error(f"[Tavily] Error fetching content: {e}")
            raise RuntimeError(f"Failed to fetch from Tavily: {e}")

    def search_custom(self, query: str, max_results: int = 5, topic: str = "general") -> List[NewsItem]:
        """Perform a custom search with Tavily.

        Args:
            query: Custom search query
            max_results: Maximum number of results
            topic: Search topic ('general' or 'news')

        Returns:
            List of NewsItem objects
        """
        if not self.is_available():
            raise RuntimeError("Tavily source is not available")

        try:
            logger.info(f"[Tavily] Custom search: {query}")

            results = self.tavily_client.invoke(query)

            news_items = []

            if isinstance(results, str):
                news_item = NewsItem(
                    title=query,
                    url=None,
                    description=results[:300],
                    source_name='tavily',
                    category='custom',
                    published_at=datetime.now(),
                    metadata={'query': query, 'topic': topic}
                )
                news_items.append(news_item)

            elif isinstance(results, list):
                for result in results[:max_results]:
                    if isinstance(result, dict):
                        news_item = NewsItem(
                            title=result.get('title', query),
                            url=result.get('url'),
                            description=result.get('content', result.get('snippet', ''))[:300],
                            source_name='tavily',
                            category='custom',
                            published_at=None,
                            metadata={
                                'query': query,
                                'topic': topic,
                                'score': result.get('score', 0)
                            }
                        )
                        news_items.append(news_item)

            logger.info(f"[Tavily] Custom search returned {len(news_items)} items")
            return news_items

        except Exception as e:
            logger.error(f"[Tavily] Error in custom search: {e}")
            return []

    def __repr__(self) -> str:
        """String representation."""
        status = "available" if self.is_available() else "unavailable"
        return f"<TavilySource categories={self.categories} status='{status}'>"
