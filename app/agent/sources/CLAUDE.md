# app/agent/sources/CLAUDE.md

Multi-source news architecture and source development guide.

## Architecture Overview

The multi-source system enables the agent to fetch news from multiple providers with automatic fallback:

```
User Request → NewsSourceManager → [HackerNews, Reddit, Wikipedia, Tavily]
                    ↓
              Priority-Based Fallback
                    ↓
              Unified NewsItem Format
```

## Core Components

```
sources/
├── CLAUDE.md                  # This file
├── __init__.py               # Exports NewsSource, NewsItem, NewsSourceManager
├── base.py                   # Abstract NewsSource + NewsItem dataclass
├── manager.py                # NewsSourceManager (orchestration + fallback)
├── hackernews_source.py      # HackerNews implementation
├── reddit_source.py          # Reddit (PRAW) implementation
├── wikipedia_source.py       # Wikipedia API implementation
└── tavily_source.py          # Tavily search implementation
```

## NewsItem Data Model

All sources return `NewsItem` objects with standardized fields:

```python
@dataclass
class NewsItem:
    title: str                    # Headline or title
    url: Optional[str]            # Link to content
    description: Optional[str]    # Summary or excerpt
    source_name: str              # Source identifier ('hackernews', 'reddit', etc.)
    category: str                 # Content category ('tech', 'science', etc.)
    published_at: Optional[datetime]  # Publication timestamp
    metadata: Dict[str, Any]      # Source-specific data (points, score, etc.)
```

## NewsSource Base Class

All sources inherit from `NewsSource` abstract class:

```python
class MyNewsSource(NewsSource):
    def __init__(self):
        super().__init__(name='my_source', categories=['tech', 'science'])
        # Initialize your source

    def is_available(self) -> bool:
        """Check if source can be used (API keys, network, etc.)."""
        return True  # or check API key

    def fetch(self, category: str, max_items: int = 5, **kwargs) -> List[NewsItem]:
        """Fetch news items from this source."""
        # Your implementation
        return [NewsItem(...)]
```

## Available Sources

### 1. HackerNews Source
**File**: `hackernews_source.py`
**Categories**: `tech`, `startup`, `ai`
**Requirements**: None (uses BeautifulSoup scraper)
**API Key**: Not required
**Rate Limit**: ~60 req/min (polite scraping)

**Usage**:
```python
from app.agent.sources.hackernews_source import HackerNewsSource

hn = HackerNewsSource()
items = hn.fetch('tech', max_items=10)
```

**Metadata**:
- `points`: Upvote count
- `comments`: Comment count
- `rank`: Position on front page

### 2. Reddit Source
**File**: `reddit_source.py`
**Categories**: `tech`, `science`, `fun`, `news`, `startup`
**Requirements**: `praw>=7.7.0`
**API Key**: Not required (read-only public access)
**Rate Limit**: ~60 req/min (Reddit API limits)

**Subreddit Mappings**:
```python
{
    'tech': ['technology', 'programming', 'artificial'],
    'science': ['science', 'askscience', 'space'],
    'fun': ['todayilearned', 'explainlikeimfive', 'Damnthatsinteresting'],
    'news': ['worldnews', 'news'],
    'startup': ['startups', 'entrepreneur']
}
```

**Usage**:
```python
from app.agent.sources.reddit_source import RedditSource

reddit = RedditSource()
items = reddit.fetch('science', max_items=5, time_filter='day')
```

**Metadata**:
- `subreddit`: Subreddit name
- `score`: Reddit score (upvotes - downvotes)
- `num_comments`: Comment count
- `author`: Post author

### 3. Wikipedia Source
**File**: `wikipedia_source.py`
**Categories**: `news`, `history`, `fun`, `events`
**Requirements**: `requests` (already included)
**API Key**: Not required (public Wikimedia API)
**Rate Limit**: ~200 req/min (generous)

**Features**:
- "On this day" historical events
- Current events portal
- Rich metadata with year information

**Usage**:
```python
from app.agent.sources.wikipedia_source import WikipediaSource

wiki = WikipediaSource()
items = wiki.fetch('history', max_items=5)  # Returns today's historical events
```

**Metadata**:
- `year`: For historical events
- `type`: 'historical_event' or 'current_events_portal'
- `date`: Date of the event

### 4. Tavily Source
**File**: `tavily_source.py`
**Categories**: `tech`, `science`, `news`, `fun`, `ai`
**Requirements**: `langchain-tavily>=0.1.0`
**API Key**: **Required** (`TAVILY_API_KEY` env variable)
**Rate Limit**: Depends on plan (usually 1000/month free)

**Features**:
- AI-powered search
- Custom search queries
- News-specific topic filtering

**Usage**:
```python
from app.agent.sources.tavily_source import TavilySource

tavily = TavilySource()
if tavily.is_available():
    items = tavily.fetch('tech', max_items=5)
    # Or custom search
    items = tavily.search_custom("quantum computing breakthroughs")
```

**Metadata**:
- `query`: Search query used
- `topic`: 'general' or 'news'
- `score`: Relevance score (if available)

## NewsSourceManager

The `NewsSourceManager` orchestrates multiple sources with automatic fallback:

### Initialization
```python
from app.agent.sources import NewsSourceManager

manager = NewsSourceManager()
# Automatically loads all available sources
```

### Configuration
Sources are configured in `app/config/sources.json`:

```json
{
  "priority": ["hackernews", "reddit", "tavily", "wikipedia"],
  "sources": {
    "hackernews": {
      "enabled": true,
      "categories": ["tech", "startup", "ai"],
      "requires_api_key": false
    }
  }
}
```

### Fetching with Fallback
```python
# Auto-select best source for category
items = manager.fetch_by_category('tech', max_items=5)

# Use specific source
items = manager.fetch_by_category('science', source_name='reddit', max_items=3)

# Check available sources
available = manager.get_available_sources()  # ['hackernews', 'reddit', 'wikipedia']

# Get sources for category
sources = manager.get_sources_for_category('tech')  # ['hackernews', 'reddit', 'tavily']
```

### Fallback Strategy
1. Try sources in priority order from config
2. Skip unavailable sources (no API key, network error, etc.)
3. Return first successful result
4. Return empty list if all sources fail

## Agent Tools Integration

The agent uses these tools (defined in `app/agent/tools/news_tools.py`):

### 1. fetch_news(category, source, max_items)
```python
@tool
def fetch_news(category: str, source: Optional[str] = None, max_items: int = 5) -> dict:
    """Primary tool for fetching news from multiple sources."""
```

**Agent Usage**:
```
fetch_news('tech', max_items=10)  # Auto-select
fetch_news('science', source='reddit', max_items=5)  # Specific
```

### 2. get_available_sources()
```python
@tool
def get_available_sources() -> dict:
    """Check which sources are currently available."""
```

**Agent Usage**:
```
get_available_sources()  # Returns list of available sources
```

### 3. search_news(query, max_items)
```python
@tool
def search_news(query: str, max_items: int = 5) -> dict:
    """Custom search using Tavily (requires API key)."""
```

**Agent Usage**:
```
search_news("quantum computing breakthroughs", max_items=3)
```

## Adding a New Source

### Step 1: Create Source Class

```python
# app/agent/sources/newsapi_source.py
from typing import List
from .base import NewsSource, NewsItem

class NewsAPISource(NewsSource):
    def __init__(self):
        super().__init__(
            name='newsapi',
            categories=['tech', 'science', 'business']
        )
        self._api_key = os.getenv('NEWS_API_KEY')

    def is_available(self) -> bool:
        return self._api_key is not None

    def fetch(self, category: str, max_items: int = 5, **kwargs) -> List[NewsItem]:
        if not self.supports_category(category):
            raise ValueError(f"Category '{category}' not supported")

        if not self.is_available():
            raise RuntimeError("NewsAPI key not available")

        # Your implementation
        response = requests.get(
            'https://newsapi.org/v2/top-headlines',
            params={'category': category, 'apiKey': self._api_key}
        )
        data = response.json()

        items = []
        for article in data['articles'][:max_items]:
            items.append(NewsItem(
                title=article['title'],
                url=article['url'],
                description=article['description'],
                source_name='newsapi',
                category=category,
                published_at=datetime.fromisoformat(article['publishedAt']),
                metadata={'source': article['source']['name']}
            ))

        return items
```

### Step 2: Register in Manager

Update `app/agent/sources/manager.py` in the `_load_sources()` method:

```python
def _load_sources(self):
    # ... existing sources ...

    # Try to load NewsAPI source
    try:
        from .newsapi_source import NewsAPISource
        newsapi_source = NewsAPISource()
        if newsapi_source.is_available():
            self.register_source(newsapi_source)
            logger.info("[NewsSourceManager] ✓ NewsAPI source registered")
        else:
            logger.warning("[NewsSourceManager] ✗ NewsAPI unavailable (missing API key)")
    except Exception as e:
        logger.warning(f"[NewsSourceManager] Failed to load NewsAPI source: {e}")
```

### Step 3: Add Configuration

Update `app/config/sources.json`:

```json
{
  "priority": ["hackernews", "reddit", "newsapi", "tavily", "wikipedia"],
  "sources": {
    "newsapi": {
      "enabled": true,
      "categories": ["tech", "science", "business"],
      "description": "NewsAPI - Global news from 80,000+ sources",
      "rate_limit_per_minute": 100,
      "requires_api_key": true,
      "api_key_env": "NEWS_API_KEY"
    }
  }
}
```

### Step 4: Write Tests

Create tests in `tests/test_sources.py`:

```python
class TestNewsAPISource:
    def test_newsapi_source_initialization(self):
        source = NewsAPISource()
        assert source.name == 'newsapi'
        assert 'tech' in source.categories

    @patch.dict('os.environ', {'NEWS_API_KEY': 'test_key'})
    @patch('requests.get')
    def test_newsapi_fetch(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = {
            'articles': [{'title': 'Test', 'url': 'https://example.com'}]
        }
        mock_get.return_value = mock_response

        source = NewsAPISource()
        items = source.fetch('tech', max_items=1)

        assert len(items) == 1
        assert items[0].title == 'Test'
```

### Step 5: Update Documentation

Add to this file under "Available Sources" section.

## Testing

### Unit Tests
```bash
# Test all sources
pytest tests/test_sources.py -v

# Test specific source
pytest tests/test_sources.py::TestHackerNewsSource -v

# Test manager
pytest tests/test_sources.py::TestNewsSourceManager -v
```

### Manual Testing
```bash
conda activate news_push
cd app
python -c "
from agent.sources import NewsSourceManager
manager = NewsSourceManager()
print(f'Available sources: {manager.get_available_sources()}')
items = manager.fetch_by_category('tech', max_items=3)
print(f'Fetched {len(items)} items')
for item in items:
    print(f'  - {item.title} ({item.source_name})')
"
```

## Best Practices

✅ **DO:**
- Implement `is_available()` to check API keys/dependencies
- Handle network errors gracefully
- Return empty list on failure (don't raise unless critical)
- Use `logger.info/warning/error` for debugging
- Validate category support
- Add rich metadata for debugging
- Write comprehensive tests

❌ **DON'T:**
- Make API calls in `__init__()` or `is_available()`
- Raise exceptions on fetch failures (return [] instead)
- Forget to set `source_name` in NewsItem
- Skip error handling
- Hardcode API keys
- Return inconsistent data formats

## Performance Considerations

- **Caching**: Not implemented yet (future enhancement)
- **Rate Limits**: Respect source rate limits
- **Timeouts**: Set reasonable timeouts (10s recommended)
- **Parallelization**: Not currently supported (sequential fallback)
- **Retry Logic**: Implement in individual sources if needed

## Debugging

### Check Source Availability
```python
from app.agent.sources.reddit_source import RedditSource
source = RedditSource()
print(f"Available: {source.is_available()}")
print(f"Info: {source.get_info()}")
```

### Test Manager Fallback
```python
from app.agent.sources import NewsSourceManager
import logging
logging.basicConfig(level=logging.INFO)

manager = NewsSourceManager()
items = manager.fetch_by_category('tech', max_items=3)
# Check logs to see which sources were tried
```

### Enable Verbose Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
# Now all source operations will be logged
```

## Configuration Reference

### Source Priority
Controls fallback order:
```json
"priority": ["hackernews", "reddit", "tavily", "wikipedia"]
```

### Category Preferences
Fine-tune which sources to use for each category:
```json
"category_preferences": {
  "tech": {
    "preferred_sources": ["hackernews", "reddit"],
    "max_items_per_source": 3
  }
}
```

## Environment Variables

- `TAVILY_API_KEY`: Required for Tavily source
- `NEWS_API_KEY`: Example for future source
- `OPENAI_API_KEY`: Required for agent LLM calls (not source-specific)

## Future Enhancements

- [ ] **Caching Layer**: 5-minute TTL to reduce API calls
- [ ] **Async Fetching**: Parallel requests to multiple sources
- [ ] **Source Scoring**: Track reliability and prefer better sources
- [ ] **User Preferences**: Let users customize source priority
- [ ] **RSS Feed Source**: Generic RSS aggregator
- [ ] **NewsAPI.ai Integration**: Professional news API
- [ ] **Rate Limit Management**: Automatic throttling

## Related Files

- `/app/agent/core.py`: Agent system prompt using new tools
- `/app/agent/tools/news_tools.py`: Agent tool implementations
- `/app/config/sources.json`: Source configuration
- `/tests/test_sources.py`: Comprehensive test suite
- `/CLAUDE.md`: Main project documentation
