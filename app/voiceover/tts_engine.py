"""Text-to-Speech engine using OpenAI TTS."""

import os
import tempfile
from typing import Optional
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_openai_client() -> Optional[OpenAI]:
    """Get OpenAI client for TTS."""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        return None
    
    return OpenAI(api_key=api_key)

def generate_audio_from_script(script: str, voice: str = "alloy") -> Optional[str]:
    """Generate audio from script using OpenAI TTS.
    
    Args:
        script: The voiceover script text
        voice: Voice to use (alloy, echo, fable, onyx, nova, shimmer)
    
    Returns:
        Path to the generated audio file, or None if failed
    """
    client = get_openai_client()
    if client is None:
        return None
    
    try:
        # Clean the script for TTS (remove pause markers and format for speech)
        clean_script = clean_script_for_tts(script)
        
        # Generate audio using OpenAI TTS
        response = client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=clean_script
        )
        
        # Save to a more permanent location that Streamlit can serve
        import uuid
        from pathlib import Path
        
        # Create audio directory if it doesn't exist
        audio_dir = Path(__file__).parent / "generated"
        audio_dir.mkdir(exist_ok=True)
        
        # Generate unique filename
        audio_filename = f"voiceover_{uuid.uuid4().hex[:8]}.mp3"
        audio_path = audio_dir / audio_filename
        
        # Save the audio file
        with open(audio_path, 'wb') as audio_file:
            audio_file.write(response.content)
            
        return str(audio_path)
            
    except Exception as e:
        print(f"Error generating audio: {e}")
        return None

def clean_script_for_tts(script: str) -> str:
    """Clean script for TTS by removing pause markers and formatting."""
    # Remove pause markers
    clean_script = script.replace("[pause]", "...")
    
    # Remove any other formatting markers
    clean_script = clean_script.replace("[", "").replace("]", "")
    
    # Ensure proper punctuation for natural speech
    clean_script = clean_script.replace("  ", " ")  # Remove double spaces
    
    return clean_script.strip()

def get_available_voices() -> list:
    """Get list of available TTS voices."""
    return [
        {"id": "alloy", "name": "Alloy", "description": "Neutral, balanced voice"},
        {"id": "echo", "name": "Echo", "description": "Clear, professional voice"},
        {"id": "fable", "name": "Fable", "description": "Warm, storytelling voice"},
        {"id": "onyx", "name": "Onyx", "description": "Deep, authoritative voice"},
        {"id": "nova", "name": "Nova", "description": "Bright, energetic voice"},
        {"id": "shimmer", "name": "Shimmer", "description": "Soft, gentle voice"}
    ]

def estimate_audio_duration(script: str) -> str:
    """Estimate audio duration based on script length."""
    # Rough estimate: average speaking rate is 150-160 words per minute
    word_count = len(script.split())
    estimated_minutes = word_count / 155  # 155 words per minute average
    
    if estimated_minutes < 1:
        return f"~{int(estimated_minutes * 60)} seconds"
    else:
        return f"~{estimated_minutes:.1f} minutes"
