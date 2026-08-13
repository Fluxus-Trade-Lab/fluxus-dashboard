from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ARCHIVE_DIR = REPO_ROOT / "_source_material" / "tweets"
MEDIA_DIR = ARCHIVE_DIR / "media"

# Persistent Playwright profile. First-time `login` command writes here.
# Dedicated profile (not the user's real Chrome) so cookie state is isolated
# and headless runs don't fight the user's live session.
PROFILE_DIR = Path.home() / ".local" / "share" / "x-bookmarks" / "profile"

BOOKMARKS_URL = "https://x.com/i/bookmarks"
LOGIN_URL = "https://x.com/login"

# Scraper stopping conditions
STOP_AFTER_N_SEEN = 5   # incremental sync: after this many consecutive already-archived tweets, stop
MAX_SCROLL_STEPS = 200  # backfill hard cap so we can't run forever
SCROLL_PAUSE_MS = 1500  # ms between scroll ticks
IDLE_TICKS_TO_STOP = 3  # scroll stops when this many consecutive ticks yield no new tweets

# HTTP for image fetches
IMAGE_TIMEOUT_S = 20
IMAGE_SIZE = "large"  # pbs.twimg.com `name=` param — highest lossless

# User-agent for Playwright launch. Match a real desktop Chrome so X doesn't
# serve a stripped-down layout.
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)
