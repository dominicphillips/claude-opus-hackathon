"""API routes for AI agent operations — with SSE streaming for live feedback."""

import asyncio
import json
import os
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from app.core.config import settings

router = APIRouter(prefix="/api/agents")


class ImageSearchRequest(BaseModel):
    query: str


class ChildProfile(BaseModel):
    hair_color: str = "brown"
    hair_style: str = "short and curly"
    eye_color: str = "blue"
    skin_tone: str = "light"
    height: str = "small"
    age: int = 4
    outfit: str = "red t-shirt and blue shorts"
    extra: str = ""


class ImageCustomizeRequest(BaseModel):
    scene_image_url: str  # URL of the asset to customize
    child_profile: ChildProfile
    mask_position: str = "center"


# --- SSE Streaming Image Search ---

@router.get("/images/search/stream")
async def search_images_stream(query: str):
    """SSE stream: search for images with live agent feedback."""

    async def event_generator():
        yield {"event": "status", "data": json.dumps({"step": "init", "detail": f"Starting search for: {query}"})}

        yield {"event": "status", "data": json.dumps({"step": "agent_start", "detail": "Claude Agent is browsing the web..."})}

        # Run the agent
        try:
            from app.agents.image_finder import find_images
            images = await find_images(query)

            yield {"event": "status", "data": json.dumps({
                "step": "found",
                "detail": f"Found {len(images)} images, downloading...",
            })}

            yield {"event": "result", "data": json.dumps({
                "step": "complete",
                "images": images,
                "count": len(images),
            })}

        except Exception as e:
            yield {"event": "error", "data": json.dumps({"step": "error", "detail": str(e)})}

    return EventSourceResponse(event_generator())


# --- SSE Streaming Image Customization ---

@router.post("/images/customize/stream")
async def customize_image_stream(
    scene_image_url: str = Form(...),
    hair_color: str = Form("brown"),
    hair_style: str = Form("short and curly"),
    eye_color: str = Form("blue"),
    skin_tone: str = Form("light"),
    height: str = Form("small"),
    age: int = Form(4),
    outfit: str = Form("red t-shirt and blue shorts"),
    extra: str = Form(""),
    mask_position: str = Form("center"),
):
    """SSE stream: customize an image by adding a child character."""

    # Build child description
    child_desc = (
        f"a {height} {age}-year-old child with {hair_style} {hair_color} hair, "
        f"{eye_color} eyes, {skin_tone} skin, wearing {outfit}"
    )
    if extra:
        child_desc += f", {extra}"

    # Resolve the scene image to a local path
    scene_path = _resolve_asset_path(scene_image_url)
    if not scene_path or not Path(scene_path).exists():
        raise HTTPException(400, f"Scene image not found: {scene_image_url}")

    async def event_generator():
        from app.services.image_customizer import stream_customize_image

        async for update in stream_customize_image(scene_path, child_desc, mask_position):
            event_type = "result" if update.get("step") == "complete" else "status"
            yield {"event": event_type, "data": json.dumps(update)}

    return EventSourceResponse(event_generator())


# --- Non-streaming fallbacks ---

@router.post("/images/search")
async def search_images(request: ImageSearchRequest):
    """Search for images (non-streaming)."""
    from app.agents.image_finder import find_images
    images = await find_images(request.query)
    return {"images": images, "count": len(images)}


@router.post("/images/customize")
async def customize_image(request: ImageCustomizeRequest):
    """Customize an image (non-streaming)."""
    from app.services.image_customizer import stream_customize_image

    child_desc = (
        f"a {request.child_profile.height} {request.child_profile.age}-year-old child with "
        f"{request.child_profile.hair_style} {request.child_profile.hair_color} hair, "
        f"{request.child_profile.eye_color} eyes, {request.child_profile.skin_tone} skin, "
        f"wearing {request.child_profile.outfit}"
    )
    if request.child_profile.extra:
        child_desc += f", {request.child_profile.extra}"

    scene_path = _resolve_asset_path(request.scene_image_url)
    if not scene_path:
        raise HTTPException(400, "Scene image not found")

    result = None
    async for update in stream_customize_image(scene_path, child_desc, request.mask_position):
        if update.get("step") == "complete":
            result = update

    return result


# --- Asset browsing ---

@router.get("/assets/images")
async def list_image_assets():
    """List all downloaded/generated/customized image assets."""
    assets_dir = Path(settings.clip_storage_path) / "assets"
    images = []

    for subdir in ["images", "generated", "customized"]:
        dir_path = assets_dir / subdir
        if not dir_path.exists():
            continue
        for f in sorted(dir_path.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
            if f.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp", ".gif"]:
                images.append({
                    "filename": f.name,
                    "path": str(f),
                    "category": subdir,
                    "url": f"/api/agents/assets/file/{subdir}/{f.name}",
                    "size_bytes": f.stat().st_size,
                })

    # Enrich with metadata if available
    metadata_path = assets_dir / "images" / "metadata.json"
    if metadata_path.exists():
        with open(metadata_path) as mf:
            meta_list = json.load(mf)
            metadata = {m.get("filename", ""): m for m in meta_list}
            for img in images:
                if img["filename"] in metadata:
                    img["title"] = metadata[img["filename"]].get("title")
                    img["source"] = metadata[img["filename"]].get("source")
                    img["relevance"] = metadata[img["filename"]].get("relevance")

    return {"images": images, "count": len(images)}


@router.get("/assets/file/{category}/{filename}")
async def serve_asset_file(category: str, filename: str):
    """Serve an asset file."""
    if category not in ["images", "generated", "customized", "videos"]:
        raise HTTPException(400, "Invalid category")

    filepath = Path(settings.clip_storage_path) / "assets" / category / filename
    if not filepath.exists():
        raise HTTPException(404, "File not found")

    return FileResponse(str(filepath))


def _resolve_asset_path(url_or_path: str) -> str | None:
    """Resolve an asset URL like /api/agents/assets/file/images/xyz.jpg to a local path."""
    if url_or_path.startswith("/api/agents/assets/file/"):
        parts = url_or_path.replace("/api/agents/assets/file/", "").split("/", 1)
        if len(parts) == 2:
            return str(Path(settings.clip_storage_path) / "assets" / parts[0] / parts[1])
    # Try as absolute path
    if Path(url_or_path).exists():
        return url_or_path
    return None
