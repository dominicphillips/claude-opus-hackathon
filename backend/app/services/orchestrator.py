"""Clip generation orchestrator — coordinates the full pipeline."""

import logging
import time
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Character, Child, Clip, ClipAsset, ClipStatus, Scenario
from app.services.generation import generate_script
from app.services.safety import review_safety
from app.services.tts import mix_with_background, synthesize_speech

logger = logging.getLogger(__name__)


async def generate_clip(clip_id: uuid.UUID, db: AsyncSession) -> Clip:
    """Run the full clip generation pipeline.

    Pipeline: Script Generation → Safety Review → TTS → Audio Mixing
    """
    # Load clip with relationships
    clip = await db.get(Clip, clip_id)
    if not clip:
        raise ValueError(f"Clip {clip_id} not found")

    character = await db.get(Character, clip.character_id)
    child = await db.get(Child, clip.child_id)

    scenario_result = await db.execute(
        select(Scenario).where(Scenario.type == clip.scenario_type)
    )
    scenario = scenario_result.scalar_one_or_none()
    if not scenario:
        raise ValueError(f"Scenario type {clip.scenario_type} not found")

    start_time = time.time()

    try:
        # Step 1: Generate script
        clip.status = ClipStatus.GENERATING
        await db.commit()

        generation_result, tokens, gen_time_ms = await generate_script(
            character=character,
            scenario=scenario,
            child_name=child.name,
            child_age=child.age,
            parent_note=clip.parent_note,
        )

        clip.generated_script = generation_result.script
        clip.scene_description = {
            "setting": generation_result.scene_setting,
            "mood": generation_result.scene_mood,
            "ambient_sounds": generation_result.ambient_sounds,
        }
        clip.voice_params = {
            "emotion": generation_result.voice_emotion,
            "pacing": generation_result.voice_pacing,
            "background_track": generation_result.background_track,
        }
        clip.llm_tokens_used = tokens
        await db.commit()

        # Step 2: Safety review
        clip.status = ClipStatus.SAFETY_REVIEW
        await db.commit()

        safety_result = await review_safety(
            script=generation_result.script,
            character_name=character.name,
            scenario_type=clip.scenario_type,
            child_name=child.name,
        )

        clip.safety_status = "approved" if safety_result.approved else "rejected"
        clip.safety_feedback = safety_result.feedback
        clip.safety_checks = safety_result.checks

        if not safety_result.approved:
            clip.status = ClipStatus.SAFETY_FAILED
            await db.commit()
            return clip

        # Step 3: TTS synthesis
        clip.status = ClipStatus.SYNTHESIZING
        await db.commit()

        voice_path, duration = await synthesize_speech(
            script=generation_result.script,
            character_name=character.name,
            voice_emotion=generation_result.voice_emotion,
            voice_pacing=generation_result.voice_pacing,
        )

        # Step 4: Audio mixing
        final_path = await mix_with_background(
            voice_path=voice_path,
            background_track=generation_result.background_track,
        )

        # Save asset
        asset = ClipAsset(
            clip_id=clip.id,
            audio_file_path=voice_path,
            mixed_audio_path=final_path if final_path != voice_path else None,
            duration_seconds=duration,
            tts_provider="openai",
        )
        db.add(asset)

        clip.audio_url = f"/api/clips/{clip.id}/audio"
        clip.duration_seconds = duration
        clip.status = ClipStatus.READY
        clip.generation_time_ms = int((time.time() - start_time) * 1000)

        await db.commit()

        logger.info(
            f"Clip {clip.id} generated successfully in {clip.generation_time_ms}ms "
            f"({tokens} tokens, {duration:.1f}s audio)"
        )

        return clip

    except Exception as e:
        logger.error(f"Clip generation failed for {clip_id}: {e}")
        clip.status = ClipStatus.FAILED
        await db.commit()
        raise
