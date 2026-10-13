"""
generate_image.py - Generate images using Google Gemini API (Imagen 3).

Generates images from text prompts using the Gemini API.
Supports single image generation and batch processing from segments.json.
"""

import argparse
import os
import time
import hashlib
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from dotenv import load_dotenv
from google import genai
from google.genai import types

from utils import load_segments, ensure_dir, get_all_segments



def generate_fallback_visual(prompt: str, output_path: str) -> bool:
    """Create a polished local visual when the image API has no available quota."""
    try:
        width, height = 1280, 720
        digest = hashlib.sha256(prompt.encode("utf-8")).digest()
        c1 = (12 + digest[0] % 22, 24 + digest[1] % 30, 48 + digest[2] % 38)
        c2 = (18 + digest[3] % 28, 50 + digest[4] % 50, 75 + digest[5] % 65)
        image = Image.new("RGB", (width, height))
        px = image.load()
        for y in range(height):
            t = y / (height - 1)
            for x in range(width):
                glow = max(0.0, 1 - math.sqrt(((x - width*.78)/(width*.8))**2 + ((y-height*.25)/(height*.9))**2))
                px[x, y] = tuple(int(c1[k]*(1-t) + c2[k]*t + glow*(12 if k == 2 else 4)) for k in range(3))
        draw = ImageDraw.Draw(image, "RGBA")
        accent = (83 + digest[6] % 100, 165 + digest[7] % 70, 220, 85)
        for i in range(5):
            r = 120 + i * 42
            draw.ellipse((850-r, 330-r, 850+r, 330+r), outline=accent, width=2)
        draw.rounded_rectangle((70, 68, 290, 112), radius=20, fill=(255,255,255,22), outline=(255,255,255,65), width=1)
        draw.text((92, 81), "EDUCATIONAL FILM", fill=(225,239,255,235))
        clean = prompt.replace("_", " ").replace("-", " ")
        words = [w.strip(".,:;!?()[]{}") for w in clean.split() if w.strip(".,:;!?()[]{}")]
        heading = " ".join(words[:9]) or "Новая тема"
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 43)
            small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)
        except OSError:
            font, small = ImageFont.load_default(), ImageFont.load_default()
        lines, current = [], ""
        for word in heading.split():
            candidate = (current + " " + word).strip()
            if draw.textbbox((0,0), candidate, font=font)[2] > 700 and current:
                lines.append(current)
                current = word
            else:
                current = candidate
        if current:
            lines.append(current)
        y = 245
        for line in lines[:4]:
            draw.text((76, y), line, font=font, fill=(255,255,255,255), stroke_width=1, stroke_fill=(0,0,0,100))
            y += 58
        draw.rounded_rectangle((76, 535, 520, 590), radius=14, fill=(255,255,255,20), outline=(255,255,255,55), width=1)
        draw.text((98, 552), "Краткая визуальная сцена", font=small, fill=(205,225,245,255))
        for i in range(34):
            x = 650 + digest[i % len(digest)] * 2
            ydot = (digest[(i+11) % len(digest)] * 3) % height
            radius = 2 + digest[(i+17) % len(digest)] % 5
            draw.ellipse((x-radius, ydot-radius, x+radius, ydot+radius), fill=(170,220,255,90))
        image.save(output_path, "PNG")
        print("  Image API unavailable; created a local motion-graphic visual instead.")
        return True
    except Exception as fallback_error:
        print(f"  Could not create fallback visual: {fallback_error}")
        return False


def generate_image(prompt: str, output_path: str, api_key: str) -> bool:
    """
    Generate a single image from a text prompt using Nano Banana Pro.

    Args:
        prompt: The image generation prompt
        output_path: Path to save the generated image
        api_key: Gemini API key

    Returns:
        True if successful, False otherwise
    """
    client = genai.Client(api_key=api_key)

    try:
        # Nano Banana Pro uses generate_content with IMAGE modality
        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
            ),
        )

        # Extract image from response
        if response.candidates and response.candidates[0].content.parts:
            part = response.candidates[0].content.parts[0]
            if hasattr(part, 'inline_data') and part.inline_data:
                # Save the image data
                image_data = part.inline_data.data
                with open(output_path, 'wb') as f:
                    f.write(image_data)
                return True

        print(f"  No image generated for prompt")
        return False

    except Exception as e:
        print(f"  Error generating image: {e}")
        return generate_fallback_visual(prompt, output_path)


def batch_generate(segments_file: str, output_dir: str, api_key: str, delay: float = 2.0) -> None:
    """
    Generate images for all segments in a segments.json file.

    Args:
        segments_file: Path to segments.json
        output_dir: Directory to save images
        api_key: Gemini API key
        delay: Delay between API calls in seconds
    """
    data = load_segments(segments_file)
    output_path = ensure_dir(Path(output_dir))

    segments = get_all_segments(data)
    total = len(segments)

    print(f"Generating {total} images...")

    for i, (segment, chapter) in enumerate(segments, 1):
        segment_id = segment["segment_id"]
        image_file = output_path / f"{segment_id}.png"

        # Skip if already exists
        if image_file.exists():
            print(f"[{i}/{total}] Skipping {segment_id} (already exists)")
            continue

        prompt = segment.get("image_prompt", "")
        if not prompt:
            print(f"[{i}/{total}] Skipping {segment_id} (no prompt)")
            continue

        print(f"[{i}/{total}] Generating {segment_id}...")

        success = generate_image(prompt, str(image_file), api_key)

        if success:
            print(f"  Saved to {image_file}")
        else:
            print(f"  Failed to generate {segment_id}")

        # Delay between requests to avoid rate limiting
        if i < total:
            time.sleep(delay)

    print("Done!")


def main():
    parser = argparse.ArgumentParser(
        description="Generate images using Gemini API (Imagen 3)"
    )
    subparsers = parser.add_subparsers(dest="command")

    # Single image
    single = subparsers.add_parser("single", help="Generate a single image")
    single.add_argument("--prompt", required=True, help="Image generation prompt")
    single.add_argument("--output", required=True, help="Output file path")

    # Batch mode
    batch = subparsers.add_parser("batch", help="Batch generate from segments.json")
    batch.add_argument("--segments", required=True, help="Path to segments.json")
    batch.add_argument("--output-dir", required=True, help="Output directory for images")
    batch.add_argument("--delay", type=float, default=2.0, help="Delay between API calls (seconds)")

    args = parser.parse_args()

    # Load environment variables
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        print("Error: GEMINI_API_KEY not found in environment variables")
        print("Please set it in your .env file")
        return

    if args.command == "single":
        print(f"Generating image...")
        success = generate_image(args.prompt, args.output, api_key)
        if success:
            print(f"Saved to {args.output}")
        else:
            print("Failed to generate image")

    elif args.command == "batch":
        batch_generate(args.segments, args.output_dir, api_key, args.delay)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
