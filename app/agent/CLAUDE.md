# app/agent/CLAUDE.md

LangGraph ReAct agent architecture and tool development guide.

## Agent Architecture

The digest generation is powered by a **LangGraph ReAct agent** that autonomously decides which tools to call and in what order.

```
User Preferences → Agent → Tools → Structured Output (DigestResponse)
                      ↓
                 Agent Logger (tracks all decisions)
```

## Core Files

```
agent/
├── CLAUDE.md         # This file - agent architecture
├── __init__.py       # Exports: generate_digest_with_agent, get_agent_logs
├── core.py           # Agent orchestration, system prompt, Pydantic models
├── sources/          # Multi-source news system (see sources/CLAUDE.md)
│   ├── base.py              # NewsSource abstract class
│   ├── manager.py           # NewsSourceManager orchestration
│   ├── hackernews_source.py # HackerNews implementation
│   ├── reddit_source.py     # Reddit (PRAW) implementation
│   ├── wikipedia_source.py  # Wikipedia API implementation
│   └── tavily_source.py     # Tavily search implementation
└── tools/            # Agent tools
    ├── __init__.py
    ├── news_tools.py        # NEW: Multi-source news tools
    ├── hacker_news.py       # HackerNews scraper
    ├── retrieval_tools.py   # Content retrieval
    └── content_tools.py     # LLM-based processing
```

## Agent Flow (core.py)

1. **Initialize LLM**: GPT-4o with `temperature=0` for deterministic output
2. **Load Tools**: Dynamically add available tools (checks for TAVILY_API_KEY)
3. **Create Agent**: `create_react_agent(llm, tools, state_modifier=system_prompt)`
4. **Execute**: Agent autonomously calls tools based on user preferences
5. **Structure Output**: Return `DigestResponse` with validated Pydantic models

## Pydantic Models (core.py)

### DigestItem
```python
class DigestItem(BaseModel):
    text: str = Field(description="Main content text")
    url: str = Field(default="", description="Optional URL")
```

### DigestSection
```python
class DigestSection(BaseModel):
    id: str          # e.g., "quick_hits", "deep_dive"
    title: str       # e.g., "📌 Quick Hits You Should Know"
    kind: str        # "need" or "nice"
    items: List[DigestItem]
```

### DigestResponse
```python
class DigestResponse(BaseModel):
    sections: List[DigestSection]
```

## System Prompt (core.py)

The agent's behavior is defined by a comprehensive system prompt:

1. **Role**: Morning digest creator mixing need-to-know and nice-to-know
2. **Section Types**:
   - `quick_hits`: Tech/AI headlines (need)
   - `deep_dive`: In-depth analysis (need)
   - `did_you_know`: Historical facts (nice)
   - `fun_spark`: Playful what-ifs (nice)
   - `quote`: Inspirational quotes (nice)
3. **Tool Usage Rules**:
   - **NEW Multi-Source System**:
     - Use `fetch_news(category, source, max_items)` as primary news tool
     - Use `get_available_sources()` to check what's available
     - Use `search_news(query, max_items)` for custom searches
   - **Legacy Tools** (still available):
     - Use `scrape_hacker_news` for direct HackerNews access
     - Use `fetch_content_by_type` as fallback
     - Use `process_content_item` for summaries
4. **Content Rules**:
   - Interleave pattern: need → nice → need (3-4 sections max)
   - One-sentence summaries (≤25 words)
   - Include "why it matters" context
   - Playful but tasteful scenarios
5. **Output Format**: Structured `DigestResponse`

## Available Tools

### NEW: Multi-Source News Tools

### 1. fetch_news (news_tools.py) ⭐ PRIMARY TOOL
**Purpose**: Fetch news from multiple sources with automatic fallback
**Input**:
```python
{
    "category": str,      # 'tech', 'science', 'news', 'fun', 'history', 'startup', 'ai'
    "source": str,        # Optional: 'hackernews', 'reddit', 'wikipedia', 'tavily'
    "max_items": int      # Default: 5
}
```
**Output**: Dict with items list, source_used, category, count
**When to use**: Primary tool for fetching ANY news content
**Examples**:
- `fetch_news('tech', max_items=10)` - Auto-select best source
- `fetch_news('science', source='reddit', max_items=5)` - Specific source
- `fetch_news('fun', source='reddit', max_items=3)` - Fun facts from Reddit

**Available Sources**:
- **hackernews**: Tech/AI/startup news (no API key needed)
- **reddit**: Community discussions, diverse topics (no API key needed)
- **wikipedia**: Current events, "On this day" history (no API key needed)
- **tavily**: AI-powered search (requires TAVILY_API_KEY)

### 2. get_available_sources (news_tools.py)
**Purpose**: Check which news sources are currently available
**Input**: `{}`
**Output**: Dict with available_sources list, total_sources count, sources_info
**When to use**: At start of digest generation to know what sources you can use
**Example**:
```python
result = get_available_sources()
# Returns: {'available_sources': ['hackernews', 'reddit', 'wikipedia'], ...}
```

### 3. search_news (news_tools.py)
**Purpose**: Custom search queries using Tavily AI search
**Input**:
```python
{
    "query": str,         # Custom search query
    "max_items": int      # Default: 5
}
```
**Output**: Dict with items list, query, count
**When to use**: For specific, creative topics not covered by categories
**Note**: Requires `TAVILY_API_KEY` environment variable
**Examples**:
- `search_news("quantum computing breakthroughs", max_items=3)`
- `search_news("medieval siege warfare techniques", max_items=2)`
- `search_news("strange animal mating rituals", max_items=2)`

### Legacy Tools (Still Available)

### 4. analyze_user_preferences (content_tools.py)
**Purpose**: Parse user preferences into actionable strategy
**Input**: `{"preferences": {...}}`
**Output**: Strategy dict with max_items, include_tech, include_quotes, etc.
**When to use**: ALWAYS call this first

### 5. scrape_hacker_news (hacker_news.py)
**Purpose**: Direct HackerNews scraping (legacy, use fetch_news instead)
**Input**: `{"max_items": int}`
**Output**: List of HN items with title, url, points, comments
**When to use**: For tech/AI/startup news (prefer fetch_news)

### 6. fetch_content_by_type (retrieval_tools.py)
**Purpose**: Retrieve content from static samples (fallback)
**Input**: `{"content_type": "hacker_news"|"quotes"|"wikipedia"}`
**Output**: Static sample data
**When to use**: Fallback when live data unavailable

### 7. process_content_item (content_tools.py)
**Purpose**: LLM-based content processing and summarization
**Input**: `{"item": {...}, "item_type": "serious"|"fun"}`
**Output**: Processed item with text, url, kind
**When to use**: To transform raw content into digest format

## Adding New Tools

### 1. Create Tool Function

```python
# app/agent/tools/my_tool.py
from langchain_core.tools import tool

@tool
def my_new_tool(param: str) -> dict:
    """Tool description for the agent.

    Args:
        param: Parameter description

    Returns:
        Result dictionary
    """
    # Your implementation
    return {"result": "data"}
```

### 2. Register Tool (core.py)

```python
# In core.py, add to imports
from .tools import my_new_tool

# In generate_digest_with_agent(), add to tools list
tools = [
    analyze_user_preferences,
    scrape_hacker_news,
    fetch_content_by_type,
    process_content_item,
    my_new_tool,  # Add here
]
```

### 3. Update System Prompt

Add tool usage guidelines to the system prompt in `core.py`:
```python
SYSTEM_PROMPT = """
...
Available tools:
- my_new_tool: When to use this tool and what it does
...
"""
```

## Agent Logging

The `AgentLogger` class tracks all agent decisions:

```python
from agent.core import agent_logger

# Log messages
agent_logger.log("[Tool] HackerNews scraping started")
agent_logger.log("[Agent] Preference analysis complete")

# Get logs
logs = agent_logger.get_logs()

# Clear logs
agent_logger.clear_logs()
```

**Log Format**: `[Component] Message`
- `[Agent]`: Agent decisions
- `[Tool]`: Tool execution
- `[Error]`: Error conditions

## Configuration

### LLM Settings (core.py)
```python
llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0,  # Deterministic output
    streaming=False
)
```

### Agent Settings
- **ReAct Pattern**: Reason → Act → Observe loop
- **Max Iterations**: Default (LangGraph manages)
- **State Modifier**: System prompt injection

## Testing

Test agent behavior in `test_real_agent.py`:
```bash
conda activate news_push
python test_real_agent.py
```

Test individual tools:
```bash
cd app
python -c "from agent.tools.hacker_news import scrape_hacker_news; print(scrape_hacker_news.invoke({'max_items': 3}))"
```

## Debugging

### Enable Verbose Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Inspect Agent State
```python
# Agent returns state with messages
result = app.invoke(input_state)
print(result['messages'])
```

### Check Tool Calls
Agent log shows all tool calls:
```
[Real Agent] Starting generation...
[Real Agent] Calling tool: analyze_user_preferences
[Real Agent] Calling tool: scrape_hacker_news
[Real Agent] Digest generation complete
```

## Best Practices

✅ **DO:**
- Write clear tool docstrings (agent reads them)
- Return structured data from tools
- Handle errors gracefully
- Log important decisions
- Use Pydantic for structured output

❌ **DON'T:**
- Make tools too complex (single responsibility)
- Return unstructured text from tools
- Call OpenAI API without error handling
- Forget to update system prompt when adding tools
- Skip tool testing

## Common Issues

### "Agent returns empty sections"
- Check system prompt clarity
- Verify tools return expected format
- Check agent logs for errors

### "Tool not called"
- Update system prompt with usage guidelines
- Check tool docstring is clear
- Verify tool is in tools list

### "Structured output validation error"
- Check Pydantic model matches output
- Verify all required fields present
- Use `.with_structured_output(DigestResponse)` on LLM

## Environment Variables

- `OPENAI_API_KEY`: Required for LLM calls
- `TAVILY_API_KEY`: Optional, enables Tavily search tool

## Performance

- **Cold start**: ~5-10s (LLM initialization)
- **Digest generation**: ~10-20s (depends on tool calls)
- **Fallback mode**: ~1-2s (static data only)

Optimization tips:
- Cache static samples
- Use `temperature=0` for consistency
- Limit tool calls via prompt engineering
