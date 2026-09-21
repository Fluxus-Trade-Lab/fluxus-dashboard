"""Episodic-Pivot hits, grouped by earnings season and by industry cohort --
course "Rotation" outline point 5 (T-0921-85).

Andy 2026-09-21: 「财报名单按族群计数这个先手工截图写，然后挂给ALEX」-- outline point 5
("Rotation") wants, each earnings season, the industries where post-earnings
gap-and-drive names cluster, and how that composition changed season over
season (TraderLion 2026-08-25 Shake Pryzby interview: 「名单的族群构成换了，就是
钱换了地方」).

What "EP hit" means here (a union, not a new definition):
    ep_stockbee + ep_qullamaggie (author-verbatim since 2026-09-18) UNION the
    retired ``episodic_pivot`` screener (rows <= 2026-09-17). This is the same
    union ``delayed_ep_scan.EP_SCREENERS`` already uses so ITS OWN lookback
    window doesn't go blind across the 09-18 screener switch. The new
    author-verbatim screeners alone only have ~1 trading day of archive at
    the time this tool was written -- nowhere near two earnings seasons --
    so the retired definition is the only way to reach back into Q1/Q2 2026.
    This is a DOCUMENTED DEVIATION, not a silent splice: the retired
    definition (close +10% x rel_volume 3 x market cap >= $500M) matched
    none of the three published EP definitions (audit 2026-09-18 #44, see
    ``pipeline/screeners/ep_stockbee.py`` module docstring). The pre-09-18
    counts below are only as reliable as that retired scan was. See
    ``data/reference/METRIC_SOURCES.md``.

What "post-earnings" means here (a proxy, not a filter): no screener or
archive in this pipeline carries a per-row earnings-date flag over the full
~5,600-ticker universe -- earnings-date coverage
(``pipeline/tickers/ticker_data_fetcher.py``) is scoped to ~244
tracker-relevant tickers (open/recent positions + top heating-up names), not
an EP scan's universe. Stockbee's own definition says the scan output is a
candidate list a human then reads for "neglect + game-changing earnings"
(see ``ep_stockbee.UNMEASURED``) -- not every hit is earnings-driven (M&A,
FDA, guidance revisions, short squeezes also produce EP-shaped bars). We do
NOT filter by an actual earnings date; "EP hit" is used as a proxy for
"post-earnings gap" per the course outline's own framing, and that
substitution is named here rather than hidden.

What "earnings season" means here (an industry convention, not an SEC date):
the SEC sets no start/end date for earnings season -- the only official
requirement is a filing deadline of 45 days after quarter end (FINRA
Investor Insights, confirmed by web search 2026-09-21; no exchange or index
methodology book publishes numeric season boundaries either). The widely
cited retail/press convention (FINRA / Yahoo Finance / Corporate Finance
Institute, same search) is: a quarter's season opens roughly two weeks after
quarter-end and runs through the end of the following month. We operationalize
that shape as:
    Q4 season (of year y-1), observed in year y:  y-01-15 .. y-02-{28,29}
    Q1 season:  y-04-15 .. y-05-31
    Q2 season:  y-07-15 .. y-08-31
    Q3 season:  y-10-15 .. y-11-30
This is OUR reading of a descriptive convention, not a number anyone
publishes -- flagged as a deviation in METRIC_SOURCES.md, per the "先找口径，
别自己造" rule (searched, no numeric standard exists; convention cited).
It is not an unmotivated guess either: EP-hit density in the archive
(2026-03-09 .. 2026-09-18) spikes almost exactly inside these windows
(2026-04-20..05-08 and 2026-08-04..08-21) -- which is what "earnings season"
should look like if the union above is measuring something real.

Industry taxonomy: Finviz ``industry`` (``data/output/universe.json``), per
Andy's 2026-09-21 ruling in ``DATA_CONTRACTS.md`` §七 (real per-ticker GICS is
licensed/unavailable; the 144-ETF constants list is a tradeable watchlist,
not a per-ticker taxonomy). Industry is joined from TODAY's universe.json
snapshot by ticker -- historical hits are not re-classified as of their own
hit date, and ``ticker_events.csv`` does not archive ``industry``
historically (only ``sector``). Tickers no longer in the current ~5,600-row
universe (delisted, renamed, acquired) can't be mapped; they're counted
separately under ``unmapped_tickers``, not silently dropped or bucketed into
a fake industry.

Run:
    python -m pipeline.tools.ep_industry_seasons [--as-of 2026-09-18] [--seasons 2]
"""

from __future__ import annotations

import argparse
import calendar
import csv
import json
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from pipeline.marketcal import last_completed_session  # noqa: E402
from pipeline.tools.delayed_ep_scan import EP_SCREENERS  # noqa: E402

EVENTS = Path("data/history/ticker_events.csv")
UNIVERSE = Path("data/output/universe.json")
OUTPUT = Path("data/output/ep_industry_seasons.json")

DEFINITION = (
    "EP hit = ep_stockbee UNION ep_qullamaggie (author-verbatim, from "
    "2026-09-18) UNION retired episodic_pivot (rows <= 2026-09-17, "
    "self-invented, kept for historical continuity only -- see "
    "METRIC_SOURCES.md). Used as a proxy for 'post-earnings gap', not "
    "filtered by an actual earnings date (none exists universe-wide)."
)
SEASON_RULE = (
    "Earnings season has no SEC/exchange-official date range (only a "
    "45-day filing deadline). We use the widely cited convention "
    "(FINRA / Yahoo Finance / CFI): quarter-end + ~2 weeks through the "
    "end of the following month. Self-invented operationalization of a "
    "descriptive convention -- see METRIC_SOURCES.md."
)


@dataclass(frozen=True)
class Season:
    season_id: str
    start: date
    end: date


def season_defs_for_year(year: int) -> list[Season]:
    """The 4 earnings-season windows observed during `year`. Q4's window
    lands in Jan/Feb of `year` but reports the PRIOR year's Q4, so its id
    is `{year-1}Q4`."""
    feb_end = 29 if calendar.isleap(year) else 28
    return [
        Season(f"{year - 1}Q4", date(year, 1, 15), date(year, 2, feb_end)),
        Season(f"{year}Q1", date(year, 4, 15), date(year, 5, 31)),
        Season(f"{year}Q2", date(year, 7, 15), date(year, 8, 31)),
        Season(f"{year}Q3", date(year, 10, 15), date(year, 11, 30)),
    ]


def recent_complete_seasons(as_of: date, n: int = 2) -> list[Season]:
    """The `n` most recent seasons whose window has fully ended by `as_of`,
    oldest first."""
    candidates: list[Season] = []
    for y in (as_of.year - 1, as_of.year, as_of.year + 1):
        candidates.extend(season_defs_for_year(y))
    complete = sorted((s for s in candidates if s.end < as_of), key=lambda s: s.end)
    return complete[-n:]


def load_events(path: Path = EVENTS) -> list[dict]:
    with path.open(newline="") as fh:
        return [r for r in csv.DictReader(fh) if r.get("screener") in EP_SCREENERS]


def load_industry_map(path: Path = UNIVERSE) -> dict[str, str]:
    rows = json.loads(path.read_text())["rows"]
    return {r["ticker"]: (r.get("industry") or "") for r in rows}


def aggregate_season(events: list[dict], season: Season, industry_map: dict[str, str]) -> dict:
    hits_by_industry: Counter = Counter()
    tickers_by_industry: dict[str, set] = defaultdict(set)
    unmapped_tickers: set = set()
    all_tickers: set = set()
    total_hits = 0
    for r in events:
        try:
            d = datetime.strptime(r["date"], "%Y-%m-%d").date()
        except ValueError:
            continue
        if not (season.start <= d <= season.end):
            continue
        t = r["ticker"]
        total_hits += 1
        all_tickers.add(t)
        industry = industry_map.get(t)
        if not industry:
            unmapped_tickers.add(t)
            industry = "UNKNOWN"
        hits_by_industry[industry] += 1
        tickers_by_industry[industry].add(t)
    industries = sorted(
        (
            {"industry": ind, "tickers": len(tickers_by_industry[ind]), "hits": hits_by_industry[ind]}
            for ind in hits_by_industry
        ),
        key=lambda x: (-x["tickers"], -x["hits"], x["industry"]),
    )
    return {
        "season_id": season.season_id,
        "start_date": season.start.isoformat(),
        "end_date": season.end.isoformat(),
        "total_hits": total_hits,
        "unique_tickers": len(all_tickers),
        "unmapped_tickers": sorted(unmapped_tickers),
        "industries": industries,
    }


def rotation_delta(prev: dict, cur: dict, top_n: int = 5) -> dict:
    prev_top = [x["industry"] for x in prev["industries"][:top_n]]
    cur_top = [x["industry"] for x in cur["industries"][:top_n]]
    prev_set, cur_set = set(prev_top), set(cur_top)
    return {
        "prior_season_id": prev["season_id"],
        "current_season_id": cur["season_id"],
        "prior_top5": prev_top,
        "current_top5": cur_top,
        "entered_top5": sorted(cur_set - prev_set),
        "dropped_from_top5": sorted(prev_set - cur_set),
    }


def build(as_of: Optional[date] = None, n_seasons: int = 2,
          events_path: Path = EVENTS, universe_path: Path = UNIVERSE) -> dict:
    if as_of is None:
        as_of = last_completed_session()
    events = load_events(events_path)
    industry_map = load_industry_map(universe_path)
    seasons = recent_complete_seasons(as_of, n_seasons)
    season_results = [aggregate_season(events, s, industry_map) for s in seasons]
    rotation = rotation_delta(season_results[-2], season_results[-1]) if len(season_results) >= 2 else None
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "as_of": as_of.isoformat(),
        "definition": DEFINITION,
        "season_window_rule": SEASON_RULE,
        "industry_source": "Finviz industry field, data/output/universe.json (current snapshot; see module docstring)",
        "seasons": season_results,
        "rotation_vs_prior_season": rotation,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--as-of", type=str, default=None, help="YYYY-MM-DD, default = last completed session")
    ap.add_argument("--seasons", type=int, default=2, help="how many recent complete seasons to report")
    ap.add_argument("--out", type=str, default=str(OUTPUT))
    args = ap.parse_args()
    as_of = datetime.strptime(args.as_of, "%Y-%m-%d").date() if args.as_of else None
    payload = build(as_of=as_of, n_seasons=args.seasons)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {out_path} -- {len(payload['seasons'])} seasons")
    for s in payload["seasons"]:
        top5 = ", ".join(f"{x['industry']}({x['tickers']})" for x in s["industries"][:5])
        print(f"  {s['season_id']} [{s['start_date']}..{s['end_date']}] "
              f"hits={s['total_hits']} tickers={s['unique_tickers']} top5: {top5}")


if __name__ == "__main__":
    main()
