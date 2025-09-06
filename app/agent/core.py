"""Core AI Agent system for the Agentic Morning Digest using LangGraph."""

import os
import json
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging

# LangGraph imports
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI

# Import tools
from .tools import (
    analyze_user_preferences,
    process_content_item, 
    fetch_content_by_type,
    scrape_hacker_news
)

logger = logging.getLogger(__name__)

# Initialize the LLM (will use OpenAI GPT by default)
def get_llm() -> ChatOpenAI:
    """Get the configured LLM."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        # For demo purposes, we'll use a mock mode
        return None
    
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.2,
        api_key=api_key
    )

class AgentLogger:
    """Helper class to log agent decisions."""
    
    def __init__(self):
        self.logs = []
    
    def log(self, message: str):
        """Add a message to the agent log."""
        self.logs.append(message)
        logger.info(f"[AGENT] {message}")
    
    def get_logs(self) -> List[str]:
        """Get all logged messages."""
        return self.logs.copy()
    
    def clear_logs(self):
        """Clear all logged messages."""
        self.logs.clear()

# Global logger instance
agent_logger = AgentLogger()

def create_digest_agent() -> Optional[Any]:
    """Create the main digest planning agent using LangGraph."""
    llm = get_llm()
    
    if llm is None:
        agent_logger.log("[Agent] No OpenAI API key found - running in mock mode")
        return None
    
    # Define the tools the agent can use
    tools = [
        analyze_user_preferences,
        fetch_content_by_type, 
        process_content_item,
        scrape_hacker_news
    ]
    
    # Create the agent with a system prompt
    system_prompt = """You are the Agentic Morning Digest Planner. Your job is to:

1. Analyze user preferences to understand what they want to learn about
2. Create a content strategy that alternates between serious (need-to-know) and fun (nice-to-know) items
3. Fetch relevant content from available sources
4. Process content items for presentation

Always follow the alternating pattern: serious → fun → serious → fun.
Be concise and focused on creating a personalized experience.
Log your reasoning as you work through each step."""
    
    try:
        agent = create_react_agent(
            model=llm,
            tools=tools,
            prompt=system_prompt
        )
        
        agent_logger.log("[Agent] Created LangGraph ReAct agent with content planning tools")
        return agent
    except Exception as e:
        agent_logger.log(f"[Agent] Error creating agent: {e}")
        return None

def generate_digest_with_agent(preferences: Dict[str, Any], use_live_data: bool = False) -> List[Dict[str, Any]]:
    """Generate digest using the AI agent system.
    
    Args:
        preferences: User preferences dictionary
        use_live_data: Whether to use live data sources (default: False)
    
    Returns:
        List of processed digest sections
    """
    agent_logger.log("[Agent] Starting agentic digest generation...")
    
    # Clear previous logs
    agent_logger.clear_logs()
    agent_logger.log("[Agent] Starting agentic digest generation...")
    
    # Try to create the agent
    agent = create_digest_agent()
    
    if agent is None:
        # Fallback to mock generation if no agent available
        agent_logger.log("[Agent] Falling back to mock generation (no OpenAI API key)")
        return generate_mock_digest(preferences, use_live_data)
    
    try:
        # Use the agent to generate the digest
        result = agent.invoke({
            "messages": [{
                "role": "user", 
                "content": f"Create a personalized morning digest based on these preferences: {json.dumps(preferences, indent=2)}. Use live_data={use_live_data} for content fetching."
            }]
        })
        
        # Extract the final content from agent response
        # This would need to be parsed from the agent's final response
        agent_logger.log("[Agent] Agent completed successfully")
        
        # For now, return mock data while we build the full integration
        return generate_mock_digest(preferences, use_live_data)
        
    except Exception as e:
        agent_logger.log(f"[Agent] Error during agent execution: {e}")
        agent_logger.log("[Agent] Falling back to mock generation")
        return generate_mock_digest(preferences, use_live_data)

def generate_mock_digest(preferences: Dict[str, Any], use_live_data: bool = False) -> List[Dict[str, Any]]:
    """Generate digest using mock data and rule-based logic."""
    
    # Use the agent tools directly for mock generation
    strategy = analyze_user_preferences.func(preferences)
    
    items_to_add = []
    
    # Fetch and process content based on strategy
    if strategy['include_tech']:
        tech_content = fetch_content_by_type.func('tech', use_live_data)
        if tech_content['items']:
            processed = process_content_item.func(tech_content['items'][0], 'serious')
            items_to_add.append(processed)
    
    if strategy['include_quotes']:
        quote_content = fetch_content_by_type.func('quotes', False)  # Always use mock for quotes
        if quote_content['items']:
            processed = process_content_item.func(quote_content['items'][0], 'fun')
            items_to_add.append(processed)
    
    if strategy['include_tech'] and len(items_to_add) < strategy['max_items']:
        tech_content = fetch_content_by_type.func('tech', use_live_data) 
        if len(tech_content['items']) > 1:
            processed = process_content_item.func(tech_content['items'][1], 'serious')
            items_to_add.append(processed)
    
    if strategy['include_history'] and len(items_to_add) < strategy['max_items']:
        history_content = fetch_content_by_type.func('history', False)  # Always use mock for history
        if history_content['items']:
            processed = process_content_item.func(history_content['items'][0], 'fun')
            items_to_add.append(processed)
    
    # Convert to sections format
    sections = []
    for i, item in enumerate(items_to_add):
        sections.append({
            'id': f'agent_item_{i+1}',
            'title': f'Agent Item {i+1}',
            'kind': item['kind'],
            'items': [{
                'text': item['text'],
                'url': item.get('url')
            }]
        })
    
    method = "live + mock data" if use_live_data else "mock data"
    agent_logger.log(f"[Agent] Generated {len(sections)} items using agent tools with {method}")
    return sections

def get_agent_logs() -> List[str]:
    """Get the current agent thinking logs."""
    return agent_logger.get_logs()