"""Rebuild the run_all smoke fixture from a committed universe.json.

The smoke test needs a universe that looks like what the ADAPTERS hand the
orchestrator -- i.e. before compute_universe_scores runs -- otherwise the test
would assert on numbers it never recomputed. So this drops every column
compute_universe_scores assigns and keeps the raw/enriched ones.

Deterministic slice (every STRIDE-th ticker, sorted) so the fixture is stable
across rebuilds and a diff is readable.

    python3 -m pipeline.tools.make_smoke_fixture [path/to/universe.json]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "pipeline" / "tests" / "fixtures" / "smoke_universe.json"
STRIDE = 37

# Assigned by compute_universe_scores -- must NOT be pre-baked into the fixture.
COMPUTED = {
    "adr_pct", "atr_from_sma50", "c_low52w", "ema21_atr_dist", "ema21_r",
    "f_score", "h_score", "high_52w_dist", "i_score", "liquid_leader",
    "momentum_97", "perf_1w_pctile", "perf_3m_pctile", "rs_126d", "rs_1m",
    "rs_21d", "rs_3m", "rs_63d", "rs_6m", "rs_ibd", "sma50_r", "tradeable",
}
# NOT computed here: `vcs` is adapter-supplied and run_all only coerces its
# dtype (line ~434). Stripping it made the smoke's quality gate go severe on a
# 100%-missing column -- the fixture, not the pipeline, was the bug.


def build(src: Path) -> dict:
    payload = json.loads(src.read_text())
    rows = sorted(payload["rows"], key=lambda r: str(r.get("ticker")))
    sliced = rows[::STRIDE]
    trimmed = [{k: v for k, v in r.items() if k not in COMPUTED} for r in sliced]
    bar_dates = sorted({r.get("bar_date") for r in trimmed if r.get("bar_date")})
    return {
        "source_bar_dates": [bar_dates[0], bar_dates[-1]] if bar_dates else None,
        "stride": STRIDE,
        "note": "pre-scoring slice; compute_universe_scores must fill the rest",
        "rows": trimmed,
    }


def main() -> None:
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "output" / "universe.json"
    fixture = build(src)
    OUT.write_text(json.dumps(fixture, separators=(",", ":")))
    print(f"{OUT}: {len(fixture['rows'])} rows, bars {fixture['source_bar_dates']}")


if __name__ == "__main__":
    main()
