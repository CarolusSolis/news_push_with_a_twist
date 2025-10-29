"""Base abstraction for news sources in the Agentic Morning Digest."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class NewsItem:
    """A single news item from any source."""
    title: str
    url: Optional[str] = None
    description: Optional[str] = None
    source_name: str = ""
    category: str = ""
    published_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            'title': self.title,
            'url': self.url,
            'description': self.description,
            'source_name': self.source_name,
            'category': self.category,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'metadata': self.metadata
        }


class NewsSource(ABC):
    """Abstract base class for all news sources."""

    def __init__(self, name: str, categories: List[str]):
        """Initialize news source.

        Args:
            name: Unique identifier for this source
            categories: List of content categories this source supports
        """
        self.name = name
        self.categories = categories
        self._is_initialized = False

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this source is available (API keys, network, etc.).

        Returns:
            True if source can be used, False otherwise
        """
        pass

    @abstractmethod
    def fetch(self, category: str, max_items: int = 5, **kwargs) -> List[NewsItem]:
        """Fetch news items from this source.

        Args:
            category: Content category to fetch
            max_items: Maximum number of items to return
            **kwargs: Additional source-specific parameters

        Returns:
            List of NewsItem objects

        Raises:
            ValueError: If category not supported
            RuntimeError: If source is not available
        """
        pass

    def supports_category(self, category: str) -> bool:
        """Check if this source supports a given category.

        Args:
            category: Category to check

        Returns:
            True if category is supported
        """
        return category in self.categories

    def get_info(self) -> Dict[str, Any]:
        """Get information about this source.

        Returns:
            Dictionary with source metadata
        """
        return {
            'name': self.name,
            'categories': self.categories,
            'available': self.is_available(),
            'initialized': self._is_initialized
        }

    def __repr__(self) -> str:
        """String representation of the source."""
        status = "available" if self.is_available() else "unavailable"
        return f"<{self.__class__.__name__} name='{self.name}' status='{status}'>"
