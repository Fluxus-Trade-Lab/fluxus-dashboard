"""Pull Andy's shortlist feedback from the GAS Sheet -- the loop's data half.

Frontend POSTs shortlist_upsert rows (one per ✗/★/note, idempotent on
(ticker, added_date)); GAS stores them in the `Shortlist` tab. This module
pulls them nightly (action=shortlist_pull), archives to
data/history/shortlist_feedback.csv, refreshes the manual list (status
'starred'/'noted' = active manual names, capped 20), and upgrades matching
rows in shortlist_seat_log.csv from 'shown' to the fed-back outcome.

Chat-recorded feedback (Selection Lab / direct vetoes) stays authoritative
in decisions.csv; this file is the BUTTON channel only. ✗ semantics are
pinned by the frontend as「不是这个，今天」-- analysis must not read more
into it (contracts §七 [08-20]).

Env: FLUXUS_GAS_URL + FLUXUS_SYNC_TOKEN (same pair trade_postmortem uses);
absent -> quiet no-op, the loop simply has no button half that night."""

from __future__ import annotations

import csv
import json
import logging
import os
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

FEEDBACK = Path("data/history/shortlist_feedback.csv")
SEAT_LOG = Path("data/history/shortlist_seat_log.csv")
MANUAL = Path("data/reference/shortlist_manual.json")
FIELDS = ["pulled_at", "ticker", "added_date", "status", "note", "seat", "readings_json"]


def fetch_rows(url: Optional[str] = None, token: Optional[str] = None,
               timeout: int = 30) -> Optional[List[Dict[str, Any]]]:
    url = url or os.environ.get("FLUXUS_GAS_URL")
    token = token or os.environ.get("FLUXUS_SYNC_TOKEN")
    if not url or not token:
        return None
    q = urllib.parse.urlencode({"action": "shortlist_pull", "token": token})
    with urllib.request.urlopen(f"{url}?{q}", timeout=timeout) as resp:
        payload = json.loads(resp.read().decode())
    if not payload.get("ok"):
        raise RuntimeError(f"shortlist_pull refused: {payload}")
    return payload.get("rows") or []


def apply(rows: List[Dict[str, Any]], pulled_at: str,
          feedback_path: Path = FEEDBACK, seat_log_path: Path = SEAT_LOG,
          manual_path: Path = MANUAL) -> Dict[str, int]:
    """Archive the sheet state (full snapshot, idempotent by (ticker,added_date)),
    refresh the manual list, upgrade seat-log outcomes."""
    seen = {}
    for r in rows:
        key = (str(r.get("ticker", "")).upper(), str(r.get("added_date", "")))
        if key[0]:
            seen[key] = r
    feedback_path.parent.mkdir(parents=True, exist_ok=True)
    with feedback_path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        for (t, d), r in sorted(seen.items()):
            w.writerow({"pulled_at": pulled_at, "ticker": t, "added_date": d,
                        "status": r.get("status", ""), "note": r.get("note", ""),
                        "seat": r.get("seat", ""),
                        "readings_json": json.dumps(r.get("readings") or {}, ensure_ascii=False)})
    manual = [t for (t, _), r in sorted(seen.items())
              if r.get("status") in ("starred", "noted")][:20]
    try:
        cur = json.loads(manual_path.read_text())
    except Exception:  # noqa: BLE001
        cur = {}
    cur["tickers"] = manual
    cur["source"] = "gas_shortlist_pull"
    manual_path.write_text(json.dumps(cur, ensure_ascii=False, indent=1))
    upgraded = 0
    if seat_log_path.exists():
        with seat_log_path.open(newline="") as fh:
            log_rows = list(csv.DictReader(fh))
        fields = log_rows[0].keys() if log_rows else None
        by_td = {(t, d): r.get("status") for (t, d), r in seen.items()}
        for lr in log_rows:
            st = by_td.get((lr.get("ticker", ""), lr.get("date", "")))
            if st in ("vetoed", "starred") and lr.get("outcome") == "shown":
                lr["outcome"] = st
                upgraded += 1
        if fields and upgraded:
            with seat_log_path.open("w", newline="") as fh:
                w = csv.DictWriter(fh, fieldnames=list(fields))
                w.writeheader()
                w.writerows(log_rows)
    return {"rows": len(seen), "manual": len(manual), "upgraded": upgraded}
