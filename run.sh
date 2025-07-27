#!/bin/bash

# Reddit Poem Video Generation Pipeline
# This script runs the complete pipeline to create a Reddit poem video with video background

# Default parameters
COMMENT_LIMIT=${1:-10000}
SUBREDDITS=${2:-"ArtificialInteligence"}

echo "=== Reddit Poem Video Generation Pipeline (with Video Background) ==="
echo "Parameters:"
echo "  Comment limit: $COMMENT_LIMIT"
echo "  Subreddits: $SUBREDDITS"
echo

# Check for required files
echo "Checking required files..."
if [ ! -f "assets/xKRNDalWE-E.webm" ]; then
    echo "Error: Background video file not found!"
    echo "Please ensure 'xKRNDalWE-E.webm' is in the assets directory"
    exit 1
fi

if [ ! -f "assets/energetic-upbeat-background-music-377668.mp3" ]; then
    echo "Warning: Background music file not found!"
    echo "Video will be created without background music"
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "1. Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "Error: Failed to create virtual environment"
        exit 1
    fi
else
    echo "1. Virtual environment already exists"
fi

# Activate virtual environment
echo "   Activating virtual environment..."
source venv/bin/activate

# Install requirements if needed
if [ -f "requirements.txt" ]; then
    echo "   Installing/updating requirements..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "Error: Failed to install requirements"
        exit 1
    fi
else
    echo "Warning: requirements.txt not found, skipping dependency installation"
fi

# Fetch Reddit comments
echo "2. Fetching Reddit comments (limit: $COMMENT_LIMIT, subreddits: $SUBREDDITS)..."
python 1_reddit_comments_fetcher.py $COMMENT_LIMIT $SUBREDDITS
if [ $? -ne 0 ]; then
    echo "Error: Failed to fetch Reddit comments"
    exit 1
fi

# Compose poem from comments
echo "3. Composing poem from comments using Claude Code..."
python 2_reddit_poem_composer_claude_v2.py
if [ $? -ne 0 ]; then
    echo "Error: Failed to compose poem"
    exit 1
fi

# Generate transparent Reddit comment screenshots
echo "4. Generating transparent Reddit comment screenshots..."
python 3_reddit_comment_screenshots_transparent.py
if [ $? -ne 0 ]; then
    echo "Error: Failed to generate transparent screenshots"
    exit 1
fi

# Generate audio files with Kokoro TTS
echo "5. Generating audio files with Kokoro TTS..."
# Download Kokoro model files if they don't exist
if [ ! -f "kokoro-v1.0.onnx" ]; then
    echo "   Downloading Kokoro model file..."
    curl -L -o kokoro-v1.0.onnx https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
    if [ $? -ne 0 ]; then
        echo "Error: Failed to download Kokoro model file"
        exit 1
    fi
fi
if [ ! -f "voices-v1.0.bin" ]; then
    echo "   Downloading Kokoro voices file..."
    curl -L -o voices-v1.0.bin https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
    if [ $? -ne 0 ]; then
        echo "Error: Failed to download Kokoro voices file"
        exit 1
    fi
fi
python 4_reddit_audio_generator_kokoro.py
if [ $? -ne 0 ]; then
    echo "Error: Failed to generate audio files"
    exit 1
fi

# Create final video with video background
echo "6. Creating final video with video background and music..."
python 5_reddit_video_generator_video_bg_fixed.py
if [ $? -ne 0 ]; then
    echo "Error: Failed to create video"
    exit 1
fi

echo
echo "=== Pipeline completed successfully! ==="
echo "Output video: output/reddit_poem_video.mp4"
echo

# Optional: Display video information
if command -v ffprobe &> /dev/null; then
    echo "Video information:"
    ffprobe -v quiet -print_format json -show_format -show_streams output/reddit_poem_video.mp4 2>/dev/null | \
        python -m json.tool | grep -E '"duration"|"width"|"height"|"codec_name"' | head -10
fi

# Show file size
echo
echo "File size: $(ls -lh output/reddit_poem_video.mp4 | awk '{print $5}')"
