# Reddit Rhymes

Turn Reddit comments into rhyming poetry videos with AI.

## Overview

This project fetches Reddit comments, uses Claude AI to compose them into rhyming poems, and generates videos with comment screenshots, text-to-speech audio, and background video/music.

## Setup

1. Install dependencies:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Download Kokoro TTS models (automatically done by `run.sh`):
- kokoro-v1.0.onnx
- voices-v1.0.bin

3. Check that background assets are in `assets/` folder:
- Background video (webm format)
- Background music (mp3 format)

## Usage

Run the complete pipeline:
```bash
./run.sh [comment_limit] [subreddits]
```

Examples:
- `./run.sh` - Default: 10000 comments from ArtificialInteligence
- `./run.sh 5000` - 5000 comments from ArtificialInteligence  
- `./run.sh 20000 "AmItheAsshole,ArtificialInteligence"` - 20000 comments from both subreddits

## Pipeline Steps

1. **Fetch Reddit Comments** - Collects poetic comments from specified subreddits
2. **Compose Poem** - Claude AI arranges comments into rhyming poems
3. **Generate Screenshots** - Creates Reddit-style comment images
4. **Generate Audio** - Kokoro TTS converts comments to speech
5. **Create Video** - Combines everything with background video and music

## Output

All output files are saved to the `output/` directory:
- `reddit_poetic_comments.csv` - Filtered comments
- `reddit_poem.csv` - Final poem comments
- `reddit_comment_images_transparent/` - Comment screenshots
- `audio_files/` - TTS audio files
- `reddit_poem_video.mp4` - Final video

## Requirements

- Python 3.8+
- FFmpeg
- Claude CLI (`claude` command)
- Internet connection for Reddit API