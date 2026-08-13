# X Bookmarks → Local Markdown Archive

Mirror your X/Twitter Bookmarks folder into `_source_material/tweets/` as
grep-able `.md` files. Same frontmatter schema as `JeffSun_Wiki/sources/tweets/`
plus `bookmarked_at` and `media` fields.

## Why

Your bookmarks are a hand-curated signal filter — you only bookmark what
matters. Having them locally means you (and Claude) can grep, quote, and
reference them without opening the app.

## How it works

- **Playwright + persistent Chromium profile.** No X Developer API dependency
  (Free tier no longer covers reads), no MCP dependency.
- **First run:** headed browser opens, you log into X once, cookies persist to
  `~/.local/share/x-bookmarks/profile/`.
- **After that:** headless daily runs use those cookies. Cron-schedulable.

## Setup

Install dependencies (one-time):

```bash
.venv/bin/pip install -r pipeline/requirements.txt
.venv/bin/playwright install chromium
```

Log into X (one-time; opens a browser window):

```bash
.venv/bin/python -m pipeline.x_bookmarks login
```

Complete the X login, then close the window. Cookies are saved to the
persistent profile.

## Usage

```bash
# One-off full backfill (safe to re-run — dedups by tweet_id)
.venv/bin/python -m pipeline.x_bookmarks backfill

# Daily incremental (stops after N consecutive already-archived tweets)
.venv/bin/python -m pipeline.x_bookmarks sync

# Optional cap: safe smoke test
.venv/bin/python -m pipeline.x_bookmarks backfill --limit 5

# Archive stats
.venv/bin/python -m pipeline.x_bookmarks status
```

## What gets saved

For each bookmarked tweet:

- `_source_material/tweets/{handle}-{tweet_id}.md` — frontmatter + body
- `_source_material/tweets/media/{tweet_id}/img_N.jpg` — images (rewritten to
  `name=large` for archival quality)
- Videos are linked-only in frontmatter (`media[].kind = "video"`) — the raw
  MP4 URL isn't easily extractable from X's DOM and would balloon disk usage.

The entire `_source_material/` tree is `.gitignore`d — grep-only, not for git.

## Where to fix things when X changes their DOM

Every selector is centralized in `extractor.py` at the top (`EXTRACT_JS`
constant). If X ships a redesign, that's the one file to touch.

## Scheduling (later)

For a daily cron, wrap in launchd or `cron`:

```
30 22 * * *  cd /Users/taolezhu/Documents/AI-Trading-System && .venv/bin/python -m pipeline.x_bookmarks sync >> /tmp/x-bookmarks.log 2>&1
```

Don't schedule until you've verified `sync` runs cleanly a few times manually.
