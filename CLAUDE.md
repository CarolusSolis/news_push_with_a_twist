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
- **Environment setup:** Ensure `OPENAI_API_KEY` is set in environment (for future LLM integration)

### Demo Constraints (3-minute screen recording)
- Must show: pick preferences → show "Agent plan" → interleaved sections (need/nice) → regenerate.
- Fast and reliable: prefer **cached/mocked** data if scraping/LLM is slow.

## 2) Tech Stack (MVP)
- **Frontend:** Streamlit
- **LLM:** GPT (for summaries/reframes); keep calls minimal and deterministic (temperature low)
- **Retrieval:** Playwright (JS sites) + BeautifulSoup (parse). Provide **mock switch** + **cache**
- **Lang orchestration:** Simple Python functions; only add LangGraph/Strands/CrewAI if needed
- **Storage:** In-memory / JSON file for prefs + cached content

## 3) Sources (start with 3)
- **Hacker News** (front page) → “Quick Hits” tech/AI headlines  
- **Wikipedia – Selected anniversaries / On This Day** → “Did You Know” history bits  
- **quotes.toscrape.com** → “Quote / Fun Spark”  
Add RSS/API later only if time allows.

## 4) Architecture & Code Structure

### Core Architecture
The application follows a modular pipeline architecture:
1. **Preferences Collection** → **Planning** → **Content Retrieval** → **Content Processing** → **Presentation**
2. **Agent Thinking Log** runs parallel to track all decisions and actions
3. **Fallback Strategy** ensures resilience: Live Data → Cache → Static Samples

### Module Responsibilities
- **app.py**: Streamlit UI + wiring + Agent Log display
- **manager.py**: Plans sections & order (need/nice interleave) + decision logging  
- **retriever.py**: Scraping (HN/Wiki/Quotes) + cache + USE_LIVE flag + fallback logic
- **editors.py**: NeedToKnow / NiceToKnow content transformers + LLM calls
- **presenter.py**: Pure rendering helpers (no business logic)
- **prefs.py**: Load/save user preferences (JSON / session_state)
- **data/static_samples.json**: Fallback content for demo resilience

### Data Flow
```
User Prefs → Manager.plan_sections() → Retriever.fetch_*() → Editors.transform() → Presenter.render()
                    ↓
              Agent Log (tracks all decisions)
```

## 5) Section Contract
Each section is a dict:
{
  "id": "quick_hits" | "deep_dive" | "did_you_know" | "fun_spark" | "quote",
  "title": "📌 Quick Hits You Should Know",
  "kind": "need" | "nice",
  "items": [{"text": "...", "url": optional}]
}

## 6) Agentic Workflow (what to implement)
1. **Collect prefs** (topics, mood, time budget) in sidebar.  
2. **Manager.plan_sections(prefs)**  
   - Rules: if topics include AI/History/Politics → select `quick_hits`, `deep_dive` (need)  
   - Always include one `nice` block (`quote` or `fun_spark`)  
   - Interleave pattern: **need → nice → need** (max 3–4 sections)  
   - Log decisions to “Agent Thinking Log”.
3. **Retriever.fetch_*()**  
   - Try cached; if `USE_LIVE=True`, scrape via Playwright; else use `data/static_samples.json`.  
   - Parse with BeautifulSoup; return minimal clean fields.  
   - On failure, **fallback** to cache/static and log reason.
4. **Editors**  
   - `need_to_know(sec, data)`: one-sentence bullets; optional 1-paragraph “Deep Dive” (LLM-summarize a single item).  
   - `nice_to_know(sec, data)`: quote or playful what-if; deterministic prompt; no external calls if possible.
5. **Presenter.render(sections)**  
   - Pure formatting; add badges for need/nice; collapsible expanders.  
6. **Observability**  
   - Every step appends a concise log line: `[Planner] chose X`, `[Retriever] cache hit for HN`, etc.

## 7) Coding Standards & Safety
- Python 3.11+, type hints, small pure functions, docstrings, `black` format.
- **No secrets in code**. Expect `OPENAI_API_KEY` via env.  
- Use `@st.cache_data(ttl=600)` for network calls.  
- Timebox scraping to 3s/site; then fallback.  
- LLM: `temperature=0.2`, bounded output via explicit bullet/char limits.

## 8) Prompts (edit as needed)
**Planner prompt (system):**  
“You plan a 3–4 section morning digest mixing *need-to-know* (news/deep-dive) and *nice-to-know* (quote/what-if). Given {topics, mood, time_budget}, choose section IDs from: [`quick_hits`, `deep_dive`, `did_you_know`, `quote`, `fun_spark`]. Return JSON: `{order:[...], rationale:[...]}`. Prefer pattern need→nice→need.”

**Need summary prompt (user):**  
“Summarize this headline+snippet for a daily digest. 1 sentence, ≤25 words, neutral, add why it matters. Input:\n{headline}\n{snippet}”

**Fun spark prompt (user):**  
“Write one playful ‘what-if’ (≤25 words) connecting {topic} to history/politics. Keep it tasteful, no speculation about real people’s private lives.”

## 9) Implementation Priority
**Build in this order to maintain demo readiness:**
1. **MVP Foundation**: `app.py` skeleton with sidebar prefs, Generate button, Agent Log expander
2. **Static Data**: Create `data/static_samples.json` with sample content from all sources
3. **Planning Logic**: Implement `manager.plan_sections()` with decision rules and logging
4. **Presentation Layer**: Build `presenter.render()` with markdown cards and collapsible expanders
5. **Content Pipeline**: Implement `retriever.py` cache + mock + optional live scraping
6. **LLM Integration**: Add minimal LLM calls for "Deep Dive" summaries only

**Critical Path**: Steps 1-4 create a working demo. Steps 5-6 add real functionality.

## 10) Failure & Fallback Policy
If any scraper/LLM step fails or exceeds latency budget:  
- Log: reason + switch (“fallback to cache”).  
- Keep UI responsive; never crash app.  
- Regenerate only the failed section, not the whole page.
