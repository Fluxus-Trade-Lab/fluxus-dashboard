"""Archive invariants -- the nightly gate and the weekly sweep.

Every append-only archive under data/history is keyed by US trading session.
The guards that exist (quality.py null-rate baselines, breadth_store
check_quality, ticker_events.is_plausible_day, bar_consistency) each watch
ONE writer at write time; nothing re-reads the archives as a set. 2026-08-19
showed the gap: a premarket dispatch filed a breadth row under a session that
had not traded and rewrote the previous session's watchlist rows, and the
only thing that caught it was a human asking "what is today's reading".

This tool checks the invariants that hold for every archive, reports, and
(with --repair) removes rows that can never be right:

  I1  date is a real trading session (marketcal), never in the future
      (> last completed session)
  I2  no duplicate primary keys (date[, ticker, ...])
  I3  breadth: spx_close never identical to the previous session's row
  I4  per-session row counts inside [floor, 3x] of the trailing-20 median
      for the event archives (a 1/4-size day is a half scrape, a 5x day is a
      broken enrichment) -- reported, never repaired automatically
  I5  the newest session in each nightly archive is the last completed
      session (stale archive = a writer silently stopped)
  I7  a series (screener / panel / kind) the registry calls "reliable" --
      present on >=95% of sessions with a median of >=20 rows -- wrote zero
      rows for the newest session. This is the invariant a whole-file row
      count cannot express: on 2026-08-07/11/12/13 gainers_4pct and
      vol_up_gainers each wrote nothing while the file's total stayed at
      0.68-1.17x its median. Bands live in data/reference/i4_bands.json,
      built by pipeline/tools/calibrate_i4.py, committed and only moved by
      an explicit --update.

  I6  reconciliation: watchlist.json counts == watchlist_hits rows; the seven
      screener JSONs' rows == ticker_events rows for that date; breadth
      universe_size ~ universe.json rows (mismatch = two writers disagree)

Exit code 1 when any I1/I2/I3/I7 violation exists (CI refuses to commit the run
on that), 0 otherwise; I4/I5 are warnings in the report. --repair rewrites
the file without I1/I2/I3 rows after writing a .bak next to it.

    python -m pipeline.tools.audit_archives            # report
    python -m pipeline.tools.audit_archives --repair   # also fix I1-I3
    python -m pipeline.tools.audit_archives --json out.json
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from pipeline.marketcal import is_trading_day, last_completed_session

HISTORY = Path("data/history")

# archive -> (date column, primary key columns, counts-checked, nightly)
# archive -> date column, primary key, counts-checked, nightly, series column
# "series" is the sub-feed whose disappearance a whole-file row count cannot
# see (see I7 and pipeline/tools/calibrate_i4.py).
ARCHIVES: Dict[str, Dict[str, Any]] = {
    "breadth_archive.csv":   {"date": "date",  "key": ["date"],                       "counts": False, "nightly": True,  "series": None},
    "ticker_events.csv":     {"date": "date",  "key": ["date", "ticker", "screener"], "counts": True,  "nightly": True,  "series": "screener"},
    "watchlist_hits.csv":    {"date": "date",  "key": ["date", "panel", "ticker"],    "counts": True,  "nightly": True,  "series": "panel"},
    "leaders_log.csv":       {"date": "date",  "key": ["date", "ticker"],             "counts": True,  "nightly": True,  "series": None},
    "groups_archive.csv":    {"date": "date",  "key": ["date", "kind", "group"],      "counts": True,  "nightly": True,  "series": "kind"},
    "momentum97_shadow.csv": {"date": "date",  "key": ["date", "recipe", "ticker"],   "counts": False, "nightly": True,  "series": "recipe"},
    "universe_quality.csv":  {"date": "date",  "key": ["date"],                       "counts": False, "nightly": True,  "series": None},
    "delayed_ep_log.csv":    {"date": "as_of", "key": ["as_of", "ticker"],            "counts": False, "nightly": False, "series": None},
}
# Fallback band, used only where the registry has no measured one. The
# measured total band for ticker_events is [0.58, 2.45]; these numbers were
# guessed in 2026-08-19 and have never fired on 96 sessions.
COUNT_FLOOR = 0.30
COUNT_CEIL = 3.0
BANDS_PATH = Path("data/reference/i4_bands.json")


def load_bands(path: Path = BANDS_PATH) -> Dict[str, Any]:
    """The committed I4/I7 registry, or an empty one. Never raises."""
    try:
        return json.loads(path.read_text())
    except Exception:  # noqa: BLE001
        return {"archives": {}}


def _sessions(dates: pd.Series, last_done: dt.date) -> pd.DataFrame:
    """Per unique date: is_session, is_future."""
    out = []
    for d in sorted(set(dates.dropna().astype(str))):
        try:
            day = dt.date.fromisoformat(d[:10])
        except ValueError:
            out.append({"date": d, "session": False, "future": False, "unparsable": True}); continue
        out.append({"date": d, "session": is_trading_day(day), "future": day > last_done, "unparsable": False})
    return pd.DataFrame(out)


def audit_one(name: str, spec: Dict[str, Any], frame: pd.DataFrame, last_done: dt.date,
              bands: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    dcol = spec["date"]
    rep: Dict[str, Any] = {"archive": name, "rows": int(len(frame)), "violations": [], "warnings": [], "drop_dates": [], "drop_dupes": 0}
    if dcol not in frame.columns:
        rep["violations"].append(f"no '{dcol}' column"); return rep
    info = _sessions(frame[dcol], last_done)
    bad = info[(~info.session) | info.future | info.unparsable]
    for _, r in bad.iterrows():
        why = "unparsable" if r.unparsable else ("future" if r.future else "not a trading session")
        rep["violations"].append(f"I1 {r.date}: {why}")
        rep["drop_dates"].append(r.date)
    # I2 duplicates
    key = [k for k in spec["key"] if k in frame.columns]
    if key:
        dup = frame.duplicated(subset=key, keep="last")
        if dup.any():
            rep["violations"].append(f"I2 {int(dup.sum())} duplicate rows on {key}")
            rep["drop_dupes"] = int(dup.sum())
    # I3 breadth identical close
    if name == "breadth_archive.csv" and "spx_close" in frame.columns:
        f = frame.sort_values(dcol)
        spx = pd.to_numeric(f["spx_close"], errors="coerce")
        same = spx.eq(spx.shift(1)) & spx.notna()
        for d in f.loc[same, dcol].astype(str):
            rep["violations"].append(f"I3 {d}: spx_close identical to previous session's row")
            if d not in rep["drop_dates"]:
                rep["drop_dates"].append(d)
    # I4 per-session counts, against the measured band when we have one
    band_entry = (bands or {}).get("archives", {}).get(name, {})
    if spec["counts"] and len(frame):
        per = frame.groupby(frame[dcol].astype(str)).size().sort_index()
        if len(per) >= 6:
            med = per.iloc[-21:-1].median() if len(per) > 21 else per.iloc[:-1].median()
            last_d, last_n = per.index[-1], int(per.iloc[-1])
            tb = band_entry.get("total") or {}
            lo = float(tb.get("floor", COUNT_FLOOR))
            hi = float(tb.get("ceil", COUNT_CEIL))
            src = "measured" if tb else "default"
            if med and (last_n < lo * med or last_n > hi * med):
                rep["warnings"].append(
                    f"I4 {last_d}: {last_n} rows vs trailing median {med:.0f} "
                    f"(outside [{lo:g}, {hi:g}] {src})")
    # I7 a series that has always been there wrote nothing
    scol = spec.get("series")
    series_reg = band_entry.get("series") or {}
    if scol and scol in frame.columns and series_reg and len(frame):
        newest = frame[dcol].astype(str).max()
        day = frame[frame[dcol].astype(str) == newest]
        present = day.groupby(day[scol].astype(str)).size().to_dict()
        for series, meta in sorted(series_reg.items()):
            n = int(present.get(series, 0))
            if meta.get("kind") == "reliable" and n == 0:
                rep["violations"].append(
                    f"I7 {newest} {series}: 0 rows, but present on "
                    f"{meta.get('presence', 0):.0%} of sessions "
                    f"(median {meta.get('median_rows')} rows)")
            elif n and meta.get("band"):
                med = meta.get("median_rows") or 0
                if med:
                    ratio = n / med
                    b = meta["band"]
                    if ratio < b["floor"] or ratio > b["ceil"]:
                        rep["warnings"].append(
                            f"I4s {newest} {series}: {n} rows = {ratio:.2f}x its "
                            f"median {med:g} (band [{b['floor']}, {b['ceil']}])")
    # I5 freshness
    if spec["nightly"] and len(info):
        newest = info.date.max()
        if newest < last_done.isoformat():
            rep["warnings"].append(f"I5 newest session {newest} < last completed {last_done}")
    return rep


def repair(path: Path, spec: Dict[str, Any], frame: pd.DataFrame, rep: Dict[str, Any]) -> int:
    dcol = spec["date"]
    before = len(frame)
    if rep["drop_dates"]:
        frame = frame[~frame[dcol].astype(str).isin(set(rep["drop_dates"]))]
    key = [k for k in spec["key"] if k in frame.columns]
    if key and rep["drop_dupes"]:
        frame = frame.drop_duplicates(subset=key, keep="last")
    removed = before - len(frame)
    if removed:
        shutil.copy2(path, path.with_suffix(path.suffix + ".bak"))
        frame.to_csv(path, index=False)
    return removed


def reconcile(history: Path = HISTORY, output: Path = Path("data/output")) -> Dict[str, Any]:
    """I6 -- cross-file agreement for the newest session. Two writers that
    describe the same thing must agree; a mismatch is a writer bug, not data.
      a) watchlist.json panel counts == watchlist_hits.csv rows per panel (same date)
      b) ticker_events.csv core screener counts (newest date) == the screener JSONs' row counts
      c) breadth_archive.csv newest universe_size == universe.json row count
    Reported as violations only when the dates line up (a stale file is I5's job)."""
    rep: Dict[str, Any] = {"archive": "reconcile(I6)", "rows": 0, "violations": [], "warnings": [], "drop_dates": [], "drop_dupes": 0}
    try:
        wl = json.loads((output / "watchlist.json").read_text())
        hits = pd.read_csv(history / "watchlist_hits.csv", dtype=str)
        h = hits[hits["date"] == wl["date"]]
        if len(h):
            per = h.groupby("panel").size().to_dict()
            for z in wl["zones"]:
                for p in z["panels"]:
                    if p.get("measured") and per.get(p["key"], 0) != p["count"]:
                        rep["violations"].append(f"I6a {wl['date']} {p['key']}: watchlist.json count {p['count']} vs watchlist_hits {per.get(p['key'], 0)}")
        else:
            rep["warnings"].append(f"I6a no watchlist_hits rows for watchlist.json date {wl['date']}")
    except Exception as e:  # noqa: BLE001
        rep["warnings"].append(f"I6a skipped: {type(e).__name__}")
    try:
        from pipeline.screeners.ticker_events import SCREENER_FILES, extract_events
        te = pd.read_csv(history / "ticker_events.csv", dtype=str)
        newest = te["date"].max()
        day = te[te["date"] == newest]
        for scr in SCREENER_FILES:
            p = output / f"{scr}.json"
            if not p.exists():
                continue
            payload = json.loads(p.read_text())
            n_json = len(extract_events(scr, payload, newest))
            n_csv = int((day["screener"] == scr).sum())
            if n_json != n_csv:
                rep["violations"].append(f"I6b {newest} {scr}: {scr}.json {n_json} rows vs ticker_events {n_csv}")
    except Exception as e:  # noqa: BLE001
        rep["warnings"].append(f"I6b skipped: {type(e).__name__}")
    try:
        ba = pd.read_csv(history / "breadth_archive.csv", dtype=str)
        u = json.loads((output / "universe.json").read_text())
        last = ba.sort_values("date").iloc[-1]
        if int(float(last["universe_size"])) != len(u["rows"]):
            rep["warnings"].append(f"I6c breadth universe_size {last['universe_size']} ({last['date']}) vs universe.json rows {len(u['rows'])}")
    except Exception as e:  # noqa: BLE001
        rep["warnings"].append(f"I6c skipped: {type(e).__name__}")
    return rep


def run(history: Path = HISTORY, do_repair: bool = False, last_done: Optional[dt.date] = None,
        output: Optional[Path] = Path("data/output"),
        bands: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    last_done = last_done or last_completed_session()
    bands = bands if bands is not None else load_bands()
    reports: List[Dict[str, Any]] = []
    for name, spec in ARCHIVES.items():
        p = history / name
        if not p.exists():
            reports.append({"archive": name, "rows": 0, "violations": [], "warnings": ["missing (not yet created)"], "drop_dates": [], "drop_dupes": 0})
            continue
        try:
            frame = pd.read_csv(p, dtype=str, keep_default_na=False)
        except Exception as e:  # noqa: BLE001
            reports.append({"archive": name, "rows": 0, "violations": [f"unreadable: {e}"], "warnings": [], "drop_dates": [], "drop_dupes": 0})
            continue
        frame = frame.replace({"": None})
        rep = audit_one(name, spec, frame, last_done, bands)
        if do_repair and (rep["drop_dates"] or rep["drop_dupes"]):
            rep["repaired_rows"] = repair(p, spec, frame, rep)
        reports.append(rep)
    if output is not None and output.exists():
        reports.append(reconcile(history, output))
    n_viol = sum(len(r["violations"]) for r in reports)
    return {"as_of_session": last_done.isoformat(), "ok": n_viol == 0, "violations": n_viol,
            "warnings": sum(len(r["warnings"]) for r in reports), "archives": reports}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repair", action="store_true")
    ap.add_argument("--json", help="write the report here")
    ap.add_argument("--history", default=str(HISTORY))
    args = ap.parse_args(argv)
    out = run(Path(args.history), args.repair)
    for r in out["archives"]:
        flag = "OK " if not r["violations"] else "BAD"
        print(f"{flag} {r['archive']:24s} rows {r['rows']:>6d}  " + "; ".join(r["violations"] + r["warnings"]) + (f"  [repaired {r['repaired_rows']} rows]" if r.get("repaired_rows") else ""))
    print(f"\n{'OK' if out['ok'] else 'VIOLATIONS'}: {out['violations']} violations, {out['warnings']} warnings (session {out['as_of_session']})")
    if args.json:
        Path(args.json).write_text(json.dumps(out, indent=1))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
