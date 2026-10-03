"""Tests for the Delayed Reaction EP classifier (pipeline/tools/delayed_ep_scan.py)."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from pipeline.tools.delayed_ep_scan import classify


def bars(rows):
    """rows: list of (open, high, low, close, volume); dates are business days."""
    idx = pd.bdate_range("2026-07-01", periods=len(rows))
    return pd.DataFrame(rows, columns=["Open", "High", "Low", "Close", "Volume"], index=idx)


BASE = [(100, 101, 99, 100, 1_000_000)] * 30
EP = (120, 130, 118, 125, 8_000_000)          # gap day: wide range, big volume
EP_DATE = pd.bdate_range("2026-07-01", periods=31)[-1].strftime("%Y-%m-%d")


class TestStages:
    def test_basing_when_held_and_contracting(self):
        post = [(124, 126, 122, 124, 900_000)] * 5           # tight, above EP low, no breakout
        d = classify(bars(BASE + [EP] + post), EP_DATE)
        assert d.stage == "basing" and d.held and d.contracting and not d.breakout
        assert d.days_since == 5

    def test_breaking_when_today_clears_the_post_ep_high_on_volume(self):
        post = [(124, 126, 122, 124, 900_000)] * 4 + [(125, 132, 124, 131, 2_500_000)]
        d = classify(bars(BASE + [EP] + post), EP_DATE)
        assert d.stage == "breaking" and d.breakout
        assert d.base_high == 126

    def test_failed_when_the_ep_low_is_undercut(self):
        post = [(124, 126, 122, 124, 900_000)] * 3 + [(121, 122, 117, 118, 1_200_000)]
        d = classify(bars(BASE + [EP] + post), EP_DATE)
        assert d.stage == "failed" and not d.held

    def test_drifting_when_held_but_still_wide(self):
        post = [(124, 131, 119, 125, 3_000_000)] * 5        # wide bars, no contraction
        d = classify(bars(BASE + [EP] + post), EP_DATE)
        assert d.stage == "drifting"

    def test_breakout_needs_a_green_close_and_volume(self):
        # closes above base high but red (open > close) -> not a breakout
        post = [(124, 126, 122, 124, 900_000)] * 4 + [(133, 134, 126, 127, 2_500_000)]
        d = classify(bars(BASE + [EP] + post), EP_DATE)
        assert not d.breakout
        # green above base high but on dead volume -> not a breakout
        post = [(124, 126, 122, 124, 900_000)] * 4 + [(125, 132, 124, 131, 200_000)]
        d = classify(bars(BASE + [EP] + post), EP_DATE)
        assert not d.breakout

    def test_near_flag_and_vs_ep_close(self):
        post = [(124, 126, 122, 124, 900_000)] * 5
        d = classify(bars(BASE + [EP] + post), EP_DATE)
        assert d.vs_ep_close_pct == pytest.approx(124 / 125 - 1)
        assert d.near is True

    def test_ep_day_must_be_in_bars_and_not_last(self):
        assert classify(bars(BASE), EP_DATE) is None
        assert classify(bars(BASE + [EP]), EP_DATE) is None


class TestArchive:
    def test_idempotent_per_as_of_and_appends_across_dates(self, tmp_path):
        from pipeline.tools.delayed_ep_scan import archive, LOG_FIELDS
        import csv
        post = [(124, 126, 122, 124, 900_000)] * 5
        d = classify(bars(BASE + [EP] + post), EP_DATE, ticker="T")
        log = tmp_path / "log.csv"
        assert archive([d], "2026-08-14", log) == 1
        assert archive([d], "2026-08-14", log) == 1          # re-run same day: replaced, not doubled
        assert archive([d], "2026-08-15", log) == 1
        rows = list(csv.DictReader(log.open()))
        assert len(rows) == 2 and {r["as_of"] for r in rows} == {"2026-08-14", "2026-08-15"}
        assert list(rows[0].keys()) == LOG_FIELDS
        assert rows[0]["stage"] == "basing"


class TestCandidatesAfterEpSplit:
    """2026-09-18 (Andy 「12 注册 EP Stockbee和 EP Qullamaggie」): the EP archive
    rows now come from two screeners; the retired 'episodic_pivot' rows
    (<= 09-17) stay candidates so the watch does not go blind in the switch."""

    def _events(self, tmp_path, rows):
        p = tmp_path / "ev.csv"
        p.write_text("date,ticker,screener,group,change_pct,rel_volume,volume,sector,atr_ext,"
                     "num_contractions,pct_to_pivot\n"
                     + "".join(f"{d},{t},{s},,0.12,4.0,,Tech,,,\n" for d, t, s in rows))
        return p

    def test_both_new_screeners_and_retired_rows_are_candidates(self, tmp_path, monkeypatch):
        import pipeline.tools.delayed_ep_scan as D
        monkeypatch.setattr(D, "EVENTS", self._events(tmp_path, [
            ("2026-09-15", "OLD", "episodic_pivot"),
            ("2026-09-21", "SBX", "ep_stockbee"),
            ("2026-09-21", "QMX", "ep_qullamaggie"),
            ("2026-09-21", "GNX", "gainers_4pct"),           # negative: not an EP screener
        ]))
        got = D.load_candidates("2026-09-25", 3, 15)
        assert set(got) == {"OLD", "SBX", "QMX"}


# ── 当天那根 K 线缺失时不许拿前一天冒充（09-02 与 09-30 同形两次）──

def test_session_bar_check_rejects_a_frame_that_stops_the_day_before():
    """vendor 当天 Close=NaN → dropna 丢掉 → 最后一根是前一天：必须判「不是当天」。"""
    import pandas as pd
    from pipeline.tools import delayed_ep_scan as S
    idx = pd.to_datetime(["2026-09-28", "2026-09-29"])     # 09-30 那根被 dropna 掉了
    df = pd.DataFrame({"Close": [10.0, 10.5]}, index=idx)
    assert S._is_session_bar(df, "2026-09-30") is False


def test_session_bar_check_accepts_the_real_session():
    import pandas as pd
    from pipeline.tools import delayed_ep_scan as S
    idx = pd.to_datetime(["2026-09-29", "2026-09-30"])
    df = pd.DataFrame({"Close": [10.5, 10.4]}, index=idx)
    assert S._is_session_bar(df, "2026-09-30") is True


def test_session_bar_check_survives_intraday_timestamps():
    """yfinance 有时带时分秒/时区：按日比，不按时刻比。"""
    import pandas as pd
    from pipeline.tools import delayed_ep_scan as S
    idx = pd.to_datetime(["2026-09-29 00:00", "2026-09-30 00:00"])
    df = pd.DataFrame({"Close": [10.5, 10.4]}, index=idx)
    assert S._is_session_bar(df, "2026-09-30") is True
    assert S._is_session_bar(pd.DataFrame(), "2026-09-30") is False
