"""Scroll the Bookmarks page, extract each tweet card, save markdown + media."""
from __future__ import annotations

import asyncio
from typing import Literal

from . import config
from .browser import is_logged_in, open_context
from .extractor import EXTRACT_JS, raw_to_tweet
from .media import download_images_for
from .writer import is_archived, write_tweet


class NotLoggedIn(RuntimeError):
    pass


class NoTweetsFound(RuntimeError):
    pass


async def _sync_async(mode: Literal["sync", "backfill"], limit: int | None) -> int:
    """Return the number of newly-saved tweets. Raises on non-recoverable errors."""
    saved = 0
    seen_streak = 0
    idle_streak = 0
    processed_ids: set[str] = set()

    async with open_context(headless=True) as ctx:
        if not await is_logged_in(ctx):
            raise NotLoggedIn("run: python -m pipeline.x_bookmarks login")

        page = await ctx.new_page()
        await page.goto(config.BOOKMARKS_URL, wait_until="domcontentloaded", timeout=30_000)
        try:
            await page.wait_for_selector('article[data-testid="tweet"]', timeout=15_000)
        except Exception as exc:
            raise NoTweetsFound("no tweet cards rendered — bookmarks empty or DOM changed") from exc

        for _step in range(config.MAX_SCROLL_STEPS):
            raws = await page.evaluate(EXTRACT_JS)
            new_this_tick = 0
            for raw in raws:
                tid = raw["tweet_id"]
                if tid in processed_ids:
                    continue
                processed_ids.add(tid)
                new_this_tick += 1

                if is_archived(tid):
                    seen_streak += 1
                    if mode == "sync" and seen_streak >= config.STOP_AFTER_N_SEEN:
                        print(f"Sync stop: {seen_streak} consecutive already-archived tweets.")
                        return saved
                    continue
                seen_streak = 0

                tweet = raw_to_tweet(raw)
                download_images_for(tweet)
                path = write_tweet(tweet)
                saved += 1
                print(f"[{saved}] {tweet['author']} {tid} -> {path.name}")

                if limit is not None and saved >= limit:
                    print(f"Hit --limit {limit}, stopping.")
                    return saved

            if new_this_tick == 0:
                idle_streak += 1
                if idle_streak >= config.IDLE_TICKS_TO_STOP:
                    print(f"Scroll bottom reached (idle {idle_streak} ticks).")
                    return saved
            else:
                idle_streak = 0

            await page.evaluate("window.scrollBy(0, window.innerHeight * 0.85)")
            await page.wait_for_timeout(config.SCROLL_PAUSE_MS)

        print(f"Hit MAX_SCROLL_STEPS ({config.MAX_SCROLL_STEPS}), stopping.")
        return saved


def run_scrape(mode: Literal["sync", "backfill"], limit: int | None = None) -> int:
    try:
        saved = asyncio.run(_sync_async(mode=mode, limit=limit))
    except NotLoggedIn as exc:
        print(f"Not logged in ({exc}).")
        return 2
    except NoTweetsFound as exc:
        print(f"Nothing to fetch ({exc}).")
        return 3
    print(f"Done. Saved {saved} new tweet(s).")
    return 0
