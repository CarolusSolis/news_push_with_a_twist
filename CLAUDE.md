# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 0) Identity & Mission
You are the **Agentic Morning Digest** dev assistant. Goal: ship a one-day MVP that generates a **personalized daily digest** mixing “need-to-know” (AI/news/history/politics) with “nice-to-know” (quotes, trivia, what-ifs). Output lives in a **Streamlit** app with a visible “Agent Thinking Log.”

**Non-goals:** building auth, multi-user infra, production DB, fancy styling, or real-time crawling beyond the three sources.

## 1) Commands

### Development
- **Environment:** Use the `news_push` conda/virtual environment
- **Install dependencies:** `pip install -r requirements.txt`
- **Run the application:** `cd app && streamlit run app.py`
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

## 3) Sources
- **Hacker News** (front page) → "Quick Hits" tech/AI headlines (via custom scraper)
- **Tavily Search** → Intelligent web search for specific, interesting content
- **Static samples** → Fallback content in `data/static_samples.json`

## 4) Architecture & Code Structure

### Core Architecture
The application uses a **LangGraph ReAct agent** architecture:
1. **Preferences Collection** → **Agent Planning & Tool Execution** → **Content Retrieval** → **Structured Output** → **Presentation**
2. **Agent Thinking Log** tracks all tool calls and decisions
3. **Fallback Strategy** ensures resilience: Static Samples available in `data/static_samples.json`

### Module Responsibilities
- **app/app.py**: Streamlit UI, session state management, voiceover integration
- **app/agent/core.py**: LangGraph ReAct agent orchestration, tool coordination, structured output generation
- **app/agent/tools/**: Agent tools (retrieval, content processing, HackerNews scraping, user preference analysis)
  - **hacker_news.py**: HackerNews scraper with BeautifulSoup
  - **retrieval_tools.py**: `fetch_content_by_type` tool for content retrieval
  - **content_tools.py**: `process_content_item` for LLM-based content processing
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

## 6) Agentic Workflow (Current Implementation)
1. **Collect prefs** (topics, mood, time budget) in sidebar via `prefs.py`
2. **LangGraph Agent Execution** (`agent/core.py`)
   - Agent receives user preferences via `analyze_user_preferences` tool
   - Agent autonomously decides which tools to call and in what order
   - Available tools:
     - `analyze_user_preferences`: Parse user preferences
     - `fetch_content_by_type`: Retrieve content from HackerNews or static samples
     - `process_content_item`: LLM-based content processing and summarization
     - `scrape_hacker_news`: Direct HackerNews scraping
     - `tavily_search`: Web search for specific, interesting content (if TAVILY_API_KEY available)
   - Agent constructs sections following pattern: **need → nice → need** (max 3–4 sections)
   - All tool calls logged to "Agent Thinking Log"
3. **Structured Output Generation**
   - Agent returns `DigestResponse` with properly structured sections
   - Automatic validation via Pydantic models
4. **Presenter.render(sections)**
   - Pure formatting; badges for need/nice; collapsible expanders
5. **Optional Voiceover Generation**
   - Generate TTS-friendly script from digest content
   - Convert to audio using OpenAI TTS
6. **Observability**
   - Agent tool calls automatically logged
   - Custom logging via `AgentLogger` class in `core.py`

## 7) Coding Standards & Safety
- Python 3.11+, type hints, small pure functions, docstrings, `black` format
- **No secrets in code**. Store `OPENAI_API_KEY` and `TAVILY_API_KEY` in `.env` file
- Load environment variables using `python-dotenv`
- Use `@st.cache_data(ttl=600)` for network calls
- LLM: GPT-4o (`gpt-4o`) with `temperature=0` for deterministic output
- Structured output using Pydantic models and `.with_structured_output()`

## 8) Agent System Prompt
The LangGraph agent uses a comprehensive system prompt (defined in `agent/core.py`) that includes:

1. **Role & Purpose**: Morning digest creator mixing need-to-know and nice-to-know content
2. **Section Types**: Definitions for `quick_hits`, `deep_dive`, `did_you_know`, `fun_spark`, `quote`
3. **Tool Usage Guidelines**:
   - `analyze_user_preferences`: Always call first to understand user preferences
   - `scrape_hacker_news`: For tech/AI/startup news
   - `tavily_search`: For specific, interesting content (NOT general encyclopedia entries)
   - `fetch_content_by_type`: Fallback for static samples
   - `process_content_item`: For summaries and transformations
4. **Content Rules**:
   - Interleave pattern: need → nice → need (3-4 sections max)
   - One-sentence summaries (≤25 words)
   - Include "why it matters" context
   - Playful but tasteful "what-if" scenarios
5. **Output Format**: Structured `DigestResponse` with proper section structure

## 9) Implementation Status
**✅ Completed:**
1. **Streamlit UI**: `app.py` with sidebar prefs, Generate button, Agent Log display
2. **Static Fallback Data**: `data/static_samples.json` with sample content
3. **LangGraph Agent**: ReAct agent with tool orchestration in `agent/core.py`
4. **Agent Tools**:
   - User preference analysis
   - HackerNews scraper
   - Content processing (LLM-based)
   - Tavily search integration
   - Fallback content retrieval
5. **Presentation Layer**: `presenter.py` with markdown cards and collapsible expanders
6. **Voiceover System**: Script generation + OpenAI TTS integration
7. **Structured Output**: Pydantic models with automatic validation

**🔄 Current Features:**
- Personalized digest generation based on user preferences
- Autonomous agent decision-making via LangGraph
- Real-time HackerNews scraping
- Intelligent web search via Tavily
- Audio digest generation with voiceover
- Agent thinking log for transparency

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
