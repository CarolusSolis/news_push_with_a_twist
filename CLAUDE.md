# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## IMPORTANT: Maintaining Context Files

**This project uses hierarchical CLAUDE.md files for different modules:**

- `/CLAUDE.md` (this file): High-level architecture, mission, environment setup
- `/tests/CLAUDE.md`: Testing philosophy, running tests, test structure
- `/app/agent/CLAUDE.md`: Agent architecture, tools, system prompts
- `/app/agent/sources/CLAUDE.md`: Multi-source news system, source development
- `/app/voiceover/CLAUDE.md`: Voiceover generation, TTS, script logic

**When making changes:**
1. Update the relevant CLAUDE.md file (not just code)
2. Keep hierarchy clear - no duplication between levels
3. Main CLAUDE.md = high-level, subdirectory CLAUDE.md = implementation details
4. If architecture changes, update MULTIPLE CLAUDE.md files as needed
5. Keep context files concise, relevant, and organized

## 0) Identity & Mission
You are the **Agentic Morning Digest** dev assistant. Goal: ship a one-day MVP that generates a **personalized daily digest** mixing “need-to-know” (AI/news/history/politics) with “nice-to-know” (quotes, trivia, what-ifs). Output lives in a **Streamlit** app with a visible “Agent Thinking Log.”

**Non-goals:** building auth, multi-user infra, production DB, fancy styling, or real-time crawling beyond the three sources.

## 1) Commands

### Development
- **Environment:** Use the `news_push` conda environment: `conda activate news_push`
- **Install dependencies:** `pip install -r requirements.txt`
- **Run the application:** `cd app && streamlit run app.py`
- **Run tests:** `pytest` (see `/tests/CLAUDE.md` for details)
- **Environment setup:** Ensure `OPENAI_API_KEY` and `TAVILY_API_KEY` are set in `.env` file

### Demo Constraints (3-minute screen recording)
- Must show: pick preferences → show "Agent plan" → interleaved sections (need/nice) → regenerate.
- Fast and reliable: prefer **cached/mocked** data if scraping/LLM is slow.

## 2) Tech Stack (MVP)
- **Frontend:** Streamlit
- **LLM:** GPT (for summaries/reframes); keep calls minimal and deterministic (temperature low)
- **Agent Framework:** LangGraph ReAct agent for AI agent orchestration (see tutorials in `/tutorials/langgraph-docs/`)
- **Search:** Tavily API for intelligent web search
- **Retrieval:** BeautifulSoup + requests for web scraping
- **Storage:** In-memory / JSON file for prefs + cached content
- **Voiceover:** OpenAI TTS for audio generation

### LangGraph Resources
Reference documentation in `/tutorials/langgraph-docs/`:
- **Agent Overview:** `/agents/overview.md` - Core agent concepts and patterns
- **Prebuilt Components:** `/agents/prebuilt.md` - Ready-to-use agent building blocks  
- **Multi-Agent Systems:** `/agents/multi-agent.md` - Coordinating multiple agents
- **Memory Integration:** How-to guides for session and persistent memory
- **Human-in-the-loop:** Patterns for interactive agent workflows

## 3) Sources (Multi-Source System)

The application uses a **pluggable multi-source architecture** with automatic fallback:

### Primary Sources
- **HackerNews** → Tech/AI/startup news (BeautifulSoup scraper, no API key needed)
- **Reddit** → Community discussions via PRAW (tech, science, fun categories, no API key needed)
- **Wikipedia** → Current events + "On this day" historical facts (Wikimedia API, no API key needed)
- **Tavily** → AI-powered intelligent search (requires TAVILY_API_KEY)

### Fallback Strategy
- Sources are tried in priority order (configurable in `app/config/sources.json`)
- Automatic fallback to next source if one fails
- Static samples in `data/static_samples.json` as final fallback

### Source Manager
- Located in `app/agent/sources/manager.py`
- Auto-discovers available sources (checks API keys, dependencies)
- Provides unified `NewsItem` format across all sources
- See `/app/agent/sources/CLAUDE.md` for source development guide

## 4) Architecture & Code Structure

### Core Architecture
The application uses a **LangGraph ReAct agent** architecture:
1. **Preferences Collection** → **Agent Planning & Tool Execution** → **Content Retrieval** → **Structured Output** → **Presentation**
2. **Agent Thinking Log** tracks all tool calls and decisions
3. **Fallback Strategy** ensures resilience: Static Samples available in `data/static_samples.json`

### Module Responsibilities
- **app/app.py**: Streamlit UI, session state management, voiceover integration
- **app/agent/core.py**: LangGraph ReAct agent orchestration, tool coordination, structured output generation
- **app/agent/sources/**: Multi-source news system (see `/app/agent/sources/CLAUDE.md`)
  - **base.py**: `NewsSource` abstract class + `NewsItem` dataclass
  - **manager.py**: `NewsSourceManager` orchestration with automatic fallback
  - **hackernews_source.py**: HackerNews implementation
  - **reddit_source.py**: Reddit (PRAW) implementation
  - **wikipedia_source.py**: Wikipedia API implementation
  - **tavily_source.py**: Tavily search implementation
- **app/agent/tools/**: Agent tools (retrieval, content processing, news fetching)
  - **news_tools.py**: Multi-source news tools (`fetch_news`, `search_news`, `get_available_sources`)
  - **hacker_news.py**: HackerNews scraper with BeautifulSoup
  - **retrieval_tools.py**: `fetch_content_by_type` tool for content retrieval
  - **content_tools.py**: `process_content_item` for LLM-based content processing
- **app/config/sources.json**: Multi-source configuration (priority, settings)
- **app/presenter.py**: Pure rendering helpers (no business logic)
- **app/prefs.py**: User preference collection UI and state management
- **app/voiceover/**: Audio digest generation
  - **script_generator.py**: Generate TTS-friendly scripts from digest content
  - **tts_engine.py**: OpenAI TTS integration for audio generation
- **app/data/static_samples.json**: Fallback content for demo resilience

### Data Flow
```
User Prefs → LangGraph Agent (with tools) → Structured DigestResponse → Presenter.render()
                    ↓                                      ↓
              Agent Log (tool calls)              Optional: Voiceover generation
```

## 5) Section Contract (Pydantic Models)
Sections are defined using Pydantic models in `app/agent/core.py`:

**DigestItem:**
```python
{
  "text": str,        # Main content text
  "url": str          # Optional URL (default: "")
}
```

**DigestSection:**
```python
{
  "id": str,          # e.g., "quick_hits", "deep_dive", "did_you_know", "fun_spark", "quote"
  "title": str,       # e.g., "📌 Quick Hits You Should Know"
  "kind": str,        # "need" or "nice"
  "items": List[DigestItem]
}
```

**DigestResponse:**
```python
{
  "sections": List[DigestSection]
}
```

## 6) Agentic Workflow (High-Level)
1. **Collect prefs** (topics, mood, time budget) in sidebar via `prefs.py`
2. **LangGraph Agent Execution** (see `/app/agent/CLAUDE.md` for details)
   - Agent autonomously decides which tools to call and in what order
   - Agent constructs sections following pattern: **need → nice → need** (max 3–4 sections)
   - All tool calls logged to "Agent Thinking Log"
3. **Structured Output Generation**
   - Agent returns `DigestResponse` with Pydantic-validated sections
4. **Presenter.render(sections)**
   - Pure formatting; badges for need/nice; collapsible expanders
5. **Optional Voiceover Generation** (see `/app/voiceover/CLAUDE.md` for details)
   - Generate TTS-friendly script from digest content
   - Convert to audio using OpenAI TTS
6. **Observability**
   - Agent tool calls automatically logged

## 7) Coding Standards & Safety
- Python 3.11+, type hints, small pure functions, docstrings, `black` format
- **No secrets in code**. Store `OPENAI_API_KEY` and `TAVILY_API_KEY` in `.env` file
- Load environment variables using `python-dotenv`
- Use `@st.cache_data(ttl=600)` for network calls
- LLM: GPT-4o (`gpt-4o`) with `temperature=0` for deterministic output
- Structured output using Pydantic models and `.with_structured_output()`

## 8) Agent System & Testing

### Agent System
The LangGraph ReAct agent autonomously orchestrates digest generation. See `/app/agent/CLAUDE.md` for:
- System prompt structure
- Available tools and when to use them
- Adding new tools
- Agent debugging

### Testing
Backend and frontend are fully tested with pytest. See `/tests/CLAUDE.md` for:
- Running tests
- Writing new tests
- Coverage reporting
- Testing best practices

## 9) Implementation Status
**✅ Completed:**
1. **Streamlit UI**: Clean separation between UI (`app.py`) and business logic (`services.py`)
2. **Backend Services**: `DigestService` and `VoiceoverService` for testable business logic
3. **LangGraph Agent**: ReAct agent with autonomous tool orchestration (see `/app/agent/CLAUDE.md`)
4. **Multi-Source News System**: Pluggable architecture with 4 sources (see `/app/agent/sources/CLAUDE.md`)
   - HackerNews, Reddit, Wikipedia, Tavily
   - Automatic fallback and priority-based source selection
   - Unified NewsItem format across all sources
5. **Agent Tools**: Multi-source fetching, HackerNews scraping, Tavily search, content processing
6. **Voiceover System**: TTS script generation + OpenAI audio (see `/app/voiceover/CLAUDE.md`)
7. **Testing Suite**: 57+ unit and integration tests with pytest (see `/tests/CLAUDE.md`)
8. **Structured Output**: Pydantic models with automatic validation

**🔄 Current Features:**
- Personalized digest generation based on user preferences
- Autonomous agent decision-making via LangGraph
- **Multi-source news aggregation** (HackerNews, Reddit, Wikipedia, Tavily)
- **Automatic fallback** when sources are unavailable
- Real-time content scraping and AI-powered search
- Audio digest generation with voiceover
- Agent thinking log for transparency
- Comprehensive test coverage (90%+ on sources)

## 10) Failure & Fallback Policy
The application implements graceful degradation:

1. **Content Retrieval Fallback**:
   - Primary: Live scraping (HackerNews) or search (Tavily)
   - Secondary: Static samples from `data/static_samples.json`
   - Agent logs the fallback reason

2. **Agent Error Handling**:
   - Try-except blocks around agent execution
   - Status messages displayed to user
   - Errors logged to Agent Thinking Log

3. **API Key Validation**:
   - Tavily search only added if `TAVILY_API_KEY` is available
   - Agent works with or without Tavily (graceful degradation)

4. **UI Resilience**:
   - Keep UI responsive; never crash app
   - Clear error messages when issues occur
   - Regenerate button always available
