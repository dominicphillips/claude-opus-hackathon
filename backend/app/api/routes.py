"""API routes for StorySpark."""

import asyncio
import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session, get_db
from app.models.models import Character, Child, Clip, ClipAsset, ClipStatus, Parent, Scenario
from app.schemas.schemas import (
    CharacterOut,
    ChildCreate,
    ChildOut,
    ClipApproveRequest,
    ClipGenerateRequest,
    ClipOut,
    ScenarioOut,
)
from app.services.orchestrator import generate_clip

router = APIRouter(prefix="/api")


# --- Characters ---


@router.get("/characters", response_model=list[CharacterOut])
async def list_characters(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Character).order_by(Character.name))
    return result.scalars().all()


@router.get("/characters/{character_id}", response_model=CharacterOut)
async def get_character(character_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    character = await db.get(Character, character_id)
    if not character:
        raise HTTPException(404, "Character not found")
    return character


# --- Scenarios ---


@router.get("/scenarios", response_model=list[ScenarioOut])
async def list_scenarios(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Scenario).order_by(Scenario.name))
    return result.scalars().all()


# --- Children ---


@router.get("/children", response_model=list[ChildOut])
async def list_children(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Child).order_by(Child.name))
    return result.scalars().all()


@router.post("/children", response_model=ChildOut)
async def create_child(data: ChildCreate, db: AsyncSession = Depends(get_db)):
    # For hackathon: use first parent or create one
    result = await db.execute(select(Parent).limit(1))
    parent = result.scalar_one_or_none()
    if not parent:
        parent = Parent(name="Demo Parent")
        db.add(parent)
        await db.flush()

    child = Child(parent_id=parent.id, **data.model_dump())
    db.add(child)
    await db.commit()
    await db.refresh(child)
    return child


# --- Clips ---


@router.get("/clips", response_model=list[ClipOut])
async def list_clips(
    child_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Clip).order_by(Clip.created_at.desc())
    if child_id:
        query = query.where(Clip.child_id == child_id)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/clips/{clip_id}", response_model=ClipOut)
async def get_clip(clip_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    clip = await db.get(Clip, clip_id)
    if not clip:
        raise HTTPException(404, "Clip not found")
    return clip


@router.post("/clips/generate", response_model=ClipOut)
async def generate_clip_endpoint(
    request: ClipGenerateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Start clip generation pipeline. Returns immediately with pending clip."""
    # Validate references exist
    character = await db.get(Character, request.character_id)
    if not character:
        raise HTTPException(404, "Character not found")

    child = await db.get(Child, request.child_id)
    if not child:
        raise HTTPException(404, "Child not found")

    # Create clip record
    clip = Clip(
        child_id=request.child_id,
        character_id=request.character_id,
        scenario_type=request.scenario_type,
        parent_note=request.parent_note,
        status=ClipStatus.PENDING,
    )
    db.add(clip)
    await db.commit()
    await db.refresh(clip)

    # Run generation in background
    async def _run_generation(clip_id: uuid.UUID):
        async with async_session() as session:
            try:
                await generate_clip(clip_id, session)
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Background generation failed: {e}")

    background_tasks.add_task(_run_generation, clip.id)

    return clip


@router.get("/clips/{clip_id}/audio")
async def get_clip_audio(clip_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Serve the generated audio file."""
    result = await db.execute(
        select(ClipAsset).where(ClipAsset.clip_id == clip_id)
    )
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(404, "Audio not found")

    # Prefer mixed audio if available
    audio_path = asset.mixed_audio_path or asset.audio_file_path
    if not Path(audio_path).exists():
        raise HTTPException(404, "Audio file not found on disk")

    return FileResponse(audio_path, media_type="audio/mpeg")


@router.post("/clips/{clip_id}/approve", response_model=ClipOut)
async def approve_clip(
    clip_id: uuid.UUID,
    request: ClipApproveRequest,
    db: AsyncSession = Depends(get_db),
):
    clip = await db.get(Clip, clip_id)
    if not clip:
        raise HTTPException(404, "Clip not found")

    from app.models.models import Approval

    approval = Approval(
        clip_id=clip.id,
        approved=request.approved,
        reviewer_note=request.reviewer_note,
    )
    db.add(approval)

    clip.status = ClipStatus.APPROVED if request.approved else ClipStatus.REJECTED
    await db.commit()
    await db.refresh(clip)
    return clip
