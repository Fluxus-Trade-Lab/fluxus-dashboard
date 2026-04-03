#!/usr/bin/env python3
"""Fetch tweet content via FxTwitter API (free, no auth) with syndication fallback.
Populates stub .md files in sources/tweets/ with actual content."""

import json, os, re, sys, time, urllib.request

TWEETS_DIR = os.path.join(os.path.dirname(__file__), "..", "sources", "tweets")
MANIFEST = os.path.join(os.path.dirname(__file__), "tweet_manifest.json")
DELAY = 0.5  # seconds between requests


def fetch_fxtwitter(tweet_id):
    """Primary: FxTwitter API — best data, no auth."""
    url = f"https://api.fxtwitter.com/i/status/{tweet_id}"
    req = urllib.request.Request(url, headers={"User-Agent": "JeffSunWiki/1.0"})
    resp = urllib.request.urlopen(req, timeout=15)
    data = json.loads(resp.read())
    if data.get("code") == 200:
        t = data["tweet"]
        return {
            "text": t["text"],
            "author": t["author"]["screen_name"],
            "date": t.get("created_at", ""),
            "likes": t.get("likes", 0),
            "retweets": t.get("retweets", 0),
            "replies": t.get("replies", 0),
        }
    return None


def fetch_syndication(tweet_id):
    """Fallback: Twitter syndication endpoint — no auth."""
    url = f"https://cdn.syndication.twimg.com/tweet-result?id={tweet_id}&token=0"
    req = urllib.request.Request(url, headers={"User-Agent": "JeffSunWiki/1.0"})
    resp = urllib.request.urlopen(req, timeout=15)
    data = json.loads(resp.read())
    return {
        "text": data.get("text", ""),
        "author": data.get("user", {}).get("screen_name", ""),
        "date": data.get("created_at", ""),
        "likes": data.get("favorite_count", 0),
        "retweets": data.get("retweet_count", 0),
        "replies": 0,
    }


def fetch_tweet(tweet_id):
    """Try FxTwitter first, then syndication fallback."""
    for fetcher in [fetch_fxtwitter, fetch_syndication]:
        try:
            result = fetcher(tweet_id)
            if result and result.get("text"):
                return result
        except Exception:
            continue
    return None


def write_md(filepath, author, tweet_id, tweet_url, source_file, data):
    """Write a populated tweet .md file."""
    date_str = data.get("date", "null") or "null"
    text = data["text"]
    # Escape any YAML-breaking chars in text for frontmatter
    likes = data.get("likes", 0)
    retweets = data.get("retweets", 0)

    content = f"""---
title: "@{author} — tweet {tweet_id}"
author: "@{author}"
tweet_id: "{tweet_id}"
url: "{tweet_url}"
date: "{date_str}"
tags: []
referenced_by: []
status: "fetched"
source_file: "{source_file}"
likes: {likes}
retweets: {retweets}
---

## Tweet Content

{text}

## Source

[View on X]({tweet_url})
"""
    with open(filepath, "w") as f:
        f.write(content)


def main():
    with open(MANIFEST) as f:
        tweets = json.load(f)

    fetched = 0
    failed = 0
    skipped = 0

    for i, t in enumerate(tweets):
        author = t["author"].lstrip("@")
        tweet_id = t["tweet_id"]
        tweet_url = t["url"]
        source_file = t.get("source_file", "")

        filename = f"{author}-{tweet_id}.md"
        filepath = os.path.join(TWEETS_DIR, filename)

        # Skip already-fetched tweets
        if os.path.exists(filepath):
            with open(filepath) as f:
                content = f.read()
                if 'status: "fetched"' in content:
                    skipped += 1
                    continue

        # Fetch
        data = fetch_tweet(tweet_id)
        time.sleep(DELAY)

        if data:
            write_md(filepath, author, tweet_id, tweet_url, source_file, data)
            fetched += 1
            status = "OK"
        else:
            failed += 1
            status = "FAIL"

        progress = f"[{i+1}/{len(tweets)}]"
        print(f"{progress} {status} @{author}/{tweet_id}", flush=True)

    print(f"\nDone: {fetched} fetched, {failed} failed, {skipped} skipped (already fetched)")


if __name__ == "__main__":
    main()
