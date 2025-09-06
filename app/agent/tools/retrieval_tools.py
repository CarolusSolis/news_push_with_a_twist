"""Content retrieval tools for the AI agent."""

import json
from typing import Dict
from pathlib import Path
from langchain.tools import tool
import logging

from .hacker_news import get_hacker_news_content

logger = logging.getLogger(__name__)

@tool 
def fetch_content_by_type(content_type: str, use_live: bool = False) -> dict:
    """Fetch content from available sources.
    
    Args:
        content_type: Type of content to fetch ('tech', 'history', 'quotes')
        use_live: Whether to use live data sources (default: False for mock data)
    
    Returns:
        Dictionary with fetched content
    """
    logger.info(f"[Retriever] Fetching {content_type} content (live={use_live})...")
    
    if use_live and content_type == 'tech':
        # Use live Hacker News scraping
        try:
            result = get_hacker_news_content(method='scrape', max_items=10)
            if result['items']:
                logger.info(f"[Retriever] Found {len(result['items'])} live tech items")
                return result
            else:
                logger.warning("[Retriever] No live tech items found, falling back to mock data")
        except Exception as e:
            logger.error(f"[Retriever] Error fetching live tech content: {e}")
            logger.warning("[Retriever] Falling back to mock data")
    
    # Load mock data (fallback or default)
    try:
        data_path = Path(__file__).parent.parent.parent / 'data' / 'static_samples.json'
        with open(data_path, 'r') as f:
            mock_data = json.load(f)
        
        content_map = {
            'tech': mock_data.get('hacker_news', []),
            'history': mock_data.get('wikipedia_today', []),  
            'quotes': mock_data.get('quotes', [])
        }
        
        result = content_map.get(content_type, [])
        logger.info(f"[Retriever] Found {len(result)} {content_type} items from mock data")
        return {'items': result, 'source': content_type}
        
    except Exception as e:
        logger.error(f"[Retriever] Error fetching {content_type}: {e}")
        return {'items': [], 'source': content_type}