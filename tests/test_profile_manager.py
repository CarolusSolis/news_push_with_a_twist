"""Tests for profile manager."""

import pytest
from pathlib import Path
import tempfile
import shutil

# Add app directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'app'))

from profile.models import UserProfile, Preferences
from profile.storage import JSONProfileStorage
from profile.manager import ProfileManager


class TestProfileManager:
    """Tests for ProfileManager class."""

    @pytest.fixture
    def temp_profiles_dir(self):
        """Create a temporary directory for test profiles."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def storage(self, temp_profiles_dir):
        """Create storage instance with temp directory."""
        return JSONProfileStorage(profiles_dir=temp_profiles_dir)

    @pytest.fixture
    def manager(self, storage):
        """Create ProfileManager instance with temp storage."""
        return ProfileManager(storage=storage)

    def test_manager_initialization(self, manager):
        """Test manager initializes correctly."""
        assert manager.storage is not None
        assert manager._active_profile is None

    def test_manager_creates_default_profile(self, manager):
        """Test manager auto-creates default profile."""
        # Check default profile was created
        assert manager.storage.exists("default")

        # Load it
        default = manager.storage.load("default")
        assert default.id == "default"
        assert default.name == "Default Profile"

    def test_create_profile(self, manager):
        """Test creating a new profile."""
        profile = manager.create_profile(
            profile_id="work",
            name="Work Profile",
            preferences={"mood": "serious", "time_budget": "deep"}
        )

        assert profile.id == "work"
        assert profile.name == "Work Profile"
        assert profile.preferences.mood == "serious"
        assert manager.storage.exists("work")

    def test_create_profile_duplicate_id(self, manager):
        """Test creating profile with existing ID raises error."""
        manager.create_profile("test", "Test")

        with pytest.raises(ValueError, match="already exists"):
            manager.create_profile("test", "Test 2")

    def test_create_profile_with_defaults(self, manager):
        """Test creating profile without preferences uses defaults."""
        profile = manager.create_profile("simple", "Simple Profile")

        assert profile.preferences.mood == "balanced"
        assert profile.preferences.time_budget == "quick"

    def test_load_profile(self, manager):
        """Test loading a profile."""
        manager.create_profile("test", "Test")

        loaded = manager.load_profile("test")

        assert loaded is not None
        assert loaded.id == "test"
        assert loaded.name == "Test"

    def test_load_nonexistent_profile(self, manager):
        """Test loading profile that doesn't exist."""
        loaded = manager.load_profile("nonexistent")
        assert loaded is None

    def test_save_profile(self, manager):
        """Test saving a profile."""
        profile = manager.create_profile("test", "Test")

        # Modify
        profile.preferences.mood = "playful"

        # Save
        manager.save_profile(profile)

        # Reload and verify
        reloaded = manager.load_profile("test")
        assert reloaded.preferences.mood == "playful"

    def test_delete_profile(self, manager):
        """Test deleting a profile."""
        manager.create_profile("deleteme", "Delete Me")
        assert manager.profile_exists("deleteme")

        success = manager.delete_profile("deleteme")

        assert success is True
        assert not manager.profile_exists("deleteme")

    def test_delete_default_profile_raises_error(self, manager):
        """Test deleting default profile is prevented."""
        with pytest.raises(ValueError, match="Cannot delete the default profile"):
            manager.delete_profile("default")

    def test_delete_active_profile_raises_error(self, manager):
        """Test deleting active profile is prevented."""
        manager.create_profile("active", "Active")
        manager.set_active_profile("active")

        with pytest.raises(ValueError, match="Cannot delete the currently active profile"):
            manager.delete_profile("active")

    def test_list_profiles(self, manager):
        """Test listing all profiles."""
        # Create additional profiles
        manager.create_profile("work", "Work")
        manager.create_profile("personal", "Personal")

        profiles = manager.list_profiles()

        assert len(profiles) == 3  # default + work + personal
        assert "default" in profiles
        assert "work" in profiles
        assert "personal" in profiles

    def test_get_profile_names(self, manager):
        """Test getting profile ID -> name mapping."""
        manager.create_profile("work", "Work Profile")
        manager.create_profile("personal", "Personal Profile")

        names = manager.get_profile_names()

        assert isinstance(names, dict)
        assert names["default"] == "Default Profile"
        assert names["work"] == "Work Profile"
        assert names["personal"] == "Personal Profile"

    def test_profile_exists(self, manager):
        """Test checking if profile exists."""
        assert manager.profile_exists("default")
        assert not manager.profile_exists("nonexistent")

        manager.create_profile("test", "Test")
        assert manager.profile_exists("test")

    def test_set_active_profile(self, manager):
        """Test setting active profile."""
        manager.create_profile("work", "Work")

        active = manager.set_active_profile("work")

        assert active.id == "work"
        assert manager._active_profile_id == "work"
        assert manager._active_profile == active

    def test_set_active_profile_nonexistent_raises_error(self, manager):
        """Test setting nonexistent profile as active raises error."""
        with pytest.raises(ValueError, match="not found"):
            manager.set_active_profile("nonexistent")

    def test_get_active_profile(self, manager):
        """Test getting active profile."""
        # Should auto-load default
        active = manager.get_active_profile()

        assert active.id == "default"
        assert manager._active_profile is not None

    def test_get_active_profile_loads_default(self, manager):
        """Test get_active_profile loads default if none active."""
        # Initially no active profile
        assert manager._active_profile is None

        # Get active loads default
        active = manager.get_active_profile()

        assert active.id == "default"
        assert manager._active_profile_id == "default"

    def test_save_active_profile(self, manager):
        """Test saving active profile."""
        manager.set_active_profile("default")

        # Modify active profile
        manager._active_profile.preferences.mood = "playful"

        # Save
        manager.save_active_profile()

        # Reload and verify
        reloaded = manager.load_profile("default")
        assert reloaded.preferences.mood == "playful"

    def test_get_active_preferences(self, manager):
        """Test getting active preferences as dict."""
        manager.set_active_profile("default")

        prefs_dict = manager.get_active_preferences()

        assert isinstance(prefs_dict, dict)
        assert 'mood' in prefs_dict
        assert 'time_budget' in prefs_dict

    def test_update_active_preferences(self, manager):
        """Test updating active preferences from dict."""
        manager.set_active_profile("default")

        manager.update_active_preferences({
            'mood': 'serious',
            'time_budget': 'deep'
        })

        # Verify changes
        prefs = manager.get_active_preferences()
        assert prefs['mood'] == "serious"
        assert prefs['time_budget'] == "deep"

        # Verify saved
        reloaded = manager.load_profile("default")
        assert reloaded.preferences.mood == "serious"

    def test_mark_active_profile_used(self, manager):
        """Test marking active profile as used."""
        manager.set_active_profile("default")

        original_count = manager._active_profile.metadata.use_count

        manager.mark_active_profile_used()

        assert manager._active_profile.metadata.use_count == original_count + 1

        # Verify saved
        reloaded = manager.load_profile("default")
        assert reloaded.metadata.use_count == original_count + 1

    def test_copy_profile(self, manager):
        """Test copying a profile."""
        # Create source
        manager.create_profile("source", "Source", {"mood": "playful"})

        # Copy
        copied = manager.copy_profile("source", "copy", "Copy Profile")

        assert copied.id == "copy"
        assert copied.name == "Copy Profile"
        assert copied.preferences.mood == "playful"
        assert manager.profile_exists("copy")

    def test_copy_nonexistent_profile_raises_error(self, manager):
        """Test copying nonexistent profile raises error."""
        with pytest.raises(ValueError, match="not found"):
            manager.copy_profile("nonexistent", "copy", "Copy")

    def test_copy_to_existing_id_raises_error(self, manager):
        """Test copying to existing ID raises error."""
        manager.create_profile("source", "Source")
        manager.create_profile("existing", "Existing")

        with pytest.raises(ValueError, match="already exists"):
            manager.copy_profile("source", "existing", "Copy")

    def test_export_profile(self, manager):
        """Test exporting profile as dict."""
        manager.create_profile("test", "Test", {"mood": "playful"})

        exported = manager.export_profile("test")

        assert isinstance(exported, dict)
        assert exported['id'] == "test"
        assert exported['name'] == "Test"
        assert exported['preferences']['mood'] == "playful"

    def test_export_nonexistent_profile_raises_error(self, manager):
        """Test exporting nonexistent profile raises error."""
        with pytest.raises(ValueError, match="not found"):
            manager.export_profile("nonexistent")

    def test_import_profile(self, manager):
        """Test importing profile from dict."""
        # Create and export a profile
        original = manager.create_profile("original", "Original", {"mood": "playful"})
        exported = manager.export_profile("original")

        # Import with new ID
        imported = manager.import_profile(exported, new_id="imported")

        assert imported.id == "imported"
        assert imported.name == "Original"
        assert imported.preferences.mood == "playful"
        assert manager.profile_exists("imported")

    def test_import_profile_to_existing_id_raises_error(self, manager):
        """Test importing to existing ID raises error."""
        original = manager.create_profile("test", "Test")
        exported = manager.export_profile("test")

        with pytest.raises(ValueError, match="already exists"):
            manager.import_profile(exported)

    def test_import_profile_without_id_raises_error(self, manager):
        """Test importing profile without ID raises error."""
        with pytest.raises(ValueError, match="Profile ID must be provided"):
            manager.import_profile({})


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
