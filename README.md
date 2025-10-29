# Agentic Morning Digest

> **Your daily dose of wisdom—personalized, intelligent, enriching.**

Learn what you need to know. Discover what you love to learn. Start every day smarter.

## Mission

In a world drowning in content, we curate what matters to *you*. The Agentic Morning Digest uses AI to blend **need-to-know** insights (tech, news, history) with **nice-to-know** gems (quotes, trivia, what-ifs)—delivered in a personalized daily digest that advances your personal enrichment.

No endless scrolling. No algorithm traps. Just signal, served fresh.

## What It Does

1. **You set preferences**: Topics, mood, time budget
2. **AI agent orchestrates**: Autonomously fetches, filters, and curates content
3. **You get your digest**: Interleaved sections of substance and spark
4. **Optional voiceover**: Listen to your digest on the go

## Features

- 🤖 **Autonomous AI Agent**: LangGraph-powered ReAct agent makes smart decisions about what to fetch
- 🌐 **Multi-Source News Aggregation**: Fetches from 4+ sources with automatic fallback
  - **HackerNews**: Tech/AI/startup news
  - **Reddit**: Community discussions (tech, science, fun)
  - **Wikipedia**: Current events + "On this day" historical facts
  - **Tavily**: AI-powered intelligent search
- 🔄 **Smart Fallback**: Automatic source prioritization and fallback when sources fail
- 🎯 **Personalized**: Your interests, your pace, your style
- 🔊 **Audio Digest**: TTS voiceover for hands-free learning
- 🪵 **Agent Transparency**: See exactly what the agent is thinking and doing
- ⚡ **Fast & Reliable**: Redundant sources ensure content is always available

## Quick Start

```bash
# 1. Set up environment
conda activate news_push
pip install -r requirements.txt

# 2. Configure API keys (see API_KEYS.md for details)
cp .env.example .env
# Edit .env and add your keys:
#   - OPENAI_API_KEY (required)
#   - TAVILY_API_KEY (optional but recommended)

# 3. Run the app
cd app && streamlit run app.py
```

**API Keys Required:**
- ✅ **OPENAI_API_KEY** (required) - Get at https://platform.openai.com/api-keys
- 🔷 **TAVILY_API_KEY** (optional) - Get at https://tavily.com (1000 free searches/month)
- ✅ **No keys needed** for HackerNews, Reddit, Wikipedia (built-in)

See **[API_KEYS.md](./API_KEYS.md)** for detailed setup instructions.

## Tech Stack

- **Frontend**: Streamlit
- **Agent Framework**: LangGraph (ReAct pattern)
- **LLM**: GPT-4o
- **News Sources**: HackerNews, Reddit (PRAW), Wikipedia, Tavily
- **Audio**: OpenAI TTS

## Architecture

```
User Preferences → LangGraph Agent → Multi-Source News System
                         ↓                     ↓
                    News Tools         NewsSourceManager
                         ↓                     ↓
              (HackerNews, Reddit, Wikipedia, Tavily)
                         ↓
                  Structured Output (Pydantic)
                         ↓
                  Presentation Layer → Optional Voiceover
```

### Multi-Source Architecture
- **Pluggable Sources**: Each source implements `NewsSource` interface
- **Priority-Based Fallback**: Sources tried in configurable priority order
- **Unified Format**: All sources return standardized `NewsItem` objects
- **Graceful Degradation**: System works even if some sources are unavailable

## Development

```bash
# Run tests
pytest

# Generate coverage report
pytest --cov=app --cov-report=html

# Format code
black app/ tests/
```

## Documentation

- `/CLAUDE.md`: High-level architecture and commands
- `/tests/CLAUDE.md`: Testing philosophy and patterns
- `/app/agent/CLAUDE.md`: Agent architecture and tools
- `/app/agent/sources/CLAUDE.md`: Multi-source news system and source development
- `/app/voiceover/CLAUDE.md`: Audio generation system

## Status

✅ MVP Complete: Personalized digest generation with autonomous AI agent
✅ Multi-Source System: 4 news sources with automatic fallback
✅ Voiceover: Full TTS integration
✅ Testing: 57+ tests with 90%+ coverage on sources
✅ Live Data: HackerNews, Reddit, Wikipedia, Tavily integration

## Contributing

This is a prototype built to explore agentic content curation. Feel free to fork and experiment!

## License

MIT
