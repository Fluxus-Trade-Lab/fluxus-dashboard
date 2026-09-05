"""Screener presets, evaluated nightly on the data side.

The Screener page's presets (`frontend/public/data/screener-presets.json`)
are filtered in the browser, so until 2026-08-19 they left no record: the
scanner validation (data/research/scanner_validation_2026-08) could not test
Sugar Babies / Monthly Leader 97 / Vol Up Gainers / Stockbee 9M at all --
"no history". This module is a faithful port of
`frontend/src/lib/screenerFilter.js::applyFilters` so that every preset's
hits go into `data/history/ticker_events.csv` under the screener name
`preset:<slug>` (e.g. `preset:sugar_babies`), next to the seven screeners.

Pure functions; the same preset file the page reads is the single source of
truth for the recipes -- change the JSON, both sides move.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence

PRESETS_PATH = Path("frontend/public/data/screener-presets.json")
PREFIX = "preset:"

# filter key -> (row column, multiplier applied to the ROW before comparing).
# Mirrors screenerFilter.js: pct/decimal columns are compared in whole %,
# everything else raw.
_RANGES: Dict[str, tuple] = {
    "dailyPct": ("change_pct", 100.0),
    "weeklyPct": ("perf_1w", 100.0),
    "monthlyPct": ("perf_1m", 100.0),
    "fromOpenPct": ("from_open_pct", 100.0),
    "sma20Dist": ("sma20_dist", 100.0),
    "sma50Dist": ("sma50_dist", 100.0),
    "sma200Dist": ("sma200_dist", 100.0),
    "ema21Atr": ("ema21_atr_dist", 1.0),
    "sma50Atr": ("atr_from_sma50", 1.0),
    "ema21LowDist": ("ema21_low_dist", 100.0),
    "adrPct": ("adr_pct", 1.0),
    "vcs": ("vcs", 1.0),
    "dcrPct": ("dcr_pct", 100.0),
    "ppCount": ("pp_count_30d", 1.0),
    "hScore": ("h_score", 1.0),
    "fScore": ("f_score", 1.0),
    "iScore": ("i_score", 1.0),
    "rs21d": ("rs_21d", 1.0),
    "rs63d": ("rs_63d", 1.0),
    "rs126d": ("rs_126d", 1.0),
    "rsIbd": ("rs_rating", 1.0),   # renamed 2026-09-04; preset key kept for compatibility
    "perf1wPctile": ("perf_1w_pctile", 1.0),
    "perf3mPctile": ("perf_3m_pctile", 1.0),
    "high52wDist": ("high_52w_dist", 100.0),
    "boCount1m": ("bo_count_1m", 1.0),
    "boCount3m": ("bo_count_3m", 1.0),
    "boCount6m": ("bo_count_6m", 1.0),
    "boCount1y": ("bo_count_1y", 1.0),
    "relVolume": ("rel_volume", 1.0),
}

_FLAGS = {"trendBaseOnly": "trend_base", "pocketPivotOnly": "pocket_pivot",
          "momentum97Only": "momentum_97"}


def slug(name: str) -> str:
    """'Weekly 20%+ Gainers' -> 'preset:weekly_20_gainers' (stable, ascii)."""
    s = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return PREFIX + s


def load_presets(path: Path = PRESETS_PATH) -> List[Dict[str, Any]]:
    data = json.loads(Path(path).read_text())
    return [p for p in data if isinstance(p, dict) and p.get("name") and isinstance(p.get("filters"), dict)]


def _num(v):
    if v is None or v == "" or isinstance(v, bool):
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return None if f != f else f


def _flag(v) -> bool:
    """True for True / numpy.bool_(True) / 1; False for None, NaN, strings, 0."""
    if v is None or isinstance(v, str):
        return False
    try:
        return bool(v == True)  # noqa: E712 -- numpy bools compare, NaN does not
    except Exception:  # noqa: BLE001
        return False


def _in_range(val, f: Mapping[str, Any]) -> bool:
    lo, hi = _num(f.get("min")), _num(f.get("max"))
    if lo is not None and val < lo:
        return False
    if hi is not None and val > hi:
        return False
    return True


def passes(row: Mapping[str, Any], filters: Mapping[str, Any]) -> bool:
    """One row against one preset's filter dict. Same semantics as the page:
    a range filter with a null column value fails; disabled filters are skipped."""
    if filters.get("marketCapEnabled", True) is not False and _num(filters.get("marketCapMin")):
        cap = _num(row.get("market_cap"))
        if cap is None or cap < float(filters["marketCapMin"]) * 1e9:
            return False
    if filters.get("vol50dEnabled", True) is not False and _num(filters.get("vol50dMin")):
        av = _num(row.get("avg_volume"))
        if av is None or av < float(filters["vol50dMin"]) * 1e6:
            return False
    if filters.get("excludeHealthcare") and row.get("sector") == "Healthcare":
        return False
    for fk, col in _FLAGS.items():
        if filters.get(fk) and not _flag(row.get(col)):
            return False
    for fk, (col, mult) in _RANGES.items():
        f = filters.get(fk)
        if not (isinstance(f, Mapping) and f.get("enabled")):
            continue
        val = _num(row.get(col))
        if val is None or not _in_range(val * mult, f):
            return False
    return True


def apply_preset(rows: Iterable[Mapping[str, Any]], filters: Mapping[str, Any]) -> List[Mapping[str, Any]]:
    return [r for r in rows if r.get("ticker") and passes(r, filters)]


def extract_preset_events(rows: Sequence[Mapping[str, Any]], presets: Sequence[Mapping[str, Any]],
                          date_iso: str) -> List[Dict[str, Any]]:
    """Event rows (ticker_events.EVENT_COLUMNS shape) for every preset hit."""
    from pipeline.screeners.ticker_events import _row
    out: List[Dict[str, Any]] = []
    for p in presets:
        name = slug(p["name"])
        for r in apply_preset(rows, p["filters"]):
            ev = _row(dict(r), name, "", date_iso)
            if ev:
                out.append(ev)
    return out
