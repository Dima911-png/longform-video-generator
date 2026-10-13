"""
generate_voice.py - Generate voice narration using Edge TTS.

Converts text to speech using Microsoft Edge TTS (free, no API key required).
Supports single audio generation and batch processing from segments.json.
"""

import argparse
import asyncio
import os
import subprocess
import tempfile
from pathlib import Path

import edge_tts
from dotenv import load_dotenv

from utils import load_segments, ensure_dir, get_all_segments


async def generate_voice_async(
    text: str,
    output_path: str,
    voice: str = "en-US-DavisNeural",
    rate: str = "+0%"
) -> bool:
    """
    Generate speech from text using Edge TTS.

    Args:
        text: The text to convert to speech
        output_path: Path to save the audio file
        voice: Edge TTS voice name
        rate: Speech rate adjustment (e.g., "+10%", "-10%")

    Returns:
        True if successful, False otherwise
    """
    try:
        communicate = edge_tts.Communicate(text, voice, rate=rate)
        await communicate.save(output_path)
        return True
    except Exception as e:
        print(f"  Edge TTS unavailable ({e}); using local eSpeak voice.")
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        wav_path = None
        try:
            output.unlink(missing_ok=True)
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp:
                wav_path = temp.name
            lang = "ru" if voice.startswith("ru-") or any("\u0400" <= ch <= "\u04FF" for ch in text) else "en"
            result = subprocess.run(["espeak-ng", "-v", lang, "-s", "155", "-w", wav_path, text], capture_output=True, text=True, timeout=180)
            if result.returncode != 0 or not Path(wav_path).exists() or Path(wav_path).stat().st_size < 1000:
                raise RuntimeError(result.stderr or "eSpeak did not create a valid WAV")
            convert = subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", wav_path, "-codec:a", "libmp3lame", "-q:a", "3", str(output)], capture_output=True, text=True, timeout=180)
            Path(wav_path).unlink(missing_ok=True)
            if convert.returncode != 0 or not output.exists() or output.stat().st_size < 1000:
                raise RuntimeError(convert.stderr or "FFmpeg did not create a valid MP3")
            print("  Saved fallback narration using local eSpeak NG.")
            return True
        except Exception as fallback_error:
            if wav_path:
                Path(wav_path).unlink(missing_ok=True)
            output.unlink(missing_ok=True)
            print(f"  Local voice fallback failed: {fallback_error}")
            return False


def generate_voice(
    text: str,
    output_path: str,
    voice: str = "en-US-DavisNeural",
    rate: str = "+0%"
) -> bool:
    """
    Synchronous wrapper for generate_voice_async.
    """
    return asyncio.run(generate_voice_async(text, output_path, voice, rate))


def batch_generate(
    segments_file: str,
    output_dir: str,
    voice: str = None,
    rate: str = "+0%"
) -> None:
    """
    Generate voice audio for all segments in a segments.json file.

    Args:
        segments_file: Path to segments.json
        output_dir: Directory to save audio files
        voice: Override voice (uses segments.json voice if not specified)
        rate: Speech rate adjustment
    """
    data = load_segments(segments_file)
    output_path = ensure_dir(Path(output_dir))

    # Use voice from segments.json if not overridden
    default_voice = voice or data.get("voice", "en-US-DavisNeural")

    segments = get_all_segments(data)
    total = len(segments)

    print(f"Generating {total} audio files with voice: {default_voice}...")

    for i, (segment, chapter) in enumerate(segments, 1):
        segment_id = segment["segment_id"]
        audio_file = output_path / f"{segment_id}.mp3"

        # Reuse only valid non-empty audio files; remove failed empty placeholders.
        if audio_file.exists() and audio_file.stat().st_size > 1000:
            probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(audio_file)], capture_output=True, text=True)
            if probe.returncode == 0 and probe.stdout.strip():
                print(f"[{i}/{total}] Skipping {segment_id} (valid audio already exists)")
                continue
        audio_file.unlink(missing_ok=True)

        narration = segment.get("narration", "")
        if not narration:
            print(f"[{i}/{total}] Skipping {segment_id} (no narration)")
            continue

        print(f"[{i}/{total}] Generating {segment_id}...")

        success = generate_voice(narration, str(audio_file), default_voice, rate)

        if success:
            print(f"  Saved to {audio_file}")
        else:
            print(f"  Failed to generate {segment_id}")

    print("Done!")


async def list_voices_async():
    """List all available Edge TTS voices."""
    voices = await edge_tts.list_voices()
    return voices


def list_voices():
    """List available voices, filtered to English."""
    voices = asyncio.run(list_voices_async())

    # Filter to English voices
    english_voices = [v for v in voices if v["Locale"].startswith("en-")]

    print("Available English voices:\n")
    print(f"{'Voice ID':<30} {'Gender':<10} {'Description'}")
    print("-" * 70)

    for voice in sorted(english_voices, key=lambda x: x["ShortName"]):
        print(f"{voice['ShortName']:<30} {voice['Gender']:<10} {voice['Locale']}")


def main():
    # Load environment variables
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Generate voice narration using Edge TTS"
    )
    subparsers = parser.add_subparsers(dest="command")

    # Single audio
    single = subparsers.add_parser("single", help="Generate a single audio file")
    single.add_argument("--text", required=True, help="Text to convert to speech")
    single.add_argument("--output", required=True, help="Output file path")
    single.add_argument(
        "--voice",
        default=os.getenv("DEFAULT_VOICE", "en-US-DavisNeural"),
        help="Edge TTS voice name"
    )
    single.add_argument(
        "--rate",
        default=os.getenv("DEFAULT_SPEECH_RATE", "+0%"),
        help="Speech rate (e.g., '+10%%', '-10%%')"
    )

    # Batch mode
    batch = subparsers.add_parser("batch", help="Batch generate from segments.json")
    batch.add_argument("--segments", required=True, help="Path to segments.json")
    batch.add_argument("--output-dir", required=True, help="Output directory for audio")
    batch.add_argument("--voice", help="Override voice from segments.json")
    batch.add_argument(
        "--rate",
        default=os.getenv("DEFAULT_SPEECH_RATE", "+0%"),
        help="Speech rate"
    )

    # List voices
    subparsers.add_parser("list-voices", help="List available voices")

    args = parser.parse_args()

    if args.command == "single":
        print(f"Generating audio with voice: {args.voice}...")
        success = generate_voice(args.text, args.output, args.voice, args.rate)
        if success:
            print(f"Saved to {args.output}")
        else:
            print("Failed to generate audio")

    elif args.command == "batch":
        batch_generate(args.segments, args.output_dir, args.voice, args.rate)

    elif args.command == "list-voices":
        list_voices()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
