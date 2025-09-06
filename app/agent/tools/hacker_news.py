"""Hacker News scraper tool for the AI agent."""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
from langchain.tools import tool
import time
import logging

# Set up logging for debugging
logger = logging.getLogger(__name__)

@tool 
def scrape_hacker_news(max_items: int = 10) -> Dict[str, Any]:
    """Scrape latest headlines from Hacker News front page.
    
    Args:
        max_items: Maximum number of items to scrape (default: 10)
    
    Returns:
        Dictionary with scraped items and metadata
    """
    try:
        logger.info(f"[HN Scraper] Starting to scrape {max_items} items from Hacker News")
        
        # Headers to appear more like a real browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        # Fetch the HN front page
        response = requests.get('https://news.ycombinator.com', headers=headers, timeout=10)
        response.raise_for_status()
        
        logger.info("[HN Scraper] Successfully fetched HN front page")
        
        # Parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        items = []
        
        # Find all story rows (they have class 'athing')
        story_rows = soup.find_all('tr', class_='athing')[:max_items]
        
        for i, story in enumerate(story_rows):
            try:
                # Get the title and link
                title_cell = story.find('span', class_='titleline')
                if not title_cell:
                    continue
                
                title_link = title_cell.find('a')
                if not title_link:
                    continue
                    
                title = title_link.get_text(strip=True)
                url = title_link.get('href', '')
                
                # Handle relative URLs
                if url.startswith('item?id='):
                    url = f'https://news.ycombinator.com/{url}'
                
                # Get the subtext row (next sibling with metadata)
                subtext_row = story.find_next_sibling('tr')
                points = 0
                comments = 0
                author = ""
                
                if subtext_row:
                    subtext = subtext_row.find('td', class_='subtext')
                    if subtext:
                        # Extract points
                        score_span = subtext.find('span', class_='score')
                        if score_span:
                            points_text = score_span.get_text()
                            points = int(points_text.split()[0]) if points_text.split() else 0
                        
                        # Extract author
                        author_link = subtext.find('a', class_='hnuser')
                        if author_link:
                            author = author_link.get_text(strip=True)
                        
                        # Extract comment count
                        comment_links = subtext.find_all('a')
                        for link in comment_links:
                            if 'item?id=' in link.get('href', '') and 'comment' in link.get_text().lower():
                                comment_text = link.get_text()
                                try:
                                    comments = int(comment_text.split()[0]) if comment_text.split() and comment_text.split()[0].isdigit() else 0
                                except:
                                    comments = 0
                                break
                
                # Create a snippet from the title (since HN doesn't have descriptions)
                snippet = f"Posted by {author}" if author else "Hacker News discussion"
                if points > 0:
                    snippet += f" • {points} points"
                if comments > 0:
                    snippet += f" • {comments} comments"
                
                item = {
                    'title': title,
                    'url': url,
                    'snippet': snippet,
                    'points': points,
                    'comments': comments,
                    'author': author,
                    'source': 'hacker_news',
                    'rank': i + 1
                }
                
                items.append(item)
                logger.debug(f"[HN Scraper] Scraped item {i+1}: {title[:50]}...")
                
            except Exception as e:
                logger.warning(f"[HN Scraper] Error parsing story {i+1}: {e}")
                continue
        
        result = {
            'items': items,
            'source': 'hacker_news',
            'scraped_at': time.time(),
            'total_items': len(items)
        }
        
        logger.info(f"[HN Scraper] Successfully scraped {len(items)} items")
        return result
        
    except requests.RequestException as e:
        logger.error(f"[HN Scraper] Network error: {e}")
        return {
            'items': [],
            'source': 'hacker_news', 
            'error': f'Network error: {str(e)}',
            'scraped_at': time.time(),
            'total_items': 0
        }
    except Exception as e:
        logger.error(f"[HN Scraper] Unexpected error: {e}")
        return {
            'items': [],
            'source': 'hacker_news',
            'error': f'Scraping error: {str(e)}',
            'scraped_at': time.time(), 
            'total_items': 0
        }

def get_top_stories(limit: int = 5) -> List[Dict[str, Any]]:
    """Get top stories from Hacker News API (alternative method).
    
    Args:
        limit: Number of top stories to fetch
        
    Returns:
        List of story dictionaries
    """
    try:
        # Get top story IDs
        response = requests.get('https://hacker-news.firebaseio.com/v0/topstories.json', timeout=10)
        response.raise_for_status()
        story_ids = response.json()[:limit]
        
        stories = []
        for story_id in story_ids:
            try:
                # Get individual story details
                story_response = requests.get(f'https://hacker-news.firebaseio.com/v0/item/{story_id}.json', timeout=5)
                story_response.raise_for_status()
                story_data = story_response.json()
                
                if story_data.get('type') == 'story':
                    story = {
                        'title': story_data.get('title', ''),
                        'url': story_data.get('url', f'https://news.ycombinator.com/item?id={story_id}'),
                        'snippet': f"Posted by {story_data.get('by', 'unknown')} • {story_data.get('score', 0)} points • {story_data.get('descendants', 0)} comments",
                        'points': story_data.get('score', 0),
                        'comments': story_data.get('descendants', 0),
                        'author': story_data.get('by', ''),
                        'source': 'hacker_news',
                        'id': story_id
                    }
                    stories.append(story)
                    
            except Exception as e:
                logger.warning(f"Error fetching story {story_id}: {e}")
                continue
                
        logger.info(f"[HN API] Fetched {len(stories)} stories via API")
        return stories
        
    except Exception as e:
        logger.error(f"[HN API] Error fetching top stories: {e}")
        return []

def get_hacker_news_content(method: str = 'scrape', max_items: int = 5) -> Dict[str, Any]:
    """Get Hacker News content using specified method.
    
    Args:
        method: 'scrape' for web scraping or 'api' for HN API
        max_items: Maximum number of items to fetch
        
    Returns:
        Dictionary with items and metadata
    """
    if method == 'api':
        items = get_top_stories(max_items)
        return {
            'items': items,
            'source': 'hacker_news',
            'method': 'api',
            'total_items': len(items)
        }
    else:
        return scrape_hacker_news.func(max_items)