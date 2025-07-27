#!/usr/bin/env python3
"""
Generate audio files from Reddit poem comments using Kokoro TTS
"""

import os
import pandas as pd
import numpy as np
import wave
from kokoro_onnx import Kokoro
import random

def generate_audio_files(poem_df, output_dir='output/audio_files'):
    """
    Generate audio files for each line in the poem using Kokoro TTS
    """
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"\nGenerating {len(poem_df)} audio files using Kokoro TTS...")
    
    # Initialize Kokoro with the model and voices files
    kokoro = Kokoro("kokoro-v1.0.onnx", "voices-v1.0.bin")
    
    # Available voices/styles for variety
    voices = [
        "af_bella",
        "af_nicole", 
        "af_sky",
        "af_sarah",
        "am_adam",
        "am_michael",
        "bf_emma",
        "bf_isabella",
        "bm_george",
        "bm_lewis"
    ]
    
    # Generate audio for each comment
    for idx, row in poem_df.iterrows():
        text = row['text']
        file_number = idx + 1
        output_path = os.path.join(output_dir, f'audio_{file_number:02d}.wav')
        
        # Select a random voice for this comment
        voice = random.choice(voices)
        
        print(f"  Comment {file_number}/{len(poem_df)}: Using voice '{voice}' - {text[:50]}...")
        
        try:
            # Generate speech with Kokoro
            samples, sample_rate = kokoro.create(text, voice=voice)
            
            # Convert float32 samples to int16 for WAV
            samples = np.clip(samples, -1, 1)
            samples = (samples * 32767).astype(np.int16)
            
            # Save as WAV file
            with wave.open(output_path, 'w') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 2 bytes per sample (int16)
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(samples.tobytes())
            
            print(f"    Created: {output_path}")
            
        except Exception as e:
            print(f"    Error generating audio for comment {file_number}: {e}")
    
    print(f"\nAll audio files generated successfully!")
    return output_dir

def main():
    """
    Generate audio files from Reddit poem CSV
    """
    # Read the poem CSV
    try:
        df = pd.read_csv('output/reddit_poem.csv')
    except FileNotFoundError:
        print("output/reddit_poem.csv not found. Please run reddit_poem_composer.py first.")
        return
    
    print(f"Found {len(df)} comments to generate audio for.")
    
    # Generate audio files
    generate_audio_files(df)

if __name__ == "__main__":
    main()