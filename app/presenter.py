"""Pure rendering helpers for the Agentic Morning Digest."""

import streamlit as st
from typing import Dict, List, Any

def render_section(section: Dict[str, Any]) -> None:
    """Render a single digest section."""
    section_id = section.get('id', '')
    title = section.get('title', 'Untitled Section')
    kind = section.get('kind', 'need')
    items = section.get('items', [])
    
    # Add kind badge
    badge_emoji = "📌" if kind == "need" else "✨"
    badge_color = "red" if kind == "need" else "blue"
    
    # Create expander for section
    with st.expander(f"{badge_emoji} {title}", expanded=True):
        if kind == "need":
            st.markdown(f"<div style='background-color: #ffebee; padding: 10px; border-radius: 5px; margin-bottom: 10px;'><b>Need-to-Know</b></div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div style='background-color: #e3f2fd; padding: 10px; border-radius: 5px; margin-bottom: 10px;'><b>Nice-to-Know</b></div>", unsafe_allow_html=True)
        
        # Render items
        for i, item in enumerate(items):
            text = item.get('text', '')
            url = item.get('url')
            
            if url:
                st.markdown(f"• [{text}]({url})")
            else:
                st.markdown(f"• {text}")

def render_sections(sections: List[Dict[str, Any]]) -> None:
    """Render all digest sections."""
    if not sections:
        st.info("No sections to display. Generate your digest to get started!")
        return
    
    st.header("📰 Your Personalized Morning Digest")
    
    for section in sections:
        render_section(section)

def render_agent_log(log_entries: List[str]) -> None:
    """Render the agent thinking log."""
    with st.expander("🤖 Agent Thinking Log", expanded=False):
        if not log_entries:
            st.write("No agent activity yet. Generate a digest to see how the AI plans your content.")
        else:
            for entry in log_entries:
                st.text(entry)

def show_empty_state() -> None:
    """Show the initial empty state before digest generation."""
    st.title("🌅 Agentic Morning Digest")
    st.markdown("""
    Welcome to your personalized morning digest! This AI agent will create a custom blend of:
    
    **Need-to-Know** 📌
    - AI/Tech headlines from Hacker News
    - Important political and world events
    - Deep dive analysis on topics you care about
    
    **Nice-to-Know** ✨ 
    - Historical events that happened "on this day"
    - Inspirational quotes to start your day
    - Fun "what-if" scenarios and trivia
    
    Configure your preferences in the sidebar and click **Generate My Digest** to get started!
    """)

def show_generation_status(status: str) -> None:
    """Show current generation status."""
    status_messages = {
        'planning': '🧠 Planning your perfect digest...',
        'fetching': '📡 Gathering fresh content...',
        'processing': '⚙️ Processing and summarizing...',
        'rendering': '🎨 Putting it all together...',
        'complete': '✅ Your digest is ready!'
    }
    
    if status in status_messages:
        st.info(status_messages[status])
    else:
        st.info(f"Status: {status}")