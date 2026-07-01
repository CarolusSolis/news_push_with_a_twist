"""Tests for profile data models."""

import pytest
from pathlib import Path
from datetime import datetime
from pydantic import ValidationError

# Add app directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'app'))

from profile.models import Preferences, ProfileMetadata, UserProfile


class TestPreferences:
    """Tests for Preferences model."""

    def test_preferences_default_creation(self):
        """Test creating preferences with defaults."""
        prefs = Preferences()

        assert prefs.mood == "balanced"
        assert prefs.time_budget == "quick"
        assert prefs.include_deep_dive is True
        assert prefs.include_quotes is True
        assert prefs.use_live_data is True
        assert prefs.voiceover_voice == "alloy"
        assert prefs.reading_level == "intermediate"

    def test_preferences_custom_values(self):
        """Test creating preferences with custom values."""
        prefs = Preferences(
            learn_about="quantum physics, machine learning",
            fun_learning="ancient civilizations, astronomy",
            mood="playful",
            time_budget="deep",
            voiceover_voice="nova"
        )

        assert prefs.learn_about == "quantum physics, machine learning"
        assert prefs.fun_learning == "ancient civilizations, astronomy"
        assert prefs.mood == "playful"
        assert prefs.time_budget == "deep"
        assert prefs.voiceover_voice == "nova"

    def test_preferences_validation_mood(self):
        """Test mood validation."""
        # Valid values
        for mood in ["serious", "balanced", "playful"]:
            prefs = Preferences(mood=mood)
            assert prefs.mood == mood

        # Invalid value
        with pytest.raises(ValidationError):
            Preferences(mood="invalid")

    def test_preferences_validation_time_budget(self):
        """Test time_budget validation."""
        # Valid values
        for budget in ["quick", "standard", "deep"]:
            prefs = Preferences(time_budget=budget)
            assert prefs.time_budget == budget

        # Invalid value
        with pytest.raises(ValidationError):
            Preferences(time_budget="invalid")

    def test_preferences_validation_voice(self):
        """Test voiceover_voice validation."""
        # Valid values
        for voice in ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]:
            prefs = Preferences(voiceover_voice=voice)
            assert prefs.voiceover_voice == voice

        # Invalid value
        with pytest.raises(ValidationError):
            Preferences(voiceover_voice="invalid")

    def test_preferences_validation_empty_strings(self):
        """Test validation of empty preference strings."""
        # Empty strings fail min_length=3 constraint
        with pytest.raises(ValidationError):
            Preferences(learn_about="   ")

        with pytest.raises(ValidationError):
            Preferences(fun_learning="")

    def test_preferences_validation_string_length(self):
        """Test string length validation."""
        # Too short
        with pytest.raises(ValidationError):
            Preferences(learn_about="AI")

        # Too long
        with pytest.raises(ValidationError):
            Preferences(learn_about="x" * 501)

    def test_preferences_to_dict(self):
        """Test converting preferences to dict."""
        prefs = Preferences(
            learn_about="AI technology",
            mood="serious"
        )

        prefs_dict = prefs.to_dict()

        assert isinstance(prefs_dict, dict)
        assert prefs_dict['learn_about'] == "AI technology"
        assert prefs_dict['mood'] == "serious"
        assert 'time_budget' in prefs_dict

    def test_preferences_custom_settings(self):
        """Test extensible custom_settings field."""
        prefs = Preferences(
            custom_settings={"theme": "dark", "font_size": 14}
        )

        assert prefs.custom_settings["theme"] == "dark"
        assert prefs.custom_settings["font_size"] == 14

    def test_preferences_favorite_sources(self):
        """Test favorite_sources field."""
        prefs = Preferences(
            favorite_sources=["hackernews", "reddit"]
        )

        assert prefs.favorite_sources == ["hackernews", "reddit"]


class TestProfileMetadata:
    """Tests for ProfileMetadata model."""

    def test_metadata_default_creation(self):
        """Test creating metadata with defaults."""
        metadata = ProfileMetadata()

        assert isinstance(metadata.created_at, datetime)
        assert isinstance(metadata.last_modified, datetime)
        assert isinstance(metadata.last_used, datetime)
        assert metadata.use_count == 0
        assert metadata.version == "1.0.0"

    def test_metadata_touch_method(self):
        """Test touch() method updates last_used and use_count."""
        metadata = ProfileMetadata()

        original_last_used = metadata.last_used
        original_count = metadata.use_count

        # Wait a tiny bit to ensure timestamp changes
        import time
        time.sleep(0.01)

        metadata.touch()

        assert metadata.last_used > original_last_used
        assert metadata.use_count == original_count + 1

    def test_metadata_mark_modified_method(self):
        """Test mark_modified() method updates last_modified."""
        metadata = ProfileMetadata()

        original_last_modified = metadata.last_modified

        # Wait a tiny bit to ensure timestamp changes
        import time
        time.sleep(0.01)

        metadata.mark_modified()

        assert metadata.last_modified > original_last_modified

    def test_metadata_use_count_validation(self):
        """Test use_count cannot be negative."""
        with pytest.raises(ValidationError):
            ProfileMetadata(use_count=-1)


class TestUserProfile:
    """Tests for UserProfile model."""

    def test_profile_default_creation(self):
        """Test creating a profile with create_default()."""
        profile = UserProfile.create_default()

        assert profile.id == "default"
        assert profile.name == "Default Profile"
        assert isinstance(profile.preferences, Preferences)
        assert isinstance(profile.metadata, ProfileMetadata)
        assert profile.history is None

    def test_profile_custom_creation(self):
        """Test creating a profile with custom values."""
        prefs = Preferences(mood="playful")

        profile = UserProfile(
            id="work",
            name="Work Profile",
            preferences=prefs
        )

        assert profile.id == "work"
        assert profile.name == "Work Profile"
        assert profile.preferences.mood == "playful"

    def test_profile_id_validation_lowercase(self):
        """Test profile ID must be lowercase."""
        # Pattern constraint rejects uppercase
        with pytest.raises(ValidationError):
            UserProfile(
                id="WorkProfile",
                name="Work"
            )

    def test_profile_id_validation_pattern(self):
        """Test profile ID pattern validation."""
        # Valid IDs
        for profile_id in ["work", "personal", "work-profile", "profile_1"]:
            profile = UserProfile(id=profile_id, name="Test")
            assert profile.id == profile_id

        # Invalid IDs (uppercase, spaces, special chars)
        with pytest.raises(ValidationError):
            UserProfile(id="Work Profile", name="Test")

        with pytest.raises(ValidationError):
            UserProfile(id="work@home", name="Test")

    def test_profile_to_dict(self):
        """Test converting profile to dict."""
        profile = UserProfile.create_default()
        profile_dict = profile.to_dict()

        assert isinstance(profile_dict, dict)
        assert profile_dict['id'] == "default"
        assert profile_dict['name'] == "Default Profile"
        assert 'preferences' in profile_dict
        assert 'metadata' in profile_dict

    def test_profile_get_preferences_dict(self):
        """Test get_preferences_dict() for backward compatibility."""
        profile = UserProfile.create_default()
        prefs_dict = profile.get_preferences_dict()

        assert isinstance(prefs_dict, dict)
        assert 'mood' in prefs_dict
        assert 'time_budget' in prefs_dict
        assert prefs_dict['mood'] == "balanced"

    def test_profile_update_preferences(self):
        """Test update_preferences() method."""
        profile = UserProfile.create_default()

        original_modified = profile.metadata.last_modified

        # Wait a bit to ensure timestamp changes
        import time
        time.sleep(0.01)

        # Update preferences
        profile.update_preferences({
            'mood': 'serious',
            'time_budget': 'deep'
        })

        assert profile.preferences.mood == "serious"
        assert profile.preferences.time_budget == "deep"
        assert profile.metadata.last_modified > original_modified

    def test_profile_update_preferences_validation(self):
        """Test update_preferences() validates input."""
        profile = UserProfile.create_default()

        with pytest.raises(ValidationError):
            profile.update_preferences({'mood': 'invalid_mood'})

    def test_profile_mark_used(self):
        """Test mark_used() method."""
        profile = UserProfile.create_default()

        original_count = profile.metadata.use_count
        original_last_used = profile.metadata.last_used

        # Wait a bit to ensure timestamp changes
        import time
        time.sleep(0.01)

        profile.mark_used()

        assert profile.metadata.use_count == original_count + 1
        assert profile.metadata.last_used > original_last_used

    def test_profile_with_history(self):
        """Test profile with history tracking."""
        profile = UserProfile(
            id="test",
            name="Test Profile",
            history={
                "digest_count": 42,
                "favorite_topics": ["AI", "space"],
                "last_digest_date": "2025-10-13"
            }
        )

        assert profile.history["digest_count"] == 42
        assert "AI" in profile.history["favorite_topics"]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
