"""Stockbee anticipation x VCS -- print today's candidate list from universe.json.

Stockbee's anticipation idea: circle the names BEFORE the breakout day. His
three Telechart scans share one skeleton -- a "has been strong" ratio plus a
"quiet today" gate -- and then he narrows by eye (3-10 days of narrow range,
no 4% down day in the pullback, dry volume). Our VCS v2 is that eye, made
mechanical. So the combination is:

    strong (any of TI65 > 1.05 | c/minl252 >= 1.8 | c/avgc126 > 1.19)
    AND quiet today (|change_pct| <= 1%)
    AND liquid (min 3-day volume > 100k; we also default to $1B market cap)
    AND compressed (vcs >= --vcs, default 60)
    AND alive (adr_pct >= --adr-min, default 3): without this the top of the
        list is takeover targets pinned to their deal price -- ADR under 2%,
        10-25 ATRs above the 50-day, VCS 90-100 because nothing moves. Pinned
        is not compressed. Found on the first run, 2026-08-14 data.

Ratios: universe columns ti65 / c_low52w / mdt (the first two need one more
enrichment run after 2026-08-17 to be populated; c_low52w is available now).

Run:  python -m pipeline.tools.anticipation_scan [--vcs 60] [--cap 1e9] [--all]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

UNIVERSE = Path("data/output/universe.json")


def strong(r: dict) -> list[str]:
    tags = []
    if (r.get("ti65") or 0) > 1.05:
        tags.append("TI65")
    if (r.get("c_low52w") or 0) >= 1.8:
        tags.append("DT")
    if (r.get("mdt") or 0) > 1.19:
        tags.append("MDT")
    return tags


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--vcs", type=float, default=60.0)
    ap.add_argument("--cap", type=float, default=1e9)
    ap.add_argument("--quiet", type=float, default=0.01, help="|change_pct| gate (fraction)")
    ap.add_argument("--all", action="store_true", help="skip the VCS gate")
    ap.add_argument("--adr-min", type=float, default=3.0, help="ADR%% floor; pinned takeover names sit under 2")
    a = ap.parse_args()
    rows = json.loads(UNIVERSE.read_text())["rows"]

    have = {k: sum(1 for r in rows if r.get(k) is not None) for k in ("ti65", "mdt", "c_low52w", "vcs")}
    print("field coverage:", have)

    out = []
    for r in rows:
        if (r.get("market_cap") or 0) < a.cap:
            continue
        if r.get("change_pct") is None or abs(r["change_pct"]) > a.quiet:
            continue
        mv3 = r.get("min_vol_3d")
        if (mv3 if mv3 is not None else (r.get("avg_volume") or 0)) <= 100_000:
            continue
        if (r.get("adr_pct") or 0) < a.adr_min:
            continue
        tags = strong(r)
        if not tags:
            continue
        if not a.all and (r.get("vcs") is None or r["vcs"] < a.vcs):
            continue
        out.append((r["ticker"], r.get("vcs"), tags, r.get("rs_21d"), r.get("atr_from_sma50"), r.get("adr_pct")))

    out.sort(key=lambda x: -(x[1] or 0))
    print(f"\n{len(out)} names  (cap >= ${a.cap/1e9:.0f}B, |chg| <= {a.quiet*100:.0f}%, "
          f"{'no VCS gate' if a.all else f'vcs >= {a.vcs:.0f}'}, adr >= {a.adr_min:.0f}%)\n")
    print(f"{'ticker':<7}{'vcs':>6}  {'strong':<14}{'rs21':>5}{'atrx50':>8}{'adr%':>6}")
    for t, v, tags, rs, ax, adr in out:
        print(f"{t:<7}{(v if v is not None else float('nan')):>6.1f}  {'+'.join(tags):<14}"
              f"{(rs if rs is not None else float('nan')):>5.0f}{(ax if ax is not None else float('nan')):>8.2f}"
              f"{(adr if adr is not None else float('nan')):>6.1f}")


if __name__ == "__main__":
    main()
