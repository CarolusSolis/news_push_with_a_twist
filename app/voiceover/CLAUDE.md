# app/voiceover/CLAUDE.md

Voiceover generation system using OpenAI TTS.

## Purpose

Generate audio versions of digest content for hands-free consumption (e.g., during commute, exercise).

## Architecture

```
Digest Sections → Script Generator → TTS Engine → Audio File
                      (GPT-4o)       (OpenAI TTS)    (.mp3)
```

## Core Files

```
voiceover/
├── CLAUDE.md            # This file - voiceover system
├── __init__.py          # Exports: generate_voiceover_script, generate_audio_from_script
├── script_generator.py  # Convert digest → TTS-friendly script
├── tts_engine.py        # OpenAI TTS integration
└── generated/           # Output directory for audio files (gitignored)
```

## Workflow

### 1. Script Generation (script_generator.py)

**Input**: Digest sections + user preferences
**Output**: TTS-optimized script (plain text)

The script generator:
- Converts digest sections into natural spoken text
- Adds transitions between sections
- Personalizes based on user preferences (mood, time budget)
- Optimizes for TTS pronunciation

**Key function**:
```python
def generate_voiceover_script(sections: List[Dict], preferences: Dict) -> str:
    """Generate TTS-friendly script from digest sections."""
```

**Script Structure**:
```
Good morning! Here's your personalized digest.

[Section 1: Need]
Quick hits you should know...
- Item 1 text
- Item 2 text

[Section 2: Nice]
Quote of the day...
"Quote text"

[Closing]
That's your digest for today. Have a great day!
```

### 2. Audio Generation (tts_engine.py)

**Input**: Script text + voice selection
**Output**: Audio file path (.mp3)

Uses OpenAI's TTS API with:
- Model: `tts-1` (standard quality, faster)
- Voice: Configurable (alloy, echo, fable, onyx, nova, shimmer)
- Format: MP3
- Output: `voiceover/generated/digest_{timestamp}.mp3`

**Key function**:
```python
def generate_audio_from_script(
    script: str,
    voice: str = 'alloy',
    model: str = 'tts-1'
) -> Optional[str]:
    """Convert script to audio using OpenAI TTS."""
```

## OpenAI TTS Configuration

### Voices Available

- **alloy**: Neutral, balanced (default)
- **echo**: Male, clear
- **fable**: British accent, expressive
- **onyx**: Deep male voice
- **nova**: Female, energetic
- **shimmer**: Soft female voice

### Models

- **tts-1**: Standard quality, faster, cheaper ($0.015/1K chars)
- **tts-1-hd**: High definition, slower, better quality ($0.030/1K chars)

Current default: `tts-1` for speed and cost-effectiveness

### Output Format

- **Format**: MP3
- **Sample Rate**: 24kHz (tts-1) or 48kHz (tts-1-hd)
- **Bitrate**: Optimized for voice
- **Duration**: ~3-5 minutes for standard digest

## File Management

### Output Directory
```
voiceover/generated/
├── digest_20240906_143022.mp3
├── digest_20240906_145513.mp3
└── ...
```

### Naming Convention
```python
filename = f"digest_{timestamp}.mp3"
# Example: digest_20240906_143022.mp3
```

### Cleanup
Audio files are:
- Created on-demand
- Stored temporarily
- Cleaned up via UI "Clear Voiceover" button
- NOT committed to git (in .gitignore)

## Script Generation Logic

### Personalization Based on Preferences

```python
# Mood affects tone
if preferences['mood'] == 'energized':
    opening = "Good morning! Let's dive into today's exciting updates!"
elif preferences['mood'] == 'calm':
    opening = "Good morning. Here's your digest for today."

# Time budget affects length
if preferences['time_budget'] == 'quick':
    # Shorter script, skip transitions
elif preferences['time_budget'] == 'deep':
    # Longer script, add context
```

### Section Handling

**Need-to-Know Sections** (quick_hits, deep_dive):
- Direct, concise language
- "Here's what matters today..."
- Focus on "why it matters"

**Nice-to-Know Sections** (quote, fun_spark):
- More relaxed tone
- "For some inspiration..."
- Allow for pauses

### TTS Optimization

- **Avoid complex punctuation**: Keep it simple
- **Use natural pauses**: Periods and commas for breath
- **Spell out acronyms** (sometimes): AI → "A I" if needed
- **Avoid URLs**: Say "Link in the digest" instead of reading URL
- **Numbers**: Write out for clarity ("ten percent" not "10%")

## Error Handling

### Common Issues

**1. OpenAI API Key Missing**
```python
if not os.getenv('OPENAI_API_KEY'):
    return None  # Graceful failure
```

**2. Script Too Long**
- OpenAI TTS limit: 4096 characters per request
- Solution: Split into chunks or truncate script

**3. Audio Generation Fails**
```python
try:
    response = client.audio.speech.create(...)
except Exception as e:
    logger.error(f"TTS failed: {e}")
    return None
```

**4. File System Issues**
```python
# Ensure output directory exists
output_dir = Path(__file__).parent / 'generated'
output_dir.mkdir(exist_ok=True)
```

## Testing

### Test Script Generation
```bash
conda activate news_push
cd app
python -c "
from voiceover import generate_voiceover_script
sections = [{'id': 'test', 'title': 'Test', 'kind': 'need', 'items': [{'text': 'Test item'}]}]
prefs = {'mood': 'focused', 'time_budget': 'standard'}
print(generate_voiceover_script(sections, prefs))
"
```

### Test Audio Generation
```bash
cd app
python -c "
from voiceover import generate_audio_from_script
script = 'This is a test voiceover script.'
audio_path = generate_audio_from_script(script)
print(f'Audio generated: {audio_path}')
"
```

### Play Generated Audio
```bash
# macOS
afplay app/voiceover/generated/digest_*.mp3

# Linux
mpg123 app/voiceover/generated/digest_*.mp3
```

## UI Integration (app.py)

Voiceover is generated on-demand:

1. User generates digest
2. User clicks "🎙️ Generate Voiceover"
3. Script is generated (step 1)
4. Audio is generated (step 2)
5. Audio player appears in UI
6. User can listen, download, or clear

## Performance

### Timing
- **Script generation**: ~2-3s (GPT-4o call)
- **Audio generation**: ~5-10s (depends on script length)
- **Total**: ~7-13s for complete voiceover

### Costs (OpenAI)
- **Script generation**: ~$0.01 per digest (GPT-4o)
- **Audio generation**: ~$0.02 per digest (tts-1, ~1000 chars)
- **Total**: ~$0.03 per voiceover

## Best Practices

✅ **DO:**
- Keep scripts conversational and natural
- Test with different voices to find best match
- Handle API errors gracefully
- Clean up old audio files periodically
- Use tts-1 for development, tts-1-hd for production

❌ **DON'T:**
- Read URLs aloud
- Generate audio without user request
- Store audio indefinitely
- Use complex punctuation in scripts
- Forget to check OPENAI_API_KEY

## Future Enhancements

Potential improvements:
- **Voice cloning**: Custom voice for brand identity
- **Multilingual**: Support multiple languages
- **Background music**: Add intro/outro music
- **Speed control**: Allow playback speed adjustment
- **Podcast format**: RSS feed for daily digests
- **Streaming**: Stream audio instead of file download

## Debugging

### Enable Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check Generated Files
```bash
ls -lh app/voiceover/generated/
```

### Verify OpenAI API Key
```bash
echo $OPENAI_API_KEY
# Or check .env file
cat .env | grep OPENAI_API_KEY
```

### Test OpenAI TTS Directly
```python
from openai import OpenAI
client = OpenAI()

response = client.audio.speech.create(
    model="tts-1",
    voice="alloy",
    input="Hello! This is a test."
)

response.stream_to_file("test_output.mp3")
```

## Environment Variables

- `OPENAI_API_KEY`: Required for both script generation (GPT) and TTS

## Dependencies

```python
# requirements.txt
openai>=1.0.0        # OpenAI API client
python-dotenv>=1.0.0  # Environment variables
```

## References

- [OpenAI TTS Guide](https://platform.openai.com/docs/guides/text-to-speech)
- [OpenAI TTS API Reference](https://platform.openai.com/docs/api-reference/audio/createSpeech)
- [Available Voices Demo](https://platform.openai.com/docs/guides/text-to-speech/voice-options)
