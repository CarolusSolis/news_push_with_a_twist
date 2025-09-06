"""Core AI Agent system for the Agentic Morning Digest using LangGraph."""

import os
import json
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import logging

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# LangGraph imports
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain_core.tools import BaseTool

# Tavily search
from langchain_tavily import TavilySearch

# Pydantic for structured output
from pydantic import BaseModel, Field
from typing import List as TypingList

# Import tools
from .tools import (
    analyze_user_preferences,
    process_content_item, 
    fetch_content_by_type,
    scrape_hacker_news
)

logger = logging.getLogger(__name__)

# Pydantic schemas for structured output
class DigestItem(BaseModel):
    """A single item in a digest section."""
    text: str = Field(description="The main content text of the item")
    url: str = Field(default="", description="Optional URL for the item")

class DigestSection(BaseModel):
    """A section in the morning digest."""
    id: str = Field(description="Unique identifier for the section")
    title: str = Field(description="Display title for the section")
    kind: str = Field(description="Type of content: 'need' for need-to-know or 'nice' for nice-to-know")
    items: TypingList[DigestItem] = Field(description="List of items in this section")

class DigestResponse(BaseModel):
    """The complete digest response from the agent."""
    sections: TypingList[DigestSection] = Field(description="List of digest sections")
    summary: str = Field(description="Brief summary of what was generated")

# Initialize the LLM (will use OpenAI GPT by default)
def get_llm() -> Optional[ChatOpenAI]:
    """Get the configured LLM."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        # For demo purposes, we'll use a mock mode
        return None
    
    return ChatOpenAI(
        model="gpt-4o",
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


def create_real_digest_agent() -> Optional[Any]:
    """Create the real digest agent using LangGraph with live data only."""
    llm = get_llm()
    
    if llm is None:
        agent_logger.log("[Real Agent] No OpenAI API key found - cannot create real agent")
        return None
    
    # Define the tools the real agent can use (LIVE DATA ONLY)
    tools = [
        scrape_hacker_news,  # Hacker News for tech/AI content
        DigestResponse  # Add the structured output schema as a tool
    ]
    
    # Add Tavily search if API key is available
    tavily_api_key = os.getenv('TAVILY_API_KEY')
    if tavily_api_key:
        tavily_search_tool = TavilySearch(
            max_results=5,
            topic="general",
        )
        tools.append(tavily_search_tool)
        agent_logger.log("[Real Agent] Tavily search tool added")
    else:
        agent_logger.log("[Real Agent] No TAVILY_API_KEY found - Tavily search not available")
    
    try:
        # First bind tools, then apply structured output (as per documentation)
        model_with_tools = llm.bind_tools(tools)
        
        system_prompt = """You are the Real Agentic Morning Digest Planner. Your job is to:

1. Use ONLY live data sources - no mock or cached data
2. Fetch real content using available tools:
   - scrape_hacker_news: For tech/AI headlines and news
   - tavily_search: For fun facts, current events, historical content, and additional information
3. Create a personalized digest based on user preferences
4. Mix tech/AI content with fun facts, current events, and historical content
5. Process and format the content for presentation
6. ALWAYS use the DigestResponse tool to return your final structured response

SECTION REQUIREMENTS:
- Generate exactly 10 sections total
- Balance between "need" (need-to-know) and "nice" (nice-to-know) content
- Use alternating pattern: need → nice → need → nice → need → nice → need → nice → need → nice
- Each section should have 2-4 items for comprehensive coverage
- Mix tech/AI news (need) with fun facts, current events, or historical content (nice)

CONTENT STRUCTURE:
- Use article TITLES as your section titles (e.g., "OpenAI Releases GPT-5 with 10x Performance Improvements")
- For each section, create 2-4 items where each item's text is a detailed description/explanation
- Generate sensible, informative descriptions for each headline
- Make descriptions engaging and informative, explaining the significance and implications

IMPORTANT: 
- Only use live data. If a data source fails, log the error but do not fall back to mock data.
- Be comprehensive and create a rich, balanced experience with real, current information.
- Use Tavily search to find interesting fun facts, current events, and historical content to balance the digest.
- ALWAYS call the DigestResponse tool at the end to return your structured digest with exactly 10 sections."""
        
        agent = create_react_agent(
            model=model_with_tools,
            tools=tools,
            prompt=system_prompt
        )
        
        agent_logger.log("[Real Agent] Created LangGraph ReAct agent with live data tools")
        return agent
    except Exception as e:
        agent_logger.log(f"[Real Agent] Error creating agent: {e}")
        return None

def create_mock_digest_agent() -> Any:
    """Create a mock digest agent for fallback scenarios."""
    agent_logger.log("[Mock Agent] Creating mock digest agent for fallback")
    
    # Mock agent is just a placeholder that will use generate_mock_digest
    class MockAgent:
        def __init__(self):
            self.name = "MockAgent"
        
        def invoke(self, input_data):
            # Extract preferences from the input
            messages = input_data.get("messages", [])
            if messages:
                content = messages[0].get("content", "")
                # Parse preferences from the content (simplified)
                preferences = {
                    'learn_about': 'technology',
                    'fun_learning': 'quotes',
                    'time_budget': 'quick'
                }
                return generate_mock_digest(preferences, use_live_data=False)
            return []
    
    return MockAgent()

def generate_digest_with_real_agent(preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate digest using the real AI agent with live data only.
    
    Args:
        preferences: User preferences dictionary
    
    Returns:
        List of processed digest sections from live data
    """
    agent_logger.log("[Real Agent] Starting real agentic digest generation with live data...")
    
    # Try to create the real agent
    agent = create_real_digest_agent()
    
    if agent is None:
        agent_logger.log("[Real Agent] Cannot create real agent - no OpenAI API key")
        return []
    
    try:
        # Use the real agent to generate the digest with live data only
        result = agent.invoke({
            "messages": [{
                "role": "user", 
                "content": f"Create a personalized morning digest using ONLY live data sources. User preferences: {json.dumps(preferences, indent=2)}. Focus on tech/AI content from Hacker News."
            }]
        })
        
        agent_logger.log("[Real Agent] Real agent completed successfully")
        
        # Parse the result from the agent
        agent_logger.log(f"[Real Agent] Agent returned: {type(result)}")

        print("----------------REAL AGENT RESULT----------------")
        print(result)
        print("--------------------------------")
        
        if isinstance(result, dict) and 'messages' in result:
            # LangGraph agents return a dict with 'messages' key
            messages = result['messages']
            if messages and len(messages) > 0:
                # Look for the last message that has tool calls
                for message in reversed(messages):
                    if hasattr(message, 'tool_calls') and message.tool_calls:
                        # Check if it's a DigestResponse tool call
                        for tool_call in message.tool_calls:
                            if tool_call.get('name') == 'DigestResponse':
                                # Extract the structured data
                                args = tool_call.get('args', {})
                                agent_logger.log(f"[Real Agent] Found DigestResponse tool call with {len(args.get('sections', []))} sections")
                                
                                # Convert to our expected format
                                sections = []
                                for section_data in args.get('sections', []):
                                    section_dict = {
                                        'id': section_data.get('id', 'unknown'),
                                        'title': section_data.get('title', 'Untitled'),
                                        'kind': section_data.get('kind', 'need'),
                                        'items': [
                                            {
                                                'text': item.get('text', ''),
                                                'url': item.get('url') if item.get('url') else None
                                            }
                                            for item in section_data.get('items', [])
                                        ]
                                    }
                                    sections.append(section_dict)
                                
                                agent_logger.log(f"[Real Agent] Successfully parsed {len(sections)} sections from structured output")
                                return sections
                
                # No DigestResponse tool call found
                agent_logger.log("[Real Agent] No DigestResponse tool call found in agent response")
                return []
        elif isinstance(result, list):
            # Direct list format
            return result
        else:
            # If agent returns something else, log and return empty
            agent_logger.log(f"[Real Agent] Agent returned unexpected format: {type(result)}")
            return []
        
    except Exception as e:
        agent_logger.log(f"[Real Agent] Error during real agent execution: {e}")
        return []

def generate_digest_with_agent(preferences: Dict[str, Any], use_live_data: bool = False) -> List[Dict[str, Any]]:
    """Generate digest using the appropriate agent system.
    
    Args:
        preferences: User preferences dictionary
        use_live_data: Whether to prefer live data sources (default: False)
    
    Returns:
        List of processed digest sections
    """
    agent_logger.log("[Agent] Starting agentic digest generation...")
    
    # Clear previous logs
    agent_logger.clear_logs()
    agent_logger.log("[Agent] Starting agentic digest generation...")
    
    if use_live_data:
        # Try real agent first
        agent_logger.log("[Agent] Attempting to use real agent with live data...")
        real_result = generate_digest_with_real_agent(preferences)
        
        if real_result:
            agent_logger.log(f"[Agent] Real agent generated {len(real_result)} sections")
            return real_result
        else:
            agent_logger.log("[Agent] Real agent failed, falling back to mock agent")
    
    # Fallback to mock agent
    agent_logger.log("[Agent] Using mock agent for digest generation")
    return generate_mock_digest(preferences, use_live_data=False)

def generate_mock_digest(preferences: Dict[str, Any], use_live_data: bool = False) -> List[Dict[str, Any]]:
    """Generate digest using mock data and rule-based logic."""
    
    # Use the agent tools directly for mock generation
    strategy = analyze_user_preferences.invoke({"preferences": preferences})
    
    items_to_add = []
    
    # Fetch and process content based on strategy
    if strategy['include_tech']:
        tech_content = fetch_content_by_type.invoke({"content_type": 'tech', "use_live_data": use_live_data})
        if tech_content['items']:
            processed = process_content_item.invoke({"item": tech_content['items'][0], "item_type": 'serious'})
            items_to_add.append(processed)
    
    if strategy['include_quotes']:
        quote_content = fetch_content_by_type.invoke({"content_type": 'quotes', "use_live_data": False})  # Always use mock for quotes
        if quote_content['items']:
            processed = process_content_item.invoke({"item": quote_content['items'][0], "item_type": 'fun'})
            items_to_add.append(processed)
    
    if strategy['include_tech'] and len(items_to_add) < strategy['max_items']:
        tech_content = fetch_content_by_type.invoke({"content_type": 'tech', "use_live_data": use_live_data}) 
        if len(tech_content['items']) > 1:
            processed = process_content_item.invoke({"item": tech_content['items'][1], "item_type": 'serious'})
            items_to_add.append(processed)
    
    if strategy['include_history'] and len(items_to_add) < strategy['max_items']:
        history_content = fetch_content_by_type.invoke({"content_type": 'history', "use_live_data": False})  # Always use mock for history
        if history_content['items']:
            processed = process_content_item.invoke({"item": history_content['items'][0], "item_type": 'fun'})
            items_to_add.append(processed)
    
    # Convert to sections format with proper title/description structure
    sections = []
    for i, item in enumerate(items_to_add):
        # Extract title and description from the processed item
        # The item text should be in format "Title - Description" or just "Description"
        item_text = item['text']
        
        # Try to split title and description, but if no dash, use the whole text as description
        if ' - ' in item_text:
            title, description = item_text.split(' - ', 1)
        else:
            # For items without clear title/description split, use a generic title
            title = f"Tech Update {i+1}" if item['kind'] == 'need' else f"Interesting Fact {i+1}"
            description = item_text
        
        sections.append({
            'id': f'agent_item_{i+1}',
            'title': title.strip(),
            'kind': item['kind'],
            'items': [{
                'text': description.strip(),
                'url': item.get('url')
            }]
        })
    
    method = "live + mock data" if use_live_data else "mock data"
    agent_logger.log(f"[Agent] Generated {len(sections)} items using agent tools with {method}")
    return sections

def get_agent_logs() -> List[str]:
    """Get the current agent thinking logs."""
    return agent_logger.get_logs()