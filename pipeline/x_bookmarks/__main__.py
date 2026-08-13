"""CLI entrypoint: `python -m pipeline.x_bookmarks [login|sync|backfill|status]`."""
from __future__ import annotations

import argparse
import asyncio
import sys

from . import config


def cmd_status(_: argparse.Namespace) -> int:
    from .writer import list_archived
    archived = list_archived()
    print(f"Archive dir:      {config.ARCHIVE_DIR}")
    print(f"Profile dir:      {config.PROFILE_DIR}")
    print(f"Tweets archived:  {len(archived)}")
    if archived:
        authors: dict[str, int] = {}
        for _tid, path in archived.items():
            author = path.name.rsplit("-", 1)[0]
            authors[author] = authors.get(author, 0) + 1
        top = sorted(authors.items(), key=lambda kv: -kv[1])[:10]
        print("Top authors:")
        for a, n in top:
            print(f"  @{a:<24} {n}")
    return 0


def cmd_sync(args: argparse.Namespace) -> int:
    from .scraper import run_scrape
    return run_scrape(mode="sync", limit=args.limit)


def cmd_backfill(args: argparse.Namespace) -> int:
    from .scraper import run_scrape
    return run_scrape(mode="backfill", limit=args.limit)


def cmd_login(_: argparse.Namespace) -> int:
    """Open a headed browser at x.com/login. User logs in manually, then closes
    the browser. Cookies are written to the persistent profile.
    """
    from .browser import open_context

    async def _run() -> int:
        async with open_context(headless=False) as ctx:
            page = await ctx.new_page()
            await page.goto(config.LOGIN_URL, wait_until="domcontentloaded")
            print("=" * 60)
            print("A browser window opened.")
            print("1. Log into X.")
            print("2. Once you see your home timeline, close the window.")
            print("3. Cookies will be saved to:", config.PROFILE_DIR)
            print("=" * 60)
            # Wait for the user to close the page.
            try:
                await page.wait_for_event("close", timeout=0)
            except Exception:
                pass
        print("Login flow ended. Try: python -m pipeline.x_bookmarks status")
        return 0

    return asyncio.run(_run())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m pipeline.x_bookmarks")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_login = sub.add_parser("login", help="One-time: open headed browser to log into X and save cookies.")
    p_login.set_defaults(func=cmd_login)

    p_sync = sub.add_parser("sync", help="Incremental: stop when consecutive already-archived tweets hit threshold.")
    p_sync.add_argument("--limit", type=int, default=None)
    p_sync.set_defaults(func=cmd_sync)

    p_bf = sub.add_parser("backfill", help="Scroll to the bottom, save everything not already archived.")
    p_bf.add_argument("--limit", type=int, default=None)
    p_bf.set_defaults(func=cmd_backfill)

    p_st = sub.add_parser("status", help="Show archive stats.")
    p_st.set_defaults(func=cmd_status)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
