"""One-command check of the first TML night (Moglen 2020, merged 2026-09-18).

Answers three things off the published outputs: did the nightly run under the
NEW definition yet (weinstein_stage present), how many TMLs today, and does the
panel agree with leaders_log. profit_margin / roe coverage is reported because a
low share is why the first ~8 nights under-report.
"""
import csv
import json
from pathlib import Path

import pytest

from pipeline.tools import audit_tml as A


def _write(tmp, universe_rows, panel, log_rows, ts="2026-09-18T23:10:00+00:00"):
    out = tmp / "data" / "output"; out.mkdir(parents=True)
    hist = tmp / "data" / "history"; hist.mkdir(parents=True)
    (out / "universe.json").write_text(json.dumps({"timestamp": ts, "rows": universe_rows}))
    (out / "watchlist.json").write_text(json.dumps(
        {"date": "2026-09-18", "zones": [{"panels": [dict(panel, key="true_market_leaders")]}]}))
    with (hist / "leaders_log.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["date", "ticker", "tml"])
        w.writeheader()
        for r in log_rows:
            w.writerow(r)
    return out, hist


def _rows(n, **over):
    base = {"weinstein_stage": 2, "profit_margin": 0.3, "roe": 0.2}
    base.update(over)
    return [dict(base, ticker=f"T{i}") for i in range(n)]


def test_new_definition_live_and_panel_matches_log(tmp_path):
    out, hist = _write(
        tmp_path,
        _rows(100),
        {"count": 2, "tickers": [{"ticker": "DELL"}, {"ticker": "HPE"}]},
        [{"date": "2026-09-18", "ticker": t, "tml": "True"} for t in ("DELL", "HPE")]
        + [{"date": "2026-09-18", "ticker": "X", "tml": "False"}],
    )
    r = A.audit(out, hist)
    assert r["live"] is True
    assert r["count"] == 2 and r["tickers"] == ["DELL", "HPE"]
    assert r["consistent"] is True
    assert r["exit"] == 0


def test_not_live_when_weinstein_stage_absent(tmp_path):
    out, hist = _write(
        tmp_path,
        [{"ticker": f"T{i}", "rs_1m": 90} for i in range(50)],   # old universe, no new fields
        {"count": 0, "tickers": []}, [],
    )
    r = A.audit(out, hist)
    assert r["live"] is False and r["exit"] == 2


def test_panel_log_mismatch_is_flagged(tmp_path):
    out, hist = _write(
        tmp_path, _rows(80),
        {"count": 1, "tickers": [{"ticker": "DELL"}]},
        [{"date": "2026-09-18", "ticker": "DELL", "tml": "True"},
         {"date": "2026-09-18", "ticker": "HPE", "tml": "True"}],   # log has 2, panel 1
    )
    r = A.audit(out, hist)
    assert r["consistent"] is False and r["exit"] == 1


def test_reports_fundamental_coverage(tmp_path):
    rows = _rows(10, profit_margin=None)                 # margins missing on all
    for r in rows[:4]:
        r["profit_margin"] = 0.3                          # 4/10 covered
    out, hist = _write(tmp_path, rows, {"count": 0, "tickers": []}, [])
    r = A.audit(out, hist)
    assert r["coverage"]["profit_margin"] == (4, 10)
    assert r["coverage"]["weinstein_stage"] == (10, 10)


def test_the_real_outputs_parse(tmp_path):
    """Smoke: the command runs on whatever is in data/output today without raising."""
    repo = Path(__file__).resolve().parents[2]
    if not (repo / "data/output/watchlist.json").exists():
        pytest.skip("no outputs in checkout")
    r = A.audit(repo / "data/output", repo / "data/history")
    assert "live" in r and "count" in r and r["exit"] in (0, 1, 2)
