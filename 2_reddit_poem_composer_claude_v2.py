#!/usr/bin/env python3
import pandas as pd
import os
import random
import subprocess
import json
import tempfile

def read_reddit_comments(filename='output/reddit_poetic_comments.csv'):
    """
    Read Reddit comments from CSV file and return full dataframe
    """
    try:
        df = pd.read_csv(filename)
        return df
    except FileNotFoundError:
        print(f"File {filename} not found. Please run reddit_comments_fetcher.py first.")
        return None

def compose_poem_with_claude(df):
    """
    Use Claude Code CLI to compose a rhythmic poem from Reddit comments
    Each line should be one complete comment
    """
    # Select a subset of comments for the poem
    sample_size = min(len(df), 30)
    sampled_df = df.sample(n=sample_size)
    comments = sampled_df['text'].tolist()
    
    # Create prompt with comments included
    comments_list = '\n'.join([f'{i+1}. {comment}' for i, comment in enumerate(comments)])
    
    prompt = f"""Here are Reddit comments. Create a rhyming poem using ONLY these exact comments as lines:

{comments_list}

Rules:
- Each line MUST be one complete comment from above
- Do NOT modify the comments AT ALL
- Arrange 8-16 of them into a rhyming poem (AABB, ABAB, or ABCB)
- Focus on rhythm and rhyme
- Look for comments that end with similar sounds

Return the poem as comment numbers followed by the comment text, one per line, in this format:
5: He is smart
12: This is unintelligible.
3: Context engineering Vibe coding
18: Una mezcla entre Efootball y Football Manager :D
(etc.)

This format helps me verify the poem visually while ensuring accurate matching."""

    try:
        # Ensure output directory exists
        os.makedirs('output', exist_ok=True)
        
        # Debug: save prompt to file for inspection
        with open('output/claude_prompt.txt', 'w') as f:
            f.write(prompt)
        print("Prompt saved to output/claude_prompt.txt for inspection")
        
        # Call Claude Code CLI
        print("Calling Claude Code to compose poem...")
        result = subprocess.run(
            ['claude'],
            input=prompt,
            capture_output=True,
            text=True,
            check=False
        )
        
        poem_text = result.stdout.strip()
        
        # Check for errors
        if result.returncode != 0 or not poem_text:
            error_text = result.stderr.strip() if result.stderr else "No output from Claude"
            print(f"\nError from Claude: {error_text}")
            if not poem_text:
                poem_text = error_text
        
        # Show Claude's output
        print("\nClaude's output:")
        print("-" * 50)
        print(poem_text)
        print("-" * 50)
        
        # Extract the comments used in the poem
        poem_lines = []
        
        # Parse the comment IDs from Claude's output
        comment_ids = []
        for line in poem_text.split('\n'):
            line = line.strip()
            if line and ':' in line:
                # Extract the ID from lines like "5: He is smart"
                id_part = line.split(':')[0].strip()
                if id_part.isdigit():
                    comment_id = int(id_part) - 1  # Convert to 0-based index
                    if 0 <= comment_id < len(sampled_df):
                        comment_ids.append(comment_id)
        
        print(f"\nExtracted {len(comment_ids)} comment IDs from Claude's response")
        
        if comment_ids:
            # Get the actual comments based on IDs
            sampled_list = sampled_df.reset_index(drop=True)
            for comment_id in comment_ids:
                poem_lines.append(sampled_list.iloc[comment_id])
            
            # Create the poem text from selected comments
            poem_text = '\n'.join([row['text'] for row in poem_lines])
            print(f"\nComposed poem with {len(poem_lines)} lines")
        else:
            print("\nWarning: Could not extract comment IDs from Claude's response")
            print("Trying to manually parse...")
            # Fallback: just take the first 8-12 comments that rhyme
            poem_lines = find_rhyming_comments(sampled_df, 8, 12)
            poem_text = '\n'.join([row['text'] for row in poem_lines])
        
        return poem_text, poem_lines
        
    except Exception as e:
        print(f"Error generating poem: {str(e)}")
        # Fallback to algorithmic approach
        print("Falling back to algorithmic poem generation...")
        poem_lines = find_rhyming_comments(sampled_df, 8, 12)
        poem_text = '\n'.join([row['text'] for row in poem_lines])
        return poem_text, poem_lines

def find_rhyming_comments(df, min_lines=8, max_lines=12):
    """
    Simple algorithm to find comments that might rhyme
    """
    # Get last word of each comment
    comments_with_endings = []
    for idx, row in df.iterrows():
        text = row['text'].strip()
        words = text.split()
        if words:
            last_word = words[-1].lower().strip('.,!?;:"')
            comments_with_endings.append((row, last_word))
    
    # Sort by last word to group potential rhymes
    comments_with_endings.sort(key=lambda x: x[1][-3:])  # Sort by last 3 characters
    
    # Select comments trying to create AABB pattern
    selected = []
    i = 0
    while len(selected) < max_lines and i < len(comments_with_endings) - 1:
        # Look for pairs with similar endings
        if comments_with_endings[i][1][-2:] == comments_with_endings[i+1][1][-2:]:
            selected.append(comments_with_endings[i][0])
            selected.append(comments_with_endings[i+1][0])
            i += 2
        else:
            i += 1
    
    # If not enough, add more
    if len(selected) < min_lines:
        for row, _ in comments_with_endings:
            if len(selected) >= max_lines:
                break
            if not any(row['text'] == s['text'] for s in selected):
                selected.append(row)
    
    return selected[:max_lines]

def save_poem_csv(poem_lines, filename='output/reddit_poem.csv'):
    """
    Save the poem lines to a CSV file with all original columns
    """
    if poem_lines:
        # Ensure output directory exists
        os.makedirs('output', exist_ok=True)
        
        poem_df = pd.DataFrame(poem_lines)
        poem_df.to_csv(filename, index=False, encoding='utf-8')
        print(f"\nPoem data saved to {filename}")

def main():
    """
    Main function to compose poems from Reddit comments using Claude Code
    """
    # Read comments
    print("Reading Reddit comments...")
    df = read_reddit_comments()
    
    if df is None or len(df) == 0:
        print("No comments found. Please run reddit_comments_fetcher.py first.")
        return
    
    print(f"Found {len(df)} poetic comments.")
    print("\nComposing poem with Claude Code...\n")
    
    # Generate poem
    poem_text, poem_lines = compose_poem_with_claude(df)
    
    if poem_text:
        print("=" * 50)
        print("REDDIT RHYTHM")
        print("=" * 50)
        print(poem_text)
        print("=" * 50)
        
        # Save CSV version with all columns
        save_poem_csv(poem_lines)
        
    else:
        print("Failed to generate poem.")

if __name__ == "__main__":
    main()