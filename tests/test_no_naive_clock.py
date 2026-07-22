"""Guardrail: trading code must not read the naive host clock for dates.

This Mac runs in JST (~13h ahead of ET); `date.today()` / `datetime.now()`
without a timezone returns "tomorrow" for most of the US session, silently
mis-stamping trading dates. Use pipeline.marketcal.market_today / market_now
instead (see that module).

This test scans pipeline/ and scripts/ for bare `date.today()` /
`datetime.now()` calls. A genuinely-local, non-trading timestamp may opt out
with a trailing `# localtime-ok` comment (with a reason), which is deliberately
noisy so it shows up in review.
"""
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SCAN_DIRS = ("pipeline", "scripts")
# Bare .now()/.today() with no argument (a tz arg makes it explicit & fine).
BARE = re.compile(r"\b(?:dt\.)?(?:date\.today|datetime\.now)\(\s*\)")
OPT_OUT = "localtime-ok"


def _py_files():
    for d in SCAN_DIRS:
        for p in (REPO / d).rglob("*.py"):
            if "__pycache__" in p.parts:
                continue
            yield p


def _offending_lines(path: Path):
    """Lines with a bare naive-clock call, excluding strings/comments/opt-outs.

    Crude but effective: skip the module docstring by ignoring lines whose match
    sits inside a string is overkill here; instead we exclude the marketcal
    module (which names the banned calls in prose) and honour the opt-out.
    """
    out = []
    for i, line in enumerate(path.read_text().splitlines(), 1):
        code = line.split("#", 1)[0]
        if not BARE.search(code):
            continue
        if OPT_OUT in line:
            continue
        out.append((i, line.strip()))
    return out


def test_no_bare_naive_clock_in_trading_code():
    marketcal = REPO / "pipeline" / "marketcal.py"
    offenders = []
    for p in _py_files():
        if p == marketcal:            # documents the banned calls in prose
            continue
        for ln, text in _offending_lines(p):
            offenders.append(f"{p.relative_to(REPO)}:{ln}: {text}")
    assert not offenders, (
        "Bare date.today()/datetime.now() found in trading code — use "
        "pipeline.marketcal.market_today()/market_now(), or add a trailing "
        "'# localtime-ok <reason>' if it is genuinely a local, non-trading "
        "timestamp:\n  " + "\n  ".join(offenders)
    )
