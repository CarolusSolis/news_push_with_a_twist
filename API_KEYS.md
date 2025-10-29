# API Keys & Environment Variables

This document explains all API keys and environment variables needed for the Agentic Morning Digest.

## Quick Setup

1. Copy the example file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your API keys

3. **Minimum setup** (basic functionality):
   ```bash
   OPENAI_API_KEY=sk-...
   ```

4. **Recommended setup** (full functionality):
   ```bash
   OPENAI_API_KEY=sk-...
   TAVILY_API_KEY=tvly-...
   ```

## Required API Keys

### 1. OpenAI API Key (REQUIRED)

**Used for:**
- 🤖 GPT-4o agent orchestration (LangGraph ReAct agent)
- ✍️ Content processing and summarization
- 🔊 Text-to-speech voiceover generation

**How to get:**
1. Sign up at https://platform.openai.com
2. Go to https://platform.openai.com/api-keys
3. Click "Create new secret key"
4. Copy the key (starts with `sk-proj-...` or `sk-...`)

**Pricing:**
- GPT-4o: ~$2.50 per 1M input tokens, ~$10 per 1M output tokens
- TTS: ~$15 per 1M characters
- Typical digest: ~5-10 cents per generation (with voiceover)

**Environment variable:**
```bash
OPENAI_API_KEY=sk-proj-your_key_here
```

**What happens without it:**
- ❌ Application will not work
- ❌ Agent cannot make decisions
- ❌ No content processing or voiceover

---

## Optional API Keys

### 2. Tavily API Key (OPTIONAL but recommended)

**Used for:**
- 🔍 AI-powered intelligent web search
- 🎲 Creative/specific content queries ("medieval siege warfare", "quantum computing breakthroughs")
- 🌐 Real-time news search

**How to get:**
1. Sign up at https://tavily.com
2. Get your API key from dashboard
3. Copy the key (starts with `tvly-...`)

**Pricing:**
- Free tier: **1000 searches/month** (sufficient for personal use)
- Pro tier: $49/month for 10,000 searches

**Environment variable:**
```bash
TAVILY_API_KEY=tvly-your_key_here
```

**What happens without it:**
- ✅ Application still works
- ✅ Uses HackerNews, Reddit, and Wikipedia
- ❌ `search_news()` tool unavailable
- ❌ Tavily source unavailable
- ⚠️ Less content diversity for "nice-to-know" facts

**Recommendation:** Include this for best experience, especially for creative/diverse content.

---

## No API Keys Needed

### 3. HackerNews (Built-in)

**Used for:**
- 💻 Tech/AI/startup news
- 🚀 Front page headlines

**How it works:**
- Web scraping with BeautifulSoup
- Public access, no authentication needed

**Cost:** Free

---

### 4. Reddit (Built-in)

**Used for:**
- 🗣️ Community discussions (tech, science, fun)
- 📰 Reddit front page content from various subreddits

**How it works:**
- PRAW (Python Reddit API Wrapper) in read-only mode
- Public content access without OAuth

**Cost:** Free

**Subreddits accessed:**
- **Tech**: r/technology, r/programming, r/artificial
- **Science**: r/science, r/askscience, r/space
- **Fun**: r/todayilearned, r/explainlikeimfive, r/Damnthatsinteresting

---

### 5. Wikipedia (Built-in)

**Used for:**
- 📅 "On this day" historical events
- 🌍 Current events portal

**How it works:**
- Public Wikimedia API (no authentication)
- Feed API for structured content

**Cost:** Free

---

## Environment Variable Reference

```bash
# .env file structure

# REQUIRED
OPENAI_API_KEY=sk-proj-xxxxx...

# OPTIONAL
TAVILY_API_KEY=tvly-xxxxx...
```

## Security Best Practices

✅ **DO:**
- Keep `.env` file in `.gitignore` (already configured)
- Never commit API keys to version control
- Use `.env.example` as a template (safe to commit)
- Rotate keys periodically
- Use separate keys for development and production

❌ **DON'T:**
- Share your `.env` file
- Commit API keys to Git
- Use production keys in development
- Hardcode keys in source code

## Testing Without API Keys

You can run **most tests** without API keys using mocks:

```bash
# Run tests (mocks external APIs)
pytest tests/test_sources.py -v

# Skip tests that require API keys
pytest -m "not requires_api_key"
```

However, to test **real agent functionality**, you need `OPENAI_API_KEY`.

## Troubleshooting

### "No module named 'langgraph'"
```bash
pip install -r requirements.txt
```

### "OpenAI API key not found"
1. Check `.env` file exists
2. Verify `OPENAI_API_KEY` is set
3. Restart the application

### "Tavily source unavailable"
This is normal if `TAVILY_API_KEY` is not set. The application will work with other sources.

### "Rate limit exceeded"
- **OpenAI**: Upgrade plan or wait
- **Tavily**: Wait for monthly reset or upgrade plan
- **Reddit/HackerNews/Wikipedia**: Very generous limits, rarely hit

## Source Availability Matrix

| Source      | API Key Needed? | Free Tier | Rate Limit     |
|-------------|----------------|-----------|----------------|
| HackerNews  | ❌ No          | ✅ Yes    | ~60 req/min    |
| Reddit      | ❌ No          | ✅ Yes    | ~60 req/min    |
| Wikipedia   | ❌ No          | ✅ Yes    | ~200 req/min   |
| Tavily      | ✅ Yes         | ✅ Yes    | 1000/month     |

## Cost Estimation

**Typical usage (daily digest with voiceover):**
- Agent execution: ~$0.03
- Content processing: ~$0.02
- Voiceover (TTS): ~$0.05
- **Total per digest: ~$0.10**

**Monthly cost (daily use):**
- ~$3 per month with OpenAI
- +$0 with free Tavily tier (1000 searches/month)

## Getting Help

If you need help with API keys:
1. Check this document
2. See `.env.example` for format
3. Consult source documentation:
   - OpenAI: https://platform.openai.com/docs
   - Tavily: https://docs.tavily.com

## Future API Keys (Not Yet Implemented)

These sources are planned but not yet implemented:

- ❌ NewsAPI.ai (professional news API)
- ❌ RSS feeds (custom feeds)
- ❌ YouTube (video transcripts)
- ❌ ArXiv (academic papers)

See `/app/agent/sources/CLAUDE.md` for adding new sources.
