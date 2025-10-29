"""News source manager for orchestrating multiple news sources."""

import logging
from typing import List, Dict, Optional, Any
from pathlib import Path
import json

from .base import NewsSource, NewsItem

logger = logging.getLogger(__name__)


class NewsSourceManager:
    """Manages multiple news sources with priority-based fallback."""

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize the news source manager.

        Args:
            config_path: Optional path to sources.json configuration file
        """
        self.sources: Dict[str, NewsSource] = {}
        self.source_priority: List[str] = []
        self.config_path = config_path or Path(__file__).parent.parent.parent / 'config' / 'sources.json'

        logger.info("[NewsSourceManager] Initializing news source manager")
        self._load_config()
        self._load_sources()

    def _load_config(self):
        """Load configuration from sources.json if it exists."""
        if not self.config_path.exists():
            logger.warning(f"[NewsSourceManager] Config file not found: {self.config_path}")
            logger.info("[NewsSourceManager] Using default configuration")
            self._use_default_config()
            return

        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)

            # Extract source priority
            self.source_priority = config.get('priority', [])
            self.source_config = config.get('sources', {})

            logger.info(f"[NewsSourceManager] Loaded config with {len(self.source_config)} sources")
        except Exception as e:
            logger.error(f"[NewsSourceManager] Error loading config: {e}")
            self._use_default_config()

    def _use_default_config(self):
        """Use default configuration if config file is not available."""
        self.source_priority = ['hackernews', 'reddit', 'wikipedia', 'tavily']
        self.source_config = {
            'hackernews': {'enabled': True, 'categories': ['tech', 'startup']},
            'reddit': {'enabled': True, 'categories': ['tech', 'science', 'fun']},
            'wikipedia': {'enabled': True, 'categories': ['news', 'history', 'fun']},
            'tavily': {'enabled': True, 'categories': ['tech', 'news', 'science', 'fun']}
        }

    def _load_sources(self):
        """Auto-discover and load available news sources."""
        logger.info("[NewsSourceManager] Loading available news sources...")

        # Import and register sources dynamically
        # This allows graceful degradation if dependencies are missing

        # Try to load HackerNews source
        try:
            from .hackernews_source import HackerNewsSource
            hn_source = HackerNewsSource()
            if hn_source.is_available():
                self.register_source(hn_source)
                logger.info("[NewsSourceManager] ✓ HackerNews source registered")
            else:
                logger.warning("[NewsSourceManager] ✗ HackerNews source unavailable")
        except Exception as e:
            logger.warning(f"[NewsSourceManager] Failed to load HackerNews source: {e}")

        # Try to load Reddit source
        try:
            from .reddit_source import RedditSource
            reddit_source = RedditSource()
            if reddit_source.is_available():
                self.register_source(reddit_source)
                logger.info("[NewsSourceManager] ✓ Reddit source registered")
            else:
                logger.warning("[NewsSourceManager] ✗ Reddit source unavailable")
        except Exception as e:
            logger.warning(f"[NewsSourceManager] Failed to load Reddit source: {e}")

        # Try to load Wikipedia source
        try:
            from .wikipedia_source import WikipediaSource
            wiki_source = WikipediaSource()
            if wiki_source.is_available():
                self.register_source(wiki_source)
                logger.info("[NewsSourceManager] ✓ Wikipedia source registered")
            else:
                logger.warning("[NewsSourceManager] ✗ Wikipedia source unavailable")
        except Exception as e:
            logger.warning(f"[NewsSourceManager] Failed to load Wikipedia source: {e}")

        # Try to load Tavily source
        try:
            from .tavily_source import TavilySource
            tavily_source = TavilySource()
            if tavily_source.is_available():
                self.register_source(tavily_source)
                logger.info("[NewsSourceManager] ✓ Tavily source registered")
            else:
                logger.warning("[NewsSourceManager] ✗ Tavily source unavailable (missing API key)")
        except Exception as e:
            logger.warning(f"[NewsSourceManager] Failed to load Tavily source: {e}")

        logger.info(f"[NewsSourceManager] Loaded {len(self.sources)} available sources")

    def register_source(self, source: NewsSource):
        """Register a news source.

        Args:
            source: NewsSource instance to register
        """
        self.sources[source.name] = source
        logger.debug(f"[NewsSourceManager] Registered source: {source.name}")

    def get_available_sources(self) -> List[str]:
        """Get list of currently available source names.

        Returns:
            List of source names that are available
        """
        return [name for name, source in self.sources.items() if source.is_available()]

    def get_sources_for_category(self, category: str) -> List[str]:
        """Get list of sources that support a given category.

        Args:
            category: Content category

        Returns:
            List of source names supporting the category
        """
        return [
            name for name, source in self.sources.items()
            if source.is_available() and source.supports_category(category)
        ]

    def fetch_by_category(
        self,
        category: str,
        max_items: int = 5,
        source_name: Optional[str] = None,
        **kwargs
    ) -> List[NewsItem]:
        """Fetch news items by category with automatic fallback.

        Args:
            category: Content category to fetch
            max_items: Maximum number of items to return
            source_name: Optional specific source to use
            **kwargs: Additional source-specific parameters

        Returns:
            List of NewsItem objects
        """
        logger.info(f"[NewsSourceManager] Fetching {category} content (max_items={max_items})")

        # If specific source requested, use it
        if source_name:
            if source_name not in self.sources:
                logger.error(f"[NewsSourceManager] Source '{source_name}' not found")
                return []

            source = self.sources[source_name]
            if not source.is_available():
                logger.error(f"[NewsSourceManager] Source '{source_name}' is not available")
                return []

            if not source.supports_category(category):
                logger.error(f"[NewsSourceManager] Source '{source_name}' doesn't support category '{category}'")
                return []

            try:
                items = source.fetch(category, max_items, **kwargs)
                logger.info(f"[NewsSourceManager] Fetched {len(items)} items from {source_name}")
                return items
            except Exception as e:
                logger.error(f"[NewsSourceManager] Error fetching from {source_name}: {e}")
                return []

        # Auto-select sources by priority
        available_sources = self.get_sources_for_category(category)

        if not available_sources:
            logger.warning(f"[NewsSourceManager] No sources available for category '{category}'")
            return []

        # Try sources in priority order
        priority_sources = [s for s in self.source_priority if s in available_sources]
        remaining_sources = [s for s in available_sources if s not in priority_sources]
        ordered_sources = priority_sources + remaining_sources

        for source_name in ordered_sources:
            try:
                source = self.sources[source_name]
                items = source.fetch(category, max_items, **kwargs)

                if items:
                    logger.info(f"[NewsSourceManager] Successfully fetched {len(items)} items from {source_name}")
                    return items
                else:
                    logger.debug(f"[NewsSourceManager] No items from {source_name}, trying next source")

            except Exception as e:
                logger.warning(f"[NewsSourceManager] Error fetching from {source_name}: {e}")
                continue

        logger.warning(f"[NewsSourceManager] All sources failed for category '{category}'")
        return []

    def get_source_info(self) -> Dict[str, Any]:
        """Get information about all sources.

        Returns:
            Dictionary with source information
        """
        return {
            'total_sources': len(self.sources),
            'available_sources': len(self.get_available_sources()),
            'sources': {
                name: source.get_info()
                for name, source in self.sources.items()
            },
            'priority': self.source_priority
        }

    def __repr__(self) -> str:
        """String representation of the manager."""
        available = len(self.get_available_sources())
        total = len(self.sources)
        return f"<NewsSourceManager sources={available}/{total} available>"
