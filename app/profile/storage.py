"""Profile storage layer with file-based implementation.

This module provides an abstract storage interface and a JSON file-based
implementation for persisting user profiles.
"""

import json
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
import shutil

from .models import UserProfile

logger = logging.getLogger(__name__)


class ProfileStorage(ABC):
    """Abstract base class for profile storage.

    This interface allows swapping storage backends (JSON, SQLite, PostgreSQL)
    without changing the ProfileManager code.
    """

    @abstractmethod
    def save(self, profile: UserProfile) -> None:
        """Save a profile.

        Args:
            profile: UserProfile to save.

        Raises:
            IOError: If save operation fails.
        """
        pass

    @abstractmethod
    def load(self, profile_id: str) -> Optional[UserProfile]:
        """Load a profile by ID.

        Args:
            profile_id: Profile identifier.

        Returns:
            UserProfile if found, None otherwise.
        """
        pass

    @abstractmethod
    def delete(self, profile_id: str) -> bool:
        """Delete a profile.

        Args:
            profile_id: Profile identifier.

        Returns:
            True if deleted, False if not found.
        """
        pass

    @abstractmethod
    def list_profiles(self) -> List[str]:
        """List all profile IDs.

        Returns:
            List of profile IDs.
        """
        pass

    @abstractmethod
    def exists(self, profile_id: str) -> bool:
        """Check if a profile exists.

        Args:
            profile_id: Profile identifier.

        Returns:
            True if profile exists, False otherwise.
        """
        pass


class JSONProfileStorage(ProfileStorage):
    """JSON file-based profile storage implementation.

    Profiles are stored as individual JSON files in a profiles directory:
        data/profiles/default.json
        data/profiles/work.json
        data/profiles/personal.json

    Features:
    - Automatic backup on save
    - Pretty-printed JSON for readability
    - Atomic writes (write to temp, then rename)
    """

    def __init__(self, profiles_dir: Optional[Path] = None):
        """Initialize JSON profile storage.

        Args:
            profiles_dir: Directory for profile files (default: data/profiles/)
        """
        if profiles_dir is None:
            # Default to data/profiles/ relative to this file's parent
            self.profiles_dir = Path(__file__).parent.parent / "data" / "profiles"
        else:
            self.profiles_dir = Path(profiles_dir)

        # Create profiles directory if it doesn't exist
        self.profiles_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"[ProfileStorage] Initialized with directory: {self.profiles_dir}")

    def _get_profile_path(self, profile_id: str) -> Path:
        """Get the file path for a profile.

        Args:
            profile_id: Profile identifier.

        Returns:
            Path to the profile JSON file.
        """
        return self.profiles_dir / f"{profile_id}.json"

    def _backup_profile(self, profile_id: str) -> None:
        """Create a backup of an existing profile.

        Args:
            profile_id: Profile identifier.
        """
        profile_path = self._get_profile_path(profile_id)
        if profile_path.exists():
            backup_path = self.profiles_dir / f"{profile_id}.bak"
            shutil.copy2(profile_path, backup_path)
            logger.debug(f"[ProfileStorage] Backed up profile '{profile_id}' to {backup_path}")

    def save(self, profile: UserProfile) -> None:
        """Save a profile to JSON file.

        Creates a backup of the existing file before overwriting.
        Uses atomic write (temp file + rename) for safety.

        Args:
            profile: UserProfile to save.

        Raises:
            IOError: If save operation fails.
        """
        try:
            # Backup existing profile
            if self.exists(profile.id):
                self._backup_profile(profile.id)

            # Convert profile to dict with datetime serialization
            profile_dict = profile.model_dump()

            # Serialize datetimes to ISO format
            if "metadata" in profile_dict:
                for key in ["created_at", "last_modified", "last_used"]:
                    if key in profile_dict["metadata"]:
                        dt = profile_dict["metadata"][key]
                        if isinstance(dt, datetime):
                            profile_dict["metadata"][key] = dt.isoformat()

            # Write to temporary file first (atomic write)
            profile_path = self._get_profile_path(profile.id)
            temp_path = profile_path.with_suffix('.tmp')

            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(profile_dict, f, indent=2, ensure_ascii=False)

            # Atomic rename
            temp_path.replace(profile_path)

            logger.info(f"[ProfileStorage] Saved profile '{profile.id}' to {profile_path}")

        except Exception as e:
            logger.error(f"[ProfileStorage] Failed to save profile '{profile.id}': {e}")
            raise IOError(f"Failed to save profile: {e}")

    def load(self, profile_id: str) -> Optional[UserProfile]:
        """Load a profile from JSON file.

        Args:
            profile_id: Profile identifier.

        Returns:
            UserProfile if found, None otherwise.
        """
        profile_path = self._get_profile_path(profile_id)

        if not profile_path.exists():
            logger.debug(f"[ProfileStorage] Profile '{profile_id}' not found at {profile_path}")
            return None

        try:
            with open(profile_path, 'r', encoding='utf-8') as f:
                profile_dict = json.load(f)

            # Parse datetime fields
            if "metadata" in profile_dict:
                for key in ["created_at", "last_modified", "last_used"]:
                    if key in profile_dict["metadata"]:
                        dt_str = profile_dict["metadata"][key]
                        if isinstance(dt_str, str):
                            profile_dict["metadata"][key] = datetime.fromisoformat(dt_str)

            # Create UserProfile from dict
            profile = UserProfile(**profile_dict)

            logger.info(f"[ProfileStorage] Loaded profile '{profile_id}' from {profile_path}")
            return profile

        except Exception as e:
            logger.error(f"[ProfileStorage] Failed to load profile '{profile_id}': {e}")
            return None

    def delete(self, profile_id: str) -> bool:
        """Delete a profile file.

        Args:
            profile_id: Profile identifier.

        Returns:
            True if deleted, False if not found.
        """
        profile_path = self._get_profile_path(profile_id)

        if not profile_path.exists():
            logger.debug(f"[ProfileStorage] Profile '{profile_id}' not found for deletion")
            return False

        try:
            # Backup before deletion
            self._backup_profile(profile_id)

            # Delete the file
            profile_path.unlink()

            logger.info(f"[ProfileStorage] Deleted profile '{profile_id}'")
            return True

        except Exception as e:
            logger.error(f"[ProfileStorage] Failed to delete profile '{profile_id}': {e}")
            return False

    def list_profiles(self) -> List[str]:
        """List all profile IDs.

        Returns:
            List of profile IDs (sorted alphabetically).
        """
        try:
            profile_files = self.profiles_dir.glob("*.json")
            profile_ids = [f.stem for f in profile_files if f.is_file()]
            return sorted(profile_ids)

        except Exception as e:
            logger.error(f"[ProfileStorage] Failed to list profiles: {e}")
            return []

    def exists(self, profile_id: str) -> bool:
        """Check if a profile exists.

        Args:
            profile_id: Profile identifier.

        Returns:
            True if profile exists, False otherwise.
        """
        return self._get_profile_path(profile_id).exists()

    def get_backup_path(self, profile_id: str) -> Optional[Path]:
        """Get the backup file path for a profile.

        Args:
            profile_id: Profile identifier.

        Returns:
            Path to backup file if it exists, None otherwise.
        """
        backup_path = self.profiles_dir / f"{profile_id}.bak"
        return backup_path if backup_path.exists() else None
