"""Render tweet dicts to markdown files matching the JeffSun_Wiki schema."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from . import config


def _slug(handle: str) -> str:
    return handle.lstrip("@").strip()


def archive_path_for(author: str, tweet_id: str) -> Path:
    return config.ARCHIVE_DIR / f"{_slug(author)}-{tweet_id}.md"


def list_archived() -> dict[str, Path]:
    """Return {tweet_id: path} for every tweet already on disk."""
    if not config.ARCHIVE_DIR.exists():
        return {}
    out: dict[str, Path] = {}
    for p in config.ARCHIVE_DIR.glob("*-*.md"):
        # filename shape: `{handle}-{tweet_id}.md`
        stem = p.stem
        _, _, tid = stem.rpartition("-")
        if tid.isdigit():
            out[tid] = p
    return out


def is_archived(tweet_id: str) -> bool:
    return any(p.stem.endswith(f"-{tweet_id}") for p in config.ARCHIVE_DIR.glob(f"*-{tweet_id}.md"))


def _yaml_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def _yaml_list(items: Iterable[str]) -> str:
    items = list(items)
    if not items:
        return "[]"
    return "[" + ", ".join(f'"{_yaml_escape(x)}"' for x in items) + "]"


def render_markdown(tweet: dict) -> str:
    """Build the .md text for one tweet.

    Required keys in `tweet`:
      author, tweet_id, url, date, text
    Optional:
      likes, retweets, tags, media (list of {kind, url, local_path?})
    """
    author = tweet["author"]
    tweet_id = tweet["tweet_id"]
    url = tweet["url"]
    date = tweet.get("date", "")
    text = tweet.get("text", "").rstrip()
    likes = tweet.get("likes", 0)
    retweets = tweet.get("retweets", 0)
    tags = list(tweet.get("tags") or ["bookmark"])
    if "bookmark" not in tags:
        tags.append("bookmark")
    media = tweet.get("media", [])
    bookmarked_at = tweet.get("bookmarked_at") or datetime.now(timezone.utc).isoformat(timespec="seconds")

    handle = _slug(author)

    fm_lines = [
        "---",
        f'title: "@{handle} — tweet {tweet_id}"',
        f'author: "@{handle}"',
        f'tweet_id: "{tweet_id}"',
        f'url: "{url}"',
        f'date: "{_yaml_escape(date)}"',
        f"tags: {_yaml_list(tags)}",
        "referenced_by: []",
        'status: "fetched"',
        'source_file: "x-bookmarks"',
        f"likes: {int(likes) if isinstance(likes, (int, float, str)) and str(likes).replace('.', '').isdigit() else 0}",
        f"retweets: {int(retweets) if isinstance(retweets, (int, float, str)) and str(retweets).replace('.', '').isdigit() else 0}",
        f'bookmarked_at: "{bookmarked_at}"',
    ]

    if media:
        fm_lines.append("media:")
        for m in media:
            fm_lines.append(f'  - kind: "{m.get("kind", "image")}"')
            fm_lines.append(f'    url: "{_yaml_escape(m.get("url", ""))}"')
            if m.get("local_path"):
                fm_lines.append(f'    local_path: "{_yaml_escape(m["local_path"])}"')
    else:
        fm_lines.append("media: []")

    fm_lines.append("---")

    body_lines = [
        "",
        "## Tweet Content",
        "",
        text or "_(no text — media/quote only)_",
        "",
        "## Source",
        "",
        f"[View on X]({url})",
        "",
    ]

    if media:
        body_lines.append("## Media")
        body_lines.append("")
        for i, m in enumerate(media, 1):
            kind = m.get("kind", "image")
            u = m.get("url", "")
            lp = m.get("local_path")
            if kind == "image" and lp:
                body_lines.append(f"![image {i}]({lp})")
            elif kind == "video":
                body_lines.append(f"- Video {i}: {u}")
            else:
                body_lines.append(f"- {kind} {i}: {u}")
        body_lines.append("")

    return "\n".join(fm_lines + body_lines)


def write_tweet(tweet: dict) -> Path:
    """Write one tweet to disk, returning the file path. Idempotent."""
    config.ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    path = archive_path_for(tweet["author"], tweet["tweet_id"])
    path.write_text(render_markdown(tweet), encoding="utf-8")
    return path
