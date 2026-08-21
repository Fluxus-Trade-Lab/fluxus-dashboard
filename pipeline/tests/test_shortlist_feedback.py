import csv
import json

from pipeline.screeners import shortlist_feedback as F


def test_apply_archives_manual_and_upgrades_seat_log(tmp_path):
    fb = tmp_path / "fb.csv"; sl = tmp_path / "seat.csv"; man = tmp_path / "m.json"
    with sl.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["date", "seat", "ticker", "outcome"])
        w.writeheader()
        w.writerow({"date": "2026-08-20", "seat": "burning", "ticker": "APPS", "outcome": "shown"})
        w.writerow({"date": "2026-08-20", "seat": "asset", "ticker": "GLD", "outcome": "shown"})
    rows = [{"ticker": "APPS", "added_date": "2026-08-20", "status": "vetoed", "note": "太extended", "seat": "burning"},
            {"ticker": "NVDA", "added_date": "2026-08-21", "status": "starred", "note": "", "seat": ""},
            {"ticker": "APPS", "added_date": "2026-08-20", "status": "vetoed", "note": "dup", "seat": "burning"}]
    stats = F.apply(rows, "2026-08-21", feedback_path=fb, seat_log_path=sl, manual_path=man)
    assert stats == {"rows": 2, "manual": 1, "upgraded": 1}        # dedup by (ticker,added_date)
    assert json.loads(man.read_text())["tickers"] == ["NVDA"]
    got = {r["ticker"]: r["outcome"] for r in csv.DictReader(sl.open())}
    assert got["APPS"] == "vetoed" and got["GLD"] == "shown"


def test_fetch_rows_noop_without_env(monkeypatch):
    monkeypatch.delenv("FLUXUS_GAS_URL", raising=False)
    assert F.fetch_rows() is None
