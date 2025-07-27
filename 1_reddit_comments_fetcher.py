#!/usr/bin/env python3
import praw
import pandas as pd
from datetime import datetime
import requests
import json
import time
import re
import sys
import os

def is_poetic_comment(text):
    """
    Check if a comment could work as a poem line
    """
    # Remove extra whitespace
    text = text.strip()
    
    # Check length (good poem lines are typically 5-80 characters)
    if len(text) < 5 or len(text) > 80:
        return False
    
    # Check for URLs
    if re.search(r'https?://|www\.', text, re.IGNORECASE):
        return False
    
    # Check for markdown elements
    markdown_patterns = [
        r'\[.*?\]\(.*?\)',  # Links [text](url)
        r'\*\*.*?\*\*',     # Bold **text**
        r'__.*?__',         # Bold __text__
        r'\*.*?\*',         # Italic *text*
        r'_.*?_',           # Italic _text_
        r'~~.*?~~',         # Strikethrough
        r'^#{1,6}\s',       # Headers
        r'^\s*[-*+]\s',     # Lists
        r'^\s*\d+\.\s',     # Numbered lists
        r'```.*?```',       # Code blocks
        r'`.*?`',           # Inline code
        r'^\s*>',           # Quotes
        r'/r/',             # Subreddit links
        r'/u/',             # User links
        r'&amp;|&lt;|&gt;', # HTML entities
    ]
    
    for pattern in markdown_patterns:
        if re.search(pattern, text):
            return False
    
    # Check for too many special characters (not poetic)
    special_char_count = len(re.findall(r'[^\w\s\'",.!?-]', text))
    if special_char_count > 3:
        return False
    
    # Check if it has at least some alphabetic characters
    if not re.search(r'[a-zA-Z]', text):
        return False
    
    # Filter out common non-poetic patterns
    non_poetic_patterns = [
        r'^\s*lol\s*$',
        r'^\s*lmao\s*$',
        r'^\s*omg\s*$',
        r'^\s*wtf\s*$',
        r'^\s*idk\s*$',
        r'^\s*imo\s*$',
        r'^\s*tbh\s*$',
        r'^this\.$',
        r'^same\.$',
        r'^\^+$',
    ]
    
    for pattern in non_poetic_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return False
    
    return True

def fetch_reddit_comments(limit=10000, subreddits=None):
    """
    Fetch latest comments from Reddit without authentication
    Filters for poetic comments only
    Note: Reddit API limits to 100 per request, so we'll need multiple requests
    """
    comments_data = []
    
    # Use provided subreddits or default
    if subreddits is None:
        subreddits = ['AmItheAsshole', 'ArtificialInteligence']
    
    for subreddit in subreddits:
        print(f"Fetching from r/{subreddit}...")
        subreddit_comments = 0
        after = None
        
        # Fetch multiple pages to get up to 'limit' comments
        pages_to_fetch = (limit + 99) // 100  # Round up division
        
        for page in range(pages_to_fetch):
            try:
                # Build URL with pagination
                url = f"https://www.reddit.com/r/{subreddit}/comments.json?limit=100"
                if after:
                    url += f"&after={after}"
                
                headers = {'User-Agent': 'Mozilla/5.0 (compatible; Comment Fetcher 1.0)'}
                
                response = requests.get(url, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Get the 'after' token for pagination
                    after = data['data'].get('after')
                    
                    # Process each comment
                    for item in data['data']['children']:
                        comment = item['data']
                        text = comment.get('body', '').replace('\n', ' ').replace('\r', ' ')
                        
                        # Filter for poetic comments
                        if is_poetic_comment(text):
                            # Extract required fields
                            comment_info = {
                                'comment_url': f"https://www.reddit.com{comment.get('permalink', '')}",
                                'text': text.strip(),
                                'author': comment.get('author', '[deleted]'),
                                'avatar_url': '',  # Reddit's JSON API doesn't provide avatar URLs directly
                                'time': datetime.fromtimestamp(comment.get('created_utc', 0)).strftime('%Y-%m-%d %H:%M:%S'),
                                'upvotes': comment.get('score', 1)  # Default to 1 if score not available
                            }
                            
                            comments_data.append(comment_info)
                            subreddit_comments += 1
                    
                    # Be respectful of rate limits
                    time.sleep(2)
                    
                    # Stop if no more pages
                    if not after:
                        break
                        
                else:
                    print(f"Error fetching data: Status code {response.status_code}")
                    break
                    
            except Exception as e:
                print(f"Error processing subreddit {subreddit} page {page+1}: {str(e)}")
                break
        
        print(f"  Found {subreddit_comments} poetic comments from r/{subreddit}")
    
    return comments_data

def save_to_csv(comments_data, filename='output/reddit_poetic_comments.csv'):
    """
    Save comments data to CSV file
    """
    # Ensure output directory exists
    os.makedirs('output', exist_ok=True)
    
    df = pd.DataFrame(comments_data)
    df.to_csv(filename, index=False, encoding='utf-8')
    print(f"Saved {len(comments_data)} comments to {filename}")

def main():
    # Get limit from command line argument or use default
    limit = 10000  # Default
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
        except ValueError:
            print(f"Invalid limit '{sys.argv[1]}', using default: {limit}")
    
    # Get subreddits from command line arguments
    subreddits = None
    if len(sys.argv) > 2:
        # Join all arguments after the first one as comma-separated subreddits
        subreddits_arg = ' '.join(sys.argv[2:])
        # Split by comma and strip whitespace
        subreddits = [s.strip() for s in subreddits_arg.split(',')]
        print(f"Using subreddits: {', '.join(subreddits)}")
    
    print("Fetching latest Reddit comments...")
    print(f"Fetching up to {limit} comments from each subreddit...")
    print("(Note: This may take a few minutes due to rate limiting)\n")
    
    # Fetch comments with specified limit and subreddits
    comments = fetch_reddit_comments(limit=limit, subreddits=subreddits)
    
    if comments:
        # Save to CSV
        save_to_csv(comments)
        
        # Display sample
        print(f"\nTotal poetic comments found: {len(comments)}")
        print("\nHere are the first 5:")
        df = pd.DataFrame(comments)
        print(df.head())
    else:
        print("No comments fetched.")

if __name__ == "__main__":
    main()