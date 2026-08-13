"""Download images referenced by bookmarked tweets. Videos are linked only."""
from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlparse

import requests

from . import config


def _rewrite_size(url: str) -> str:
    """Twitter photo URLs look like:
        https://pbs.twimg.com/media/<id>?format=jpg&name=small
    Bump `name` to `large` for archival quality.
    """
    return re.sub(r"([?&])name=[^&]+", rf"\1name={config.IMAGE_SIZE}", url)


def _ext_for(url: str) -> str:
    p = urlparse(url)
    if "format=png" in p.query:
        return ".png"
    if "format=webp" in p.query:
        return ".webp"
    return ".jpg"


def download_images_for(tweet: dict) -> dict:
    """Download every image in `tweet["media"]` (kind == image), mutating each
    entry with a repo-relative `local_path`. Videos untouched. Idempotent.
    """
    media = tweet.get("media") or []
    if not media:
        return tweet
    tweet_id = tweet["tweet_id"]
    target_dir = config.MEDIA_DIR / tweet_id
    img_idx = 0
    for m in media:
        if m.get("kind") != "image":
            continue
        img_idx += 1
        url = _rewrite_size(m["url"])
        local_name = f"img_{img_idx}{_ext_for(url)}"
        target = target_dir / local_name
        rel = target.relative_to(config.ARCHIVE_DIR).as_posix()
        m["local_path"] = rel
        if target.exists() and target.stat().st_size > 0:
            continue
        target_dir.mkdir(parents=True, exist_ok=True)
        try:
            resp = requests.get(url, timeout=config.IMAGE_TIMEOUT_S)
            resp.raise_for_status()
            target.write_bytes(resp.content)
        except requests.RequestException as exc:  # noqa: BLE001
            # Fetch failure isn't fatal — record what we tried and keep the
            # tweet's md file so the archive stays consistent.
            m["local_path"] = None
            m["fetch_error"] = str(exc)
    return tweet
