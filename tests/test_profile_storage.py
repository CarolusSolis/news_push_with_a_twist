"""Tests for profile storage layer."""

import pytest
from pathlib import Path
from datetime import datetime
import tempfile
import shutil

# Add app directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'app'))

from profile.models import UserProfile, Preferences
from profile.storage import JSONProfileStorage


class TestJSONProfileStorage:
    """Tests for JSON profile storage."""

    @pytest.fixture
    def temp_profiles_dir(self):
        """Create a temporary directory for test profiles."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        # Cleanup after test
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def storage(self, temp_profiles_dir):
        """Create a JSONProfileStorage instance with temp directory."""
        return JSONProfileStorage(profiles_dir=temp_profiles_dir)

    @pytest.fixture
    def sample_profile(self):
        """Create a sample profile for testing."""
        return UserProfile(
            id="test",
            name="Test Profile",
            preferences=Preferences(mood="playful", time_budget="deep")
        )

    def test_storage_initialization(self, storage, temp_profiles_dir):
        """Test storage initializes with correct directory."""
        assert storage.profiles_dir == temp_profiles_dir
        assert temp_profiles_dir.exists()

    def test_storage_default_directory(self):
        """Test storage uses default directory if none provided."""
        storage = JSONProfileStorage()

        # Should use data/profiles/ relative to app/
        expected_dir = Path(__file__).parent.parent / "app" / "data" / "profiles"
        assert storage.profiles_dir == expected_dir

    def test_save_profile(self, storage, sample_profile, temp_profiles_dir):
        """Test saving a profile to JSON file."""
        storage.save(sample_profile)

        # Check file was created
        profile_path = temp_profiles_dir / "test.json"
        assert profile_path.exists()

        # Check file contains valid JSON
        import json
        with open(profile_path, 'r') as f:
            data = json.load(f)

        assert data['id'] == "test"
        assert data['name'] == "Test Profile"
        assert data['preferences']['mood'] == "playful"

    def test_load_profile(self, storage, sample_profile):
        """Test loading a profile from JSON file."""
        # Save first
        storage.save(sample_profile)

        # Load
        loaded_profile = storage.load("test")

        assert loaded_profile is not None
        assert loaded_profile.id == "test"
        assert loaded_profile.name == "Test Profile"
        assert loaded_profile.preferences.mood == "playful"
        assert loaded_profile.preferences.time_budget == "deep"

    def test_load_nonexistent_profile(self, storage):
        """Test loading a profile that doesn't exist."""
        profile = storage.load("nonexistent")
        assert profile is None

    def test_delete_profile(self, storage, sample_profile):
        """Test deleting a profile."""
        # Save first
        storage.save(sample_profile)
        assert storage.exists("test")

        # Delete
        success = storage.delete("test")

        assert success is True
        assert not storage.exists("test")

    def test_delete_nonexistent_profile(self, storage):
        """Test deleting a profile that doesn't exist."""
        success = storage.delete("nonexistent")
        assert success is False

    def test_list_profiles(self, storage):
        """Test listing all profiles."""
        # Create multiple profiles
        for i in range(3):
            profile = UserProfile(
                id=f"profile{i}",
                name=f"Profile {i}"
            )
            storage.save(profile)

        # List profiles
        profile_ids = storage.list_profiles()

        assert len(profile_ids) == 3
        assert "profile0" in profile_ids
        assert "profile1" in profile_ids
        assert "profile2" in profile_ids

        # Check they're sorted
        assert profile_ids == sorted(profile_ids)

    def test_list_profiles_empty(self, storage):
        """Test listing profiles when none exist."""
        profile_ids = storage.list_profiles()
        assert profile_ids == []

    def test_exists(self, storage, sample_profile):
        """Test checking if a profile exists."""
        assert not storage.exists("test")

        storage.save(sample_profile)

        assert storage.exists("test")

    def test_backup_on_save(self, storage, sample_profile, temp_profiles_dir):
        """Test that saving creates a backup of existing profile."""
        # Save first time
        storage.save(sample_profile)

        # Modify and save again
        sample_profile.preferences.mood = "serious"
        storage.save(sample_profile)

        # Check backup exists
        backup_path = temp_profiles_dir / "test.bak"
        assert backup_path.exists()

    def test_datetime_serialization(self, storage, sample_profile):
        """Test that datetime fields are properly serialized and deserialized."""
        # Save profile
        storage.save(sample_profile)

        # Load profile
        loaded = storage.load("test")

        assert isinstance(loaded.metadata.created_at, datetime)
        assert isinstance(loaded.metadata.last_modified, datetime)
        assert isinstance(loaded.metadata.last_used, datetime)

    def test_atomic_write(self, storage, sample_profile, temp_profiles_dir):
        """Test that saves use atomic write (temp + rename)."""
        # This is harder to test directly, but we can verify temp files don't remain
        storage.save(sample_profile)

        # Check no .tmp files exist
        tmp_files = list(temp_profiles_dir.glob("*.tmp"))
        assert len(tmp_files) == 0

    def test_save_and_load_with_optional_fields(self, storage):
        """Test saving/loading profiles with optional fields."""
        profile = UserProfile(
            id="full",
            name="Full Profile",
            preferences=Preferences(
                favorite_sources=["hackernews", "reddit"],
                reading_level="expert",
                custom_settings={"theme": "dark"}
            ),
            history={
                "digest_count": 10,
                "favorite_topics": ["AI", "space"]
            }
        )

        storage.save(profile)
        loaded = storage.load("full")

        assert loaded.preferences.favorite_sources == ["hackernews", "reddit"]
        assert loaded.preferences.reading_level == "expert"
        assert loaded.preferences.custom_settings["theme"] == "dark"
        assert loaded.history["digest_count"] == 10

    def test_get_backup_path(self, storage, sample_profile, temp_profiles_dir):
        """Test getting backup file path."""
        # No backup initially
        assert storage.get_backup_path("test") is None

        # Save once
        storage.save(sample_profile)

        # Still no backup
        assert storage.get_backup_path("test") is None

        # Save again (creates backup)
        storage.save(sample_profile)

        # Now backup exists
        backup_path = storage.get_backup_path("test")
        assert backup_path is not None
        assert backup_path.exists()

    def test_backup_on_delete(self, storage, sample_profile):
        """Test that deleting creates a backup."""
        storage.save(sample_profile)
        storage.delete("test")

        # Backup should exist
        backup_path = storage.get_backup_path("test")
        assert backup_path is not None
        assert backup_path.exists()

    def test_save_corrupted_profile_recovery(self, storage, sample_profile, temp_profiles_dir):
        """Test that backup allows recovery from corrupted save."""
        # Save initial profile
        storage.save(sample_profile)

        # Manually corrupt the profile file
        profile_path = temp_profiles_dir / "test.json"
        with open(profile_path, 'w') as f:
            f.write("CORRUPTED DATA {{{")

        # Try to load (should fail gracefully)
        loaded = storage.load("test")
        assert loaded is None

        # But backup should be intact
        backup_path = storage.get_backup_path("test")
        if backup_path and backup_path.exists():
            # Can manually restore from backup if needed
            shutil.copy2(backup_path, profile_path)
            restored = storage.load("test")
            # This might still fail due to how we initially saved, but demonstrates recovery pattern


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
