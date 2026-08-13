"""Playwright session management — persistent profile so login only happens once."""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from playwright.async_api import BrowserContext, async_playwright

from . import config


@asynccontextmanager
async def open_context(headless: bool = True) -> AsyncIterator[BrowserContext]:
    """Yield a BrowserContext with the persistent x-bookmarks profile.

    Cookies + storage survive across runs. First run should be `headless=False`
    (via the `login` CLI command) so the user can complete the X login flow.
    """
    config.PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as pw:
        context = await pw.chromium.launch_persistent_context(
            user_data_dir=str(config.PROFILE_DIR),
            headless=headless,
            user_agent=config.USER_AGENT,
            viewport={"width": 1440, "height": 900},
            locale="en-US",
        )
        try:
            yield context
        finally:
            await context.close()


async def is_logged_in(context: BrowserContext) -> bool:
    """Check whether the persistent context has a live X session.

    X sets an `auth_token` cookie only for authenticated users. Logged-out
    sessions get a `guest_id` cookie with no `auth_token`. Cookie-based check
    survives the empty-body page X serves to headless browsers.
    """
    cookies = await context.cookies("https://x.com")
    return any(c["name"] == "auth_token" and c.get("value") for c in cookies)
