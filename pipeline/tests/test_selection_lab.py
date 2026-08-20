"""Selection Lab: candidates from bars, masked deal, decision recording."""
import json

import numpy as np
import pandas as pd

from pipeline.tools import selection_lab as SL


def _hist(closes, vol=2e6):
    idx = pd.bdate_range("2025-09-01", periods=len(closes))
    c = pd.Series(closes, index=idx, dtype=float)
    return pd.DataFrame({"Open": c.shift(1).bfill(), "High": c * 1.01, "Low": c * 0.985,
                         "Close": c, "Volume": [vol] * len(c)})


def _fixture():
    n = 200
    spy = list(np.linspace(100, 120, n))
    # PULL: ran to a fresh high ~20 sessions ago, pulled back 8%, above 50sma
    pull = list(np.linspace(20, 30, n - 60)) + list(np.linspace(30, 46, 40)) + list(np.linspace(46, 42.3, 20))
    flat = [50.0] * n                          # no fresh high -> excluded
    thin = pull                                # same shape, tiny volume -> excluded
    return {"SPY": _hist(spy), "PULL": _hist(pull, vol=2e6), "FLAT": _hist(flat), "THIN": _hist(thin, vol=1e4)}


def test_candidates_pick_the_pullback_only():
    bars = _fixture()
    asof = bars["SPY"].index[-25]              # leave 20+ sessions of future for answers
    cands = SL.candidates(bars, asof, bars["SPY"]["Close"][bars["SPY"].index <= asof])
    names = {c["ticker"] for c in cands}
    assert "FLAT" not in names and "THIN" not in names


def test_deal_and_record_roundtrip(tmp_path, monkeypatch):
    bars = _fixture()
    import pickle
    bp = tmp_path / "bars.pkl"
    pickle.dump(bars, open(bp, "wb"))
    monkeypatch.setattr(SL, "DECISIONS", tmp_path / "lab" / "decisions.csv")
    p = SL.deal(asof_str=str(bars["SPY"].index[-30].date()), n_cards=5, seed=7,
                bars_path=bp, lab=tmp_path / "lab")
    assert p["round"] == "r001" and p["mode"] == "blind"
    saved = json.loads((tmp_path / "lab" / "rounds" / "r001.json").read_text())
    for t, a in saved["answers"].items():
        if a:
            assert set(a) == {"fwd5", "fwd10", "fwd20", "mae20", "mfe20"}
    if p["cards"]:
        t = p["cards"][0]["ticker"]
        n = SL.record("r001", {t: {"andy_verdict": "买", "andy_reason": "位置好",
                                   "tags": "位置好", "claude_pred": "买", "claude_reason": "x"}},
                      "2026-08-20", lab=tmp_path / "lab")
        assert n == 1
        import csv
        rows = list(csv.DictReader((tmp_path / "lab" / "decisions.csv").open()))
        assert rows[0]["ticker"] == t and rows[0]["andy_verdict"] == "买"
        assert rows[0]["fwd20"] != ""
