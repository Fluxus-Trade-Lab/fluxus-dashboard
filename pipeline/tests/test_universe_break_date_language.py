"""Guards T-1003-11: six prose spots used to claim the universe break (the
step from a 3000-name pool to a 5000+-name pool) happened on 2026-08-14 at
5614 names. The archive (data/history/breadth_archive.csv) shows the real
jump is 2026-08-07 -> 2026-08-10, 3000 -> 5618; 2026-08-14/5614 is only the
first `source == 'live'` row after a backfilled segment, an artifact of
reading the archive by source instead of by date (see
data/research/universe_break_2026-08-10/README.md).

Each check: the stale claim ("5614" tied to "08-14" as if that were the
break itself) must be gone, the real numbers (3000 -> 5618 on 2026-08-10)
must be present, and wherever 08-14/5614 still appears it must be flagged
as the segmented-read artifact, not the break.
"""
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _collapse(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def _check(path: str, must_contain: list[str], must_not_contain: list[str]):
    raw = (REPO_ROOT / path).read_text(encoding="utf-8")
    flat = _collapse(raw)
    for needle in must_contain:
        assert _collapse(needle) in flat, f"{path} is missing: {needle!r}"
    for needle in must_not_contain:
        assert _collapse(needle) not in flat, f"{path} still has the stale claim: {needle!r}"


def test_breadth_metrics_comment_names_the_real_break():
    _check(
        "pipeline/screeners/breadth_metrics.py",
        must_contain=[
            "3000 -> 5618 on 2026-08-10",
            "makes it look like 3000 -> 5614 on 2026-08-14 instead",
        ],
        must_not_contain=["3000 -> 5614 on 2026-08-14)."],
    )


def test_breadth_metrics_test_docstring_names_the_real_break():
    _check(
        "pipeline/tests/test_breadth_metrics.py",
        must_contain=[
            "universe 3000 -> 5618 on 2026-08-10",
            "makes it look like",
            "3000 -> 5614 on 2026-08-14 instead",
        ],
        must_not_contain=["universe 3000 -> 5614 on 2026-08-14)."],
    )


def test_breadth_store_class_docstring_names_the_real_break():
    _check(
        "pipeline/tests/test_breadth_store.py",
        must_contain=[
            "universe stepped from 3000 to 5618 names on 2026-08-10",
            "makes it look like",
            "3000 -> 5614 on 2026-08-14 instead",
        ],
        must_not_contain=["universe stepped from 3000 to 5614 names on 2026-08-14"],
    )


def test_breadth_store_ratio_test_docstring_names_the_real_break():
    _check(
        "pipeline/tests/test_breadth_store.py",
        must_contain=[
            "happened on 2026-08-10 when the universe went",
            "3000 -> 5618",
            "look like 2026-08-14 / 5614 instead",
        ],
        must_not_contain=["happened on 2026-08-14 when the universe went"],
    )


def test_metric_sources_record_high_percent_paragraph_names_the_real_break():
    _check(
        "data/reference/METRIC_SOURCES.md",
        must_contain=[
            "对 08-10 那次 universe 从 3000 涨到 5618 的断层免疫",
            "读成 08-14/5614",
        ],
        must_not_contain=["对 08-14 那次 universe 从 3000 涨到 5614 的断层免疫"],
    )


def test_metric_sources_registered_debt_paragraph_names_the_real_break():
    _check(
        "data/reference/METRIC_SOURCES.md",
        must_contain=[
            "比值口径能让 08-10 断层",
            "5618",
            "读成 08-14/5614",
        ],
        must_not_contain=["比值口径能让 08-14 断层"],
    )
