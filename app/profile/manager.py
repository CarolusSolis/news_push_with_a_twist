"""Profile management with CRUD operations.

This module provides the ProfileManager class for high-level profile operations.
"""

import logging
from typing import Optional, List, Dict, Any
from pathlib import Path

from .models import UserProfile, Preferences
from .storage import ProfileStorage, JSONProfileStorage

logger = logging.getLogger(__name__)


class ProfileManager:
    """Manages user profiles with CRUD operations.

    Features:
    - Create, load, save, delete profiles
    - Active profile tracking
    - Auto-creation of default profile
    - Profile switching
    - Backward compatibility with dict-based preferences

    Example:
        >>> manager = ProfileManager()
        >>> profile = manager.get_active_profile()
        >>> profile.preferences.mood = "playful"
        >>> manager.save_active_profile()
    """

    def __init__(self, storage: Optional[ProfileStorage] = None):
        """Initialize ProfileManager.

        Args:
            storage: ProfileStorage implementation (default: JSONProfileStorage)
        """
        self.storage = storage or JSONProfileStorage()
        self._active_profile_id: Optional[str] = None
        self._active_profile: Optional[UserProfile] = None

        logger.info("[ProfileManager] Initialized")

        # Ensure at least a default profile exists
        self._ensure_default_profile()

    def _ensure_default_profile(self) -> None:
        """Ensure a default profile exists, creating it if necessary."""
        if not self.storage.exists("default"):
            logger.info("[ProfileManager] Creating default profile")
            default_profile = UserProfile.create_default()
            self.storage.save(default_profile)

    def create_profile(
        self,
        profile_id: str,
        name: str,
        preferences: Optional[Dict[str, Any]] = None
    ) -> UserProfile:
        """Create a new profile.

        Args:
            profile_id: Unique profile identifier (lowercase, alphanumeric).
            name: Human-readable profile name.
            preferences: Optional preferences dict. If None, uses defaults.

        Returns:
            Created UserProfile.

        Raises:
            ValueError: If profile ID already exists or is invalid.
        """
        # Validate profile doesn't already exist
        if self.storage.exists(profile_id):
            raise ValueError(f"Profile '{profile_id}' already exists")

        # Create preferences
        prefs = Preferences(**(preferences or {}))

        # Create profile
        profile = UserProfile(
            id=profile_id,
            name=name,
            preferences=prefs
        )

        # Save to storage
        self.storage.save(profile)

        logger.info(f"[ProfileManager] Created profile '{profile_id}' ({name})")
        return profile

    def load_profile(self, profile_id: str) -> Optional[UserProfile]:
        """Load a profile by ID.

        Args:
            profile_id: Profile identifier.

        Returns:
            UserProfile if found, None otherwise.
        """
        profile = self.storage.load(profile_id)

        if profile:
            logger.info(f"[ProfileManager] Loaded profile '{profile_id}'")
        else:
            logger.warning(f"[ProfileManager] Profile '{profile_id}' not found")

        return profile

    def save_profile(self, profile: UserProfile) -> None:
        """Save a profile.

        Args:
            profile: UserProfile to save.

        Raises:
            IOError: If save operation fails.
        """
        self.storage.save(profile)
        logger.info(f"[ProfileManager] Saved profile '{profile.id}'")

    def delete_profile(self, profile_id: str) -> bool:
        """Delete a profile.

        Args:
            profile_id: Profile identifier.

        Returns:
            True if deleted, False if not found.

        Raises:
            ValueError: If attempting to delete the active profile or default profile.
        """
        # Prevent deleting default profile
        if profile_id == "default":
            raise ValueError("Cannot delete the default profile")

        # Prevent deleting active profile
        if profile_id == self._active_profile_id:
            raise ValueError("Cannot delete the currently active profile. Switch to another profile first.")

        success = self.storage.delete(profile_id)

        if success:
            logger.info(f"[ProfileManager] Deleted profile '{profile_id}'")
        else:
            logger.warning(f"[ProfileManager] Profile '{profile_id}' not found for deletion")

        return success

    def list_profiles(self) -> List[str]:
        """List all profile IDs.

        Returns:
            List of profile IDs (sorted).
        """
        return self.storage.list_profiles()

    def get_profile_names(self) -> Dict[str, str]:
        """Get a mapping of profile IDs to names.

        Returns:
            Dictionary mapping profile_id -> profile_name.
        """
        profile_names = {}

        for profile_id in self.list_profiles():
            profile = self.load_profile(profile_id)
            if profile:
                profile_names[profile_id] = profile.name

        return profile_names

    def profile_exists(self, profile_id: str) -> bool:
        """Check if a profile exists.

        Args:
            profile_id: Profile identifier.

        Returns:
            True if profile exists, False otherwise.
        """
        return self.storage.exists(profile_id)

    def set_active_profile(self, profile_id: str) -> UserProfile:
        """Set the active profile.

        Args:
            profile_id: Profile identifier.

        Returns:
            The active UserProfile.

        Raises:
            ValueError: If profile doesn't exist.
        """
        profile = self.load_profile(profile_id)

        if not profile:
            raise ValueError(f"Profile '{profile_id}' not found")

        self._active_profile_id = profile_id
        self._active_profile = profile

        logger.info(f"[ProfileManager] Set active profile to '{profile_id}'")
        return profile

    def get_active_profile(self) -> UserProfile:
        """Get the current active profile.

        If no profile is active, loads the default profile.

        Returns:
            Active UserProfile.
        """
        if self._active_profile is None:
            # Load default profile
            self.set_active_profile("default")

        return self._active_profile

    def save_active_profile(self) -> None:
        """Save the currently active profile."""
        if self._active_profile:
            self.save_profile(self._active_profile)
        else:
            logger.warning("[ProfileManager] No active profile to save")

    def get_active_preferences(self) -> Dict[str, Any]:
        """Get preferences from active profile as a dict.

        This is for backward compatibility with code expecting dict-based prefs.

        Returns:
            Dictionary of preferences.
        """
        profile = self.get_active_profile()
        return profile.get_preferences_dict()

    def update_active_preferences(self, prefs_dict: Dict[str, Any]) -> None:
        """Update active profile preferences from a dict.

        Args:
            prefs_dict: Dictionary of preference key-value pairs.

        Raises:
            ValueError: If preferences are invalid.
        """
        profile = self.get_active_profile()
        profile.update_preferences(prefs_dict)
        self.save_active_profile()

        logger.info(f"[ProfileManager] Updated preferences for profile '{profile.id}'")

    def mark_active_profile_used(self) -> None:
        """Mark the active profile as used (for usage tracking)."""
        profile = self.get_active_profile()
        profile.mark_used()
        self.save_active_profile()

    def copy_profile(self, source_id: str, new_id: str, new_name: str) -> UserProfile:
        """Copy an existing profile to create a new one.

        Args:
            source_id: Source profile identifier.
            new_id: New profile identifier.
            new_name: Name for the new profile.

        Returns:
            New UserProfile.

        Raises:
            ValueError: If source doesn't exist or new ID already exists.
        """
        # Load source profile
        source = self.load_profile(source_id)
        if not source:
            raise ValueError(f"Source profile '{source_id}' not found")

        # Check new ID doesn't exist
        if self.storage.exists(new_id):
            raise ValueError(f"Profile '{new_id}' already exists")

        # Create new profile with source's preferences
        new_profile = self.create_profile(
            profile_id=new_id,
            name=new_name,
            preferences=source.preferences.to_dict()
        )

        logger.info(f"[ProfileManager] Copied profile '{source_id}' to '{new_id}'")
        return new_profile

    def export_profile(self, profile_id: str) -> Dict[str, Any]:
        """Export a profile as a dictionary (for import/export).

        Args:
            profile_id: Profile identifier.

        Returns:
            Profile dictionary.

        Raises:
            ValueError: If profile doesn't exist.
        """
        profile = self.load_profile(profile_id)
        if not profile:
            raise ValueError(f"Profile '{profile_id}' not found")

        return profile.to_dict()

    def import_profile(self, profile_dict: Dict[str, Any], new_id: Optional[str] = None) -> UserProfile:
        """Import a profile from a dictionary.

        Args:
            profile_dict: Profile dictionary (from export_profile).
            new_id: Optional new profile ID. If None, uses ID from dict.

        Returns:
            Imported UserProfile.

        Raises:
            ValueError: If profile ID already exists or data is invalid.
        """
        # Use provided ID or get from dict
        profile_id = new_id or profile_dict.get('id')
        if not profile_id:
            raise ValueError("Profile ID must be provided")

        # Check ID doesn't exist
        if self.storage.exists(profile_id):
            raise ValueError(f"Profile '{profile_id}' already exists")

        # Update ID if changed
        if new_id:
            profile_dict['id'] = new_id

        # Create profile from dict
        profile = UserProfile(**profile_dict)

        # Save
        self.storage.save(profile)

        logger.info(f"[ProfileManager] Imported profile '{profile_id}'")
        return profile
