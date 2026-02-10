"""Text-to-Speech service using ElevenLabs + audio mixing with pydub."""

import logging
import re
import uuid
from pathlib import Path

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

# Voice mapping for characters → ElevenLabs voice IDs
# These can be cloned voices or pre-existing ones
VOICE_MAP: dict[str, str | None] = {
    "frog": None,   # Will use default from settings
    "toad": None,   # Will use default from settings
}


async def synthesize_speech(
    script: str,
    character_name: str,
    voice_emotion: str = "neutral",
    voice_pacing: str = "moderate",
) -> tuple[str, float]:
    """Generate TTS audio using ElevenLabs.

    Returns (file_path, duration_seconds).
    """
    voice_id = VOICE_MAP.get(character_name.lower()) or settings.elevenlabs_voice_id
    clip_id = str(uuid.uuid4())
    output_dir = Path(settings.clip_storage_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{clip_id}.mp3"

    # Clean script for TTS
    tts_input = _prepare_tts_input(script, voice_emotion, voice_pacing)

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
            headers={
                "xi-api-key": settings.elevenlabs_api_key,
                "Content-Type": "application/json",
            },
            json={
                "text": tts_input,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.6,
                    "similarity_boost": 0.8,
                    "style": _emotion_to_style(voice_emotion),
                    "use_speaker_boost": True,
                },
            },
            timeout=60.0,
        )
        response.raise_for_status()

        with open(output_path, "wb") as f:
            f.write(response.content)

    duration = _get_audio_duration(str(output_path))
    return str(output_path), duration


async def mix_with_background(
    voice_path: str,
    background_track: str,
) -> str:
    """Mix voice audio with background music/ambiance."""
    try:
        from pydub import AudioSegment

        voice = AudioSegment.from_mp3(voice_path)

        bg_path = Path(settings.clip_storage_path) / "backgrounds" / f"{background_track}.mp3"
        if bg_path.exists():
            background = AudioSegment.from_mp3(str(bg_path))
            background = background - 18  # reduce by 18dB
            if len(background) < len(voice):
                loops_needed = (len(voice) // len(background)) + 1
                background = background * loops_needed
            background = background[: len(voice)]

            mixed = background.overlay(voice)
            mixed = mixed.fade_in(1000).fade_out(2000)

            output_path = voice_path.replace(".mp3", "_mixed.mp3")
            mixed.export(output_path, format="mp3")
            return output_path

    except Exception as e:
        logger.warning(f"Could not mix audio: {e}")

    return voice_path


def _prepare_tts_input(script: str, emotion: str, pacing: str) -> str:
    """Clean script for TTS — remove stage directions, keep pauses."""
    cleaned = re.sub(r"\[.*?\]\s*", "", script)
    cleaned = cleaned.replace("...", ", ,")
    return cleaned.strip()


def _emotion_to_style(emotion: str) -> float:
    """Map emotion to ElevenLabs style intensity (0-1)."""
    style_map = {
        "warm": 0.4,
        "excited": 0.7,
        "gentle": 0.3,
        "sleepy": 0.2,
        "encouraging": 0.5,
        "neutral": 0.3,
    }
    return style_map.get(emotion, 0.4)


def _get_audio_duration(path: str) -> float:
    """Get audio duration in seconds."""
    try:
        from pydub import AudioSegment
        audio = AudioSegment.from_mp3(path)
        return len(audio) / 1000.0
    except Exception:
        return 0.0
