"""Script generation module for converting digest into voiceover script."""

import json
from typing import Dict, List, Any, Optional
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

def get_llm() -> Optional[ChatOpenAI]:
    """Get OpenAI LLM instance for script generation."""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        return None
    
    return ChatOpenAI(
        model="gpt-4o",
        temperature=0.3,  # Slightly more creative for engaging script
        api_key=api_key
    )

def generate_voiceover_script(sections: List[Dict[str, Any]], user_preferences: Dict[str, Any]) -> str:
    """Generate a friendly morning digest voiceover script from digest sections.
    
    Args:
        sections: List of digest sections with titles and items
        user_preferences: User preferences for personalization
    
    Returns:
        Generated voiceover script as a string
    """
    llm = get_llm()
    if llm is None:
        return "Sorry, I couldn't generate the voiceover script. Please check your OpenAI API key."
    
    # Prepare the digest content for script generation
    digest_content = format_digest_for_script(sections)
    
    # Create the prompt for script generation
    script_prompt = f"""You are a friendly, engaging morning digest host. Convert this digest into a natural, conversational voiceover script.

USER PREFERENCES:
{json.dumps(user_preferences, indent=2)}

DIGEST CONTENT:
{digest_content}

SCRIPT REQUIREMENTS:
1. Start with a warm, friendly greeting
2. Speak like a professional morning show host - conversational but informative
3. Use natural transitions between sections
4. Keep the tone engaging and slightly upbeat
5. Include brief pauses indicated by [pause] for natural speech rhythm
6. End with an encouraging closing
7. Keep the total script length to 2-3 minutes when spoken
8. Use "we" and "you" to create connection with the listener
9. Make it sound like you're personally curating this content for the listener

FORMAT:
- Write in a natural, spoken style
- Use contractions (we're, you'll, it's)
- Include natural speech patterns and filler words where appropriate
- Make it sound like a real person talking, not reading a script
- DO NOT include stage directions like [music], [sound effects], or any bracketed text except [pause]
- Only use [pause] for natural speech rhythm - no other bracketed instructions

Generate the complete voiceover script:"""

    try:
        response = llm.invoke(script_prompt)
        return response.content.strip()
    except Exception as e:
        return f"Error generating script: {str(e)}"

def format_digest_for_script(sections: List[Dict[str, Any]]) -> str:
    """Format digest sections into a readable format for script generation."""
    formatted_content = []
    
    for i, section in enumerate(sections, 1):
        title = section.get('title', 'Untitled Section')
        kind = section.get('kind', 'need')
        items = section.get('items', [])
        
        # Add section header
        section_type = "Need-to-Know" if kind == "need" else "Nice-to-Know"
        formatted_content.append(f"\n{i}. {section_type}: {title}")
        
        # Add items as descriptions
        for item in items:
            text = item.get('text', '')
            if text:
                formatted_content.append(f"   - {text}")
    
    return "\n".join(formatted_content)

def estimate_script_duration(script: str) -> str:
    """Estimate the duration of the script when spoken."""
    # Rough estimate: average speaking rate is 150-160 words per minute
    word_count = len(script.split())
    estimated_minutes = word_count / 155  # 155 words per minute average
    
    if estimated_minutes < 1:
        return f"~{int(estimated_minutes * 60)} seconds"
    else:
        return f"~{estimated_minutes:.1f} minutes"
