"""User preferences management for the Agentic Morning Digest.

This module handles profile management and preference collection using the ProfileManager.
"""

import streamlit as st
from typing import Dict, Any
import json
from uuid import uuid4

from profile import ProfileManager


# Profile Templates for quick setup
PROFILE_TEMPLATES = {
    "Tech News": {
        "name": "Tech News Digest",
        "prefs": {
            "learn_about": "AI advancements, startup trends, tech policy",
            "fun_learning": "tech history, founder stories, interesting startups",
            "mood": "serious",
            "time_budget": "quick",
            "include_deep_dive": True,
            "include_quotes": False,
            "use_live_data": True,
            "voiceover_voice": "onyx"
        }
    },
    "Fun Learning": {
        "name": "Fun Learning Digest",
        "prefs": {
            "learn_about": "science breakthroughs, space exploration, research discoveries",
            "fun_learning": "weird facts, ancient mysteries, unusual animals, historical trivia",
            "mood": "playful",
            "time_budget": "deep",
            "include_deep_dive": True,
            "include_quotes": True,
            "use_live_data": True,
            "voiceover_voice": "nova"
        }
    },
    "Quick Brief": {
        "name": "Quick Morning Brief",
        "prefs": {
            "learn_about": "top news, AI updates, tech headlines",
            "fun_learning": "daily trivia, quick facts",
            "mood": "balanced",
            "time_budget": "quick",
            "include_deep_dive": False,
            "include_quotes": False,
            "use_live_data": True,
            "voiceover_voice": "alloy"
        }
    }
}


def init_profile_manager():
    """Initialize ProfileManager in session state (called once)."""
    if 'profile_manager' not in st.session_state:
        st.session_state.profile_manager = ProfileManager()


def render_profile_selector(manager: ProfileManager):
    """Render profile dropdown and action buttons."""
    st.sidebar.header("👤 Profile Management")

    # Get current profile
    current = manager.get_active_profile()
    profiles = manager.list_profiles()
    names = manager.get_profile_names()

    # Profile selector dropdown
    selected = st.sidebar.selectbox(
        "Active Profile:",
        options=profiles,
        format_func=lambda x: names[x],
        index=profiles.index(current.id),
        key="profile_selector"
    )

    # Switch profile if changed
    if selected != current.id:
        manager.set_active_profile(selected)
        st.rerun()

    # Action buttons (Create, Copy, Delete)
    col1, col2, col3 = st.sidebar.columns(3)

    with col1:
        if st.button("➕", help="Create new profile", key="btn_create", use_container_width=True):
            st.session_state.show_create_form = True

    with col2:
        if st.button("📋", help="Copy profile", key="btn_copy", use_container_width=True):
            st.session_state.show_copy_form = True

    with col3:
        can_delete = current.id != "default"
        if st.button("🗑️", help="Delete profile", key="btn_delete", disabled=not can_delete, use_container_width=True):
            if can_delete:
                st.session_state.show_delete_confirm = True

    # Handle profile actions (create, copy, delete forms)
    handle_profile_actions(manager)

    # Profile metadata expander
    with st.sidebar.expander("ℹ️ Profile Info"):
        st.caption(f"**ID:** `{current.id}`")
        st.caption(f"**Created:** {current.metadata.created_at.strftime('%Y-%m-%d')}")
        st.caption(f"**Last Used:** {current.metadata.last_used.strftime('%Y-%m-%d %H:%M')}")
        st.caption(f"**Times Used:** {current.metadata.use_count}")

    # Profile templates
    with st.sidebar.expander("📚 Create from Template"):
        template_name = st.selectbox(
            "Choose template:",
            options=list(PROFILE_TEMPLATES.keys()),
            key="template_selector"
        )

        template = PROFILE_TEMPLATES[template_name]
        st.caption(f"**Mood:** {template['prefs']['mood']} | **Time:** {template['prefs']['time_budget']}")

        if st.button("Create from Template", use_container_width=True, key="btn_create_template"):
            template_id = template_name.lower().replace(" ", "_") + "_" + uuid4().hex[:6]
            manager.create_profile(template_id, template['name'], template['prefs'])
            manager.set_active_profile(template_id)
            st.success(f"Created: {template['name']}")
            st.rerun()


def handle_profile_actions(manager: ProfileManager):
    """Handle create/copy/delete profile actions."""

    # CREATE NEW PROFILE
    if st.session_state.get('show_create_form', False):
        with st.sidebar.form("create_profile_form"):
            st.subheader("➕ Create New Profile")
            new_id = st.text_input("Profile ID (lowercase, e.g., 'work')")
            new_name = st.text_input("Profile Name (e.g., 'Work Profile')")
            copy_current = st.checkbox("Copy current preferences")

            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("Create", type="primary", use_container_width=True):
                    try:
                        if copy_current:
                            current = manager.get_active_profile()
                            prefs = current.get_preferences_dict()
                            manager.create_profile(new_id, new_name, prefs)
                        else:
                            manager.create_profile(new_id, new_name)

                        st.session_state.show_create_form = False
                        manager.set_active_profile(new_id)
                        st.success(f"Created: {new_name}")
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))

            with col2:
                if st.form_submit_button("Cancel", use_container_width=True):
                    st.session_state.show_create_form = False
                    st.rerun()

    # COPY PROFILE
    if st.session_state.get('show_copy_form', False):
        with st.sidebar.form("copy_profile_form"):
            st.subheader("📋 Copy Profile")
            current = manager.get_active_profile()
            new_id = st.text_input("New Profile ID", value=f"{current.id}_copy")
            new_name = st.text_input("New Profile Name", value=f"{current.name} (Copy)")

            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("Copy", type="primary", use_container_width=True):
                    try:
                        manager.copy_profile(current.id, new_id, new_name)
                        st.session_state.show_copy_form = False
                        manager.set_active_profile(new_id)
                        st.success(f"Copied to: {new_name}")
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))

            with col2:
                if st.form_submit_button("Cancel", use_container_width=True):
                    st.session_state.show_copy_form = False
                    st.rerun()

    # DELETE PROFILE
    if st.session_state.get('show_delete_confirm', False):
        current = manager.get_active_profile()
        st.sidebar.warning(f"⚠️ Delete **{current.name}**?")
        col1, col2 = st.sidebar.columns(2)

        with col1:
            if st.button("Yes, Delete", type="primary", key="confirm_delete", use_container_width=True):
                try:
                    # Switch to default first
                    manager.set_active_profile("default")
                    # Then delete
                    manager.delete_profile(current.id)
                    st.session_state.show_delete_confirm = False
                    st.success(f"Deleted: {current.name}")
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))

        with col2:
            if st.button("Cancel", key="cancel_delete", use_container_width=True):
                st.session_state.show_delete_confirm = False
                st.rerun()


def render_preference_controls(manager: ProfileManager):
    """Render preference input controls (text areas, selects, checkboxes)."""
    st.sidebar.header("🎛️ Preferences")

    # Get current preferences
    profile = manager.get_active_profile()
    prefs = profile.preferences

    # Learning interests
    learn_about = st.sidebar.text_area(
        "What I'd like to learn about:",
        value=prefs.learn_about,
        height=80,
        help="Describe what you're curious about or want to stay informed on",
        key="learn_about"
    )

    fun_learning = st.sidebar.text_area(
        "What I have fun learning about:",
        value=prefs.fun_learning,
        height=80,
        help="Topics that spark your curiosity or bring you joy",
        key="fun_learning"
    )

    # Mood selection
    mood = st.sidebar.selectbox(
        "Mood preference:",
        options=['serious', 'balanced', 'playful'],
        index=['serious', 'balanced', 'playful'].index(prefs.mood),
        key="mood"
    )

    # Time budget
    time_budget = st.sidebar.selectbox(
        "Time to read:",
        options=['quick', 'standard', 'deep'],
        index=['quick', 'standard', 'deep'].index(prefs.time_budget),
        key="time_budget"
    )

    # Additional options
    include_deep_dive = st.sidebar.checkbox(
        "Include deep dive section",
        value=prefs.include_deep_dive,
        key="include_deep_dive"
    )

    include_quotes = st.sidebar.checkbox(
        "Include inspirational quotes",
        value=prefs.include_quotes,
        key="include_quotes"
    )

    # Agent settings
    st.sidebar.markdown("---")
    st.sidebar.subheader("🤖 Agent Settings")

    use_live_data = st.sidebar.checkbox(
        "Use Real Agent (Live Data)",
        value=prefs.use_live_data,
        help="Real Agent: Uses live data. Mock: Uses static samples.",
        key="use_live_data"
    )

    # Voiceover settings
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎙️ Voiceover Settings")

    voice_options = [
        ("alloy", "Alloy - Neutral, balanced"),
        ("echo", "Echo - Clear, professional"),
        ("fable", "Fable - Warm, storytelling"),
        ("onyx", "Onyx - Deep, authoritative"),
        ("nova", "Nova - Bright, energetic"),
        ("shimmer", "Shimmer - Soft, gentle")
    ]

    voiceover_voice = st.sidebar.selectbox(
        "Voice for AI Voiceover",
        options=[v[0] for v in voice_options],
        index=[v[0] for v in voice_options].index(prefs.voiceover_voice),
        format_func=lambda x: next(v[1] for v in voice_options if v[0] == x),
        key="voiceover_voice"
    )

    # Import/Export section
    st.sidebar.markdown("---")
    st.sidebar.subheader("📦 Import/Export")

    col1, col2 = st.sidebar.columns(2)

    with col1:
        # Export current profile
        if st.button("📤 Export", use_container_width=True, key="btn_export"):
            profile_data = manager.export_profile(profile.id)
            st.download_button(
                "💾 Download",
                data=json.dumps(profile_data, indent=2),
                file_name=f"{profile.id}_profile.json",
                mime="application/json",
                use_container_width=True,
                key="btn_download"
            )

    with col2:
        # Import profile
        uploaded = st.file_uploader("📥 Import", label_visibility="collapsed", type="json", key="file_uploader")
        if uploaded:
            try:
                profile_data = json.load(uploaded)
                new_id = f"imported_{uuid4().hex[:6]}"
                manager.import_profile(profile_data, new_id)
                manager.set_active_profile(new_id)
                st.success("Imported!")
                st.rerun()
            except Exception as e:
                st.error(f"Import failed: {e}")

    # Collect all current values for auto-save
    current_prefs = {
        'learn_about': learn_about,
        'fun_learning': fun_learning,
        'mood': mood,
        'time_budget': time_budget,
        'include_deep_dive': include_deep_dive,
        'include_quotes': include_quotes,
        'use_live_data': use_live_data,
        'voiceover_voice': voiceover_voice
    }

    # Check if anything changed from saved preferences
    original_prefs = profile.get_preferences_dict()
    if current_prefs != original_prefs:
        # Update and save
        manager.update_active_preferences(current_prefs)
        # Show auto-saved indicator
        st.sidebar.caption("✅ Auto-saved")


def render_preferences_sidebar() -> Dict[str, Any]:
    """Render profile selector and preferences in sidebar.

    Returns:
        Dict of current preferences from active profile.
    """
    # Initialize ProfileManager
    init_profile_manager()
    manager = st.session_state.profile_manager

    # Profile Management Section
    render_profile_selector(manager)

    st.sidebar.markdown("---")

    # Preferences Section
    render_preference_controls(manager)

    # Return current preferences as dict (for digest generation)
    return manager.get_active_preferences()
