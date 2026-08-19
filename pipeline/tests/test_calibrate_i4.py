"""The I4/I7 registry is measured, not guessed (pipeline/tools/calibrate_i4.py)."""
from __future__ import annotations

import pandas as pd

from pipeline.tools import calibrate_i4 as C

DAYS = [f"2026-0{m}-{d:02d}" for m in (5, 6) for d in range(1, 16)]   # 30 sessions


def _events(tmp_path, per_day):
    rows = [{"date": d, "ticker": f"T{i}", "screener": s}
            for d, per in per_day.items() for s, n in per.items() for i in range(n)]
    pd.DataFrame(rows).to_csv(tmp_path / "ticker_events.csv", index=False)


def test_always_present_and_fat_is_reliable_thin_or_patchy_is_sparse(tmp_path):
    per_day = {}
    for i, d in enumerate(DAYS):
        per_day[d] = {"fat": 100 + i, "thin": 3}            # thin: always there, tiny
        if i % 3:
            per_day[d]["patchy"] = 200                      # fat but absent 1 day in 3
    _events(tmp_path, per_day)
    reg = C.calibrate(tmp_path)["archives"]["ticker_events.csv"]["series"]
    assert reg["fat"]["kind"] == "reliable"
    assert reg["thin"]["kind"] == "sparse"                  # median 3 rows: an empty day is ordinary
    assert reg["patchy"]["kind"] == "sparse"                # 67% presence


def test_until_freezes_the_registry_before_an_outage(tmp_path):
    """A rolling baseline learns that an outage is normal; a frozen one does not."""
    per_day = {d: {"fat": 100} for d in DAYS}
    for d in DAYS[-8:]:
        per_day[d] = {"other": 100}                         # 'fat' dies for the last 8 sessions
    _events(tmp_path, per_day)
    assert C.calibrate(tmp_path)["archives"]["ticker_events.csv"]["series"]["fat"]["kind"] == "sparse"
    frozen = C.calibrate(tmp_path, until=DAYS[-8])["archives"]["ticker_events.csv"]["series"]
    assert frozen["fat"]["kind"] == "reliable"


def test_band_is_never_tighter_than_the_guard_rails(tmp_path):
    _events(tmp_path, {d: {"flat": 50} for d in DAYS})      # zero variance
    b = C.calibrate(tmp_path)["archives"]["ticker_events.csv"]["series"]["flat"]["band"]
    assert b["floor"] <= C.FLOOR_CAP and b["ceil"] >= C.CEIL_FLOOR
