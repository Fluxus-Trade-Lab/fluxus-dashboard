"""Build `data/output/rotation.json` from the stored basket closes.

Reads `data/output/baskets/<T>.json` (daily closes, written by
`fetch_baskets.py`), aligns every series on the benchmark's session index, and
emits the line, the ribbon and the verdict.

Alignment matters more than it looks: two ETFs can differ by a holiday or a
listing gap, and an unaligned index would silently offset one basket's
fortnight against another's. Everything is reindexed onto SPY's dates, and a
basket that cannot be aligned is dropped loudly rather than drawn wrong.
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from pipeline.rotation import baskets as B
from pipeline.rotation import engine as E

log = logging.getLogger(__name__)

BASKET_DIR = Path("data/output/baskets")
OUT = Path("data/output/rotation.json")

# Ten weeks of line plus three months of lookback for the oldest state.
MIN_SESSIONS = E.STEP * (E.STEPS - 1) + E.LEVEL + E.NEAR + 1


def load_series(ticker: str, directory: Path = BASKET_DIR) -> Optional[Dict[str, float]]:
    """Date -> close, or None if the file is missing or unreadable."""
    path = directory / f"{ticker}.json"
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text())
    except (ValueError, OSError):
        return None
    bars = payload.get("bars") or []
    out = {b["date"]: float(b["close"]) for b in bars
           if b.get("date") and b.get("close") is not None}
    return out or None


def align(series: Dict[str, Dict[str, float]], benchmark: str
          ) -> tuple[List[str], Dict[str, List[float]]]:
    """Reindex every basket onto the benchmark's dates.

    A basket missing any benchmark session is dropped -- forward-filling a gap
    would invent a flat day inside a fortnight and shrink that bucket's excess
    toward zero, which reads as "nothing happened" rather than "we don't know".
    """
    dates = sorted(series[benchmark])
    out: Dict[str, List[float]] = {}
    for ticker, byday in series.items():
        missing = [d for d in dates if d not in byday]
        if missing:
            log.warning("%s missing %d of %d benchmark sessions (from %s) — dropped",
                        ticker, len(missing), len(dates), missing[0])
            continue
        out[ticker] = [byday[d] for d in dates]
    return dates, out


def build(directory: Path = BASKET_DIR) -> Dict[str, Any]:
    raw = {t: s for t in B.REQUIRED if (s := load_series(t, directory))}
    if B.BENCHMARK not in raw:
        raise SystemExit(f"benchmark {B.BENCHMARK} has no stored closes — "
                         f"run pipeline.rotation.fetch_baskets first")

    dates, closes = align(raw, B.BENCHMARK)
    if len(dates) < MIN_SESSIONS:
        raise SystemExit(f"{len(dates)} sessions stored, {MIN_SESSIONS} needed "
                         f"for ten weeks of ribbon")

    bench = closes[B.BENCHMARK]
    anchor_dates = [dates[i] for i in E.anchors(len(dates))]

    rows: List[Dict[str, Any]] = []
    for ticker, meta in B.BASKETS.items():
        if ticker not in closes:
            log.warning("basket %s unavailable — omitted from rotation.json", ticker)
            continue
        series = closes[ticker]
        rows.append({
            "ticker": ticker,
            "name": meta["name"],
            "side": meta["side"],
            "line": E.line_series(series, bench),
            "ribbon": E.ribbon(series, bench),
            **E.state_at(series, bench, len(series) - 1),
        })
    rows.sort(key=lambda r: (r["level"] is None, -(r["level"] or 0)))

    readings = [E.cut_reading(closes, bench, c) for c in B.CUTS]
    call = E.verdict(readings)

    missing = [t for t in B.REQUIRED if t not in closes]
    return {
        "date": dates[-1],
        "benchmark": B.BENCHMARK,
        "step_sessions": E.STEP,
        "bucket_dates": anchor_dates,
        "bucket_labels": [f"{2 * (E.STEPS - k)}–{2 * (E.STEPS - k - 1)}w ago"
                          if k < E.STEPS - 1 else "Last 2w" for k in range(E.STEPS)],
        "baskets": rows,
        "cuts": readings,
        "verdict": call,
        # The window the states are computed on, printed so the chart can say
        # so. A ribbon drawn on a two-week grid invites the reader to assume
        # the state is a two-week reading; it is not.
        "state_windows": {"level_sessions": E.LEVEL, "near_sessions": E.NEAR},
        "coverage": {"baskets": len(rows), "of": len(B.BASKETS),
                     "missing": missing},
    }


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args()

    payload = build()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2))
    v = payload["verdict"]
    log.info("%s — %s", payload["date"], v["sentence"])
    log.info("wrote %s (%d baskets)", args.out, payload["coverage"]["baskets"])


if __name__ == "__main__":
    main()
