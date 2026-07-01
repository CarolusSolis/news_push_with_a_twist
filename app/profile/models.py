"""Pydantic models for user profiles and preferences.

This module defines type-safe, validated data models for the profile system.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional, Literal
from pydantic import BaseModel, Field, field_validator


class Preferences(BaseModel):
    """User preferences for digest generation.

    This model defines all customizable aspects of the digest experience,
    with validation to ensure values are valid.
    """

    # Content preferences
    learn_about: str = Field(
        default="AI advancements, startup trends, emerging technologies",
        description="Topics the user wants to learn about (need-to-know)",
        min_length=3,
        max_length=500
    )

    fun_learning: str = Field(
        default="historical mysteries, space exploration, interesting science facts",
        description="Topics the user enjoys learning about (nice-to-know)",
        min_length=3,
        max_length=500
    )

    # Experience preferences
    mood: Literal["serious", "balanced", "playful"] = Field(
        default="balanced",
        description="Tone and style of the digest"
    )

    time_budget: Literal["quick", "standard", "deep"] = Field(
        default="quick",
        description="How much time user has for reading"
    )

    # Section toggles
    include_deep_dive: bool = Field(
        default=True,
        description="Include in-depth analysis section"
    )

    include_quotes: bool = Field(
        default=True,
        description="Include inspirational quotes"
    )

    # Data source preferences
    use_live_data: bool = Field(
        default=True,
        description="Use real-time data sources vs static samples"
    )

    favorite_sources: Optional[List[str]] = Field(
        default=None,
        description="Preferred news sources (e.g., ['hackernews', 'reddit'])"
    )

    # Voiceover preferences
    voiceover_voice: Literal["alloy", "echo", "fable", "onyx", "nova", "shimmer"] = Field(
        default="alloy",
        description="Voice for AI-generated voiceover"
    )

    # Future extensibility
    reading_level: Optional[Literal["beginner", "intermediate", "expert"]] = Field(
        default="intermediate",
        description="Content complexity level"
    )

    custom_settings: Dict[str, Any] = Field(
        default_factory=dict,
        description="Extensible field for future custom settings"
    )

    @field_validator('learn_about', 'fun_learning')
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        """Ensure preference strings are not empty after stripping."""
        if not v.strip():
            raise ValueError("Preference cannot be empty")
        return v.strip()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to plain dict for backward compatibility.

        Returns:
            Dictionary representation of preferences.
        """
        return self.model_dump()


class ProfileMetadata(BaseModel):
    """Metadata about profile usage and lifecycle.

    Tracks when profile was created, modified, and used.
    """

    created_at: datetime = Field(
        default_factory=datetime.now,
        description="When the profile was created"
    )

    last_modified: datetime = Field(
        default_factory=datetime.now,
        description="When preferences were last updated"
    )

    last_used: datetime = Field(
        default_factory=datetime.now,
        description="When profile was last used to generate a digest"
    )

    use_count: int = Field(
        default=0,
        description="Number of times this profile was used",
        ge=0
    )

    version: str = Field(
        default="1.0.0",
        description="Profile schema version for migrations"
    )

    def touch(self) -> None:
        """Update last_used timestamp and increment use_count."""
        self.last_used = datetime.now()
        self.use_count += 1

    def mark_modified(self) -> None:
        """Update last_modified timestamp."""
        self.last_modified = datetime.now()


class UserProfile(BaseModel):
    """Complete user profile with preferences and metadata.

    This is the main model for a user profile, combining preferences
    with metadata and future extensibility for history tracking.
    """

    id: str = Field(
        description="Unique profile identifier (e.g., 'default', 'work', 'personal')",
        pattern=r'^[a-z0-9_-]+$',
        min_length=1,
        max_length=50
    )

    name: str = Field(
        description="Human-readable profile name",
        min_length=1,
        max_length=100
    )

    preferences: Preferences = Field(
        default_factory=Preferences,
        description="User preferences for digest generation"
    )

    metadata: ProfileMetadata = Field(
        default_factory=ProfileMetadata,
        description="Profile lifecycle and usage metadata"
    )

    # Future extensibility: history tracking
    history: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional history tracking (digest count, favorite topics, etc.)"
    )

    @field_validator('id')
    @classmethod
    def validate_id_format(cls, v: str) -> str:
        """Ensure profile ID follows naming conventions."""
        if not v.islower():
            raise ValueError("Profile ID must be lowercase")
        return v

    def to_dict(self) -> Dict[str, Any]:
        """Convert to plain dict for backward compatibility.

        Returns:
            Dictionary representation of the entire profile.
        """
        return self.model_dump()

    def get_preferences_dict(self) -> Dict[str, Any]:
        """Get just the preferences as a dict.

        This is for backward compatibility with existing code that
        expects preferences as a simple dict.

        Returns:
            Dictionary of preferences only.
        """
        return self.preferences.to_dict()

    def update_preferences(self, prefs_dict: Dict[str, Any]) -> None:
        """Update preferences from a dict.

        Args:
            prefs_dict: Dictionary of preference key-value pairs.

        Raises:
            ValueError: If preferences are invalid.
        """
        # Update existing preferences
        current_prefs = self.preferences.to_dict()
        current_prefs.update(prefs_dict)

        # Validate and create new Preferences object
        self.preferences = Preferences(**current_prefs)

        # Mark as modified
        self.metadata.mark_modified()

    def mark_used(self) -> None:
        """Mark profile as used (updates last_used, increments use_count)."""
        self.metadata.touch()

    @classmethod
    def create_default(cls, profile_id: str = "default") -> "UserProfile":
        """Create a default profile with standard preferences.

        Args:
            profile_id: Profile identifier (default: "default")

        Returns:
            UserProfile with default settings.
        """
        return cls(
            id=profile_id,
            name="Default Profile",
            preferences=Preferences(),
            metadata=ProfileMetadata()
        )

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
