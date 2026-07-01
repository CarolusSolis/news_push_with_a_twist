"""User profile and preference management system.

This module provides a comprehensive profile management system for the
Agentic Morning Digest application, including:

- Type-safe preference models (Pydantic)
- Persistent profile storage (JSON files)
- Profile CRUD operations via ProfileManager
- Migration from session-state-only to persisted profiles

Example:
    >>> from profile import ProfileManager, UserProfile
    >>>
    >>> manager = ProfileManager()
    >>> profile = manager.get_active_profile()
    >>> print(profile.preferences.mood)
    'balanced'
"""

from .models import Preferences, UserProfile, ProfileMetadata
from .manager import ProfileManager

__all__ = [
    'Preferences',
    'UserProfile',
    'ProfileMetadata',
    'ProfileManager',
]
