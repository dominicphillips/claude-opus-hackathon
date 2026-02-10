"""Image Customizer — Gemini style extraction + SDXL inpainting via Replicate.

Two-step pipeline:
1. Gemini Flash analyzes the art style of the source image
2. SDXL Inpainting via Replicate paints the child into the scene
"""

import asyncio
import logging
import os
import uuid
from pathlib import Path
from typing import AsyncGenerator

from PIL import Image

from app.core.config import settings

logger = logging.getLogger(__name__)


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

    # Step 1: Create mask
    yield {"step": "mask", "status": "running", "detail": "Creating mask for character placement...", "progress": 0.1}

    mask_path = str(output_dir / f"mask_{uuid.uuid4()}.png")
    _create_mask(scene_image_path, mask_path, mask_position)

    yield {"step": "mask", "status": "done", "detail": "Mask created", "progress": 0.2}

    # Step 2: Analyze art style with Gemini
    yield {"step": "style_analysis", "status": "running", "detail": "Gemini is analyzing the art style of the scene...", "progress": 0.25}

    art_style = await _analyze_art_style(scene_image_path)

    yield {"step": "style_analysis", "status": "done", "detail": f"Style detected: {art_style[:100]}...", "progress": 0.4}

    # Step 3: Build final prompt
    yield {"step": "prompt", "status": "running", "detail": "Building generation prompt...", "progress": 0.45}

    final_prompt = (
        f"An illustration of {child_description}. "
        f"The character is standing naturally in the scene, interacting with the environment. "
        f"Art style: {art_style}. "
        "High quality, seamless blend with the existing scene, same artistic technique."
    )

    yield {"step": "prompt", "status": "done", "detail": f"Prompt: {final_prompt[:120]}...", "progress": 0.5}

    # Step 4: Generate via Replicate inpainting
    yield {"step": "inpainting", "status": "running", "detail": "SDXL is painting your child into the scene... this takes 15-30 seconds", "progress": 0.55}

    result_url = await _run_inpainting(scene_image_path, mask_path, final_prompt)

    yield {"step": "inpainting", "status": "done", "detail": "Inpainting complete!", "progress": 0.85}

    # Step 5: Download result
    yield {"step": "download", "status": "running", "detail": "Downloading generated image...", "progress": 0.9}

    local_path = await _download_result(result_url, output_dir)

    yield {"step": "download", "status": "done", "detail": "Image saved", "progress": 0.95}

    # Done
    filename = Path(local_path).name
    yield {
        "step": "complete",
        "status": "done",
        "detail": "Your child has been added to the scene!",
        "progress": 1.0,
        "result_url": f"/api/agents/assets/file/customized/{filename}",
        "result_path": local_path,
    }


async def _analyze_art_style(image_path: str) -> str:
    """Use Gemini to analyze the art style of an image."""
    from google import genai

    client = genai.Client(api_key=settings.gemini_api_key)

    # Upload the image
    with open(image_path, "rb") as f:
        image_bytes = f.read()

    import base64
    image_b64 = base64.b64encode(image_bytes).decode()

    # Determine mime type
    ext = Path(image_path).suffix.lower()
    mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}
    mime_type = mime_map.get(ext, "image/jpeg")

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
                    {
                        "text": """Analyze this image's ART STYLE precisely. Describe in one paragraph:
1. The medium (watercolor, digital, stop-motion, vector, etc.)
2. The line work (thick outlines, thin, no outlines, sketchy)
3. The color palette (muted earth tones, pastel, vibrant, warm/cool)
4. Texture (paper grain, smooth, brushstrokes visible)
5. Character style (rounded, angular, realistic, exaggerated proportions)

Output ONLY the style description paragraph, nothing else."""
                    }
                ]
            }
        ],
    )

    return response.text.strip()


async def _run_inpainting(scene_path: str, mask_path: str, prompt: str) -> str:
    """Run SDXL inpainting via Replicate."""
    import replicate

    os.environ["REPLICATE_API_TOKEN"] = settings.replicate_api_token

    output = await asyncio.to_thread(
        replicate.run,
        "stability-ai/stable-diffusion-inpainting",
        input={
            "prompt": prompt,
            "negative_prompt": "photorealistic, 3d render, distorted face, bad anatomy, text, watermark, blurry, low quality",
            "image": open(scene_path, "rb"),
            "mask": open(mask_path, "rb"),
            "prompt_strength": 0.8,
            "num_inference_steps": 30,
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


def _create_mask(image_path: str, output_path: str, position: str = "center") -> str:
    """Create an inpainting mask — white area = where to draw the child."""
    img = Image.open(image_path)
    mask = Image.new("L", img.size, 0)  # All black (keep original)
    w, h = img.size

    positions = {
        "center": (0.3, 0.3, 0.7, 0.9),
        "left": (0.05, 0.3, 0.4, 0.9),
        "right": (0.6, 0.3, 0.95, 0.9),
        "small_center": (0.35, 0.45, 0.65, 0.85),
    }

    coords = positions.get(position, positions["center"])
    left = int(w * coords[0])
    top = int(h * coords[1])
    right = int(w * coords[2])
    bottom = int(h * coords[3])

    # Draw white rectangle for the child placement area
    for x in range(left, right):
        for y in range(top, bottom):
            mask.putpixel((x, y), 255)

    mask.save(output_path)
    return output_path
