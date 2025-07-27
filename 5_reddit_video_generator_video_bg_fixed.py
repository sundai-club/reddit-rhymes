#!/usr/bin/env python3
"""
Generate a vertical 9:16 video from Reddit poem comments with video background
Fixed version with working audio
"""

import os
import pandas as pd
import subprocess
import tempfile
from pathlib import Path
import json

def get_precise_duration(audio_file):
    """Get precise audio duration in seconds"""
    cmd = [
        'ffprobe', '-v', 'quiet', '-print_format', 'json',
        '-show_format', audio_file
    ]
    
    try:
        output = subprocess.check_output(cmd)
        data = json.loads(output)
        return float(data['format']['duration'])
    except:
        # Fallback method
        cmd = ['ffprobe', '-v', 'error', '-show_entries', 
               'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', 
               audio_file]
        try:
            return float(subprocess.check_output(cmd).decode().strip())
        except:
            return 2.0

def create_vertical_video_with_video_bg(csv_file, image_dir, audio_dir, background_video, output_video):
    """Create vertical 9:16 video with video background and proper audio"""
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_video)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Read the poem CSV
    df = pd.read_csv(csv_file)
    
    # Video dimensions for 9:16 aspect ratio
    width = 1080
    height = 1920
    
    # Music file
    music_file = 'assets/energetic-upbeat-background-music-377668.mp3'
    
    # Calculate timings
    intro_duration = 2.0
    outro_duration = 2.0
    pause_duration = 0.5
    
    # Get audio durations
    audio_durations = []
    for idx in range(len(df)):
        audio_file = os.path.join(audio_dir, f'audio_{idx+1:02d}.wav')
        duration = get_precise_duration(audio_file)
        audio_durations.append(duration)
    
    # Calculate total duration
    total_duration = intro_duration + sum(audio_durations) + (len(df) - 1) * pause_duration + outro_duration
    
    print(f"Creating vertical 9:16 video with video background...")
    print(f"Total duration will be: {total_duration:.3f} seconds")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create filter complex for entire video
        filter_parts = []
        audio_parts = []
        
        # Scale and crop background video
        filter_parts.append(f'[0:v]scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},setsar=1[bg];')
        
        # Create silent audio for intro
        filter_parts.append(f'aevalsrc=0:duration={intro_duration}:sample_rate=44100:channel_layout=stereo[intro_audio];')
        audio_parts.append('[intro_audio]')
        
        # Process each comment
        current_time = intro_duration
        for idx in range(len(df)):
            file_number = idx + 1
            duration = audio_durations[idx]
            
            # Trim background video for this segment
            filter_parts.append(f'[bg]trim={current_time}:{current_time + duration},setpts=PTS-STARTPTS[bg{idx}];')
            
            # Scale overlay image
            filter_parts.append(f'[{idx + 1}:v]scale={width}:{height}[overlay{idx}];')
            
            # Overlay comment on background
            filter_parts.append(f'[bg{idx}][overlay{idx}]overlay=0:0[v{idx}];')
            
            # Add audio
            audio_parts.append(f'[{len(df) + idx + 1}:a]')
            
            current_time += duration
            
            # Add pause if not last segment
            if idx < len(df) - 1:
                # Create pause video segment
                filter_parts.append(f'[bg]trim={current_time}:{current_time + pause_duration},setpts=PTS-STARTPTS[pause{idx}];')
                # Create pause audio
                filter_parts.append(f'aevalsrc=0:duration={pause_duration}:sample_rate=44100:channel_layout=stereo[pause_audio{idx}];')
                audio_parts.append(f'[pause_audio{idx}]')
                current_time += pause_duration
        
        # Create outro
        filter_parts.append(f'[bg]trim={current_time}:{current_time + outro_duration},setpts=PTS-STARTPTS[outro_v];')
        filter_parts.append(f'aevalsrc=0:duration={outro_duration}:sample_rate=44100:channel_layout=stereo[outro_audio];')
        audio_parts.append('[outro_audio]')
        
        # Concatenate video segments
        video_concat = '[intro_v]' if intro_duration > 0 else ''
        video_parts = []
        
        # Add intro segment (just background)
        filter_parts.append(f'[bg]trim=0:{intro_duration},setpts=PTS-STARTPTS[intro_v];')
        video_parts.append('[intro_v]')
        
        # Add comment segments and pauses
        for idx in range(len(df)):
            video_parts.append(f'[v{idx}]')
            if idx < len(df) - 1:
                video_parts.append(f'[pause{idx}]')
        
        # Add outro
        video_parts.append('[outro_v]')
        
        # Concatenate all video segments
        concat_count = len(video_parts)
        filter_parts.append(f'{"".join(video_parts)}concat=n={concat_count}:v=1:a=0[video];')
        
        # Concatenate all audio segments
        audio_concat_count = len(audio_parts)
        filter_parts.append(f'{"".join(audio_parts)}concat=n={audio_concat_count}:v=0:a=1[concat_audio];')
        
        # Mix with background music
        if os.path.exists(music_file):
            # Process voice and music
            filter_parts.append('[concat_audio]volume=1.5,highpass=f=100,lowpass=f=3000[voice];')
            filter_parts.append(f'[{len(df) * 2 + 1}:a]volume=0.08[music];')
            filter_parts.append('[voice][music]amix=inputs=2:duration=first:weights=1 0.5[final_audio]')
            audio_output = '[final_audio]'
        else:
            # Just use voice
            filter_parts.append('[concat_audio]volume=1.5[final_audio]')
            audio_output = '[final_audio]'
        
        # Build filter complex
        filter_complex = ''.join(filter_parts)
        
        # Build ffmpeg command
        cmd = ['ffmpeg', '-y']
        
        # Input background video
        cmd.extend(['-i', background_video])
        
        # Input comment images
        for idx in range(len(df)):
            image_file = os.path.join(image_dir, f'comment_{idx + 1:02d}_transparent.png')
            cmd.extend(['-i', image_file])
        
        # Input audio files
        for idx in range(len(df)):
            audio_file = os.path.join(audio_dir, f'audio_{idx + 1:02d}.wav')
            cmd.extend(['-i', audio_file])
        
        # Input background music if exists
        if os.path.exists(music_file):
            cmd.extend(['-i', music_file])
        
        # Add filter complex
        cmd.extend(['-filter_complex', filter_complex])
        
        # Map outputs
        cmd.extend(['-map', '[video]', '-map', audio_output])
        
        # Output settings
        cmd.extend([
            '-c:v', 'libx264',
            '-preset', 'slow',  # High quality preset
            '-crf', '18',  # Even better quality (lower = better)
            '-pix_fmt', 'yuv420p',
            '-g', '30',  # Keyframe interval
            '-bf', '3',  # More B-frames for better quality
            '-refs', '4',  # More reference frames
            '-qmin', '10',  # Minimum quantizer
            '-qmax', '51',  # Maximum quantizer
            '-profile:v', 'high',  # H.264 high profile for better quality
            '-level', '4.1',  # Compatibility level
            '-c:a', 'aac',
            '-b:a', '256k',  # Higher audio bitrate too
            '-ar', '48000',  # Higher sample rate
            '-t', str(total_duration),
            '-movflags', '+faststart',
            output_video
        ])
        
        # Execute command
        print("Running ffmpeg command...")
        print(f"Processing {len(df)} comments with video background...")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"\nVideo created successfully: {output_video}")
            print(f"Total duration: {total_duration:.3f} seconds")
            print(f"Resolution: {width}x{height} (9:16 vertical)")
        else:
            print(f"Error creating video: {result.stderr}")
            # Save command for debugging
            with open('debug_command.txt', 'w') as f:
                f.write(' '.join(cmd))
            print("Command saved to debug_command.txt")

def main():
    # File paths
    poem_csv = 'output/reddit_poem.csv'
    image_dir = 'output/comment_images_transparent'
    audio_dir = 'output/audio_files'
    background_video = 'assets/xKRNDalWE-E.webm'
    output_video = 'output/reddit_poem_video.mp4'
    
    # Check requirements
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
    except:
        print("Error: ffmpeg is not installed.")
        return
    
    if not all(os.path.exists(p) for p in [poem_csv, image_dir, audio_dir, background_video]):
        print("Error: Required files not found.")
        print(f"  CSV: {os.path.exists(poem_csv)}")
        print(f"  Images: {os.path.exists(image_dir)}")
        print(f"  Audio: {os.path.exists(audio_dir)}")
        print(f"  Background video: {os.path.exists(background_video)}")
        return
    
    create_vertical_video_with_video_bg(poem_csv, image_dir, audio_dir, background_video, output_video)

if __name__ == "__main__":
    main()