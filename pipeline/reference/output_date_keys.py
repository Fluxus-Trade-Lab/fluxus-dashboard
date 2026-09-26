"""Canonical + recognized date-key registry for data/output/*.json (T-0926-56).

The 09-26 口径日期审计 found 7 different top-level key spellings across
data/output for "what date is this file's data" (timestamp/date/as_of/asof/
members_asof/proxy_map_date/parallel_until) and one file (etf_data.json)
with none at all. A staleness check that only recognizes some of those names
will silently pass a file using the 8th name it hasn't seen yet -- that is
exactly how the audit's own first draft misjudged 11 files. This module is
the one place both the enforcing test (pipeline/tests/test_output_date_keys.py)
and the docs (data/reference/METRIC_SOURCES.md) read from, so the two cannot
drift apart the way a rule copied into two files tends to.

CANONICAL_DATE_KEY is what NEW data/output files must use. Existing files
keep their legacy key (rewriting ~15 write sites for a cosmetic rename was
judged not worth the risk to the death-line pipeline -- see METRIC_SOURCES.md)
and are grandfathered via RECOGNIZED_DATE_KEYS.
"""

from __future__ import annotations

CANONICAL_DATE_KEY = "as_of"

# Real freshness signals only. `proxy_map_date` (theme_board.json) and
# `parallel_until` (theme_board.json) are dates but not freshness dates --
# see pipeline/themes/proxy_board.py's build() -- so they are deliberately
# left out: a file that only has one of those two would still fail this
# check, which is correct (it has no way to say "as of when").
RECOGNIZED_DATE_KEYS = frozenset({
    CANONICAL_DATE_KEY,
    "timestamp",
    "date",
    "asof",
    "members_asof",
})

# Top-level shapes that carry no per-run freshness date by design, with why:
EXEMPT_FILES = frozenset({
    "briefs.json",              # bare list of demo/seed rows, no top-level object at all
    "h1_2026_stats.json",       # one-off H1 2026 backtest; dated by meta.csv snapshot, not a daily run
    "performance.json",         # portfolio performance dump, not refreshed by the daily pipeline
    "portfolio_backtest.json",  # one-off backtest run (generated_at is the run time, not a session date)
    "x_heat.json",               # rolling 7d research window (start/end), not a session-date file
})
