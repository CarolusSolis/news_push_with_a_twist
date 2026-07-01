# app/profile/CLAUDE.md

User profile and preference management system documentation.

## Overview

The profile system provides **persistent, type-safe user preferences** with support for multiple profiles. It enables users to save, switch, and manage different preference configurations (e.g., work, personal, casual) while maintaining backward compatibility with the existing dict-based code.

**Key Features:**
- ✅ Pydantic v2 models with validation
- ✅ JSON file storage with atomic writes
- ✅ Automatic backups before overwrites
- ✅ Multiple switchable profiles
- ✅ Protected default profile (cannot delete)
- ✅ Usage tracking (timestamps, counts)
- ✅ Backward compatible with dict-based code
- ✅ Extensible for future features

## Architecture

```
User Interface → ProfileManager → ProfileStorage (ABC)
                        ↓              ↓
                   UserProfile    JSONProfileStorage
                        ↓              ↓
                  Preferences    JSON Files (.json)
```

**Design Principles:**
1. **Type Safety**: Pydantic models validate all inputs
2. **Single Responsibility**: Clear separation between models, storage, and management
3. **Abstraction**: Storage layer is swappable (JSON now, SQLite/PostgreSQL later)
4. **Data Integrity**: Atomic writes and automatic backups prevent corruption
5. **Backward Compatibility**: `to_dict()` methods for existing code

## Core Files

```
profile/
├── CLAUDE.md         # This file
├── __init__.py       # Exports: Preferences, UserProfile, ProfileMetadata, ProfileManager
├── models.py         # Pydantic models (Preferences, UserProfile, ProfileMetadata)
├── storage.py        # Abstract storage + JSON implementation
└── manager.py        # High-level CRUD operations, active profile management
```

## Data Models (models.py)

### Preferences

User preferences for digest generation with Pydantic validation:

```python
from profile import Preferences

# Create with defaults
prefs = Preferences()

# Create with custom values
prefs = Preferences(
    learn_about="quantum computing, space exploration",
    fun_learning="historical mysteries, ancient civilizations",
    mood="playful",
    time_budget="deep",
    voiceover_voice="nova",
    favorite_sources=["hackernews", "reddit"],
    reading_level="expert"
)

# Convert to dict (backward compatibility)
prefs_dict = prefs.to_dict()

# Fields with validation
prefs.mood            # Literal["serious", "balanced", "playful"]
prefs.time_budget     # Literal["quick", "standard", "deep"]
prefs.voiceover_voice # Literal["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
```

**Field Reference:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `learn_about` | str | "AI advancements..." | Need-to-know topics (3-500 chars) |
| `fun_learning` | str | "historical mysteries..." | Nice-to-know topics (3-500 chars) |
| `mood` | Literal | "balanced" | Tone: serious/balanced/playful |
| `time_budget` | Literal | "quick" | Reading time: quick/standard/deep |
| `include_deep_dive` | bool | True | Include analysis section |
| `include_quotes` | bool | True | Include quote section |
| `use_live_data` | bool | True | Use real-time vs static data |
| `favorite_sources` | List[str] \| None | None | Preferred sources (e.g., ['hackernews']) |
| `reading_level` | Literal \| None | "intermediate" | beginner/intermediate/expert |
| `voiceover_voice` | Literal | "alloy" | TTS voice selection |
| `custom_settings` | dict | {} | Extensible custom settings |

### ProfileMetadata

Tracks profile lifecycle and usage:

```python
from profile import ProfileMetadata

metadata = ProfileMetadata()
print(f"Created: {metadata.created_at}")
print(f"Use count: {metadata.use_count}")

# Update timestamps
metadata.touch()              # Increments use_count, updates last_used
metadata.mark_modified()      # Updates last_modified
```

**Fields:**
- `created_at`: datetime - When profile was created
- `last_modified`: datetime - When preferences were last updated
- `last_used`: datetime - When profile was last used for digest
- `use_count`: int - Number of times profile was used
- `version`: str - Schema version (for migrations)

### UserProfile

Complete user profile combining preferences and metadata:

```python
from profile import UserProfile, Preferences

# Create default profile
profile = UserProfile.create_default()

# Create custom profile
profile = UserProfile(
    id="work",
    name="Work Profile",
    preferences=Preferences(mood="serious", time_budget="quick"),
    history={"digest_count": 42, "favorite_topics": ["AI", "startups"]}
)

# Update preferences (validates input)
profile.update_preferences({"mood": "playful", "time_budget": "deep"})

# Mark profile as used
profile.mark_used()

# Convert to dict
profile_dict = profile.to_dict()

# Get preferences dict only
prefs_dict = profile.get_preferences_dict()
```

**Validation Rules:**
- `id`: Lowercase alphanumeric + hyphens/underscores, 1-50 chars (regex: `^[a-z0-9_-]+$`)
- `name`: 1-100 chars
- All Preferences fields validated per Preferences model

## Storage Layer (storage.py)

### Abstract Interface

```python
from profile.storage import ProfileStorage

class ProfileStorage(ABC):
    """Abstract base class for profile storage."""

    def save(self, profile: UserProfile) -> None: ...
    def load(self, profile_id: str) -> Optional[UserProfile]: ...
    def delete(self, profile_id: str) -> bool: ...
    def list_profiles(self) -> List[str]: ...
    def exists(self, profile_id: str) -> bool: ...
```

### JSON Storage

Default implementation using JSON files:

```python
from profile.storage import JSONProfileStorage

# Use default directory (app/data/profiles/)
storage = JSONProfileStorage()

# Use custom directory
storage = JSONProfileStorage(profiles_dir=Path("/custom/path"))

# Save profile (atomic write + backup)
storage.save(profile)

# Load profile
profile = storage.load("work")  # Returns None if not found

# Delete profile (creates .bak backup)
success = storage.delete("work")

# List all profiles
profile_ids = storage.list_profiles()  # ['default', 'work', 'personal']

# Check existence
if storage.exists("work"):
    profile = storage.load("work")

# Get backup path (if exists)
backup_path = storage.get_backup_path("work")
```

**Storage Location:**
- Default: `app/data/profiles/`
- Format: `{profile_id}.json`
- Backups: `{profile_id}.bak`
- Ignored by git (see `app/data/profiles/.gitignore`)

**Atomic Write Process:**
1. Write to temporary file (`{profile_id}.tmp`)
2. Rename to actual file (atomic operation)
3. Ensures no corruption on write failure

**Datetime Serialization:**
- ISO format strings in JSON
- Automatically converted back to datetime on load

## ProfileManager (manager.py)

High-level API for profile operations and active profile management:

```python
from profile import ProfileManager

# Initialize (auto-creates default profile)
manager = ProfileManager()

# Or with custom storage
manager = ProfileManager(storage=custom_storage)
```

### CRUD Operations

```python
# Create profile
profile = manager.create_profile(
    profile_id="work",
    name="Work Profile",
    preferences={"mood": "serious", "time_budget": "quick"}
)

# Load profile
profile = manager.load_profile("work")  # Returns None if not found

# Save profile
manager.save_profile(profile)

# Delete profile
success = manager.delete_profile("work")  # Raises if default or active

# List all profiles
profile_ids = manager.list_profiles()  # ['default', 'work', 'personal']

# Get profile names
names = manager.get_profile_names()  # {'default': 'Default Profile', 'work': 'Work Profile'}

# Check existence
if manager.profile_exists("work"):
    profile = manager.load_profile("work")
```

### Active Profile Management

```python
# Get active profile (auto-loads 'default' if none set)
active = manager.get_active_profile()

# Set active profile
manager.set_active_profile("work")

# Get active preferences as dict
prefs_dict = manager.get_active_preferences()

# Update active preferences
manager.update_active_preferences({
    "mood": "playful",
    "time_budget": "deep"
})

# Save active profile
manager.save_active_profile()

# Mark active profile as used
manager.mark_active_profile_used()
```

### Advanced Operations

```python
# Copy profile
copied = manager.copy_profile(
    source_id="work",
    new_id="work-backup",
    new_name="Work Backup"
)

# Export profile to dict
exported = manager.export_profile("work")

# Import profile from dict
imported = manager.import_profile(
    profile_data=exported,
    new_id="work-imported"
)
```

### Protected Profiles

```python
# Cannot delete default profile
try:
    manager.delete_profile("default")
except ValueError as e:
    print(e)  # "Cannot delete the default profile"

# Cannot delete active profile
manager.set_active_profile("work")
try:
    manager.delete_profile("work")
except ValueError as e:
    print(e)  # "Cannot delete the currently active profile"
```

## Usage Examples

### Basic Usage

```python
from profile import ProfileManager

# Initialize
manager = ProfileManager()

# Get active profile
profile = manager.get_active_profile()
print(f"Active: {profile.name}")
print(f"Mood: {profile.preferences.mood}")

# Update preferences
manager.update_active_preferences({
    "mood": "serious",
    "time_budget": "deep",
    "learn_about": "quantum computing, AI safety"
})

# Mark as used (tracks usage)
manager.mark_active_profile_used()
```

### Multiple Profiles

```python
# Create work profile
work = manager.create_profile(
    "work",
    "Work Profile",
    {"mood": "serious", "time_budget": "quick", "include_quotes": False}
)

# Create personal profile
personal = manager.create_profile(
    "personal",
    "Personal Profile",
    {"mood": "playful", "time_budget": "deep", "fun_learning": "space, mythology"}
)

# Switch between profiles
manager.set_active_profile("work")
print(manager.get_active_profile().name)  # "Work Profile"

manager.set_active_profile("personal")
print(manager.get_active_profile().name)  # "Personal Profile"
```

### Backward Compatibility

```python
# Existing code expects dict - no changes needed!
prefs_dict = manager.get_active_preferences()

# Pass to existing functions
digest_sections = generate_digest_with_agent(prefs_dict)

# Update from dict
manager.update_active_preferences(prefs_dict)
```

## Integration Guide

### Streamlit App Integration (app/app.py)

**Step 1: Initialize ProfileManager**

```python
import streamlit as st
from profile import ProfileManager

# Initialize in session state
if 'profile_manager' not in st.session_state:
    st.session_state.profile_manager = ProfileManager()
```

**Step 2: Profile Selector in Sidebar**

```python
# Get available profiles
profiles = st.session_state.profile_manager.list_profiles()
profile_names = st.session_state.profile_manager.get_profile_names()

# Dropdown selector
current_profile = st.session_state.profile_manager.get_active_profile()
selected = st.selectbox(
    "Profile",
    options=profiles,
    format_func=lambda x: profile_names[x],
    index=profiles.index(current_profile.id) if current_profile.id in profiles else 0
)

# Switch if changed
if selected != current_profile.id:
    st.session_state.profile_manager.set_active_profile(selected)
    st.rerun()
```

**Step 3: Create New Profile UI**

```python
with st.expander("➕ Create New Profile"):
    new_id = st.text_input("Profile ID (lowercase, no spaces)")
    new_name = st.text_input("Profile Name")

    if st.button("Create"):
        try:
            manager = st.session_state.profile_manager
            manager.create_profile(new_id, new_name)
            st.success(f"Created profile: {new_name}")
            st.rerun()
        except ValueError as e:
            st.error(str(e))
```

**Step 4: Use Profile Preferences**

```python
# Get preferences dict (backward compatible)
manager = st.session_state.profile_manager
prefs = manager.get_active_preferences()

# Use in digest generation
digest_sections = generate_digest_with_agent(prefs)

# Mark profile as used
manager.mark_active_profile_used()
```

**Step 5: Update Preferences**

```python
# When user changes preferences in UI
manager = st.session_state.profile_manager
manager.update_active_preferences({
    'mood': mood_selection,
    'time_budget': time_budget_selection,
    'learn_about': learn_about_text
})
```

### Service Integration (app/services.py)

No changes needed! Services already accept `preferences: dict`:

```python
class DigestService:
    def generate_digest(self, preferences: dict) -> List[dict]:
        # Works with both old dict and new profile.get_preferences_dict()
        return generate_digest_with_agent(preferences)
```

## Testing

### Unit Tests

See `tests/test_profile_models.py`, `tests/test_profile_storage.py`, `tests/test_profile_manager.py`:

```bash
# Run all profile tests
pytest tests/test_profile_*.py -v

# Run specific test class
pytest tests/test_profile_manager.py::TestProfileManager -v

# Run with coverage
pytest tests/test_profile_*.py --cov=app/profile --cov-report=html
```

**Test Coverage:**
- 71 tests across models, storage, and manager
- Models: Validation, field constraints, type checking
- Storage: JSON serialization, backups, atomic writes
- Manager: CRUD operations, active profile, protected profiles

### Integration Testing

```python
def test_profile_workflow():
    """Test complete profile workflow."""
    manager = ProfileManager()

    # Create profile
    profile = manager.create_profile("test", "Test", {"mood": "playful"})
    assert profile.preferences.mood == "playful"

    # Switch and update
    manager.set_active_profile("test")
    manager.update_active_preferences({"time_budget": "deep"})

    # Verify persistence
    reloaded = manager.load_profile("test")
    assert reloaded.preferences.time_budget == "deep"
```

## Best Practices

### ✅ DO

1. **Use ProfileManager for all operations**
   ```python
   # Good
   manager = ProfileManager()
   profile = manager.get_active_profile()

   # Avoid direct storage access
   # storage = JSONProfileStorage()
   # profile = storage.load("work")
   ```

2. **Validate user input**
   ```python
   try:
       manager.create_profile(user_id, user_name, user_prefs)
   except ValueError as e:
       st.error(f"Invalid profile: {e}")
   ```

3. **Use type hints**
   ```python
   from profile import UserProfile, Preferences

   def process_profile(profile: UserProfile) -> dict:
       return profile.get_preferences_dict()
   ```

4. **Mark profiles as used**
   ```python
   # After generating digest
   manager.mark_active_profile_used()
   ```

### ❌ DON'T

1. **Don't bypass ProfileManager**
   ```python
   # Bad - bypasses validation and active profile tracking
   storage = JSONProfileStorage()
   profile = storage.load("work")
   profile.preferences.mood = "invalid"  # No validation!
   storage.save(profile)
   ```

2. **Don't mutate profile objects without saving**
   ```python
   # Bad - changes lost
   profile = manager.get_active_profile()
   profile.preferences.mood = "playful"
   # Forgot to call manager.save_active_profile()
   ```

3. **Don't hardcode profile IDs**
   ```python
   # Bad
   manager.set_active_profile("work")

   # Good - check existence first
   if manager.profile_exists("work"):
       manager.set_active_profile("work")
   ```

4. **Don't skip error handling**
   ```python
   # Bad
   manager.delete_profile("default")  # Raises ValueError!

   # Good
   try:
       manager.delete_profile(profile_id)
   except ValueError as e:
       st.warning(str(e))
   ```

## Troubleshooting

### Profile not saving

**Symptom**: Changes to profile preferences don't persist
**Solution**: Call `save_active_profile()` after updates

```python
manager.update_active_preferences({"mood": "playful"})
manager.save_active_profile()  # Don't forget this!
```

### Validation errors

**Symptom**: `ValidationError` when creating/updating profile
**Solution**: Check field constraints

```python
# Error: String too short
Preferences(learn_about="AI")  # Needs 3+ chars

# Fix
Preferences(learn_about="AI technology")
```

### Cannot delete profile

**Symptom**: `ValueError: Cannot delete the default profile`
**Solution**: Default profile is protected

```python
# Cannot delete default
manager.delete_profile("default")  # Raises error

# Cannot delete active
manager.set_active_profile("work")
manager.delete_profile("work")  # Raises error

# Fix: switch first, then delete
manager.set_active_profile("default")
manager.delete_profile("work")  # Works
```

### Profile file corrupted

**Symptom**: Profile fails to load
**Solution**: Restore from backup

```python
storage = manager.storage
backup_path = storage.get_backup_path("work")

if backup_path and backup_path.exists():
    # Manually restore
    import shutil
    profile_path = storage._get_profile_path("work")
    shutil.copy2(backup_path, profile_path)

    # Reload
    profile = manager.load_profile("work")
```

### Import errors

**Symptom**: `ModuleNotFoundError: No module named 'profile'`
**Solution**: Check Python path

```python
# From project root
import sys
sys.path.insert(0, 'app')
from profile import ProfileManager
```

## Future Enhancements

Planned improvements (not yet implemented):

- [ ] **Alternative Storage Backends**
  - SQLite storage for multi-user support
  - PostgreSQL storage for production

- [ ] **Profile Sharing**
  - Export/import profiles as JSON files
  - Share profiles between users

- [ ] **Profile Templates**
  - Pre-configured templates (e.g., "Tech News", "Fun Learning")
  - One-click profile creation

- [ ] **Profile History**
  - Track digest history per profile
  - Favorite topics over time
  - Usage analytics

- [ ] **Cloud Sync**
  - Sync profiles across devices
  - Profile versioning and conflicts

- [ ] **Profile Validation**
  - Custom validation rules
  - Profile health checks

## Related Files

- `/CLAUDE.md`: Main project documentation
- `/tests/CLAUDE.md`: Testing philosophy
- `/app/agent/CLAUDE.md`: Agent architecture
- `/app/voiceover/CLAUDE.md`: Voiceover system

## API Reference

Quick reference for common operations:

```python
# Initialization
from profile import ProfileManager
manager = ProfileManager()

# Profile CRUD
profile = manager.create_profile(id, name, prefs_dict)
profile = manager.load_profile(id)
manager.save_profile(profile)
manager.delete_profile(id)

# Active profile
active = manager.get_active_profile()
manager.set_active_profile(id)
prefs = manager.get_active_preferences()
manager.update_active_preferences(prefs_dict)
manager.save_active_profile()
manager.mark_active_profile_used()

# Utilities
ids = manager.list_profiles()
names = manager.get_profile_names()
exists = manager.profile_exists(id)
copy = manager.copy_profile(source_id, new_id, new_name)
exported = manager.export_profile(id)
imported = manager.import_profile(data, new_id)
```
