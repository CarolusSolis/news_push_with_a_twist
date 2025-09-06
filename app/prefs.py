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
        'topics': ['AI/Tech', 'History'],
        'mood': 'balanced',
        'time_budget': 'quick',
        'include_deep_dive': True,
        'include_quotes': True
    }

def render_preferences_sidebar() -> Dict[str, Any]:
    """Render preferences in sidebar and return current preferences."""
    st.sidebar.header("🎛️ Your Digest Preferences")
    
    # Topics selection
    topic_options = ['AI/Tech', 'History', 'Politics', 'Science', 'Business']
    topics = st.sidebar.multiselect(
        "Topics you care about:",
        topic_options,
        default=load_preferences().get('topics', ['AI/Tech', 'History'])
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
    
    # Build preferences dict
    prefs = {
        'topics': topics,
        'mood': mood,
        'time_budget': time_budget,
        'include_deep_dive': include_deep_dive,
        'include_quotes': include_quotes
    }
    
    # Save to session state
    save_preferences(prefs)
    
    return prefs