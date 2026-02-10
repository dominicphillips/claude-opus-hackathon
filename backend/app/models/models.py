import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class ClipStatus(str, PyEnum):
    PENDING = "pending"
    GENERATING = "generating"
    SAFETY_REVIEW = "safety_review"
    SAFETY_FAILED = "safety_failed"
    SYNTHESIZING = "synthesizing"
    READY = "ready"
    APPROVED = "approved"
    REJECTED = "rejected"
    FAILED = "failed"


class ScenarioType(str, PyEnum):
    CHORE_MOTIVATION = "chore_motivation"
    STORYTELLING = "storytelling"
    EDUCATIONAL = "educational"
    POSITIVE_REINFORCEMENT = "positive_reinforcement"
    BEDTIME = "bedtime"


class Parent(Base):
    __tablename__ = "parents"

    email: Mapped[str | None] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(255))

    children: Mapped[list["Child"]] = relationship(back_populates="parent", cascade="all, delete-orphan")


class Child(Base):
    __tablename__ = "children"

    parent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("parents.id"))
    name: Mapped[str] = mapped_column(String(100))
    age: Mapped[int | None] = mapped_column(Integer)
    interests: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    favorite_show: Mapped[str | None] = mapped_column(String(255))

    parent: Mapped["Parent"] = relationship(back_populates="children")
    clips: Mapped[list["Clip"]] = relationship(back_populates="child", cascade="all, delete-orphan")


class Character(Base):
    __tablename__ = "characters"

    name: Mapped[str] = mapped_column(String(100))
    show_name: Mapped[str] = mapped_column(String(255))
    personality: Mapped[str] = mapped_column(Text)
    speech_pattern: Mapped[str] = mapped_column(Text)
    themes: Mapped[str] = mapped_column(Text)
    system_prompt: Mapped[str] = mapped_column(Text)
    voice_config: Mapped[dict] = mapped_column(JSONB, default=dict)
    avatar_url: Mapped[str | None] = mapped_column(String(500))
    background_music_url: Mapped[str | None] = mapped_column(String(500))

    clips: Mapped[list["Clip"]] = relationship(back_populates="character")


class Scenario(Base):
    __tablename__ = "scenarios"

    type: Mapped[str] = mapped_column(String(50))
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    structure: Mapped[list] = mapped_column(JSONB)
    example_prompt: Mapped[str | None] = mapped_column(Text)
    icon: Mapped[str | None] = mapped_column(String(50))


class Clip(Base):
    __tablename__ = "clips"

    child_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("children.id"))
    character_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("characters.id"))
    scenario_type: Mapped[str] = mapped_column(String(50))
    parent_note: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default=ClipStatus.PENDING)

    # Generation outputs
    generated_script: Mapped[str | None] = mapped_column(Text)
    scene_description: Mapped[dict | None] = mapped_column(JSONB)
    voice_params: Mapped[dict | None] = mapped_column(JSONB)

    # Safety
    safety_status: Mapped[str | None] = mapped_column(String(20))
    safety_feedback: Mapped[str | None] = mapped_column(Text)
    safety_checks: Mapped[dict | None] = mapped_column(JSONB)

    # Audio
    audio_url: Mapped[str | None] = mapped_column(String(500))
    duration_seconds: Mapped[float | None] = mapped_column()

    # Metrics
    generation_time_ms: Mapped[int | None] = mapped_column(Integer)
    llm_tokens_used: Mapped[int | None] = mapped_column(Integer)

    child: Mapped["Child"] = relationship(back_populates="clips")
    character: Mapped["Character"] = relationship(back_populates="clips")
    asset: Mapped["ClipAsset | None"] = relationship(back_populates="clip", uselist=False)
    approval: Mapped["Approval | None"] = relationship(back_populates="clip", uselist=False)


class ClipAsset(Base):
    __tablename__ = "clip_assets"

    clip_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("clips.id"), unique=True)
    audio_file_path: Mapped[str] = mapped_column(String(500))
    mixed_audio_path: Mapped[str | None] = mapped_column(String(500))
    duration_seconds: Mapped[float | None] = mapped_column()
    tts_provider: Mapped[str | None] = mapped_column(String(50))

    clip: Mapped["Clip"] = relationship(back_populates="asset")


class Approval(Base):
    __tablename__ = "approvals"

    clip_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("clips.id"), unique=True)
    approved: Mapped[bool] = mapped_column()
    reviewer_note: Mapped[str | None] = mapped_column(Text)
    reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    clip: Mapped["Clip"] = relationship(back_populates="approval")
