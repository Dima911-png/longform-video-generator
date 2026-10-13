# Long-Form Video Generator

A Python-based CLI tool system for creating 30+ minute documentary-style videos using AI-generated content. The system produces professional videos from still images with Ken Burns effects, AI voiceover narration, and background music.


## One-click video generation on GitHub (phone-friendly)

This fork includes a GitHub Actions workflow that can generate a narrated educational video from a topic without installing Python or FFmpeg on your phone.

1. In the repository, open **Settings → Secrets and variables → Actions → New repository secret**.
2. Set the secret name to `GEMINI_API_KEY` and paste your key from Google AI Studio into the secret value. Never put the key in a source file or commit.
3. Open the **Actions** tab and select **Generate long-form educational video**.
4. Tap **Run workflow**, enter the topic, choose Russian or English and select 10, 15 or 20 minutes.
5. When the run succeeds, open it and download the **educational-video** artifact. It contains the MP4 with burned-in subtitles, the scene plan and subtitle file.

The workflow creates the narration and visual plan, generates scene images, creates voiceover with Edge TTS, animates images with pan/zoom, adds readable subtitles, and checks the final video duration. The target length is approximate; generated scripts and voice timing can vary.

**Important:** the workflow is committed but has not been tested with your API key yet. Google image-generation model access and free-tier quotas depend on your Google AI Studio account and can cause a run to fail or require billing. GitHub Actions must be enabled for the repository. No API key is needed for Edge TTS voice generation.

## Features

- **You Control the Content**: Write your own narration script and image prompts
- **AI Image Generation**: Turn your image prompts into visuals via Gemini API (Imagen 3)
- **AI Voice Synthesis**: Convert your script to natural speech via Edge TTS
- **Ken Burns Effects**: Smooth zoom and pan animations bring still images to life
- **Chapter-Based Structure**: Organize content into chapters with automatic YouTube chapter markers
- **Background Music**: Layer royalty-free music at configurable volumes
- **Batch Processing**: Generate all assets in one command with idempotent reruns
- **Completely Free**: Uses Gemini free tier and Edge TTS (no API costs for voice)

## Target Use Cases

- Historical documentaries (e.g., "The Fall of Rome", "The Space Race")
- Futuristic/speculative narratives (e.g., "Mars Colony 2150", "The AI Revolution")
- Educational content (e.g., "How the Internet Works", "The History of Mathematics")

## Requirements

- **Python**: 3.10 or higher
- **FFmpeg**: Must be installed on your system
- **Gemini API Key**: Free from [Google AI Studio](https://aistudio.google.com/)

### Install FFmpeg

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html
```

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd longform-video-generator
   ```

2. **Install dependencies with uv**:
   ```bash
   uv sync
   ```

   Or with pip:
   ```bash
   pip install -e .
   ```

3. **Set up environment variables**:
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add your Gemini API key:
   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

## How It Works

**You provide:**
1. Your **narration script** (the text to be spoken)
2. Your **image prompts** (descriptions of images to generate)

**The system then:**
1. Generates images from your prompts via Gemini API
2. Generates voice narration from your script via Edge TTS
3. Combines images + audio with Ken Burns effects
4. Assembles everything into a final video

All your content goes into a single `segments.json` file that defines the entire video structure.

## Quick Start

### 1. Initialize a New Project

```bash
python scripts/init_project.py "My Documentary"
```

This creates:
```
projects/my_documentary/
├── segments.json    # Your script and image prompts go here
├── images/          # Generated images
├── audio/           # Generated audio
└── clips/           # Generated video clips
```

### 2. Write Your segments.json

Edit `segments.json` with your own narration and image prompts:

```json
{
  "project_name": "My Documentary",
  "voice": "en-GB-RyanNeural",
  "chapters": [
    {
      "chapter_id": 1,
      "title": "Introduction",
      "music_track": "background.mp3",
      "music_volume": 0.15,
      "segments": [
        {
          "segment_id": "001",
          "narration": "Write your narration script here. This text will be converted to speech.",
          "image_prompt": "Describe the image you want generated here. Include style keywords like photorealistic, cinematic lighting, 16:9 aspect ratio.",
          "ken_burns_sequence": ["zoom_in"],
          "transition": "fade"
        },
        {
          "segment_id": "002",
          "narration": "Your next segment of narration goes here...",
          "image_prompt": "Description for the second image...",
          "ken_burns_sequence": ["pan_left"],
          "transition": "cut"
        }
      ]
    }
  ]
}
```

Each segment becomes one scene in your video with:
- **narration**: The script text (converted to voice)
- **image_prompt**: What image to generate for this scene
- **ken_burns_sequence**: Camera movement effect(s)
- **transition**: How to transition to the next segment

> **Tip:** Need help writing content? Optional AI prompt templates are available in `prompts/` to assist with script writing and segment planning.

### 3. Generate All Assets

```bash
# Generate images (requires Gemini API key)
python scripts/generate_image.py batch \
    --segments projects/my_documentary/segments.json \
    --output-dir projects/my_documentary/images

# Generate voice narration (free, no API key needed)
python scripts/generate_voice.py batch \
    --segments projects/my_documentary/segments.json \
    --output-dir projects/my_documentary/audio

# Create video segments with Ken Burns effects
python scripts/create_segment.py batch \
    --segments projects/my_documentary/segments.json \
    --images-dir projects/my_documentary/images \
    --audio-dir projects/my_documentary/audio \
    --output-dir projects/my_documentary/clips \
    --music-dir music/

# Assemble final video
python scripts/assemble_video.py \
    --clips-dir projects/my_documentary/clips \
    --segments projects/my_documentary/segments.json \
    --output projects/my_documentary/final_video.mp4
```

## Project Structure

```
longform-video-generator/
├── scripts/                  # Core Python tools
│   ├── generate_image.py     # Gemini API image generation
│   ├── generate_voice.py     # Edge TTS voice synthesis
│   ├── create_segment.py     # Ken Burns + audio merge
│   ├── assemble_video.py     # Final video concatenation
│   └── utils.py              # Shared utilities
│
├── prompts/                  # Optional AI prompt templates
│   ├── 1_script_generator.md # Help writing documentary scripts
│   └── 2_segment_planner.md  # Help planning segments
│
├── music/                    # Royalty-free background tracks
│
└── projects/                 # Generated project folders
    └── example_project/      # Example "Fall of Rome" project
```

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GEMINI_API_KEY` | Yes | - | Your Gemini API key |
| `DEFAULT_VOICE` | No | `en-GB-RyanNeural` | Default narration voice |
| `DEFAULT_SPEECH_RATE` | No | `+0%` | Speech rate adjustment |
| `DEFAULT_PADDING_START` | No | `0.5` | Seconds before narration |
| `DEFAULT_PADDING_END` | No | `0.5` | Seconds after narration |
| `DEFAULT_MUSIC_VOLUME` | No | `0.15` | Background music volume (0.0-1.0) |
| `GEMINI_DELAY_SECONDS` | No | `2` | Delay between API calls |

### Recommended Voices

| Voice ID | Description | Best For |
|----------|-------------|----------|
| `en-GB-RyanNeural` | British male | Historical, formal content |
| `en-GB-SoniaNeural` | British female | Elegant narration |
| `en-US-GuyNeural` | American male, deep | General content |
| `en-US-DavisNeural` | American male, warm | Friendly content |
| `en-US-AriaNeural` | American female | Expressive narration |

List all available voices:
```bash
python scripts/generate_voice.py list-voices
```

## segments.json Format

The `segments.json` file defines the entire video structure:

```json
{
  "project_name": "The Fall of Rome",
  "voice": "en-GB-RyanNeural",
  "chapters": [
    {
      "chapter_id": 1,
      "title": "The Golden Age",
      "music_track": "epic_orchestral.mp3",
      "music_volume": 0.15,
      "segments": [
        {
          "segment_id": "001",
          "narration": "At its height, the Roman Empire stretched from Britain to Mesopotamia...",
          "image_prompt": "Panoramic aerial view of ancient Rome, the Colosseum prominent, golden hour lighting, photorealistic, 16:9 aspect ratio",
          "ken_burns_sequence": ["zoom_out"],
          "transition": "fade"
        }
      ]
    }
  ]
}
```

## Ken Burns Effects

| Effect | Description | Best For |
|--------|-------------|----------|
| `zoom_in` | Slow zoom into center | Reveals, emphasis, emotional moments |
| `zoom_out` | Slow zoom out from center | Establishing shots, showing scale |
| `pan_left` | Pan from right to left | Landscapes, following movement |
| `pan_right` | Pan from left to right | Landscapes, following movement |
| `pan_up` | Tilt from bottom to top | Tall structures, looking skyward |
| `pan_down` | Tilt from top to bottom | Reveals from above |

Multiple effects can be chained in `ken_burns_sequence` - duration is split equally.

### Using Static Images (No Ken Burns)

You can disable Ken Burns effects and use static images in two ways:

**Per-segment:** Leave `ken_burns_sequence` empty or omit it entirely:
```json
{
  "segment_id": "001",
  "narration": "Your text here...",
  "image_prompt": "Your prompt here...",
  "ken_burns_sequence": [],
  "transition": "fade"
}
```

**Per-chapter:** Set `ken_burns_enabled` to `false` to disable effects for all segments in that chapter:
```json
{
  "chapter_id": 1,
  "title": "Introduction",
  "ken_burns_enabled": false,
  "music_track": "background.mp3",
  "segments": [...]
}
```

When disabled, images are scaled to fit 1920x1080 and displayed statically for the duration of the narration.

## Output Specifications

- **Resolution**: 1920x1080 (16:9)
- **Frame Rate**: 30 fps
- **Video Codec**: H.264 (libx264)
- **Audio Codec**: AAC at 192 kbps stereo

## Script Commands

### generate_image.py

```bash
# Generate a single image
python scripts/generate_image.py single \
    --prompt "Ancient Roman forum at sunset, photorealistic, 16:9" \
    --output test_image.png

# Batch generate from segments.json
python scripts/generate_image.py batch \
    --segments segments.json \
    --output-dir images/
```

### generate_voice.py

```bash
# Generate a single voice clip
python scripts/generate_voice.py single \
    --text "The Roman Empire was vast." \
    --output narration.mp3 \
    --voice en-GB-RyanNeural

# Batch generate from segments.json
python scripts/generate_voice.py batch \
    --segments segments.json \
    --output-dir audio/

# List available voices
python scripts/generate_voice.py list-voices
```

### create_segment.py

```bash
# Create a single segment
python scripts/create_segment.py single \
    --image image.png \
    --audio narration.mp3 \
    --output segment.mp4 \
    --effects zoom_in pan_left

# Batch create from segments.json
python scripts/create_segment.py batch \
    --segments segments.json \
    --images-dir images/ \
    --audio-dir audio/ \
    --output-dir clips/ \
    --music-dir music/
```

### assemble_video.py

```bash
python scripts/assemble_video.py \
    --clips-dir clips/ \
    --segments segments.json \
    --output final_video.mp4
```

This also generates a `.chapters.txt` file for YouTube chapter markers.

## Architecture

The core workflow is simple:

1. **You write** your narration script and image prompts in `segments.json`
2. **Scripts generate** images and audio from your content
3. **Scripts assemble** everything into the final video

Each Python script:
- Performs a single, well-defined task
- Reads your content from `segments.json`
- Calls one external API (Gemini for images, Edge TTS for voice)
- Supports both single-item and batch modes
- Skips existing files (idempotent/resumable)
- Prints progress to stdout

> **Optional:** AI prompt templates in `prompts/` can help you write scripts and plan segments if you'd like AI assistance with the creative process.

## Troubleshooting

### FFmpeg not found
Ensure FFmpeg is installed and in your PATH:
```bash
ffmpeg -version
```

### Edge TTS timeout
Large text blocks may timeout. The batch processor automatically handles chunking, but for manual use, keep narration under 500 words per call.

### Gemini API rate limits
The free tier has usage limits. If you hit rate limits, increase `GEMINI_DELAY_SECONDS` in your `.env` file.

### Image generation fails
Ensure your prompt includes:
- Style keywords: "photorealistic", "cinematic lighting"
- Aspect ratio: "16:9 aspect ratio"

## License

[Add your license here]

## Acknowledgments

- Inspired by [pokemon-ai-video-generator](https://github.com/bhancockio/pokemon-ai-video-generator)
- Images generated by [Google Gemini](https://ai.google.dev/)
- Voice synthesis by [Edge TTS](https://github.com/rany2/edge-tts)
