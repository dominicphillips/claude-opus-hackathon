"""API routes for AI agent operations."""

import os
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.agents.image_finder import find_images, generate_image, generate_video
from app.core.config import settings

router = APIRouter(prefix="/api/agents")


class ImageSearchRequest(BaseModel):
    query: str


class ImageGenerateRequest(BaseModel):
    prompt: str


class VideoGenerateRequest(BaseModel):
    prompt: str


# In-memory job tracking for async operations
_jobs: dict[str, dict] = {}


@router.post("/images/search")
async def search_images(request: ImageSearchRequest):
    """Use the Image Finder agent to search for show images."""
    images = await find_images(request.query)
    return {"images": images, "count": len(images)}


@router.post("/images/generate")
async def generate_image_endpoint(request: ImageGenerateRequest):
    """Generate an image using Replicate nano-banana-pro."""
    result = await generate_image(request.prompt)
    return result


@router.post("/videos/generate")
async def generate_video_endpoint(request: VideoGenerateRequest):
    """Generate a video using Replicate Veo 3.1."""
    result = await generate_video(request.prompt)
    return result


@router.get("/assets/images")
async def list_image_assets():
    """List all downloaded/generated image assets."""
    assets_dir = Path(settings.clip_storage_path) / "assets"
    images = []

    for subdir in ["images", "generated"]:
        dir_path = assets_dir / subdir
        if not dir_path.exists():
            continue
        for f in dir_path.iterdir():
            if f.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp", ".gif"]:
                images.append({
                    "filename": f.name,
                    "path": str(f),
                    "category": subdir,
                    "url": f"/api/agents/assets/file/{subdir}/{f.name}",
                    "size_bytes": f.stat().st_size,
                })

    # Also load metadata if available
    metadata_path = assets_dir / "images" / "metadata.json"
    metadata = {}
    if metadata_path.exists():
        import json
        with open(metadata_path) as mf:
            meta_list = json.load(mf)
            metadata = {m.get("filename", ""): m for m in meta_list}

    # Enrich images with metadata
    for img in images:
        if img["filename"] in metadata:
            img.update({
                "title": metadata[img["filename"]].get("title"),
                "source": metadata[img["filename"]].get("source"),
                "relevance": metadata[img["filename"]].get("relevance"),
            })

    return {"images": images, "count": len(images)}


@router.get("/assets/file/{category}/{filename}")
async def serve_asset_file(category: str, filename: str):
    """Serve an asset file (image/video)."""
    if category not in ["images", "generated", "videos"]:
        raise HTTPException(400, "Invalid category")

    filepath = Path(settings.clip_storage_path) / "assets" / category / filename
    if not filepath.exists():
        raise HTTPException(404, "File not found")

    return FileResponse(str(filepath))
