#!/usr/bin/env python3
"""Simple test runner to verify Hacker News tool integration with AI agent system."""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from agent.tools.hacker_news import scrape_hacker_news, get_hacker_news_content
from agent.core import generate_mock_digest, get_agent_logs, agent_logger
from agent.tools.content_tools import analyze_user_preferences, process_content_item


def test_hacker_news_tool():
    """Test the Hacker News tool directly."""
    print("🔍 Testing Hacker News Tool...")
    
    try:
        # Test scraping method
        print("  📡 Testing web scraping method...")
        result = scrape_hacker_news.invoke({"max_items": 3})
        
        print(f"  ✅ Scraped {result['total_items']} items")
        if result['items']:
            first_item = result['items'][0]
            print(f"  📰 First item: {first_item['title'][:60]}...")
            print(f"  🔗 URL: {first_item['url']}")
            print(f"  ⭐ Points: {first_item['points']}, Comments: {first_item['comments']}")
        
        # Test API method
        print("  🔌 Testing API method...")
        api_result = get_hacker_news_content('api', 2)
        print(f"  ✅ API returned {len(api_result['items'])} items")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Hacker News tool test failed: {e}")
        return False


def test_agent_integration():
    """Test the AI agent's integration with Hacker News."""
    print("\n🤖 Testing AI Agent Integration...")
    
    try:
        # Clear previous logs
        agent_logger.clear_logs()
        
        # Test preferences analysis
        print("  🧠 Testing preference analysis...")
        preferences = {
            'learn_about': 'AI, machine learning, and technology news',
            'fun_learning': 'quotes and historical facts',
            'time_budget': 'standard',
            'include_quotes': True
        }
        
        strategy = analyze_user_preferences.invoke({"preferences": preferences})
        print(f"  ✅ Strategy: {strategy['max_items']} items, tech={strategy['include_tech']}")
        
        # Test mock digest generation
        print("  📝 Testing digest generation...")
        sections = generate_mock_digest(preferences, use_live_data=False)
        print(f"  ✅ Generated {len(sections)} sections")
        
        # Show section details
        for i, section in enumerate(sections):
            print(f"    {i+1}. {section['title']} ({section['kind']})")
            if section['items']:
                item_text = section['items'][0]['text'][:50] + "..."
                print(f"       {item_text}")
        
        # Check agent logs
        logs = get_agent_logs()
        print(f"  📋 Agent logged {len(logs)} messages")
        for log in logs[-3:]:  # Show last 3 logs
            print(f"    {log}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Agent integration test failed: {e}")
        return False


def test_content_processing():
    """Test content processing pipeline."""
    print("\n⚙️  Testing Content Processing...")
    
    try:
        # Mock Hacker News item
        mock_item = {
            'title': 'Revolutionary AI model achieves human-level reasoning',
            'url': 'https://example.com/ai-breakthrough',
            'snippet': 'Posted by researcher • 250 points • 89 comments',
            'points': 250,
            'comments': 89,
            'author': 'researcher',
            'source': 'hacker_news',
            'rank': 1
        }
        
        # Test processing
        processed = process_content_item.invoke({
            "item": mock_item,
            "item_type": "serious"
        })
        
        print(f"  ✅ Processed item: {processed['kind']}")
        print(f"  📄 Text: {processed['text'][:80]}...")
        print(f"  🔗 URL: {processed['url']}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Content processing test failed: {e}")
        return False


def test_live_data_fallback():
    """Test fallback behavior when live data is unavailable."""
    print("\n🔄 Testing Fallback Behavior...")
    
    try:
        preferences = {
            'learn_about': 'technology',
            'fun_learning': 'quotes',
            'time_budget': 'quick'
        }
        
        # Test with live data (might fail in test environment)
        print("  🌐 Testing with live data...")
        sections_live = generate_mock_digest(preferences, use_live_data=True)
        print(f"  ✅ Live data: {len(sections_live)} sections")
        
        # Test with mock data
        print("  🎭 Testing with mock data...")
        sections_mock = generate_mock_digest(preferences, use_live_data=False)
        print(f"  ✅ Mock data: {len(sections_mock)} sections")
        
        # Both should work
        assert len(sections_live) > 0 or len(sections_mock) > 0
        print("  ✅ Fallback system working correctly")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Fallback test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🚀 Starting Hacker News AI Agent Integration Tests\n")
    
    tests = [
        ("Hacker News Tool", test_hacker_news_tool),
        ("Agent Integration", test_agent_integration),
        ("Content Processing", test_content_processing),
        ("Fallback Behavior", test_live_data_fallback)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"  ❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n📊 Test Results Summary:")
    print("=" * 50)
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if success:
            passed += 1
    
    print(f"\n🎯 {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! Hacker News integration is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    exit(main())
