# User Profiles Directory

This directory stores user profile files in JSON format.

## Structure

Each profile is stored as a separate JSON file:
- `default.json` - Default profile (auto-created on first run)
- `work.json` - Example work profile
- `personal.json` - Example personal profile

## File Format

Profile files contain:
- Profile metadata (created_at, last_modified, use_count)
- User preferences (learn_about, mood, time_budget, etc.)
- Optional history tracking

## Git Ignore

Profile files are gitignored to keep user data private. Only this README
and .gitignore are tracked in version control.

## Backup

The system automatically creates `.bak` backup files before overwriting profiles.

## Management

Profiles are managed through the `ProfileManager` class:
```python
from profile import ProfileManager

manager = ProfileManager()
profile = manager.get_active_profile()
```

See `/app/profile/CLAUDE.md` for full documentation.
