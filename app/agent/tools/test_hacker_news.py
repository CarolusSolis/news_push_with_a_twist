#!/usr/bin/env python3
"""Simple test for Hacker News scraper - clearly display what's being scraped."""

import sys
import os
from pathlib import Path

# Add parent directories to path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir.parent.parent))

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # Manual .env loading
    env_path = current_dir.parent.parent.parent / '.env'
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value

from hacker_news import scrape_hacker_news, get_hacker_news_content

def test_scraper():
    """Test the Hacker News scraper and display results."""
    print("🚀 Testing Hacker News Scraper")
    print("=" * 60)
    
    try:
        # Test scraping 10 items
        print("📡 Scraping Hacker News front page...")
        result = scrape_hacker_news.func(10)
        
        if result.get('error'):
            print(f"❌ Error: {result['error']}")
            return
        
        items = result.get('items', [])
        total = result.get('total_items', 0)
        
        print(f"✅ Successfully scraped {total} items from Hacker News")
        print("-" * 60)
        
        # Display each item clearly
        for i, item in enumerate(items, 1):
            title = item.get('title', 'No title')
            url = item.get('url', 'No URL')
            points = item.get('points', 0)
            comments = item.get('comments', 0)
            author = item.get('author', 'Unknown')
            rank = item.get('rank', i)
            
            print(f"#{rank:2d} | {title}")
            print(f"     📊 {points:3d} points • 💬 {comments:3d} comments • 👤 {author}")
            print(f"     🔗 {url}")
            print()
        
        print("-" * 60)
        print(f"📈 Summary: {len(items)} items scraped successfully")
        
        # Test the unified function
        print("\n🔄 Testing unified get_hacker_news_content function...")
        unified_result = get_hacker_news_content('scrape', 5)
        unified_items = unified_result.get('items', [])
        print(f"✅ Unified function returned {len(unified_items)} items")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

def test_api_method():
    """Test the HN API method."""
    print("\n🌐 Testing Hacker News API method...")
    
    try:
        result = get_hacker_news_content('api', 5)
        items = result.get('items', [])
        
        if items:
            print(f"✅ API method returned {len(items)} items")
            for i, item in enumerate(items[:3], 1):
                title = item.get('title', '')[:60]
                points = item.get('points', 0)
                print(f"  {i}. {title}... ({points} points)")
        else:
            print("⚠️  API method returned no items (may be rate limited)")
            
    except Exception as e:
        print(f"❌ API test failed: {e}")

if __name__ == "__main__":
    test_scraper()
    test_api_method()
    
    print("\n🎉 Hacker News scraper test completed!")
    print("\nYou can now use this tool in the agent system to get live tech news!")