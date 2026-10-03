"""tick_cycle.json `history` (T-1003-81): one row per session with a 252-day
rank, same fields as the snapshot; last row == snapshot; mid row re-derived
by hand so the test cannot just compare the code with itself."""
import json

import numpy as np
import pandas as pd

from pipeline.risk import regime_ledger as RL


def _write_tick_csv(tmp_path, n=600):
    rng = np.random.default_rng(7)
    dates = pd.bdate_range(end="2026-10-02", periods=n)
    close = rng.normal(0, 300, n)
    high = close + np.abs(rng.normal(400, 150, n))
    low = close - np.abs(rng.normal(400, 150, n))
    df = pd.DataFrame({"date": dates.strftime("%Y-%m-%d"), "high": high.round(1),
                       "low": low.round(1), "close": close.round(1)})
    df.to_csv(tmp_path / RL.TICK_CSV_NAME, index=False)


def test_history_covers_252_days_and_last_row_matches_snapshot(tmp_path, monkeypatch):
    monkeypatch.setattr(RL, "TVDIR", tmp_path)
    monkeypatch.setattr(RL, "TICK_CYCLE_JSON", tmp_path / "tick_cycle.json")
    _write_tick_csv(tmp_path)

    out = RL.write_tick_cycle_json("2026-10-02")
    on_disk = json.loads((tmp_path / "tick_cycle.json").read_text())

    assert on_disk["history"] == out["history"]
    assert len(out["history"]) >= 252
    last = out["history"][-1]
    assert last["date"] == out["as_of"]
    for k in ("ma_high", "ma_close", "ma_low", "spread_rank252", "band"):
        assert last[k] == out[k], k


def test_mid_history_row_matches_hand_calculation(tmp_path, monkeypatch):
    monkeypatch.setattr(RL, "TVDIR", tmp_path)
    monkeypatch.setattr(RL, "TICK_CYCLE_JSON", tmp_path / "tick_cycle.json")
    _write_tick_csv(tmp_path)

    out = RL.write_tick_cycle_json("2026-10-02")
    t = pd.read_csv(tmp_path / RL.TICK_CSV_NAME, parse_dates=["date"]).set_index("date")
    spread = (t["high"].rolling(15).mean() - t["low"].rolling(15).mean()).dropna()
    i = len(spread) - 100                       # a row well inside the history
    window = spread.iloc[i - 251:i + 1]
    expected_rank = round(float((window <= window.iloc[-1]).mean()), 3)

    row = next(h for h in out["history"] if h["date"] == str(spread.index[i].date()))
    assert row["spread_rank252"] == expected_rank
    assert row["ma_high"] == round(float(t["high"].rolling(15).mean().loc[spread.index[i]]), 1)
    assert row["band"] == RL._tick_band(expected_rank)
