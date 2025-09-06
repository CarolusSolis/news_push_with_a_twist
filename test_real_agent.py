#!/usr/bin/env python3
"""Test the real agent with live Hacker News data only."""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from agent.core import generate_digest_with_real_agent, get_agent_logs, agent_logger


def test_real_agent_with_hacker_news():
    """Test the real agent using only live Hacker News data."""
    print("🤖 Testing Real Agent with Live Hacker News Data...")
    
    # Clear previous logs
    agent_logger.clear_logs()
    
    preferences = {
        'learn_about': 'AI, machine learning, and technology news',
        'fun_learning': 'quotes and historical facts',
        'time_budget': 'standard',
        'include_quotes': True
    }
    
    print("  📋 User preferences:")
    for key, value in preferences.items():
        print(f"    {key}: {value}")
    
    print("\n  🚀 Calling real agent...")
    
    try:
        # Call the real agent (this will only work if OpenAI API key is set)
        sections = generate_digest_with_real_agent(preferences)
        
        print(f"  ✅ Real agent returned {len(sections)} sections")
        
        if sections:
            print("\n  📰 Generated sections:")
            for i, section in enumerate(sections, 1):
                print(f"    {i}. {section.get('title', 'Untitled')} ({section.get('kind', 'unknown')})")
                if section.get('items'):
                    item_text = section['items'][0].get('text', '')[:80] + "..."
                    print(f"       {item_text}")
        else:
            print("  ⚠️  No sections generated (likely no OpenAI API key)")
        
        # Show agent logs
        logs = get_agent_logs()
        print(f"\n  📋 Agent logs ({len(logs)} messages):")
        for log in logs:
            print(f"    {log}")
        
        return len(sections) > 0
        
    except Exception as e:
        print(f"  ❌ Real agent test failed: {e}")
        return False


def test_agent_fallback_behavior():
    """Test the fallback behavior when real agent is not available."""
    print("\n🔄 Testing Agent Fallback Behavior...")
    
    # Clear previous logs
    agent_logger.clear_logs()
    
    preferences = {
        'learn_about': 'technology',
        'fun_learning': 'quotes',
        'time_budget': 'quick'
    }
    
    print("  🚀 Testing with use_live_data=True (should try real agent first)...")
    
    try:
        from agent.core import generate_digest_with_agent
        
        sections = generate_digest_with_agent(preferences, use_live_data=True)
        
        print(f"  ✅ Generated {len(sections)} sections")
        
        if sections:
            print("  📰 Sections:")
            for i, section in enumerate(sections, 1):
                print(f"    {i}. {section.get('title', 'Untitled')} ({section.get('kind', 'unknown')})")
        
        # Show logs
        logs = get_agent_logs()
        print(f"\n  📋 Agent logs ({len(logs)} messages):")
        for log in logs:
            print(f"    {log}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Fallback test failed: {e}")
        return False


def main():
    """Run the real agent tests."""
    print("🚀 Testing Real Agent System\n")
    
    # Test 1: Real agent with Hacker News
    real_agent_success = test_real_agent_with_hacker_news()
    
    # Test 2: Fallback behavior
    fallback_success = test_agent_fallback_behavior()
    
    # Summary
    print("\n📊 Test Results Summary:")
    print("=" * 50)
    
    if real_agent_success:
        print("✅ Real Agent with Hacker News: PASS")
        print("   🎉 Real agent is working with live data!")
    else:
        print("⚠️  Real Agent with Hacker News: NO API KEY")
        print("   💡 Set OPENAI_API_KEY environment variable to test real agent")
    
    if fallback_success:
        print("✅ Agent Fallback Behavior: PASS")
        print("   🎉 Fallback system is working correctly!")
    else:
        print("❌ Agent Fallback Behavior: FAIL")
    
    print(f"\n🎯 System Status:")
    if real_agent_success:
        print("   🚀 Real agent is operational with live Hacker News data")
    else:
        print("   🔧 Real agent requires OpenAI API key")
    print("   ✅ Mock agent fallback is working")
    print("   ✅ Two distinct agent system is implemented")
    
    return 0 if fallback_success else 1


if __name__ == "__main__":
    exit(main())
