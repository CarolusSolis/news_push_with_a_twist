"""User preferences management for the Agentic Morning Digest."""

import streamlit as st
from typing import Dict, List, Any
import json

def load_preferences() -> Dict[str, Any]:
    """Load user preferences from session state or defaults."""
    if 'user_prefs' not in st.session_state:
        st.session_state.user_prefs = get_default_preferences()
    return st.session_state.user_prefs

def save_preferences(prefs: Dict[str, Any]) -> None:
    """Save user preferences to session state."""
    st.session_state.user_prefs = prefs

def get_default_preferences() -> Dict[str, Any]:
    """Return default user preferences."""
    return {
        'learn_about': 'AI advancements, startup trends, emerging technologies',
        'fun_learning': 'historical mysteries, space exploration, interesting science facts',
        'mood': 'balanced',
        'time_budget': 'quick',
        'include_deep_dive': True,
        'include_quotes': True,
        'use_live_data': True
    }

def render_preferences_sidebar() -> Dict[str, Any]:
    """Render preferences in sidebar and return current preferences."""
    st.sidebar.header("🎛️ Your Digest Preferences")
    
    # Natural language learning interests
    learn_about = st.sidebar.text_area(
        "What I'd like to learn about:",
        value=load_preferences().get('learn_about', 'AI advancements, startup trends, emerging technologies'),
        height=80,
        help="Describe what you're curious about or want to stay informed on"
    )
    
    fun_learning = st.sidebar.text_area(
        "What I have fun learning about:",
        value=load_preferences().get('fun_learning', 'historical mysteries, space exploration, interesting science facts'),
        height=80,
        help="Topics that spark your curiosity or bring you joy to discover"
    )
    
    # Mood selection
    mood = st.sidebar.selectbox(
        "Mood preference:",
        ['serious', 'balanced', 'playful'],
        index=['serious', 'balanced', 'playful'].index(load_preferences().get('mood', 'balanced'))
    )
    
    # Time budget
    time_budget = st.sidebar.selectbox(
        "Time to read:",
        ['quick', 'standard', 'deep'],
        index=['quick', 'standard', 'deep'].index(load_preferences().get('time_budget', 'quick'))
    )
    
    # Additional options
    include_deep_dive = st.sidebar.checkbox(
        "Include deep dive section",
        value=load_preferences().get('include_deep_dive', True)
    )
    
    include_quotes = st.sidebar.checkbox(
        "Include inspirational quotes",
        value=load_preferences().get('include_quotes', True)
    )
    
    # Agent type selection
    st.sidebar.markdown("---")
    st.sidebar.subheader("🤖 Agent Settings")
    
    use_live_data = st.sidebar.checkbox(
        "Use Real Agent (Live Data)",
        value=load_preferences().get('use_live_data', True),
        help="Real Agent: Uses live Hacker News data. Mock Agent: Uses static sample data for demo."
    )
    
    # Build preferences dict
    prefs = {
        'learn_about': learn_about,
        'fun_learning': fun_learning,
        'mood': mood,
        'time_budget': time_budget,
        'include_deep_dive': include_deep_dive,
        'include_quotes': include_quotes,
        'use_live_data': use_live_data
    }
    
    # Save to session state
    save_preferences(prefs)
    
    return prefs