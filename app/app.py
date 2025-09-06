"""Streamlit app for Agentic Morning Digest MVP."""

import streamlit as st
import json
from typing import Dict, List, Any
from pathlib import Path

# Import our modules
from prefs import render_preferences_sidebar
from presenter import render_sections, render_agent_log, show_empty_state, show_generation_status

# Page config
st.set_page_config(
    page_title="Agentic Morning Digest",
    page_icon="🌅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'digest_sections' not in st.session_state:
    st.session_state.digest_sections = []
if 'agent_log' not in st.session_state:
    st.session_state.agent_log = []
if 'generation_status' not in st.session_state:
    st.session_state.generation_status = None

def load_mock_data() -> Dict[str, Any]:
    """Load mock data from static samples."""
    try:
        data_path = Path(__file__).parent / 'data' / 'static_samples.json'
        with open(data_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Failed to load mock data: {e}")
        return {}

def add_agent_log(message: str) -> None:
    """Add message to agent thinking log."""
    st.session_state.agent_log.append(message)

def create_mock_sections(prefs: Dict[str, Any], mock_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Create mock digest sections based on preferences."""
    sections = []
    
    add_agent_log("[Planner] Starting digest generation...")
    add_agent_log(f"[Planner] User preferences: topics={prefs['topics']}, mood={prefs['mood']}, time_budget={prefs['time_budget']}")
    
    # Always include Quick Hits if tech topics selected
    if 'AI/Tech' in prefs['topics']:
        add_agent_log("[Planner] AI/Tech in topics → adding Quick Hits section")
        tech_items = []
        for item in mock_data.get('hacker_news', [])[:3]:
            tech_items.append({
                'text': f"{item['title']} - {item['snippet'][:80]}...",
                'url': item['url']
            })
        
        sections.append({
            'id': 'quick_hits',
            'title': '📌 Tech Quick Hits You Should Know',
            'kind': 'need',
            'items': tech_items
        })
    
    # Add history section if selected
    if 'History' in prefs['topics']:
        add_agent_log("[Planner] History in topics → adding Did You Know section")
        history_items = []
        for item in mock_data.get('wikipedia_today', [])[:2]:
            history_items.append({
                'text': f"{item['title']} - {item['snippet']}"
            })
        
        sections.append({
            'id': 'did_you_know',
            'title': '📚 Did You Know - On This Day',
            'kind': 'nice',
            'items': history_items
        })
    
    # Add deep dive if enabled and time budget allows
    if prefs['include_deep_dive'] and prefs['time_budget'] in ['standard', 'deep']:
        add_agent_log("[Planner] Deep dive enabled + time budget allows → adding Deep Dive section")
        sections.append({
            'id': 'deep_dive',
            'title': '🔍 Deep Dive Analysis',
            'kind': 'need',
            'items': [{
                'text': 'AI Model Performance: OpenAI\'s latest GPT-5 represents a significant leap in reasoning capabilities, with 10x performance improvements in complex problem-solving tasks. This matters because it signals we\'re approaching more reliable AI assistants that could transform knowledge work across industries.',
            }]
        })
    
    # Add quotes if enabled
    if prefs['include_quotes']:
        add_agent_log("[Planner] Quotes enabled → adding Fun Spark section")
        quote_items = []
        for quote in mock_data.get('quotes', [])[:2]:
            quote_items.append({
                'text': f'"{quote["text"]}" - {quote["author"]}'
            })
        
        sections.append({
            'id': 'fun_spark',
            'title': '✨ Quote & Fun Spark',
            'kind': 'nice',
            'items': quote_items
        })
    
    add_agent_log(f"[Planner] Generated {len(sections)} sections following need→nice→need pattern")
    add_agent_log("[Retriever] Using static mock data (USE_LIVE=False)")
    add_agent_log("[Presenter] Sections ready for rendering")
    
    return sections

def generate_digest(prefs: Dict[str, Any]) -> None:
    """Generate the morning digest based on preferences."""
    st.session_state.generation_status = 'planning'
    st.session_state.agent_log = []  # Clear previous log
    
    # Load mock data
    mock_data = load_mock_data()
    if not mock_data:
        st.error("Could not load mock data")
        return
    
    # Simulate generation steps with status updates
    show_generation_status('planning')
    st.session_state.generation_status = 'fetching'
    
    show_generation_status('fetching')
    st.session_state.generation_status = 'processing'
    
    show_generation_status('processing')
    st.session_state.generation_status = 'rendering'
    
    # Create sections
    sections = create_mock_sections(prefs, mock_data)
    st.session_state.digest_sections = sections
    
    show_generation_status('complete')
    st.session_state.generation_status = 'complete'

def main():
    """Main Streamlit app."""
    
    # Render sidebar preferences
    prefs = render_preferences_sidebar()
    
    # Main content area
    col1, col2 = st.columns([3, 1])
    
    with col2:
        # Generate button
        if st.button("🚀 Generate My Digest", type="primary", use_container_width=True):
            generate_digest(prefs)
        
        # Regenerate button (only show if digest exists)
        if st.session_state.digest_sections:
            if st.button("🔄 Regenerate", use_container_width=True):
                generate_digest(prefs)
    
    with col1:
        # Main content
        if not st.session_state.digest_sections:
            show_empty_state()
        else:
            render_sections(st.session_state.digest_sections)
    
    # Agent thinking log (full width at bottom)
    st.markdown("---")
    render_agent_log(st.session_state.agent_log)

if __name__ == "__main__":
    main()