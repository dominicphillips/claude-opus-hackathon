"""Image Customizer — Gemini prompt crafting + Banana Pro generation via Replicate.

Two-step pipeline:
1. Gemini Flash analyzes the art style of the source image
2. Gemini Flash crafts the perfect generation prompt
3. Google Nano Banana Pro generates the new image with the scene as reference
"""

import asyncio
import base64
import logging
import os
import uuid
from pathlib import Path
from typing import AsyncGenerator

from app.core.config import settings

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


def _load_prompt(name: str) -> str:
    """Load a prompt template from the prompts/ directory."""
    path = PROMPTS_DIR / f"{name}.txt"
    return path.read_text().strip()


async def stream_customize_image(
    scene_image_path: str,
    child_description: str,
    mask_position: str = "center",
) -> AsyncGenerator[dict, None]:
    """Stream the image customization pipeline with progress updates.

    Yields dicts with: {"step": str, "status": str, "detail": str, "progress": float}
    Final yield includes: {"step": "complete", "result_url": str}
    """
    output_dir = Path(settings.clip_storage_path) / "assets" / "customized"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Analyze art style with Gemini
    yield {"step": "style_analysis", "status": "running", "detail": "Gemini is analyzing the art style of the scene...", "progress": 0.15}

    art_style = await _analyze_art_style(scene_image_path)

    yield {"step": "style_analysis", "status": "done", "detail": f"Style detected: {art_style[:100]}...", "progress": 0.3}

    # Step 2: Ask Gemini to craft the perfect prompt
    yield {"step": "prompt", "status": "running", "detail": "Gemini is crafting the perfect generation prompt...", "progress": 0.35}

    final_prompt = await _craft_prompt(child_description, art_style, mask_position, scene_image_path)

    # Save the prompt for debugging/iteration
    prompt_log_path = output_dir / f"prompt_{uuid.uuid4()}.txt"
    prompt_log_path.write_text(
        f"Child: {child_description}\n\n"
        f"Style: {art_style}\n\n"
        f"Position: {mask_position}\n\n"
        f"Final prompt:\n{final_prompt}"
    )

    yield {"step": "prompt", "status": "done", "detail": f"Prompt: {final_prompt[:120]}...", "progress": 0.45}

    # Step 3: Generate with Banana Pro using scene as reference
    yield {"step": "generating", "status": "running", "detail": "Banana Pro is generating your character in the scene...", "progress": 0.5}

    result_url = await _run_banana_pro(scene_image_path, final_prompt)

    yield {"step": "generating", "status": "done", "detail": "Generation complete!", "progress": 0.85}

    # Step 4: Download result
    yield {"step": "download", "status": "running", "detail": "Downloading generated image...", "progress": 0.9}

    local_path = await _download_result(result_url, output_dir)

    yield {"step": "download", "status": "done", "detail": "Image saved", "progress": 0.95}

    # Done
    filename = Path(local_path).name
    yield {
        "step": "complete",
        "status": "done",
        "detail": "Your character has been added to the scene!",
        "progress": 1.0,
        "result_url": f"/api/agents/assets/file/customized/{filename}",
        "result_path": local_path,
    }


async def _analyze_art_style(image_path: str) -> str:
    """Use Gemini to analyze the art style of an image."""
    from google import genai

    client = genai.Client(api_key=settings.gemini_api_key)

    with open(image_path, "rb") as f:
        image_bytes = f.read()

    image_b64 = base64.b64encode(image_bytes).decode()

    ext = Path(image_path).suffix.lower()
    mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}
    mime_type = mime_map.get(ext, "image/jpeg")

    style_prompt = _load_prompt("style_analysis")

    response = await asyncio.to_thread(
        client.models.generate_content,
        model="gemini-2.0-flash",
        contents=[
            {
                "parts": [
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": image_b64,
                        }
                    },
                    {"text": style_prompt}
                ]
            }
        ],
    )

    return response.text.strip()


async def _craft_prompt(
    child_description: str,
    art_style: str,
    position: str,
    scene_image_path: str,
) -> str:
    """Use Gemini to craft the perfect generation prompt for Banana Pro."""
    from google import genai

    client = genai.Client(api_key=settings.gemini_api_key)

    # Load the scene image so Gemini can see what it's working with
    with open(scene_image_path, "rb") as f:
        image_bytes = f.read()

    image_b64 = base64.b64encode(image_bytes).decode()
    ext = Path(scene_image_path).suffix.lower()
    mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}
    mime_type = mime_map.get(ext, "image/jpeg")

    system_prompt = _load_prompt("scene_composite")

    user_message = (
        f"Here is the reference scene image. I want to add a character to it.\n\n"
        f"Character description: {child_description}\n\n"
        f"Art style analysis of this scene: {art_style}\n\n"
        f"Character position: {position}\n\n"
        f"Craft the generation prompt now."
    )

    response = await asyncio.to_thread(
        client.models.generate_content,
        model="gemini-2.0-flash",
        contents=[
            {
                "parts": [
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": image_b64,
                        }
                    },
                    {"text": f"{system_prompt}\n\n---\n\n{user_message}"}
                ]
            }
        ],
    )

    return response.text.strip()


async def _run_banana_pro(scene_path: str, prompt: str) -> str:
    """Run Banana Pro via Replicate with the scene as reference image."""
    import replicate

    os.environ["REPLICATE_API_TOKEN"] = settings.replicate_api_token

    output = await asyncio.to_thread(
        replicate.run,
        "google/nano-banana-pro",
        input={
            "prompt": prompt,
            "image_input": [open(scene_path, "rb")],
            "aspect_ratio": "match_input_image",
            "resolution": "2K",
            "output_format": "png",
            "safety_filter_level": "block_only_high",
        },
    )

    if isinstance(output, list) and len(output) > 0:
        return str(output[0])
    return str(output)


async def _download_result(url: str, output_dir: Path) -> str:
    """Download the generated image from Replicate."""
    import httpx

    filename = f"custom_{uuid.uuid4()}.png"
    filepath = output_dir / filename

    async with httpx.AsyncClient(follow_redirects=True, timeout=60.0) as client:
        response = await client.get(url)
        response.raise_for_status()
        with open(filepath, "wb") as f:
            f.write(response.content)

    return str(filepath)
