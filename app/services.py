"""Backend services for Agentic Morning Digest.

This module contains pure business logic separated from Streamlit UI code.
All functions are testable without Streamlit dependencies.
"""

import json
import os
from typing import Dict, List, Any, Optional
from pathlib import Path

# Import agent modules
from agent import generate_digest_with_agent, get_agent_logs
from voiceover import generate_voiceover_script, generate_audio_from_script


class DigestService:
    """Service for generating and managing digests."""

    def __init__(self, data_dir: Optional[Path] = None):
        """Initialize the digest service.

        Args:
            data_dir: Directory containing data files. If None, uses default app/data.
        """
        if data_dir is None:
            data_dir = Path(__file__).parent / 'data'
        self.data_dir = data_dir

    def load_static_samples(self) -> Dict[str, Any]:
        """Load static sample data from JSON file.

        Returns:
            Dict containing static sample data, or empty dict on error.
        """
        try:
            data_path = self.data_dir / 'static_samples.json'
            with open(data_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Failed to load static samples: {e}")
            return {}

    def generate_digest(
        self,
        preferences: Dict[str, Any],
        use_live_data: bool = True
    ) -> tuple[List[Dict[str, Any]], List[str]]:
        """Generate digest sections based on user preferences.

        Args:
            preferences: User preferences dict with keys like 'learn_about',
                        'fun_learning', 'time_budget', etc.
            use_live_data: Whether to use live data sources or static samples.

        Returns:
            Tuple of (sections list, agent log messages list)

        Raises:
            Exception: If digest generation fails.
        """
        sections = generate_digest_with_agent(preferences, use_live_data=use_live_data)
        agent_logs = get_agent_logs()
        return sections, agent_logs

    def create_mock_sections(
        self,
        prefs: Dict[str, Any],
        mock_data: Optional[Dict[str, Any]] = None
    ) -> tuple[List[Dict[str, Any]], List[str]]:
        """Create mock digest sections for fallback scenarios.

        Args:
            prefs: User preferences dict.
            mock_data: Mock data to use. If None, loads from static samples.

        Returns:
            Tuple of (sections list, log messages list)
        """
        if mock_data is None:
            mock_data = self.load_static_samples()

        log_messages = []
        sections = []

        log_messages.append("[Planner] Starting digest generation...")
        log_messages.append(f"[Planner] User wants to learn about: {prefs['learn_about'][:50]}...")
        log_messages.append(f"[Planner] User enjoys learning about: {prefs['fun_learning'][:50]}...")
        log_messages.append(f"[Planner] Mood: {prefs['mood']}, Time budget: {prefs['time_budget']}")
        log_messages.append("[Planner] Planning 1:1 alternating pattern: serious → fun → serious → fun...")

        learn_about_lower = prefs['learn_about'].lower()
        fun_learning_lower = prefs['fun_learning'].lower()

        # Create individual items that will alternate
        items_to_add = []

        # Serious item #1: Tech headline (if relevant)
        if any(keyword in learn_about_lower for keyword in ['ai', 'tech', 'startup', 'technology', 'software', 'innovation']):
            log_messages.append("[Planner] Adding serious item #1: Tech headline")
            tech_item = mock_data.get('hacker_news', [{}])[0]
            items_to_add.append({
                'kind': 'need',
                'text': f"{tech_item.get('title', 'OpenAI Releases GPT-5')} - {tech_item.get('snippet', 'Major AI breakthrough')[:80]}...",
                'url': tech_item.get('url')
            })

        # Fun item #1: Quote (if enabled)
        if prefs.get('include_quotes', True) and len(items_to_add) > 0:
            log_messages.append("[Planner] Adding fun item #1: Inspirational quote")
            quote = mock_data.get('quotes', [{}])[0]
            items_to_add.append({
                'kind': 'nice',
                'text': f'"{quote.get("text", "Innovation distinguishes between a leader and a follower.")}" - {quote.get("author", "Steve Jobs")}'
            })

        # Serious item #2: Another tech headline or deep dive
        if len(items_to_add) >= 2:
            log_messages.append("[Planner] Adding serious item #2: Second headline")
            if len(mock_data.get('hacker_news', [])) > 1:
                tech_item2 = mock_data.get('hacker_news', [{}])[1]
                items_to_add.append({
                    'kind': 'need',
                    'text': f"{tech_item2.get('title', 'Apple M4 Chip')} - {tech_item2.get('snippet', 'Hardware breakthrough')[:80]}...",
                    'url': tech_item2.get('url')
                })
            else:
                # Deep dive fallback
                deep_dive_topic = "AI Model Performance"
                if "startup" in learn_about_lower:
                    deep_dive_topic = "Startup Funding Trends"
                elif "space" in learn_about_lower:
                    deep_dive_topic = "Commercial Space Industry"

                items_to_add.append({
                    'kind': 'need',
                    'text': f'{deep_dive_topic}: OpenAI\'s latest GPT-5 represents a significant leap in reasoning capabilities, with 10x performance improvements. This matters for your interests in {prefs["learn_about"][:30]}... because it signals more reliable AI assistants transforming knowledge work.',
                })

        # Fun item #2: Historical fact (if relevant interests)
        if len(items_to_add) >= 3 and any(keyword in fun_learning_lower for keyword in ['history', 'historical', 'past', 'ancient', 'mystery', 'exploration', 'space']):
            log_messages.append("[Planner] Adding fun item #2: Historical discovery")
            history_item = mock_data.get('wikipedia_today', [{}])[0]
            items_to_add.append({
                'kind': 'nice',
                'text': f"{history_item.get('title', '1969 – Apollo 11 Moon Landing')} - {history_item.get('snippet', 'Neil Armstrong and Buzz Aldrin became the first humans to land on the Moon.')}"
            })

        # Serious item #3: Market context (if deep time budget)
        if prefs.get('time_budget') == 'deep' and len(items_to_add) >= 4:
            log_messages.append("[Planner] Adding serious item #3: Market context")
            items_to_add.append({
                'kind': 'need',
                'text': 'Tech Market Update: With Apple\'s new M4 chip announcement, the AI hardware race intensifies. This follows the trend you\'re interested in around emerging technologies and their market impact.'
            })

        # Fun item #3: Second quote or fun fact
        if len(items_to_add) >= 5 and len(mock_data.get('quotes', [])) > 1:
            log_messages.append("[Planner] Adding fun item #3: Second quote")
            quote2 = mock_data.get('quotes', [{}])[1]
            items_to_add.append({
                'kind': 'nice',
                'text': f'"{quote2.get("text", "Be yourself; everyone else is already taken.")}" - {quote2.get("author", "Oscar Wilde")}'
            })

        # Convert items to sections for rendering
        for i, item in enumerate(items_to_add):
            section_id = f"item_{i+1}"
            section_title = f"Item {i+1}"

            sections.append({
                'id': section_id,
                'title': section_title,
                'kind': item['kind'],
                'items': [{
                    'text': item['text'],
                    'url': item.get('url')
                }]
            })

        log_messages.append(f"[Planner] Generated {len(sections)} items in strict 1:1 alternating pattern")
        log_messages.append("[Retriever] Using static mock data (USE_LIVE=False)")
        log_messages.append("[Presenter] Items ready for rendering")

        return sections, log_messages


class VoiceoverService:
    """Service for generating voiceovers."""

    def generate_script(
        self,
        sections: List[Dict[str, Any]],
        preferences: Dict[str, Any]
    ) -> str:
        """Generate voiceover script from digest sections.

        Args:
            sections: List of digest sections.
            preferences: User preferences dict.

        Returns:
            Generated script text.

        Raises:
            Exception: If script generation fails.
        """
        return generate_voiceover_script(sections, preferences)

    def generate_audio(
        self,
        script: str,
        voice: str = 'alloy'
    ) -> Optional[str]:
        """Generate audio file from script.

        Args:
            script: Script text to convert to audio.
            voice: Voice to use (alloy, echo, fable, onyx, nova, shimmer).

        Returns:
            Path to generated audio file, or None on failure.

        Raises:
            Exception: If audio generation fails.
        """
        return generate_audio_from_script(script, voice=voice)

    def cleanup_audio(self, audio_path: str) -> bool:
        """Clean up audio file.

        Args:
            audio_path: Path to audio file to delete.

        Returns:
            True if deletion succeeded, False otherwise.
        """
        if audio_path and os.path.exists(audio_path):
            try:
                os.unlink(audio_path)
                return True
            except Exception:
                return False
        return False
