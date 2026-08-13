"""Parse tweet cards from x.com/i/bookmarks into structured dicts.

Selectors are centralized in EXTRACT_JS at the top so they can be adjusted in
one place when X ships a DOM change.
"""
from __future__ import annotations

from typing import Any


# Run once inside the page. Returns a list of tweet dicts for every visible card.
# Twitter's DOM uses stable-ish `data-testid` attrs; if any of these break we
# fix them here in one file.
EXTRACT_JS = r"""
() => {
  const parseCount = (raw) => {
    if (!raw) return 0;
    const s = String(raw).trim().replace(/,/g, '');
    if (!s) return 0;
    const m = s.match(/^([\d.]+)\s*([KMB]?)$/i);
    if (!m) return parseInt(s, 10) || 0;
    const n = parseFloat(m[1]);
    const mult = { '': 1, K: 1e3, M: 1e6, B: 1e9 }[m[2].toUpperCase()];
    return Math.round(n * mult);
  };

  const cards = Array.from(document.querySelectorAll('article[data-testid="tweet"]'));
  return cards.map((card) => {
    // permalink + tweet_id + iso date come from the timestamp <a><time></time></a>
    let tweetId = null;
    let handle = null;
    let iso = null;
    let permalink = null;
    const timeLink = card.querySelector('a[href*="/status/"] time');
    if (timeLink) {
      iso = timeLink.getAttribute('datetime');
      const a = timeLink.closest('a');
      if (a) {
        permalink = a.getAttribute('href');
        const m = permalink && permalink.match(/^\/([^/]+)\/status\/(\d+)/);
        if (m) { handle = m[1]; tweetId = m[2]; }
      }
    }

    // Fallback for author handle: User-Name block contains <a href="/handle">
    if (!handle) {
      const un = card.querySelector('[data-testid="User-Name"] a[href^="/"]');
      if (un) {
        const h = un.getAttribute('href');
        if (h) handle = h.replace(/^\//, '').split('/')[0];
      }
    }

    // Body text
    const textEl = card.querySelector('[data-testid="tweetText"]');
    const text = textEl ? textEl.innerText : '';

    // Engagement counts
    const likeEl = card.querySelector('[data-testid="like"] [data-testid="app-text-transition-container"]');
    const rtEl = card.querySelector('[data-testid="retweet"] [data-testid="app-text-transition-container"]');
    const likes = parseCount(likeEl && likeEl.innerText);
    const retweets = parseCount(rtEl && rtEl.innerText);

    // Media — images
    const imgEls = Array.from(card.querySelectorAll('[data-testid="tweetPhoto"] img'));
    const images = imgEls
      .map((im) => im.src)
      .filter((s) => s && s.startsWith('https://pbs.twimg.com/'));

    // Media — video presence (URL not directly extractable from DOM in most cases)
    const hasVideo = !!card.querySelector('[data-testid="videoPlayer"], video');

    return {
      tweet_id: tweetId,
      handle,
      permalink,
      date_iso: iso,
      text,
      likes,
      retweets,
      images,
      has_video: hasVideo,
    };
  }).filter((t) => t.tweet_id && t.handle);
}
"""


def raw_to_tweet(raw: dict[str, Any]) -> dict[str, Any]:
    """Normalize the raw JS-extracted dict into the schema `writer.write_tweet` expects."""
    handle = raw["handle"]
    tweet_id = raw["tweet_id"]
    url = f"https://x.com/{handle}/status/{tweet_id}"
    media = [{"kind": "image", "url": u} for u in (raw.get("images") or [])]
    if raw.get("has_video"):
        media.append({"kind": "video", "url": url})  # X hides direct video URL; link back to tweet
    return {
        "author": f"@{handle}",
        "tweet_id": tweet_id,
        "url": url,
        "date": raw.get("date_iso") or "",
        "text": raw.get("text") or "",
        "likes": raw.get("likes") or 0,
        "retweets": raw.get("retweets") or 0,
        "tags": ["bookmark"],
        "media": media,
    }
