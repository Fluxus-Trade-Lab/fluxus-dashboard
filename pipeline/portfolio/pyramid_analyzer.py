"""Pyramid campaign detector + counterfactual analyzer.

A "campaign" = ≥2 trades in the CSV, same ticker, same direction, with each
subsequent entry made within 60 business days of a still-open prior entry.
Surfaces:
  - which campaigns the user has actually run
  - aggregate campaign R (sum of realized $ across layers / first-layer R)
  - counterfactual: what if only the first layer had been held under the
    Phase-3 optimal rules — did pyramiding add or subtract R?

Pyramid is NOT a parameter swept by the main optimizer; it would double-count
behavior already encoded as separate trade records. This module is a
descriptive analysis layered on top of the same trade data.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional

import numpy as np
import pandas as pd

from pipeline.portfolio.simulator import SimParams, prep_bars, _simulate_from_bars
from pipeline.portfolio.trade_parser import Trade

logger = logging.getLogger(__name__)


@dataclass
class Campaign:
    ticker: str
    direction: str
    layers: list[Trade]                     # all layer trades, sorted by entry_date
    actual_realized_R: float                # sum across layers / first-layer R$
    counterfactual_R: Optional[float] = None  # first-layer-alone, optimal rules
    delta_R: Optional[float] = None         # actual - counterfactual

    @property
    def n_layers(self) -> int:
        return len(self.layers)

    @property
    def first_entry(self) -> date:
        return self.layers[0].entry_date

    @property
    def last_entry(self) -> date:
        return self.layers[-1].entry_date

    @property
    def span_days(self) -> int:
        return (self.last_entry - self.first_entry).days


def _business_days_between(a: date, b: date) -> int:
    """Approximate business days between two dates."""
    days = abs((b - a).days)
    return int(days * 5 / 7)


def detect_campaigns(trades: list[Trade], window_business_days: int = 60) -> list[Campaign]:
    """Group trades into pyramid campaigns.

    A campaign starts when a trade is opened, and subsequent same-ticker
    same-direction trades opened while ANY prior layer is still open
    (or within `window_business_days` of the most recent layer's entry)
    are added to the campaign.
    """
    by_ticker: dict[tuple[str, str], list[Trade]] = {}
    for t in trades:
        key = (t.ticker, t.direction)
        by_ticker.setdefault(key, []).append(t)

    campaigns: list[Campaign] = []
    for (ticker, direction), tlist in by_ticker.items():
        if len(tlist) < 2:
            continue
        # sort by entry date
        sorted_tlist = sorted(tlist, key=lambda t: t.entry_date)
        # walk and form campaigns
        current: list[Trade] = [sorted_tlist[0]]
        for t in sorted_tlist[1:]:
            # is this within window_business_days of the most recent campaign layer?
            most_recent_entry = current[-1].entry_date
            biz_gap = _business_days_between(most_recent_entry, t.entry_date)
            if biz_gap <= window_business_days:
                current.append(t)
            else:
                if len(current) >= 2:
                    campaigns.append(_make_campaign(ticker, direction, current))
                current = [t]
        if len(current) >= 2:
            campaigns.append(_make_campaign(ticker, direction, current))
    return campaigns


def _make_campaign(ticker: str, direction: str, layers: list[Trade]) -> Campaign:
    """Build Campaign with actual_realized_R = total $ across layers / first-layer R."""
    first_R = layers[0].R_dollars
    total_pl = sum(t.realized_pl for t in layers)
    actual_R = total_pl / first_R if first_R > 0 else 0
    return Campaign(
        ticker=ticker, direction=direction, layers=layers,
        actual_realized_R=actual_R,
    )


def compute_counterfactual(
    campaigns: list[Campaign],
    ohlc_by_ticker: dict,
    best_params: SimParams,
) -> None:
    """For each campaign, simulate the FIRST layer alone under `best_params`,
    out to the latest layer's exit (so the time horizon matches). Stores
    counterfactual_R and delta_R on each Campaign in place.
    """
    for c in campaigns:
        first = c.layers[0]
        ohlc = ohlc_by_ticker.get(c.ticker)
        if ohlc is None:
            continue
        # Extend the OHLC out to the campaign's last exit / today
        bars = prep_bars(first, ohlc)
        if bars is None:
            continue
        try:
            R = _simulate_from_bars(first, bars, best_params)
        except Exception as e:  # noqa: BLE001
            logger.warning(f"counterfactual sim failed for {c.ticker}: {e}")
            continue
        c.counterfactual_R = R
        c.delta_R = c.actual_realized_R - R


def build_pyramid_section(campaigns: list[Campaign]) -> list[dict]:
    """Convert campaign objects to plain dicts for the report."""
    out = []
    for c in campaigns:
        out.append({
            'ticker': c.ticker,
            'direction': c.direction,
            'n_layers': c.n_layers,
            'first_entry': c.first_entry.isoformat(),
            'last_entry': c.last_entry.isoformat(),
            'span_days': c.span_days,
            'actual_R': float(c.actual_realized_R),
            'counterfactual_R': float(c.counterfactual_R) if c.counterfactual_R is not None else None,
            'delta_R': float(c.delta_R) if c.delta_R is not None else None,
            'layer_entries': [
                {'date': l.entry_date.isoformat(), 'price': l.entry_price, 'qty': l.original_qty}
                for l in c.layers
            ],
        })
    return out
