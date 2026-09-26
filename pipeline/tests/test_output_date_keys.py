"""data/output files must carry a recognized date key -- new ones especially.

T-0926-56 audit: 7 different names were in use for "what trading day is this"
(`timestamp` x15, `date` x8, `as_of`/`asof` x2/x1 -- both spellings live at
once -- `members_asof`, `proxy_map_date`, `parallel_until` x1 each), and
`etf_data.json` had none of them: a bare JSON list with no date string
anywhere, so nothing (human or gate) could tell a stale copy from a fresh
one. The audit's own first pass only checked 6 of the 7 names and mis-fired
11 false "no date" reports -- the bug it was hunting for is exactly what a
partial key list does to whoever writes the 8th name next (`portfolio_backtest.json`
ships `generated_at`, an 8th name this test does not chase either -- it is
in EXEMPT_FILES instead, see below).

Canonical key going forward is `as_of` (YYYY-MM-DD, ET trading day --
`pipeline.marketcal.last_completed_session().isoformat()`, the same source
`timestamp`/`date` fields already use throughout run_all.py). Existing files
keep their legacy key rather than being rewritten wholesale; a genuinely new
file that lacks both `as_of` and every legacy name fails this test loudly
instead of silently joining an unrecognized 8th name.

See data/reference/DATA_CONTRACTS.md §十九 for the decision and
data/output/theme_board.json's `proxy_map_date` note for why that file has
two dates a day apart on purpose.
"""
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
OUTPUT_DIR = REPO / "data/output"

CANONICAL_KEY = "as_of"
LEGACY_DATE_KEYS = {"timestamp", "date", "asof", "members_asof",
                    "proxy_map_date", "parallel_until"}

# Static/report artifacts, not daily market-state snapshots -- each already
# carries its own de facto date (a window, a `generated_at`), just not one of
# the 7 names above, and staleness for them means something different (the
# backtest input CSV changed) than "the pipeline didn't run tonight".
EXEMPT_FILES = {
    "h1_2026_stats.json",       # meta.start/meta.end -- H1 backtest report
    "performance.json",         # _source names its own review-window file
    "portfolio_backtest.json",  # generated_at
    "x_heat.json",              # window.start/window.end, a 7-day rollup
}


def _output_files():
    return sorted(OUTPUT_DIR.glob("*.json"))


def _has_date_key(obj: dict) -> bool:
    return CANONICAL_KEY in obj or bool(LEGACY_DATE_KEYS & obj.keys())


def test_every_output_file_has_a_recognized_date_key():
    missing = []
    for path in _output_files():
        if path.name in EXEMPT_FILES:
            continue
        data = json.loads(path.read_text())
        if isinstance(data, dict):
            if not _has_date_key(data):
                missing.append(path.name)
        elif isinstance(data, list):
            if data and not all(isinstance(row, dict) and _has_date_key(row) for row in data):
                missing.append(f"{path.name} (row missing date key)")
        else:
            missing.append(f"{path.name} (unexpected top-level type {type(data).__name__})")
    assert not missing, (
        f"data/output files with no recognized date key (canonical={CANONICAL_KEY!r}, "
        f"legacy={sorted(LEGACY_DATE_KEYS)}): {missing}. New files must carry "
        f"`{CANONICAL_KEY}`; add to EXEMPT_FILES with a reason only if it is a "
        f"static report, not a daily snapshot."
    )


def test_etf_data_rows_all_carry_the_canonical_key():
    """The one file this task actually fixed -- regression guard on its own."""
    path = OUTPUT_DIR / "etf_data.json"
    rows = json.loads(path.read_text())
    assert rows, "etf_data.json is empty"
    assert all(CANONICAL_KEY in row for row in rows), (
        "etf_data.json rows are missing as_of again"
    )
