"""Replay ep_qullamaggie over every universe.json snapshot in git history.

The question (09-19 收工三问③): ep_qullamaggie printed 0 rows on its first night
(2026-09-18, the night the >=$1B cap floor landed). Is that the thresholds
failing to fire in the >=$1B population, or is that just a normal night?
One night has no information, so this walks the archive instead.

Three guards, each of which caught something real in this run:

1. SESSION LABEL = last_completed_session(ET) of the snapshot timestamp, not the
   commit date -- an 02:12 ET snapshot holds the PREVIOUS session
   (population_break._et_day, fixed 2026-09-19). 28 of 156 commits label
   differently from their commit date; two would have collided with a real
   snapshot of another session.

2. INPUT COVERAGE per session. passes() fails a row whose input is missing, so a
   field that was not written yet reads as "nothing fired"
   (pitfall_having_a_row_is_not_having_data). THIS ONE FIRED: gap_pct and
   avg_vol50_prev were both added to universe.json on 2026-09-18, the same night
   the screener was registered; coverage is 0.0 on all 129 earlier sessions, so
   the native replay has one session of data and its 130 zeros mean nothing.

3. PAYLOAD COMPLETENESS -- volratio = sum(volume)/sum(avg_volume) over the >=$1B
   rows. Guard 1 labels by the CLOCK; it cannot tell that a payload written
   04:17 ET Monday holds Monday's premarket rather than Friday's close. Five
   snapshots are premarket (volratio 0.0018-0.0029) and eight are the 07-15..24
   avg_volume outage (77-304). Both bounds sit in empty gaps: below 0.5 the
   nearest value is 0.0029, above 3 it is 77.0, and 143 of 156 snapshots sit
   inside. Found by the refutation verifier, 2026-09-20 -- before this guard,
   session 08-14 published rgap10_big=15 / rpass_big=0 off a premarket payload
   whose top "gap" was ALG +52.8% on 12 shares, while three other snapshots of
   the same session all read rpass_big=8.

Both legs of the screener are rebuilt from fields that DO have history:

    gap_pct = (1 + change_pct) / (1 + from_open_pct) - 1
              close/(1+from_open_pct) = open ; close/(1+change_pct) = prior close.
              Control on 2026-09-18 (the one session holding the native field and
              the inputs): median abs err 2.8e-5, and the >=10% classification
              agrees ticker-for-ticker, 23/23 whole universe, 0/0 inside >=$1B.
    ADV     = avg_volume (Finviz) standing in for avg_vol50_prev.
              Same control: 17 names vs the native 16, extra one SLND, no misses.
              Over the 5,258 rows carrying both, the >=1x verdict agrees 91.5%.
              So this leg is a PROXY, not a reconstruction.

Hence rgap10_big (gap leg, exact) is the UPPER BOUND on what the screener could
print in the >=$1B population, and rpass_big is the softer read beside it.

Exclusions live in the script, not in the prose: every session carries `ok` and
`why`, so re-summarising replay.csv without the filter is not silently possible.
"""
from __future__ import annotations

import csv
import datetime
import json
import subprocess
import sys
import zoneinfo
from pathlib import Path
from typing import Optional

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from pipeline.screeners import ep_qullamaggie as q  # noqa: E402
from pipeline.marketcal import last_completed_session  # noqa: E402

NY = zoneinfo.ZoneInfo("America/New_York")
PATH = "data/output/universe.json"
BIG = 1e9
MIN_COV = 0.85          # reconstruction inputs present on this share of rows
MIN_ROWS = 1000         # 2026-06-08 wrote a 200-row stub
VOL_LO, VOL_HI = 0.5, 3.0


def _f(r, k):
    v = r.get(k)
    if v is None or isinstance(v, bool):
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return None if f != f else f


def recon_gap(r):
    """gap = open/prior_close - 1, rebuilt from change_pct and from_open_pct."""
    c, o = _f(r, "change_pct"), _f(r, "from_open_pct")
    if c is None or o is None or (1 + o) == 0:
        return None
    return (1 + c) / (1 + o) - 1


def recon_passes(r):
    g, v, av = recon_gap(r), _f(r, "volume"), _f(r, "avg_volume")
    if g is None or v is None or av is None:
        return False
    return g >= q.MIN_GAP and v >= q.MIN_ADV_MULT * av


def _session(ts: Optional[str]):
    if not ts:
        return None, None
    try:
        dt = datetime.datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    except ValueError:
        return None, None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    dt = dt.astimezone(NY)
    return last_completed_session(dt).isoformat(), dt


def measure(rows):
    big = [r for r in rows if (_f(r, "market_cap") or 0) >= BIG]
    d = {"n": len(rows), "n_big": len(big)}
    vol = sum(_f(r, "volume") or 0 for r in big)
    avg = sum(_f(r, "avg_volume") or 0 for r in big)
    d["volratio"] = round(vol / avg, 4) if avg else None
    for tag, pop in (("all", rows), ("big", big)):
        if not pop:
            d.update({f"gap10_{tag}": 0, f"pass_{tag}": 0, f"cov_gap_{tag}": 0.0,
                      f"rgap10_{tag}": 0, f"rpass_{tag}": 0, f"cov_recon_{tag}": 0.0})
            continue
        d[f"gap10_{tag}"] = sum(1 for r in pop if (_f(r, "gap_pct") or -9) >= q.MIN_GAP)
        d[f"pass_{tag}"] = sum(1 for r in pop if q.passes(r))
        d[f"cov_gap_{tag}"] = round(sum(1 for r in pop if _f(r, "gap_pct") is not None) / len(pop), 4)
        d[f"rgap10_{tag}"] = sum(1 for r in pop if (recon_gap(r) or -9) >= q.MIN_GAP)
        d[f"rpass_{tag}"] = sum(1 for r in pop if recon_passes(r))
        d[f"cov_recon_{tag}"] = round(sum(1 for r in pop if recon_gap(r) is not None) / len(pop), 4)
    d["rhits_big"] = ",".join(sorted(r["ticker"] for r in big if recon_passes(r)))
    return d


def verdict(d):
    """Why this session is or is not usable. Checked in a fixed order."""
    if d["n"] < MIN_ROWS:
        return 0, f"stub snapshot ({d['n']} rows)"
    if d["volratio"] is None or not (VOL_LO <= d["volratio"] <= VOL_HI):
        return 0, f"payload not a completed session (volratio {d['volratio']})"
    if d["cov_recon_all"] < MIN_COV:
        return 0, f"reconstruction inputs missing (cov {d['cov_recon_all']})"
    return 1, ""


def main():
    shas = subprocess.run(["git", "-C", str(REPO), "log", "origin/main", "--format=%H", "--", PATH],
                          capture_output=True, text=True, check=True).stdout.split()
    by_session, skipped = {}, 0
    for sha in shas:
        r = subprocess.run(["git", "-C", str(REPO), "show", f"{sha}:{PATH}"],
                           capture_output=True, text=True)
        if r.returncode:
            skipped += 1
            continue
        try:
            payload = json.loads(r.stdout)
        except json.JSONDecodeError:
            skipped += 1
            continue
        if "rows" not in payload:
            skipped += 1
            continue
        day, dt = _session(payload.get("timestamp"))
        if not day:
            skipped += 1
            continue
        rec = {"session": day, "sha": sha[:8], "snap_et": dt.strftime("%Y-%m-%d %H:%M")}
        rec.update(measure(payload["rows"]))
        rec["ok"], rec["why"] = verdict(rec)
        by_session.setdefault(day, []).append(rec)

    rows_out = []
    for day, cands in by_session.items():
        # prefer a complete payload; among equals take the LATEST SNAPSHOT TIME
        # (not commit order -- 08-18 kept a premarket payload purely on ordering).
        usable = [c for c in cands if c["ok"]]
        pick = max(usable or cands, key=lambda c: c["snap_et"])
        pick["snapshots"] = len(cands)
        pick["rejected"] = len(cands) - len(usable)
        rows_out.append(pick)
    rows_out.sort(key=lambda r: r["session"])

    out = Path(__file__).with_name("replay.csv")
    with out.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows_out[0].keys()))
        w.writeheader()
        w.writerows(rows_out)
    good = [r for r in rows_out if r["ok"]]
    print(f"commits={len(shas)} unreadable={skipped} sessions={len(rows_out)} usable={len(good)} -> {out.name}")
    for r in rows_out:
        if not r["ok"]:
            print(f"  dropped {r['session']} ({r['sha']}, snap {r['snap_et']}): {r['why']}")


if __name__ == "__main__":
    main()
