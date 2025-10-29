"""Reddit source implementation using PRAW."""

import logging
from typing import List, Dict
from datetime import datetime

from .base import NewsSource, NewsItem

logger = logging.getLogger(__name__)


class RedditSource(NewsSource):
    """News source for Reddit content."""

    # Subreddit mappings for different categories
    SUBREDDIT_MAP = {
        'tech': ['technology', 'programming', 'artificial'],
        'science': ['science', 'askscience', 'space'],
        'fun': ['todayilearned', 'explainlikeimfive', 'Damnthatsinteresting'],
        'news': ['worldnews', 'news'],
        'startup': ['startups', 'entrepreneur']
    }

    def __init__(self):
        """Initialize Reddit source."""
        super().__init__(
            name='reddit',
            categories=['tech', 'science', 'fun', 'news', 'startup']
        )

        self.reddit = None
        self._initialize()

    def _initialize(self):
        """Initialize Reddit client."""
        try:
            import praw

            # Create Reddit instance with minimal credentials (read-only)
            # PRAW allows read-only access without API credentials for public content
            self.reddit = praw.Reddit(
                client_id='reddit_client_for_news',  # Placeholder for read-only
                client_secret='',
                user_agent='agentic_morning_digest/1.0'
            )

            self._is_initialized = True
            logger.info("[Reddit] Initialized Reddit source (read-only mode)")

        except ImportError:
            logger.warning("[Reddit] PRAW library not installed")
            self._is_initialized = False
        except Exception as e:
            logger.error(f"[Reddit] Failed to initialize: {e}")
            self._is_initialized = False

    def is_available(self) -> bool:
        """Check if Reddit source is available.

        Returns:
            True if PRAW is installed and initialized
        """
        return self._is_initialized and self.reddit is not None

    def fetch(self, category: str, max_items: int = 5, time_filter: str = 'day', **kwargs) -> List[NewsItem]:
        """Fetch items from Reddit.

        Args:
            category: Content category ('tech', 'science', 'fun', 'news', 'startup')
            max_items: Maximum number of items to return
            time_filter: Time filter ('hour', 'day', 'week', 'month', 'year', 'all')
            **kwargs: Additional parameters

        Returns:
            List of NewsItem objects

        Raises:
            ValueError: If category not supported
            RuntimeError: If Reddit is not available
        """
        if not self.supports_category(category):
            raise ValueError(f"Category '{category}' not supported by Reddit source")

        if not self.is_available():
            raise RuntimeError("Reddit source is not available")

        try:
            subreddits = self.SUBREDDIT_MAP.get(category, [])
            if not subreddits:
                logger.warning(f"[Reddit] No subreddits mapped for category '{category}'")
                return []

            news_items = []

            # Fetch from multiple subreddits
            items_per_sub = max(1, max_items // len(subreddits))

            for subreddit_name in subreddits:
                try:
                    subreddit = self.reddit.subreddit(subreddit_name)

                    # Get hot posts from the subreddit
                    for submission in subreddit.hot(limit=items_per_sub):
                        # Skip stickied posts
                        if submission.stickied:
                            continue

                        news_item = NewsItem(
                            title=submission.title,
                            url=submission.url if not submission.is_self else f"https://reddit.com{submission.permalink}",
                            description=submission.selftext[:200] if submission.is_self else None,
                            source_name='reddit',
                            category=category,
                            published_at=datetime.fromtimestamp(submission.created_utc),
                            metadata={
                                'subreddit': subreddit_name,
                                'score': submission.score,
                                'num_comments': submission.num_comments,
                                'author': str(submission.author) if submission.author else '[deleted]'
                            }
                        )
                        news_items.append(news_item)

                        if len(news_items) >= max_items:
                            break

                except Exception as e:
                    logger.warning(f"[Reddit] Error fetching from r/{subreddit_name}: {e}")
                    continue

                if len(news_items) >= max_items:
                    break

            logger.info(f"[Reddit] Successfully fetched {len(news_items)} items from {len(subreddits)} subreddits")
            return news_items[:max_items]

        except Exception as e:
            logger.error(f"[Reddit] Error fetching content: {e}")
            raise RuntimeError(f"Failed to fetch from Reddit: {e}")

    def __repr__(self) -> str:
        """String representation."""
        status = "available" if self.is_available() else "unavailable"
        return f"<RedditSource categories={self.categories} status='{status}'>"
