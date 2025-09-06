"""Content analysis and processing tools for the AI agent."""

from typing import Dict, Any
from langchain.tools import tool
import logging

logger = logging.getLogger(__name__)

@tool
def analyze_user_preferences(preferences: dict) -> dict:
    """Analyze user preferences and create a content strategy.
    
    Args:
        preferences: Dictionary containing user preferences like learn_about, fun_learning, mood, time_budget
    
    Returns:
        Dictionary with content strategy including item types and quantities
    """
    logger.info("[Planner] Analyzing user preferences...")
    logger.info(f"[Planner] Learning interests: {preferences.get('learn_about', '')[:50]}...")
    logger.info(f"[Planner] Fun interests: {preferences.get('fun_learning', '')[:50]}...")
    
    learn_about = preferences.get('learn_about', '').lower()
    fun_learning = preferences.get('fun_learning', '').lower()
    time_budget = preferences.get('time_budget', 'quick')
    
    # Determine how many items to include
    max_items = 4 if time_budget == 'quick' else 6 if time_budget == 'standard' else 8
    
    strategy = {
        'max_items': max_items,
        'include_tech': any(kw in learn_about for kw in ['ai', 'tech', 'startup', 'software', 'innovation']),
        'include_history': any(kw in fun_learning for kw in ['history', 'historical', 'past', 'exploration']),
        'include_quotes': preferences.get('include_quotes', True),
        'include_deep_dive': preferences.get('include_deep_dive', True) and time_budget != 'quick',
        'alternating_pattern': True
    }
    
    logger.info(f"[Planner] Strategy: {max_items} items, alternating serious/fun pattern")
    return strategy

@tool
def process_content_item(item: dict, item_type: str) -> dict:
    """Process a raw content item into a formatted digest item.
    
    Args:
        item: Raw content item from source
        item_type: Type of processing ('serious' or 'fun')
    
    Returns:
        Processed item ready for presentation
    """
    logger.info(f"[Editor] Processing {item_type} item...")
    
    if item_type == 'serious':
        # Process tech/news items
        title = item.get('title', 'Tech Update')
        snippet = item.get('snippet', 'Important development in technology')
        url = item.get('url')
        
        # Format as "Title - Description" for proper parsing
        text = f"{title} - {snippet}"
        
        return {
            'text': text,
            'url': url,
            'kind': 'need',
            'processed': True
        }
    
    else:  # fun content
        if 'text' in item and 'author' in item:
            # Quote format - use quote as title, author as description
            title = f'"{item["text"]}"'
            description = f"- {item['author']}"
            text = f"{title} - {description}"
        else:
            # History format - use title and snippet
            title = item.get('title', 'Historical Event')
            snippet = item.get('snippet', 'Interesting historical fact')
            text = f"{title} - {snippet}"
        
        return {
            'text': text,
            'url': item.get('url'),
            'kind': 'nice', 
            'processed': True
        }