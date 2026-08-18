"""fetch_baskets merges by date: never shorter than disk, always the newest bar."""
import json
from pathlib import Path

import pandas as pd

from pipeline.rotation import fetch_baskets as FB


def _frame(dates, tickers):
    idx = pd.to_datetime(dates)
    cols = pd.MultiIndex.from_product([tickers, ["Close"]])
    df = pd.DataFrame(index=idx, columns=cols, dtype=float)
    for t in tickers:
        df[(t, "Close")] = [100.0 + i for i in range(len(dates))]
    return df


class TestMerge:
    def test_window_slide_does_not_refuse_the_new_session(self, tmp_path, monkeypatch):
        """2026-08-18: the 2y window came back one bar shorter than the stored
        file (weekday slide) and every basket was refused; the baskets froze."""
        old = [{"date": d, "close": 1.0} for d in ["2026-08-11", "2026-08-12", "2026-08-13", "2026-08-14"]]
        (tmp_path / "SPY.json").write_text(json.dumps({"ticker": "SPY", "bars": old}))
        monkeypatch.setattr(FB, "required_tickers", lambda: ["SPY"])
        monkeypatch.setattr(FB.yf, "download", lambda *a, **k: _frame(["2026-08-12", "2026-08-13", "2026-08-14", "2026-08-17"], ["SPY"]))
        out = FB.fetch(out_dir=tmp_path)
        bars = json.loads((tmp_path / "SPY.json").read_text())["bars"]
        assert out["written"] == 1
        assert [b["date"] for b in bars] == ["2026-08-11", "2026-08-12", "2026-08-13", "2026-08-14", "2026-08-17"]
        assert bars[-1]["close"] == 103.0          # new bar present, new values win

    def test_partial_response_cannot_punch_holes(self, tmp_path, monkeypatch):
        old = [{"date": d, "close": 1.0} for d in ["2026-07-14", "2026-07-15", "2026-07-16", "2026-07-17"]]
        (tmp_path / "SPLV.json").write_text(json.dumps({"ticker": "SPLV", "bars": old}))
        monkeypatch.setattr(FB, "required_tickers", lambda: ["SPLV"])
        monkeypatch.setattr(FB.yf, "download", lambda *a, **k: _frame(["2026-07-14", "2026-07-17", "2026-07-20"], ["SPLV"]))
        FB.fetch(out_dir=tmp_path)
        bars = json.loads((tmp_path / "SPLV.json").read_text())["bars"]
        assert [b["date"] for b in bars] == ["2026-07-14", "2026-07-15", "2026-07-16", "2026-07-17", "2026-07-20"]
