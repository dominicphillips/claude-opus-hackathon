"""Safety Guardian service — reviews generated scripts for child safety."""

import json
import logging

import anthropic

from app.core.config import settings
from app.schemas.schemas import SafetyResult

logger = logging.getLogger(__name__)

SAFETY_SYSTEM_PROMPT = """You are the StorySpark Safety Guardian. You review AI-generated scripts
intended for children ages 2-8. Your job is to ensure every script is safe, appropriate, and positive.

You evaluate scripts against these mandatory safety rules:
1. NO negative reinforcement or guilt
2. NO threats or consequences
3. NO comparing child unfavorably to others
4. NO scary or anxiety-inducing elements
5. NO real-world violence or conflict references
6. NO conditional love ("I'll like you if...")
7. MUST end on a positive, warm note
8. MUST use age-appropriate vocabulary
9. MUST maintain character's canonical personality (no out-of-character behavior)
10. NO commercial content or brand mentions
11. NO personal data beyond first name
12. NO manipulation or coercion tactics

Respond with ONLY valid JSON."""

SAFETY_REVIEW_TEMPLATE = """Review this script for child safety.

CHARACTER: {character_name}
SCENARIO: {scenario_type}
CHILD'S NAME: {child_name}
SCRIPT:
---
{script}
---

Evaluate against all safety rules and respond with this JSON format:
{{
  "approved": true/false,
  "checks": {{
    "age_appropriate_language": {{"pass": true/false, "note": "brief note"}},
    "positive_framing": {{"pass": true/false, "note": "brief note"}},
    "character_fidelity": {{"pass": true/false, "note": "brief note"}},
    "emotional_safety": {{"pass": true/false, "note": "brief note"}},
    "no_manipulation": {{"pass": true/false, "note": "brief note"}},
    "warm_ending": {{"pass": true/false, "note": "brief note"}}
  }},
  "feedback": "Overall feedback or null if approved"
}}"""


async def review_safety(
    script: str,
    character_name: str,
    scenario_type: str,
    child_name: str,
) -> SafetyResult:
    """Review a generated script for child safety."""
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    prompt = SAFETY_REVIEW_TEMPLATE.format(
        character_name=character_name,
        scenario_type=scenario_type,
        child_name=child_name,
        script=script,
    )

    response = await client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=512,
        system=SAFETY_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        import re
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
        if match:
            data = json.loads(match.group(1))
        else:
            # If we can't parse safety response, fail safe — reject
            return SafetyResult(
                approved=False,
                checks={},
                feedback="Safety review response could not be parsed. Rejecting as precaution.",
            )

    return SafetyResult(**data)
