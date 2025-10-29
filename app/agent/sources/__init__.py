"""News sources for the Agentic Morning Digest."""

from .base import NewsSource, NewsItem
from .manager import NewsSourceManager

__all__ = [
    'NewsSource',
    'NewsItem',
    'NewsSourceManager',
]
