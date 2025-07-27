#!/usr/bin/env python3
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import pandas as pd
import os
from datetime import datetime
import hashlib
import random

def get_relative_time(timestamp_str):
    """
    Convert timestamp string to relative time like '2h ago'
    """
    try:
        # Try parsing the timestamp
        if isinstance(timestamp_str, str) and '-' in timestamp_str:
            # Parse datetime string
            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
        else:
            # If it's already a relative time, return as is
            return str(timestamp_str)
        
        # Get current time
        now = datetime.now()
        
        # Calculate difference
        diff = now - timestamp
        
        # Convert to relative format
        seconds = diff.total_seconds()
        
        if seconds < 60:
            return "just now"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            return f"{minutes}m ago"
        elif seconds < 86400:
            hours = int(seconds / 3600)
            return f"{hours}h ago"
        elif seconds < 604800:
            days = int(seconds / 86400)
            return f"{days}d ago"
        else:
            weeks = int(seconds / 604800)
            return f"{weeks}w ago"
            
    except:
        # If parsing fails, use a random time for demo purposes
        import random
        times = ["2h ago", "3h ago", "5h ago", "8h ago", "12h ago", "1d ago", "2d ago"]
        return random.choice(times)

def generate_avatar(username, size=40):
    """
    Generate a circular avatar based on username
    """
    # Create hash of username for consistent colors
    hash_val = int(hashlib.md5(username.encode()).hexdigest(), 16)
    
    # Generate color from hash
    r = (hash_val & 0xFF0000) >> 16
    g = (hash_val & 0x00FF00) >> 8
    b = (hash_val & 0x0000FF)
    
    # Create avatar image with transparency for circle
    avatar = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(avatar)
    
    # Draw circular background
    draw.ellipse([(0, 0), (size-1, size-1)], fill=(r, g, b, 255))
    
    # Add first letter of username
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", int(size * 0.5))
    except:
        font = ImageFont.load_default()
    
    first_letter = username[0].upper() if username else "?"
    
    # Calculate text position
    bbox = draw.textbbox((0, 0), first_letter, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    position = ((size - text_width) // 2, (size - text_height) // 2)
    
    # Draw letter
    draw.text(position, first_letter, fill=(255, 255, 255), font=font)
    
    return avatar

def create_reddit_comment_card(comment_data, card_width=500, theme='dark'):
    """
    Create a Reddit-style comment card with semi-transparent background
    """
    # Theme colors with alpha support
    if theme == 'dark':
        bg_color = (26, 26, 27, 250)  # Less transparent dark background (was 220)
        text_color = (215, 218, 220)
        secondary_color = (129, 131, 132)
        border_color = (52, 53, 54)
        upvote_color = (255, 69, 0)
    else:
        bg_color = (255, 255, 255, 250)  # Less transparent white background (was 220)
        text_color = (28, 28, 28)
        secondary_color = (138, 138, 138)
        border_color = (237, 239, 241)
        upvote_color = (255, 69, 0)
    
    # Fonts - larger for bigger cards
    try:
        font_regular = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 42)  # Was 32
        font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 26)    # Was 20
        font_username = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 32) # Was 24
    except:
        font_regular = ImageFont.load_default()
        font_small = ImageFont.load_default()
        font_username = ImageFont.load_default()
    
    # Parse comment data
    username = comment_data['author']
    text = comment_data['text']
    timestamp = get_relative_time(comment_data['time'])
    # Generate random vote numbers in a modest range
    import random
    upvotes = random.randint(10, 100)
    upvotes_display = str(upvotes)
    
    # Calculate card dimensions - scaled up for larger cards
    padding = 50  # Was 40
    line_height = 56  # Was 44
    avatar_size = 80  # Was 60
    
    # Create temporary image to measure text
    temp_img = Image.new('RGBA', (card_width - 2*padding - avatar_size - 15, 100))
    temp_draw = ImageDraw.Draw(temp_img)
    
    # Word wrap text
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        bbox = temp_draw.textbbox((0, 0), test_line, font=font_regular)
        if bbox[2] - bbox[0] > card_width - 2*padding - avatar_size - 15:
            if current_line:
                lines.append(' '.join(current_line))
                current_line = [word]
            else:
                lines.append(word)
        else:
            current_line.append(word)
    if current_line:
        lines.append(' '.join(current_line))
    
    # Calculate total height
    text_height = len(lines) * line_height
    card_height = padding + 80 + text_height + padding + 40  # Increased from 55 to 80 to match text_y
    
    # Create card with RGBA for transparency
    card = Image.new('RGBA', (card_width, card_height), color=bg_color)
    draw = ImageDraw.Draw(card)
    
    # Add subtle rounded corners effect
    corner_radius = 12
    # Create rounded rectangle mask
    mask = Image.new('L', (card_width, card_height), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle([(0, 0), (card_width-1, card_height-1)], 
                                radius=corner_radius, fill=255)
    
    # Apply mask to card
    card.putalpha(mask)
    
    # Redraw background with rounded corners
    draw.rounded_rectangle([(0, 0), (card_width-1, card_height-1)], 
                          radius=corner_radius, fill=bg_color)
    
    # Generate and paste circular avatar
    avatar = generate_avatar(username, avatar_size)
    card.paste(avatar, (padding, padding), avatar)
    
    # Draw username and timestamp on same line with dot separator
    username_x = padding + avatar_size + 15
    
    # Calculate baseline for better vertical alignment
    username_baseline_y = padding + 15
    
    # Draw username
    username_bbox = draw.textbbox((0, 0), username, font=font_username)
    username_width = username_bbox[2] - username_bbox[0]
    draw.text((username_x, username_baseline_y), username, fill=text_color, font=font_username)
    
    # Draw separator dot and timestamp with adjusted baseline for smaller font
    separator = " · "
    timestamp_text = separator + timestamp
    # Adjust timestamp position slightly lower to align baselines
    timestamp_y = username_baseline_y + 3  # Small offset to align baselines
    draw.text((username_x + username_width, timestamp_y), timestamp_text, fill=secondary_color, font=font_small)
    
    # Draw comment text - with more padding from username
    text_y = padding + 80  # Was 55, increased padding
    for line in lines:
        draw.text((username_x, text_y), line, fill=text_color, font=font_regular)
        text_y += line_height
    
    # Draw interaction buttons
    button_baseline_y = card_height - padding - 25
    
    # Arrow and text sizing - make arrows larger
    arrow_height = 12  # Increased from 8
    arrow_width = 14   # Increased from 10
    arrow_spacing = 8  # Increased from 6
    
    # Calculate text metrics for alignment
    vote_bbox = draw.textbbox((0, 0), upvotes_display, font=font_small)
    text_height = vote_bbox[3] - vote_bbox[1]
    vote_width = vote_bbox[2] - vote_bbox[0]
    
    # Vertical center for the vote number text
    text_center_y = button_baseline_y + text_height // 2
    
    # Upvote arrow - positioned lower (closer to text center)
    upvote_x = username_x
    upvote_center_y = text_center_y + 2  # Lower than text center
    # Draw two lines to form upward chevron
    draw.line([(upvote_x, upvote_center_y), 
               (upvote_x + arrow_width//2, upvote_center_y - arrow_height//2)], 
              fill=secondary_color, width=3)  # Thicker line
    draw.line([(upvote_x + arrow_width//2, upvote_center_y - arrow_height//2), 
               (upvote_x + arrow_width, upvote_center_y)], 
              fill=secondary_color, width=3)
    
    # Vote count - centered between arrows
    vote_x = upvote_x + arrow_width + arrow_spacing
    draw.text((vote_x, button_baseline_y), upvotes_display, fill=secondary_color, font=font_small)
    
    # Downvote arrow - positioned higher (closer to text center)
    downvote_x = vote_x + vote_width + arrow_spacing
    downvote_center_y = text_center_y - 2  # Higher than text center
    # Draw two lines to form downward chevron
    draw.line([(downvote_x, downvote_center_y), 
               (downvote_x + arrow_width//2, downvote_center_y + arrow_height//2)], 
              fill=secondary_color, width=3)  # Thicker line
    draw.line([(downvote_x + arrow_width//2, downvote_center_y + arrow_height//2), 
               (downvote_x + arrow_width, downvote_center_y)], 
              fill=secondary_color, width=3)
    
    # Reply button
    reply_x = downvote_x + arrow_width + 40
    draw.text((reply_x, button_baseline_y), "Reply", fill=secondary_color, font=font_small)
    
    # Award button
    award_x = reply_x + 90
    draw.text((award_x, button_baseline_y), "Award", fill=secondary_color, font=font_small)
    
    # Share button
    share_x = award_x + 100
    draw.text((share_x, button_baseline_y), "Share", fill=secondary_color, font=font_small)
    
    # Three dots menu
    dots_x = share_x + 90
    draw.text((dots_x, button_baseline_y), "•••", fill=secondary_color, font=font_small)
    
    return card

def create_transparent_reddit_image(comment_data, index, theme='dark'):
    """
    Create a transparent image with just the Reddit comment
    """
    # 9:16 aspect ratio dimensions
    width = 1080
    height = 1920
    
    # Create transparent background
    final_image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    
    # Create the comment card - larger for better visibility
    card_width = 900  # Was 750
    card = create_reddit_comment_card(comment_data, card_width, theme)
    
    # Random positioning around center
    # Define safe area (avoiding edges)
    safe_margin_x = 30  # Reduced margin since card is wider
    safe_margin_y = 150  # Reduced margin for larger cards
    
    # Center position
    center_x = (width - card_width) // 2
    center_y = (height - card.height) // 2
    
    # Add random offset - smaller range due to larger cards
    random.seed(index)  # Consistent randomness for each comment
    offset_x = random.randint(-30, 30)  # Reduced from -50, 50
    offset_y = random.randint(-150, 150)  # Reduced from -200, 200
    
    # Calculate final position
    pos_x = max(safe_margin_x, min(width - card_width - safe_margin_x, center_x + offset_x))
    pos_y = max(safe_margin_y, min(height - card.height - safe_margin_y, center_y + offset_y))
    
    # Add drop shadow for the card
    shadow = Image.new('RGBA', card.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rounded_rectangle([(5, 5), (card.width, card.height)], 
                                  radius=12, fill=(0, 0, 0, 80))
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=10))
    
    # Paste shadow then card
    final_image.paste(shadow, (pos_x + 5, pos_y + 5), shadow)
    final_image.paste(card, (pos_x, pos_y), card)
    
    return final_image

def generate_transparent_screenshots(df, theme='dark'):
    """
    Generate transparent Reddit comment screenshots
    """
    # Create output directory
    output_dir = 'output/comment_images_transparent'
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"\nGenerating {len(df)} transparent Reddit comment screenshots...")
    
    # Generate image for each comment
    for index, row in df.iterrows():
        # Create transparent image
        img = create_transparent_reddit_image(row, index, theme=theme)
        
        # Save image
        filename = f"{output_dir}/comment_{index + 1:02d}_transparent.png"
        img.save(filename, 'PNG', quality=95)
        print(f"Created: {filename}")
    
    return output_dir

def main():
    """
    Generate transparent Reddit comment screenshots
    """
    # Read the poem CSV
    try:
        df = pd.read_csv('output/reddit_poem.csv')
    except FileNotFoundError:
        print("output/reddit_poem.csv not found. Please run reddit_poem_composer.py first.")
        return
    
    print(f"Found {len(df)} comments to generate transparent screenshots for.")
    
    # Generate transparent screenshots with light theme
    output_dir = generate_transparent_screenshots(df, theme='light')
    
    print(f"\nAll transparent screenshots generated successfully!")
    print(f"Output directory: {output_dir}/")

if __name__ == "__main__":
    main()