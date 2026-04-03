#!/usr/bin/env python3
"""Extract unique tweet URLs from Notion snapshot files and produce a manifest."""
import json
import re
import sys
from pathlib import Path

NOTION_DIR = Path(__file__).parent.parent / "sources" / "notion"
OUTPUT = Path(__file__).parent / "tweet_manifest.json"

# Match x.com and twitter.com status URLs
TWEET_RE = re.compile(
    r'https?://(?:x\.com|twitter\.com)/(\w+)/status/(\d+)(?:\S*)?'
)

def extract_tweets():
    seen = set()
    tweets = []
    for md_file in sorted(NOTION_DIR.glob("*.md")):
        text = md_file.read_text(encoding="utf-8")
        for match in TWEET_RE.finditer(text):
            author = match.group(1)
            tweet_id = match.group(2)
            if tweet_id not in seen:
                seen.add(tweet_id)
                tweets.append({
                    "author": f"@{author}",
                    "tweet_id": tweet_id,
                    "url": f"https://x.com/{author}/status/{tweet_id}",
                    "source_file": md_file.name
                })
    return tweets

if __name__ == "__main__":
    tweets = extract_tweets()
    OUTPUT.write_text(json.dumps(tweets, indent=2), encoding="utf-8")
    print(f"Extracted {len(tweets)} unique tweet URLs -> {OUTPUT}")
