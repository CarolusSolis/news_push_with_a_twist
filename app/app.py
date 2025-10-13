"""Streamlit app for Agentic Morning Digest MVP."""

import streamlit as st
import os
from typing import Dict, Any

# Import our modules
from prefs import render_preferences_sidebar
from presenter import render_sections, render_agent_log, show_empty_state, show_generation_status
from services import DigestService, VoiceoverService

# Initialize services
digest_service = DigestService()
voiceover_service = VoiceoverService()

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
        sections, agent_logs = digest_service.generate_digest(prefs, use_live_data=use_live_data)
        st.session_state.digest_sections = sections
        st.session_state.agent_log = agent_logs

        show_generation_status('complete')
        st.session_state.generation_status = 'complete'

    except Exception as e:
        st.error(f"Failed to generate digest: {e}")
        # Fallback to mock generation
        try:
            sections, log_messages = digest_service.create_mock_sections(prefs)
            st.session_state.digest_sections = sections
            st.session_state.agent_log = log_messages
        except Exception as fallback_error:
            st.error(f"Fallback also failed: {fallback_error}")

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
            script = voiceover_service.generate_script(st.session_state.digest_sections, prefs)
            st.session_state.voiceover_script = script

        st.session_state.voiceover_status = 'generating_audio'

        # Generate audio from script
        with st.spinner("🔊 Converting script to audio..."):
            selected_voice = prefs.get('voiceover_voice', 'alloy')
            audio_path = voiceover_service.generate_audio(script, voice=selected_voice)
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
    if st.session_state.voiceover_audio_path:
        success = voiceover_service.cleanup_audio(st.session_state.voiceover_audio_path)
        if success:
            st.session_state.voiceover_audio_path = None

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