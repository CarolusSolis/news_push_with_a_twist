"""Streamlit app for Agentic Morning Digest MVP."""

import streamlit as st
import json
import os
from typing import Dict, List, Any
from pathlib import Path

# Import our modules
from prefs import render_preferences_sidebar
from presenter import render_sections, render_agent_log, show_empty_state, show_generation_status
from agent import generate_digest_with_agent, get_agent_logs
from voiceover import generate_voiceover_script, generate_audio_from_script

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
if 'voiceover_script' not in st.session_state:
    st.session_state.voiceover_script = None
if 'voiceover_audio_path' not in st.session_state:
    st.session_state.voiceover_audio_path = None
if 'voiceover_status' not in st.session_state:
    st.session_state.voiceover_status = None

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
    """Create mock digest sections with 1:1 alternating serious/fun items."""
    sections = []
    
    add_agent_log("[Planner] Starting digest generation...")
    add_agent_log(f"[Planner] User wants to learn about: {prefs['learn_about'][:50]}...")
    add_agent_log(f"[Planner] User enjoys learning about: {prefs['fun_learning'][:50]}...")
    add_agent_log(f"[Planner] Mood: {prefs['mood']}, Time budget: {prefs['time_budget']}")
    add_agent_log("[Planner] Planning 1:1 alternating pattern: serious → fun → serious → fun...")
    
    learn_about_lower = prefs['learn_about'].lower()
    fun_learning_lower = prefs['fun_learning'].lower()
    
    # Create individual items that will alternate
    items_to_add = []
    
    # Serious item #1: Tech headline (if relevant)
    if any(keyword in learn_about_lower for keyword in ['ai', 'tech', 'startup', 'technology', 'software', 'innovation']):
        add_agent_log("[Planner] Adding serious item #1: Tech headline")
        tech_item = mock_data.get('hacker_news', [{}])[0]
        items_to_add.append({
            'kind': 'need',
            'text': f"{tech_item.get('title', 'OpenAI Releases GPT-5')} - {tech_item.get('snippet', 'Major AI breakthrough')[:80]}...",
            'url': tech_item.get('url')
        })
    
    # Fun item #1: Quote (if enabled)
    if prefs['include_quotes'] and len(items_to_add) > 0:
        add_agent_log("[Planner] Adding fun item #1: Inspirational quote")
        quote = mock_data.get('quotes', [{}])[0]
        items_to_add.append({
            'kind': 'nice',
            'text': f'"{quote.get("text", "Innovation distinguishes between a leader and a follower.")}" - {quote.get("author", "Steve Jobs")}'
        })
    
    # Serious item #2: Another tech headline or deep dive
    if len(items_to_add) >= 2:
        add_agent_log("[Planner] Adding serious item #2: Second headline")
        if len(mock_data.get('hacker_news', [])) > 1:
            tech_item2 = mock_data.get('hacker_news', [{}])[1]
            items_to_add.append({
                'kind': 'need',
                'text': f"{tech_item2.get('title', 'Apple M4 Chip')} - {tech_item2.get('snippet', 'Hardware breakthrough')[:80]}...",
                'url': tech_item2.get('url')
            })
        else:
            # Deep dive fallback
            deep_dive_topic = "AI Model Performance"
            if "startup" in learn_about_lower:
                deep_dive_topic = "Startup Funding Trends"
            elif "space" in learn_about_lower:
                deep_dive_topic = "Commercial Space Industry"
            
            items_to_add.append({
                'kind': 'need',
                'text': f'{deep_dive_topic}: OpenAI\'s latest GPT-5 represents a significant leap in reasoning capabilities, with 10x performance improvements. This matters for your interests in {prefs["learn_about"][:30]}... because it signals more reliable AI assistants transforming knowledge work.',
            })
    
    # Fun item #2: Historical fact (if relevant interests)
    if len(items_to_add) >= 3 and any(keyword in fun_learning_lower for keyword in ['history', 'historical', 'past', 'ancient', 'mystery', 'exploration', 'space']):
        add_agent_log("[Planner] Adding fun item #2: Historical discovery")
        history_item = mock_data.get('wikipedia_today', [{}])[0]
        items_to_add.append({
            'kind': 'nice',
            'text': f"{history_item.get('title', '1969 – Apollo 11 Moon Landing')} - {history_item.get('snippet', 'Neil Armstrong and Buzz Aldrin became the first humans to land on the Moon.')}"
        })
    
    # Serious item #3: Market context (if deep time budget)
    if prefs['time_budget'] == 'deep' and len(items_to_add) >= 4:
        add_agent_log("[Planner] Adding serious item #3: Market context")
        items_to_add.append({
            'kind': 'need',
            'text': 'Tech Market Update: With Apple\'s new M4 chip announcement, the AI hardware race intensifies. This follows the trend you\'re interested in around emerging technologies and their market impact.'
        })
    
    # Fun item #3: Second quote or fun fact
    if len(items_to_add) >= 5 and len(mock_data.get('quotes', [])) > 1:
        add_agent_log("[Planner] Adding fun item #3: Second quote")
        quote2 = mock_data.get('quotes', [{}])[1]
        items_to_add.append({
            'kind': 'nice',
            'text': f'"{quote2.get("text", "Be yourself; everyone else is already taken.")}" - {quote2.get("author", "Oscar Wilde")}'
        })
    
    # Convert items to sections for rendering
    for i, item in enumerate(items_to_add):
        section_id = f"item_{i+1}"
        section_title = f"Item {i+1}"
        
        sections.append({
            'id': section_id,
            'title': section_title,
            'kind': item['kind'],
            'items': [{
                'text': item['text'],
                'url': item.get('url')
            }]
        })
    
    add_agent_log(f"[Planner] Generated {len(sections)} items in strict 1:1 alternating pattern")
    add_agent_log("[Retriever] Using static mock data (USE_LIVE=False)")
    add_agent_log("[Presenter] Items ready for rendering")
    
    return sections

def generate_digest(prefs: Dict[str, Any]) -> None:
    """Generate the morning digest based on preferences using AI agent."""
    st.session_state.generation_status = 'planning'
    st.session_state.agent_log = []  # Clear previous log
    
    # Show generation steps with status updates
    show_generation_status('planning')
    st.session_state.generation_status = 'fetching'
    
    show_generation_status('fetching')  
    st.session_state.generation_status = 'processing'
    
    show_generation_status('processing')
    st.session_state.generation_status = 'rendering'
    
    # Generate digest using AI agent based on user preference
    try:
        use_live_data = prefs.get('use_live_data', True)
        sections = generate_digest_with_agent(prefs, use_live_data=use_live_data)
        st.session_state.digest_sections = sections
        
        # Get agent logs and add to session state
        agent_logs = get_agent_logs()
        st.session_state.agent_log = agent_logs
        
        show_generation_status('complete')
        st.session_state.generation_status = 'complete'
        
    except Exception as e:
        st.error(f"Failed to generate digest: {e}")
        # Fallback to mock generation
        mock_data = load_mock_data()
        if mock_data:
            sections = create_mock_sections(prefs, mock_data)
            st.session_state.digest_sections = sections
        
        show_generation_status('complete')
        st.session_state.generation_status = 'complete'

def generate_voiceover(prefs: Dict[str, Any]) -> None:
    """Generate voiceover script and audio from the current digest."""
    if not st.session_state.digest_sections:
        st.error("Please generate a digest first before creating voiceover.")
        return
    
    st.session_state.voiceover_status = 'generating_script'
    
    try:
        # Generate voiceover script
        with st.spinner("🎙️ Generating voiceover script..."):
            script = generate_voiceover_script(st.session_state.digest_sections, prefs)
            st.session_state.voiceover_script = script
        
        st.session_state.voiceover_status = 'generating_audio'
        
                # Generate audio from script
        with st.spinner("🔊 Converting script to audio..."):
            selected_voice = prefs.get('voiceover_voice', 'alloy')
            audio_path = generate_audio_from_script(script, voice=selected_voice)
            if audio_path:
                # Store the audio path (no need to cache binary data)
                st.session_state.voiceover_audio_path = audio_path
                st.session_state.voiceover_status = 'complete'
            else:
                st.session_state.voiceover_status = 'error'
                st.error("Failed to generate audio. Please check your OpenAI API key.")
        
    except Exception as e:
        st.session_state.voiceover_status = 'error'
        st.error(f"Failed to generate voiceover: {e}")

def cleanup_audio_file():
    """Clean up audio file if it exists."""
    if st.session_state.voiceover_audio_path and os.path.exists(st.session_state.voiceover_audio_path):
        try:
            os.unlink(st.session_state.voiceover_audio_path)
            st.session_state.voiceover_audio_path = None
        except Exception:
            pass  # Ignore cleanup errors

def main():
    """Main Streamlit app."""
    
    # Render sidebar preferences
    prefs = render_preferences_sidebar()
    
    # Main content area
    col1, col2 = st.columns([3, 1])
    
    with col2:
        # Generate button
        if st.button("🤖 Generate My Digest", type="primary", use_container_width=True):
            generate_digest(prefs)
        
        # Regenerate button (only show if digest exists)
        if st.session_state.digest_sections:
            if st.button("🔄 Regenerate with AI", use_container_width=True):
                generate_digest(prefs)
            
            # Voiceover button (only show if digest exists)
            st.markdown("---")
            if st.button("🎙️ Generate Voiceover", use_container_width=True):
                generate_voiceover(prefs)
            
            
            # Show voiceover status and audio player
            if st.session_state.voiceover_status == 'generating_script':
                st.info("🎙️ Generating voiceover script...")
            elif st.session_state.voiceover_status == 'generating_audio':
                st.info("🔊 Converting script to audio...")
            elif st.session_state.voiceover_status == 'complete' and st.session_state.voiceover_audio_path:
                st.success("✅ Voiceover ready!")
                
                # Audio player
                if st.session_state.voiceover_audio_path and os.path.exists(st.session_state.voiceover_audio_path):
                    st.audio(st.session_state.voiceover_audio_path)
                else:
                    st.error("❌ Audio file not found")
                
                # Show script in expander
                if st.session_state.voiceover_script:
                    with st.expander("📝 View Voiceover Script", expanded=False):
                        st.text(st.session_state.voiceover_script)
                
                # Cleanup button
                if st.button("🗑️ Clear Voiceover", use_container_width=True):
                    cleanup_audio_file()
                    st.session_state.voiceover_script = None
                    st.session_state.voiceover_status = None
                    st.rerun()
            elif st.session_state.voiceover_status == 'error':
                st.error("❌ Voiceover generation failed")
    
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