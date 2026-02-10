"""Script generation service — single Claude API call with structured output."""

import json
import logging
import time

import anthropic

from app.core.config import settings
from app.models.models import Character, Scenario
from app.schemas.schemas import GenerationResult

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are StorySpark, an AI that writes short personalized scripts for children's TV show characters.

You write scripts that:
1. Are PERFECTLY faithful to the character's voice, vocabulary, and personality
2. Address the child by name naturally (not forced or repetitive)
3. Match the show's tone and themes
4. Are age-appropriate, warm, and encouraging
5. Accomplish the parent's goal (motivation, education, storytelling)
6. Are 30-60 seconds when spoken aloud (roughly 75-150 words)
7. Use ONLY positive reinforcement — never guilt, shame, threats, or conditional love
8. End on a warm, positive note

You respond with a JSON object containing the script and production metadata."""

USER_PROMPT_TEMPLATE = """Generate a personalized clip script.

CHARACTER: {character_name}
CHARACTER PERSONALITY: {personality}
CHARACTER SPEECH PATTERN: {speech_pattern}
CHARACTER THEMES: {themes}

SCENARIO TYPE: {scenario_type}
SCENARIO DESCRIPTION: {scenario_description}
SCENARIO STRUCTURE: {scenario_structure}

CHILD'S NAME: {child_name}
CHILD'S AGE: {child_age}

PARENT'S NOTE: {parent_note}

Respond with ONLY valid JSON in this exact format:
{{
  "script": "The full script text that the character will speak aloud. Include natural pauses marked with ... and emotional cues in [brackets] like [warmly] or [excitedly].",
  "voice_emotion": "The primary emotion for TTS (e.g., warm, excited, gentle, sleepy, encouraging)",
  "voice_pacing": "The pacing for TTS (e.g., moderate, slow_and_gentle, upbeat)",
  "scene_setting": "Brief description of the visual setting (e.g., Frog's sunny garden)",
  "scene_mood": "The mood of the scene (e.g., cheerful, cozy, adventurous)",
  "ambient_sounds": ["list", "of", "ambient", "sounds"],
  "background_track": "Type of background music (e.g., gentle_acoustic, playful_piano, lullaby)"
}}"""


async def generate_script(
    character: Character,
    scenario: Scenario,
    child_name: str,
    child_age: int | None,
    parent_note: str | None,
) -> tuple[GenerationResult, int, int]:
    """Generate a script using a single Claude API call with structured output.

    Returns (result, tokens_used, time_ms).
    """
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    user_prompt = USER_PROMPT_TEMPLATE.format(
        character_name=character.name,
        personality=character.personality,
        speech_pattern=character.speech_pattern,
        themes=character.themes,
        scenario_type=scenario.type,
        scenario_description=scenario.description,
        scenario_structure=json.dumps(scenario.structure),
        child_name=child_name,
        child_age=child_age or "unknown",
        parent_note=parent_note or "No specific notes",
    )

    start = time.time()
    response = await client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )
    elapsed_ms = int((time.time() - start) * 1000)

    raw_text = response.content[0].text
    tokens_used = response.usage.input_tokens + response.usage.output_tokens

    # Parse JSON from response
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError:
        # Try to extract JSON from markdown code blocks
        import re
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw_text, re.DOTALL)
        if match:
            data = json.loads(match.group(1))
        else:
            raise ValueError(f"Could not parse generation response as JSON: {raw_text[:200]}")

    result = GenerationResult(**data)
    return result, tokens_used, elapsed_ms
