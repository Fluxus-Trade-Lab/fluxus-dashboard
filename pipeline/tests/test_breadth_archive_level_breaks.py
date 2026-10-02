"""The universe level break in breadth_archive.csv, as an executable fact.

Seven places in this repo say the universe went "3000 -> 5614 on 2026-08-14".
The archive says the jump is on **2026-08-10** (3000 -> 5618), four sessions
earlier. 08-14/5614 is not a typo -- it is the fingerprint of a live-only
reading: the jump sits inside a five-session restated run (2026-08-07..08-13,
`source=backfill`, written by `e8ac440ef` while repairing the Finviz
`Change` -> `Change %` rename), so a reader who splits the archive by `source`
sees 08-06 at 3000, then 08-14 at 5614, and never sees the jump itself.

No runtime consumer filters on `source` -- `breadth_store.py` fills a missing
one with 'live' and derives over every row, `build_pack.py` indexes by date --
so for every piece of code the splice point is 08-10, and a window trimmed at
08-14 keeps four post-break sessions on the pre-break side.

That claim was prose for seven weeks and prose has no "I am stale" field, so
these are the three facts a future reader should get from a ruler instead:
the break is where we say it is, it is invisible to a live-only reader (the
trap), and it is the count columns -- not the ratio columns -- that care.

Study: `data/research/universe_break_2026-08-10/README.md` (T-1003-10).
"""
from __future__ import annotations

import csv
import statistics as st
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
ARCHIVE = REPO / "data/history/breadth_archive.csv"

# A universe discontinuity is a level break in every count column at once, so
# it may not arrive unannounced. Declaring one is a deliberate act: add the row
# here, and say in the same commit which archived series it severs.
DECLARED_BREAKS = {
    # (last session before, first session after): (universe before, after)
    ("2026-08-07", "2026-08-10"): (3000, 5618),
}

# How a live-only reader mis-sees each declared break. Keyed by the break's
# first session. This is the whole trap, written down.
BREAK_IS_INVISIBLE_TO_LIVE_READER = {
    "2026-08-10": {"last_live_before": "2026-08-06",
                   "first_live_after": "2026-08-14",
                   "sessions_late": 4},
}

THRESHOLD = 0.20          # a 20% one-session move in the universe is a break
WINDOW_FROM = "2026-05-01"
RATIO_COLS = ("pct_above_50sma", "pct_above_200sma", "t2108")

pytestmark = pytest.mark.skipif(not ARCHIVE.exists(), reason="archive not present")


@pytest.fixture(scope="module")
def rows() -> list[dict]:
    with ARCHIVE.open() as fh:
        out = list(csv.DictReader(fh))
    assert out, "archive is empty"
    return out


def _u(row) -> float | None:
    v = (row.get("universe_size") or "").strip()
    return None if v in ("", "nan") else float(v)


def _series(rows, col, lo, hi) -> list[float]:
    out = []
    for r in rows:
        if not (lo <= r["date"] < hi):
            continue
        v = (r.get(col) or "").strip()
        if v not in ("", "nan"):
            out.append(float(v))
    return out


def _breaks(rows) -> dict[tuple[str, str], tuple[float, float]]:
    found, prev = {}, None
    for r in rows:
        u = _u(r)
        if u is None:
            continue
        if prev and prev[1] > 0 and abs(u / prev[1] - 1) >= THRESHOLD:
            found[(prev[0], r["date"])] = (prev[1], u)
        prev = (r["date"], u)
    return found


def test_every_universe_level_break_is_declared(rows):
    """An undeclared break means a count series was severed and nobody said so."""
    found = _breaks(rows)
    assert set(found) == set(DECLARED_BREAKS), (
        f"undeclared {sorted(set(found) - set(DECLARED_BREAKS))}, "
        f"vanished {sorted(set(DECLARED_BREAKS) - set(found))}"
    )
    for span, (before, after) in DECLARED_BREAKS.items():
        got = found[span]
        assert (round(got[0]), round(got[1])) == (before, after), f"{span}: {got}"


def test_the_break_is_invisible_to_a_live_only_reader(rows):
    """The trap: filter on source=='live' and the jump reports 4 sessions late.

    This is the assertion that would have caught "3000 -> 5614 on 2026-08-14".
    It is not asserting that 08-14 is wrong in the abstract -- it is asserting
    that 08-14 is what the live-only reading yields, which is why that date
    must never be quoted without naming the reading.
    """
    for first_session, expect in BREAK_IS_INVISIBLE_TO_LIVE_READER.items():
        live = [r for r in rows if r.get("source") == "live"]
        before = [r for r in live if r["date"] < first_session]
        after = [r for r in live if r["date"] >= first_session]
        assert before and after, first_session

        assert before[-1]["date"] == expect["last_live_before"]
        assert after[0]["date"] == expect["first_live_after"]

        # How far off the live-only reading lands, and that the sessions it
        # skipped are exactly the restated ones. (An `after[0]["date"] !=
        # first_session` assertion belongs here by instinct and was dropped:
        # the equality above already implies it, so it survived every mutation
        # and measured nothing.)
        late = [r for r in rows if first_session <= r["date"] < after[0]["date"]]
        assert len(late) == expect["sessions_late"]

        # and those sessions really are restated, which is why they were missed
        assert all(r.get("source") != "live" for r in late)

        # The size a live-only reader quotes is the first live row's universe,
        # which is NOT the size at the jump -- that is where 5614 came from.
        span = next(k for k in DECLARED_BREAKS if k[1] == first_session)
        size_before, size_at_jump = DECLARED_BREAKS[span]
        assert round(_u(before[-1])) == size_before
        assert round(_u(after[0])) != size_at_jump


def test_ratio_columns_survive_a_late_splice_and_count_columns_do_not(rows):
    """Which columns care that the splice is 4 sessions late.

    Splicing at 08-14 drags 08-10..08-13 -- all on the enlarged universe --
    onto the pre-break side. The `new_highs` leg is the positive control: if it
    ever stops moving, this test has stopped measuring anything and the ratio
    legs below prove nothing.
    """
    true_break = "2026-08-10"
    late_splice = "2026-08-14"

    hi_true = _series(rows, "new_highs", WINDOW_FROM, true_break)
    hi_late = _series(rows, "new_highs", WINDOW_FROM, late_splice)
    assert hi_true and hi_late
    assert max(hi_late) >= max(hi_true) * 1.5, (
        "positive control dead: the late splice no longer moves a count column, "
        f"max {max(hi_true)} -> {max(hi_late)}"
    )

    for col in RATIO_COLS:
        a = _series(rows, col, WINDOW_FROM, true_break)
        b = _series(rows, col, WINDOW_FROM, late_splice)
        assert a and b, col
        assert max(a) == max(b), f"{col}: ratio max moved {max(a)} -> {max(b)}"
        # the median may move -- that is four extra market days, not the break
        assert abs(st.median(b) - st.median(a)) / st.median(a) < 0.05, col
