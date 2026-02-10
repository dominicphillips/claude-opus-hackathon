"""Image Finder Agent — uses Claude Agent SDK to browse the web for show images.

This agent searches the internet for images related to a TV show, character, or theme,
downloads them to a local folder, and returns metadata for the asset library.
"""

import asyncio
import json
import logging
import os
import uuid
from pathlib import Path

from claude_agent_sdk import ClaudeAgentOptions, query

from app.core.config import settings

logger = logging.getLogger(__name__)

AGENT_SYSTEM_PROMPT = """You are an image research assistant for StorySpark, a children's TV show clip studio.

Your job is to find high-quality, family-friendly images related to children's TV shows, characters, and themes.

When given a search query (e.g., "Frog & Toad", "Frog & Toad garden scene", "cartoon frog and toad friends"):

1. Use WebSearch to find relevant images from official sources, fan art sites, and image databases
2. Focus on finding:
   - Official character art and promotional images
   - Scene screenshots from the show
   - Thematic background images (gardens, ponds, cozy homes)
   - Illustrations in a similar art style
3. Use WebFetch to access image gallery pages and find direct image URLs
4. Return a JSON array of found images with this structure:
   [
     {
       "url": "https://example.com/image.jpg",
       "title": "Description of the image",
       "source": "Where it was found",
       "category": "character|scene|background|theme",
       "relevance": "high|medium|low"
     }
   ]

IMPORTANT:
- Only find family-friendly, appropriate images
- Prefer official and high-quality sources
- Include the source attribution
- Return at least 5-10 images per search
- Focus on images that would work as visual assets in a children's app
"""


async def find_images(search_query: str, output_dir: str | None = None) -> list[dict]:
    """Use Claude Agent SDK to find images for a TV show/character/theme.

    Args:
        search_query: What to search for (e.g., "Frog & Toad Apple TV")
        output_dir: Directory to store downloaded images (optional)

    Returns:
        List of image metadata dicts with url, title, source, category, relevance
    """
    if output_dir is None:
        output_dir = str(Path(settings.clip_storage_path) / "assets" / "images")

    os.makedirs(output_dir, exist_ok=True)

    prompt = f"""Search the web for images related to: "{search_query}"

Find 5-10 high-quality, family-friendly images that could be used as visual assets
in a children's storytelling app. Focus on:
- Official promotional art
- Character illustrations
- Scene/background images
- Thematic imagery

Return your findings as a JSON array with this exact format:
[
  {{
    "url": "direct image URL",
    "title": "description of what the image shows",
    "source": "website where it was found",
    "category": "character|scene|background|theme",
    "relevance": "high|medium|low"
  }}
]

IMPORTANT: Return ONLY the JSON array, no other text."""

    images = []

    async for message in query(
        prompt=prompt,
        options=ClaudeAgentOptions(
            system_prompt=AGENT_SYSTEM_PROMPT,
            allowed_tools=["WebSearch", "WebFetch"],
            max_turns=10,
        ),
    ):
        if hasattr(message, "result") and message.result:
            # Try to parse JSON from the result
            try:
                result_text = message.result
                # Extract JSON array from response
                start = result_text.find("[")
                end = result_text.rfind("]") + 1
                if start >= 0 and end > start:
                    images = json.loads(result_text[start:end])
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Could not parse agent result as JSON: {e}")

    # Download images to local storage
    downloaded = []
    import httpx

    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        for img in images:
            try:
                url = img.get("url", "")
                if not url or not url.startswith("http"):
                    continue

                response = await client.get(url)
                if response.status_code == 200:
                    content_type = response.headers.get("content-type", "")
                    if "image" not in content_type:
                        continue

                    ext = ".jpg"
                    if "png" in content_type:
                        ext = ".png"
                    elif "webp" in content_type:
                        ext = ".webp"
                    elif "gif" in content_type:
                        ext = ".gif"

                    filename = f"{uuid.uuid4()}{ext}"
                    filepath = os.path.join(output_dir, filename)

                    with open(filepath, "wb") as f:
                        f.write(response.content)

                    img["local_path"] = filepath
                    img["filename"] = filename
                    downloaded.append(img)
                    logger.info(f"Downloaded: {img.get('title', 'unknown')} -> {filename}")

            except Exception as e:
                logger.warning(f"Failed to download {img.get('url', '?')}: {e}")

    # Save metadata
    metadata_path = os.path.join(output_dir, "metadata.json")
    with open(metadata_path, "w") as f:
        json.dump(downloaded, f, indent=2)

    logger.info(f"Found {len(images)} images, downloaded {len(downloaded)}")
    return downloaded


async def generate_image(
    prompt: str,
    output_dir: str | None = None,
) -> dict:
    """Generate an image using Replicate's nano-banana-pro model.

    Args:
        prompt: Image generation prompt
        output_dir: Where to save the generated image

    Returns:
        Dict with local_path, filename, and prompt
    """
    import replicate

    if output_dir is None:
        output_dir = str(Path(settings.clip_storage_path) / "assets" / "generated")

    os.makedirs(output_dir, exist_ok=True)

    output = await asyncio.to_thread(
        replicate.run,
        "google/nano-banana-pro",
        input={
            "prompt": prompt,
            "num_outputs": 1,
        },
    )

    # Download the generated image
    filename = f"{uuid.uuid4()}.png"
    filepath = os.path.join(output_dir, filename)

    import httpx

    async with httpx.AsyncClient(follow_redirects=True, timeout=60.0) as client:
        if isinstance(output, list) and len(output) > 0:
            img_url = str(output[0])
        else:
            img_url = str(output)

        response = await client.get(img_url)
        response.raise_for_status()

        with open(filepath, "wb") as f:
            f.write(response.content)

    return {
        "local_path": filepath,
        "filename": filename,
        "prompt": prompt,
        "model": "google/nano-banana-pro",
    }


async def generate_video(
    prompt: str,
    output_dir: str | None = None,
) -> dict:
    """Generate a video using Replicate's Google Veo 3.1 model.

    Args:
        prompt: Video generation prompt
        output_dir: Where to save the generated video

    Returns:
        Dict with local_path, filename, and prompt
    """
    import replicate

    if output_dir is None:
        output_dir = str(Path(settings.clip_storage_path) / "assets" / "videos")

    os.makedirs(output_dir, exist_ok=True)

    output = await asyncio.to_thread(
        replicate.run,
        "google/veo-3.1",
        input={
            "prompt": prompt,
        },
    )

    filename = f"{uuid.uuid4()}.mp4"
    filepath = os.path.join(output_dir, filename)

    import httpx

    async with httpx.AsyncClient(follow_redirects=True, timeout=120.0) as client:
        if isinstance(output, list) and len(output) > 0:
            vid_url = str(output[0])
        else:
            vid_url = str(output)

        response = await client.get(vid_url)
        response.raise_for_status()

        with open(filepath, "wb") as f:
            f.write(response.content)

    return {
        "local_path": filepath,
        "filename": filename,
        "prompt": prompt,
        "model": "google/veo-3.1",
    }
