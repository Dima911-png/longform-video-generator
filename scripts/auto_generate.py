#!/usr/bin/env python3
"""Generate a long-form educational video plan from a topic with Gemini."""
import argparse
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path


def gemini_text(api_key: str, prompt: str) -> str:
    url = ("https://generativelanguage.googleapis.com/v1beta/models/"
           "gemini-2.5-flash:generateContent?key=" + api_key)
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.65, "responseMimeType": "application/json"},
    }
    request = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=240) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Gemini API HTTP {exc.code}: {details[:1500]}") from exc
    try:
        text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError("Gemini returned no text: " + json.dumps(data)[:1500]) from exc
    text = re.sub(r"^\x60{3}(?:json)?\s*", "", text)
    text = re.sub(r"\s*\x60{3}$", "", text)
    return text


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", required=True)
    parser.add_argument("--language", choices=["Russian", "English"], default="Russian")
    parser.add_argument("--minutes", type=int, choices=[10, 15, 20], default=10)
    parser.add_argument("--output", default="projects/auto_video/segments.json")
    args = parser.parse_args()

    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise SystemExit("Missing GEMINI_API_KEY repository secret.")

    target_words = args.minutes * 135
    voice = "ru-RU-SvetlanaNeural" if args.language == "Russian" else "en-US-AriaNeural"
    prompt = f"""
You write researched educational documentary voiceover scripts and storyboard plans.
Topic: {args.topic}
Language of narration and chapter titles: {args.language}
Duration: at least {args.minutes} minutes at a measured 135 words/minute.
Write about {target_words} words in total. Produce exactly 4 chapters and 5 scenes per chapter (20 scenes).
Each scene should contain around 100-120 spoken words, so the total script is long enough.
Narration should be natural when read aloud, specific, engaging, and factually careful.
Avoid invented quotations, unsupported claims, repeated filler, lists, and meta commentary.
For every scene provide a unique detailed English visual prompt for a cinematic documentary image in 16:9 landscape, no text, no letters, no watermark.
Return ONLY valid JSON with this structure:
{{
 "project_name": "short title",
 "voice": "{voice}",
 "chapters": [
  {{
   "chapter_id": 1,
   "title": "chapter title in {args.language}",
   "music_volume": 0.10,
   "ken_burns_enabled": true,
   "segments": [
    {{
     "segment_id": "001",
     "narration": "spoken narration in {args.language}",
     "image_prompt": "specific English visual prompt, 16:9, no text or watermark",
     "ken_burns_sequence": ["zoom_in"],
     "transition": "fade"
    }}
   ]
  }}
 ]
}}
Use chapter ids 1-4, segment ids "001" through "020" sequentially, and visual prompts that match each scene. No markdown fences.
"""
    raw = gemini_text(key, prompt)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Gemini returned invalid JSON: {exc}\n{raw[:1000]}") from exc

    segments = [segment for chapter in data.get("chapters", [])
                for segment in chapter.get("segments", [])]
    if len(segments) != 20:
        raise SystemExit(f"Expected 20 scenes, Gemini returned {len(segments)}. Retry the workflow.")
    for segment in segments:
        if not segment.get("narration") or not segment.get("image_prompt"):
            raise SystemExit(f"Scene {segment.get('segment_id')} is missing narration or image_prompt.")
    for chapter in data["chapters"]:
        chapter.pop("music_track", None)

    word_count = sum(len(segment["narration"].split()) for segment in segments)
    if word_count < target_words * 0.70:
        raise SystemExit(f"Script too short: {word_count} words, target about {target_words}. Retry.")
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Script saved: {output}; {len(segments)} scenes; {word_count} words.")
if __name__ == "__main__":
    main()
