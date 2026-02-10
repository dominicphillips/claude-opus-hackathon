from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


# --- Characters ---
class CharacterOut(BaseModel):
    id: uuid.UUID
    name: str
    show_name: str
    personality: str
    speech_pattern: str
    themes: str
    avatar_url: str | None
    voice_config: dict

    model_config = {"from_attributes": True}


# --- Scenarios ---
class ScenarioOut(BaseModel):
    id: uuid.UUID
    type: str
    name: str
    description: str
    structure: list
    example_prompt: str | None
    icon: str | None

    model_config = {"from_attributes": True}


# --- Children ---
class ChildCreate(BaseModel):
    name: str
    age: int | None = None
    interests: list[str] | None = None
    favorite_show: str | None = None


class ChildOut(BaseModel):
    id: uuid.UUID
    name: str
    age: int | None
    interests: list[str] | None
    favorite_show: str | None

    model_config = {"from_attributes": True}


# --- Clips ---
class ClipGenerateRequest(BaseModel):
    child_id: uuid.UUID
    character_id: uuid.UUID
    scenario_type: str
    parent_note: str | None = None


class ClipOut(BaseModel):
    id: uuid.UUID
    child_id: uuid.UUID
    character_id: uuid.UUID
    scenario_type: str
    parent_note: str | None
    status: str
    generated_script: str | None
    scene_description: dict | None
    safety_status: str | None
    safety_feedback: str | None
    safety_checks: dict | None
    audio_url: str | None
    duration_seconds: float | None
    generation_time_ms: int | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ClipApproveRequest(BaseModel):
    approved: bool
    reviewer_note: str | None = None


# --- Generation internal ---
class GenerationResult(BaseModel):
    script: str
    voice_emotion: str
    voice_pacing: str
    scene_setting: str
    scene_mood: str
    ambient_sounds: list[str]
    background_track: str


class SafetyResult(BaseModel):
    approved: bool
    checks: dict
    feedback: str | None = None
