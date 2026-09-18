"""True Market Leader -- Richard Moglen's 2020 definition, one implementation.

Andy 2026-09-18, verbatim: 「照 Moglen 2020（建议）可以，Stage 1 或 2 底部突破这类是
可以编写程序检测的，所以你可以搞定。steve jacobs就在做，还有很多人也在做。Deepvue也有。」
and, on the stage ruler: 「Stage Analysis本身就来自Weinstein，这点很重要。而本机pine脚本
没有完全得到验证，我从心里是倾向steve jacob做的东西，比较靠谱。」

Source: Richard Moglen (TraderLion), X thread 2020-11-06,
https://x.com/RichardMoglen/status/1324813953474678787 -- verbatim copy in
data/research/tml_origin_2026-09-18/README.md. "In one sentence a TML is an
institutional quality stock in a leading industry group with superior
fundamentals and technicals."

Called by BOTH the watchlist panel (PANELS["true_market_leaders"].test) and
leaders_log's `tml` column, so the page and the research log cannot disagree.

HARD conditions (the source's own words: "essential", "vital", or a
technical list item with a number) -- ORIGINAL TEXT -> OUR IMPLEMENTATION:
  "Dollar Volume > $30 Million is essential"
      -> sb_avg_dollar_vol_20 > 30e6: 20-session mean close x 20-session
         mean volume (the AVGC20*AVGV20 the Stockbee inputs already compute).
         The 20-session window is ours; the source gives none.
  "This. is. vital. RS Rating over 97 is ideal"
      -> rs_rating >= 97. rs_rating is our community reconstruction of IBD's
         RS Rating (run_all.py), not IBD's own number. The source says
         "ideal"; making it hard is our call (the main session's).
  "Above a Rising 30 Week Moving Average"
      -> wk_sma30_dist > 0 and wk_sma30_rising (30-week SMA of W-FRI closes,
         this week's value > last week's: a ONE-week comparison, ours).
  "Breaking out of a Stage 1 or Stage 2 Base"
      -> weinstein_stage == 2 (stage_analysis.weinstein_series, Weinstein
         1988 Ch.2 operationalized -- see there). Why only 2: a Stage-1 base
         broken out of IS the entry into Stage 2, and a Stage-2 base is a
         continuation inside Stage 2; a stock still IN Stage 1 has not broken
         out. Our operationalization (Weinstein's book, not a Pine port).
  "Trending above Key Moving Averages (10, 21ema, 50sma)"
      -> close > ema10 and close > ema21 and sma50_dist > 0. The source
         writes "10" without saying EMA or SMA; we read EMA (ema10 already
         shipped; the Pine stage script's 10 is also an EMA).
  "Up/Down Vol > 1.2"
      -> ud_vol_ratio_50 > 1.2, IBD's 50-day Up/Down Volume (stage_analysis).

"MOST OF" -- "Not every TML will have all of these criteria, but in general
their record should be outstanding with regards to most of them." Our
operationalization of "most": at least 3 of these 5 are MET.
  "Quarterly Sales Growth > 25% YoY"       -> revenue_growth > 0.25
  "Quarterly Earnings Growth > 25% YoY"    -> eps_growth_this_y > 0.25
                                              (yfinance earningsGrowth: quarterly yoy)
  "Pre+After Tax Margins >20% Recent Quarters" -> profit_margin > 0.20
                                              (yfinance profitMargins: after-tax, TTM --
                                               the pre-tax one is not in `info`)
  "ROE >17%"                               -> roe > 0.17 (yfinance returnOnEquity, TTM)
  "Annual Earnings Ests for the next year > 25%" -> eps_growth_next_y > 0.25
                                              (forwardEps / trailingEps - 1)
  A missing value is out of the denominator (reported as met/known), but a
  row still needs 3 met items to pass -- 2/2 known is NOT "most".

FLAG ONLY (the source says "often", or we cannot measure it):
  "often in the Top 20 Industry groups"  -> top20_industry = industry_rank <= 20
      (industries ranked by the median rs_3m of tradeable members -- the
      quantity behind i_score. IBD ranks its 197 groups on 6-month price
      performance; ours is a different ruler and a different group list.)
  "Volume and Price contractions within bases" -- NOT computed: no number in
      the source; the nearest existing reading is `vcs` (oratnek's VCS).
  "Huge gaps up on volume after Earning Beat" -- NOT computed: the row has
      no earnings date or surprise.
  "Story (new product/service)" -- not measurable.
"""

from __future__ import annotations

from typing import Any, Dict, Mapping, Optional, Tuple

MIN_DOLLAR_VOL = 30e6
MIN_RS_RATING = 97
MIN_UD_VOL = 1.2
STAGES_OK = frozenset({2})
FUNDAMENTALS = (
    ("revenue_growth", 0.25),
    ("eps_growth_this_y", 0.25),
    ("profit_margin", 0.20),
    ("roe", 0.17),
    ("eps_growth_next_y", 0.25),
)
MIN_FUNDAMENTALS_MET = 3
TOP_INDUSTRIES = 20

# fields that must exist in the file for the panel to count as measured
NEEDS = ("sb_avg_dollar_vol_20", "rs_rating", "wk_sma30_rising", "weinstein_stage",
         "ud_vol_ratio_50")


def _f(r: Mapping[str, Any], k: str) -> Optional[float]:
    v = r.get(k)
    if v is None or isinstance(v, bool):
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return None if f != f else f


def _gt(r, k, x) -> bool:
    v = _f(r, k)
    return v is not None and v > x


def fundamentals(r: Mapping[str, Any]) -> Tuple[int, int]:
    """(met, known) over the five Moglen fundamentals."""
    met = known = 0
    for k, th in FUNDAMENTALS:
        v = _f(r, k)
        if v is None:
            continue
        known += 1
        met += v > th
    return met, known


def hard(r: Mapping[str, Any]) -> Dict[str, bool]:
    close = _f(r, "close")
    st = r.get("weinstein_stage")
    try:
        st = int(st) if st is not None else None
    except (TypeError, ValueError):
        st = None
    return {
        "dollar_volume": _gt(r, "sb_avg_dollar_vol_20", MIN_DOLLAR_VOL),
        "rs_rating": (_f(r, "rs_rating") or -1) >= MIN_RS_RATING,
        "above_rising_30wk": _gt(r, "wk_sma30_dist", 0.0) and r.get("wk_sma30_rising") is True,
        "stage_1_2_breakout": st in STAGES_OK,
        "above_key_mas": (close is not None and _f(r, "ema10") is not None and _f(r, "ema21") is not None
                          and close > _f(r, "ema10") and close > _f(r, "ema21")
                          and _gt(r, "sma50_dist", 0.0)),
        "up_down_vol": _gt(r, "ud_vol_ratio_50", MIN_UD_VOL),
    }


def flags(r: Mapping[str, Any]) -> Dict[str, Optional[bool]]:
    rank = _f(r, "industry_rank")
    return {"top20_industry": None if rank is None else rank <= TOP_INDUSTRIES}


def passes(r: Mapping[str, Any]) -> bool:
    return all(hard(r).values()) and fundamentals(r)[0] >= MIN_FUNDAMENTALS_MET
