"""
yfinance data adapter — secondary source for ETF/macro data and VCP Layer 2.
Cherry-picked calculation functions from traderwillhu/market_dashboard build_data.py.
Per plan.md §2.4.
"""
import logging
import time

import numpy as np
import pandas as pd
import yfinance as yf
from scipy.stats import rankdata

from .base_adapter import BaseAdapter
from ..constants.tickers import STOCK_GROUPS
from ..constants.leveraged import get_leveraged_etfs
from ..screeners.atr_enrichment import atr_multiple_from_levels

logger = logging.getLogger(__name__)


def _flatten_yf_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Flatten yfinance MultiIndex columns for single-ticker downloads.
    yfinance >=0.2.31 returns MultiIndex columns like ('Close', 'SPY')
    even for single-ticker downloads. This flattens them to just 'Close'.
    """
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df


# ══════════════════════════════════════════════════════════════════════════════
# Cherry-picked calculation functions from build_data.py lines 176-240
# ══════════════════════════════════════════════════════════════════════════════

def calculate_atr(hist_data: pd.DataFrame, period: int = 14) -> float | None:
    """ATR via EMA of True Range. Cherry-picked from existing codebase."""
    try:
        hl = hist_data['High'] - hist_data['Low']
        hc = (hist_data['High'] - hist_data['Close'].shift()).abs()
        lc = (hist_data['Low'] - hist_data['Close'].shift()).abs()
        tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
        return tr.ewm(alpha=1/period, adjust=False).mean().iloc[-1]
    except Exception:
        return None


def calculate_sma(hist_data: pd.DataFrame, period: int = 50) -> float | None:
    """Simple Moving Average. Cherry-picked from existing codebase."""
    try:
        return hist_data['Close'].rolling(window=period).mean().iloc[-1]
    except Exception:
        return None


def calculate_ema(hist_data: pd.DataFrame, period: int = 10) -> float | None:
    """Exponential Moving Average. Cherry-picked from existing codebase."""
    try:
        return hist_data['Close'].ewm(span=period, adjust=False).mean().iloc[-1]
    except Exception:
        return None


def calculate_rrs(stock_data: pd.DataFrame, spy_data: pd.DataFrame,
                  atr_length: int = 14, length_rolling: int = 50,
                  length_sma: int = 20, atr_multiplier: float = 1.0) -> pd.DataFrame | None:
    """Volatility-adjusted Relative Strength vs SPY (VARS).
    Cherry-picked from existing codebase.
    RRS = (actual_move - expected_move) / stock_ATR
    where expected = (SPY_move / SPY_ATR) * stock_ATR
    """
    try:
        merged = pd.merge(
            stock_data[['High', 'Low', 'Close']],
            spy_data[['High', 'Low', 'Close']],
            left_index=True, right_index=True,
            suffixes=('_stock', '_spy'), how='inner'
        )
        if len(merged) < atr_length + 1:
            return None

        for prefix in ['stock', 'spy']:
            h = merged[f'High_{prefix}']
            l = merged[f'Low_{prefix}']
            c = merged[f'Close_{prefix}']
            tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
            merged[f'atr_{prefix}'] = tr.ewm(alpha=1/atr_length, adjust=False).mean()

        sc = merged['Close_stock'] - merged['Close_stock'].shift(1)
        spy_c = merged['Close_spy'] - merged['Close_spy'].shift(1)
        spy_pi = spy_c / merged['atr_spy']
        expected = spy_pi * merged['atr_stock'] * atr_multiplier
        rrs = (sc - expected) / merged['atr_stock']
        rolling_rrs = rrs.rolling(window=length_rolling, min_periods=1).mean()
        rrs_sma = rolling_rrs.rolling(window=length_sma, min_periods=1).mean()

        return pd.DataFrame(
            {'RRS': rrs, 'rollingRRS': rolling_rrs, 'RRS_SMA': rrs_sma},
            index=merged.index
        )
    except Exception:
        return None


SCALE_MISMATCH_TOL = 0.20


def rs_line_pctl(close: pd.Series, bench_close: pd.Series, n: int = 21) -> float | None:
    """oratnek's "RS 1M": where TODAY's relative-strength line (close / SPY
    close) sits among its own last `n` sessions -- count(RS_i <= RS_today)/n
    x 100. A SELF (time-series) percentile, not a cross-sectional one: 100 =
    the RS line is at a one-month high, whatever the whole market did.

    Reverse-engineered 2026-08-18 from his 08-17 premarket page: all eight
    distinct values he printed were k/21 (43, 57, 67, 71, 81, 90, 95, 100),
    and this definition reproduces all 29 of his numbers exactly
    (pipeline/tests/fixtures/oratnek_rs1m_*). Not to be confused with our
    rs_1m (cross-sectional percentile of the 1M return within the tradeable
    field): RELY was 100 on his page and 68 on ours the same day, and both
    were right -- they answer different questions.
    """
    a = pd.concat([close.rename('c'), bench_close.rename('b')], axis=1, join='inner').dropna()
    if len(a) < n or (a['b'] <= 0).any():
        return None
    rs = (a['c'] / a['b']).iloc[-n:]
    return float((rs <= rs.iloc[-1]).mean() * 100.0)


def range5_pctl(hist: pd.DataFrame, n: int = 252) -> float | None:
    """Self-percentile of the 5-session range (as % of close), same shape as
    `atr_pctl`. Carried BECAUSE `atr_pctl` alone cannot tell two states apart:

      真压缩      atr_pctl low AND range5_pctl low  -- genuinely quiet
      ATR没追上    atr_pctl low BUT range5_pctl high -- price ran, and ATR (a
                 14-day EMA, and divided by a now-much-higher close) has not
                 caught up. PURR on 2026-08-21 is the specimen: ATR rose 53%
                 in three sessions while price rose 47%, so ATR/close barely
                 moved and read 4 -- while its 5-day range sat at the 99th.

    They are not the same trade and they do not perform the same: measured
    2026-08-23 inside the compressed fifth, the second state won 47.0% of
    R-framed trades against 40.5% for the first (n=1607/4129, p<1e-4). So this
    is a LABEL, not a filter -- an early attempt to gate the "false" ones out
    removed the better half. Show both readings; never collapse them to one.
    """
    try:
        c, h, l = hist['Close'], hist['High'], hist['Low']
        if len(c) < 60:
            return None
        rng = (h.rolling(5).max() - l.rolling(5).min()) / c
        win = rng.dropna().iloc[-n:]
        if len(win) < 60 or not np.isfinite(float(win.iloc[-1])):
            return None
        return float((win <= win.iloc[-1]).mean() * 100.0)
    except Exception:
        return None


def atr_pctl(hist: pd.DataFrame, n: int = 252, period: int = 14) -> float | None:
    """Where TODAY's ATR% (ATR14 / close) sits among its own last `n` sessions
    -- count(ATR%_i <= ATR%_today)/n x 100. 0 = the most compressed this name
    has been in a year; 100 = the loosest.

    A SELF percentile, like `rs_line_pctl` and unlike `rs_1m`: it says nothing
    about other stocks, only about this one against its own history. That is
    the whole point -- 2% daily range is sleepy for one name and violent for
    another, so the absolute number does not travel.

    Measured 2026-08-23 over 4,107 fresh-high-pullback entries
    (data/research/tightness_2026-08/report/index.html): tightest quintile won
    48.3% of R-framed trades against 28.7% for the loosest (p<1e-8), and it
    beat every other tightness reading we have -- RMV (a 15-bar min-max of bar
    range) came in BELOW baseline at -5.7pp.

    THREE conditions travel with it, and it is wrong to use without them:

    * it is a CLOCK, not a stock-picker. Ranked within one ticker (expanding,
      no look-ahead) the spread is +13.3pp; ranked across the names available
      on the same day, only +4.3pp. It says when THIS name is ready, not which
      name to take. The picker that paired with it best was distance to the
      52-week high (+7.9pp inside the compressed half).
    * it is strongest on the day a pullback STARTS (+19.6pp) and much weaker
      on days already in the zone (+7.2pp).
    * it carries no edge at all outside a setup (-2.4pp pool-wide) -- a
      modifier within a trend, never a signal by itself. RBRK and HOOD both
      compressed in Jan 2026 and fell 28% and 27%; both were out of trend.

    Replication is honest but not flattering: on an independent sample (the
    172-name 2-year ticker store) the first-day spread was +11.8pp (p=0.047),
    positive but weaker, non-monotonic, and it split 2025 +15.1pp / 2026
    +1.2pp. Every cut run so far is positive; the MAGNITUDE is unstable. Treat
    it as a tiebreaker, not a rule, and do not build a gate on the threshold.

    Not to be confused with `adr_pct` / ATR% itself (the absolute number, which
    is what sizes a stop): that one is only +7.9pp and answers a different
    question. Both are exported; do not substitute one for the other.
    """
    try:
        c = hist['Close']
        if len(c) < max(60, n // 4):
            return None
        hl = hist['High'] - hist['Low']
        hc = (hist['High'] - c.shift()).abs()
        lc = (hist['Low'] - c.shift()).abs()
        tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
        atrp = (tr.ewm(alpha=1 / period, adjust=False).mean() / c).dropna()
        win = atrp.iloc[-n:]
        if len(win) < 60 or not np.isfinite(float(win.iloc[-1])):
            return None
        return float((win <= win.iloc[-1]).mean() * 100.0)
    except Exception:
        return None


def _crossed_up(close: pd.Series, ma: pd.Series) -> bool | None:
    """Close crossed UP through `ma` on the last bar: yesterday's close below
    yesterday's MA, today's close at or above today's. None when either of
    the two MA values is missing (warm-up)."""
    if len(close) < 2 or len(ma) < 2:
        return None
    c0, c1 = float(close.iloc[-2]), float(close.iloc[-1])
    m0, m1 = ma.iloc[-2], ma.iloc[-1]
    if pd.isna(m0) or pd.isna(m1):
        return None
    return bool(c0 < float(m0) and c1 >= float(m1))


def _expected_session():
    """The session this run is labelled with (last completed US session).
    Module-level so tests can monkeypatch it; None disables the stale check."""
    try:
        from pipeline.marketcal import last_completed_session
        return last_completed_session()
    except Exception:
        return None


def bar_consistency(hist: pd.DataFrame, expected_session, vendor_close) -> tuple[str, str | None]:
    """Is this ticker's bar history usable for TODAY's derived columns?

    Returns (status, newest_bar_date):
      'ok'             newest bar is on/after the session the run is labelled
                       with, and (if a vendor close is known) agrees with it
      'stale'          newest bar is BEFORE the session -- a batch download that
                       dropped the last bar; every derived column would lag by a
                       session while looking populated (FIRY/FBRX 2026-08-14)
      'scale_mismatch' newest close differs from the vendor close by more than
                       20% -- history on a pre-split scale (BYND 2026-08)

    A guard that only counts nulls cannot see either; this is the check that
    makes them visible, and the caller nulls the derived columns rather than
    publish a number that is one session late or one split off.
    """
    try:
        last = hist.index[-1]
        last_date = last.date() if hasattr(last, "date") else pd.Timestamp(last).date()
    except Exception:
        return "stale", None
    if expected_session is not None and last_date < expected_session:
        return "stale", str(last_date)
    try:
        c = float(hist["Close"].iloc[-1])
        v = float(vendor_close) if vendor_close is not None else None
    except (TypeError, ValueError):
        v = None
    if v and v > 0 and c > 0 and abs(c / v - 1.0) > SCALE_MISMATCH_TOL:
        return "scale_mismatch", str(last_date)
    return "ok", str(last_date)


def _window_ok(n: int) -> bool:
    return n >= 11


def vol10_green_count(closes, opens, vols, lookback: int = 30) -> int | None:
    """oratnek's "PP (Vol > 10D)": a green bar (close > open) whose volume beats
    the highest volume of the prior ten bars, ALL of them. A volume-surge
    event. This is what our `pocket_pivot` computed until 2026-08-17; renamed
    so the textbook name can carry the textbook maths (see pocket_pivot_count).
    None on fewer than 11 bars (unmeasured)."""
    n = len(closes)
    if not _window_ok(n):
        return None
    count = 0
    for j in range(max(10, n - lookback), n):
        if not closes[j] > opens[j]:
            continue
        prior = [v for v in vols[j - 10:j] if v == v]
        if prior and vols[j] > max(prior):
            count += 1
    return count


def vol10_green_today(closes, opens, vols) -> bool | None:
    n = vol10_green_count(closes, opens, vols, lookback=1)
    return None if n is None else bool(n)


def pocket_pivot_count(closes, opens, vols, lookback: int = 30) -> int | None:
    """Morales / Kacher pocket pivot, the textbook definition (accumulation_
    audit.md, 2026-08-09): an UP day -- close above the PRIOR close -- whose
    volume beats the highest volume among the DOWN days of the prior ten bars.
    Down-day volume is the yardstick because the question is buying vs
    selling. If the prior ten hold no down day the bar is not a pivot (no
    vacuous truth; measured at 0/1643 up days anyway).

    On 91 names this form correlated +0.71 with the A/D volume ratio against
    +0.52 for the all-bars form, and the two Top-10 lists shared 3 names -- a
    different quantity, not a detail. None on fewer than 11 bars.
    """
    n = len(closes)
    if not _window_ok(n):
        return None
    count = 0
    for j in range(max(10, n - lookback), n):
        if not closes[j] > closes[j - 1]:
            continue
        down = [vols[k] for k in range(j - 10, j)
                if k >= 1 and closes[k] < closes[k - 1] and vols[k] == vols[k]]
        if down and vols[j] > max(down):
            count += 1
    return count


def pocket_pivot_today(closes, opens, vols) -> bool | None:
    """Same-day Morales pocket pivot: `pocket_pivot_count` over the last bar."""
    n = pocket_pivot_count(closes, opens, vols, lookback=1)
    return None if n is None else bool(n)


SP_FIELDS = ("sp_setup", "sp_len", "sp_ll", "sp_hl", "sp_1st", "sp_2nd", "sp_tp1", "sp_tp2",
             "sp_phase", "sp_stop", "sp_ma", "sp_signal", "sp_days", "sp_dist_1st_pct",
             "sp_dist_2nd_pct", "sp_counter")


def structure_pivot_row(hist: pd.DataFrame) -> dict:
    """The Structure Pivot state as flat sp_* fields (see
    pipeline/screeners/structure_pivot.py). Never raises: on any failure every
    field is None, which the screener reads as unmeasured."""
    try:
        from pipeline.screeners.structure_pivot import run as _sp_run
        row = _sp_run(hist).to_row()
        row.pop("sp_close", None)
        return {k: row.get(k) for k in SP_FIELDS}
    except Exception:
        return {k: None for k in SP_FIELDS}


def stockbee_ratios(hist: pd.DataFrame) -> dict:
    """The 'has been strong' ratios behind Stockbee's three anticipation scans
    (Telechart syntax verbatim in the docstring of test_derived_fields), plus
    the liquidity floor input. Null when the window is not there yet.

        ti65       = avgc7 / avgc65      (TI65:  > 1.05)
        mdt        = c / avgc126         (MDT:   > 1.19)
        min_vol_3d = min volume of the last 3 bars   (all: > 100k)

    Double Trouble's c/minl252 comes from the low_52w column in run_all.
    """
    try:
        c = pd.to_numeric(hist['Close'], errors='coerce').dropna()
        v = pd.to_numeric(hist['Volume'], errors='coerce').dropna()
        n = len(c)
        ti65 = float(c.iloc[-7:].mean() / c.iloc[-65:].mean()) if n >= 65 and c.iloc[-65:].mean() > 0 else None
        mdt = float(c.iloc[-1] / c.iloc[-126:].mean()) if n >= 126 and c.iloc[-126:].mean() > 0 else None
        mv3 = float(v.iloc[-3:].min()) if len(v) >= 3 else None
        return {"ti65": ti65, "mdt": mdt, "min_vol_3d": mv3}
    except Exception:
        return {"ti65": None, "mdt": None, "min_vol_3d": None}


def accumulation_flow(hist: pd.DataFrame) -> dict:
    """The accumulation factor the 2026-08-09 audit said we lacked: volume
    weighted by price direction, accumulated across weeks. Two numbers, not
    three -- the A/D volume ratio and OBV slope are near-duplicates (+0.93);
    CMF is the different one.

        ad_ratio_20 = sum(volume on up days) / sum(volume), last 20 sessions
                      (up = close > prior close). 0.5 = balanced; the ratio,
                      not the OBV level, so names of different size compare.
        cmf21       = Chaikin Money Flow, 21 sessions:
                      sum(((c-l)-(h-c))/(h-l) * v) / sum(v)  in [-1, 1]

    None when the window is not there (20 / 21 bars + one prior close).
    """
    try:
        c = pd.to_numeric(hist['Close'], errors='coerce')
        v = pd.to_numeric(hist['Volume'], errors='coerce')
        h = pd.to_numeric(hist['High'], errors='coerce')
        l = pd.to_numeric(hist['Low'], errors='coerce')
        n = len(c)
        out = {"ad_ratio_20": None, "cmf21": None}
        if n >= 21:
            up = (c > c.shift(1)).iloc[-20:]
            vv = v.iloc[-20:]
            tot = float(vv.sum())
            if tot > 0:
                out["ad_ratio_20"] = round(float(vv[up].sum() / tot), 4)
        if n >= 21:
            rng = (h - l).iloc[-21:]
            mfm = (((c - l) - (h - c)) / rng.replace(0, np.nan)).iloc[-21:]
            vv = v.iloc[-21:]
            tot = float(vv.sum())
            if tot > 0:
                out["cmf21"] = round(float((mfm.fillna(0) * vv).sum() / tot), 4)
        return out
    except Exception:
        return {"ad_ratio_20": None, "cmf21": None}


def stockbee_ratios(hist: pd.DataFrame) -> dict:
    """The 'has been strong' ratios behind Stockbee's three anticipation scans
    (Telechart syntax verbatim in the docstring of test_derived_fields), plus
    the liquidity floor input. Null when the window is not there yet.

        ti65       = avgc7 / avgc65      (TI65:  > 1.05)
        mdt        = c / avgc126         (MDT:   > 1.19)
        min_vol_3d = min volume of the last 3 bars   (all: > 100k)

    Double Trouble's c/minl252 comes from the low_52w column in run_all.
    """
    try:
        c = pd.to_numeric(hist['Close'], errors='coerce').dropna()
        v = pd.to_numeric(hist['Volume'], errors='coerce').dropna()
        n = len(c)
        ti65 = float(c.iloc[-7:].mean() / c.iloc[-65:].mean()) if n >= 65 and c.iloc[-65:].mean() > 0 else None
        mdt = float(c.iloc[-1] / c.iloc[-126:].mean()) if n >= 126 and c.iloc[-126:].mean() > 0 else None
        mv3 = float(v.iloc[-3:].min()) if len(v) >= 3 else None
        return {"ti65": ti65, "mdt": mdt, "min_vol_3d": mv3}
    except Exception:
        return {"ti65": None, "mdt": None, "min_vol_3d": None}


def calculate_vcs(hist: pd.DataFrame) -> float | None:
    """Volatility Contraction Score (0-100), one decimal.

    Faithful port of oratnek's VCS v2 -- see pipeline/screeners/vcs.py and
    indicators/third_party/oratnek_vcs_v2.pine. Until 2026-08-17 this was a
    modified port of an older version (min(13,3) stdev, Kaufman-ER quality
    term, .3/.3/.2/.2 weights, no efficiency filter) with no tests; scores
    from before that date are on a different scale. None when history is
    under 76 bars (unmeasured).
    """
    try:
        from pipeline.screeners.vcs import vcs as _vcs
        r = _vcs(hist)
        return None if r.score is None else round(float(r.score), 1)
    except Exception:
        return None


def calculate_abc_rating(hist_data: pd.DataFrame) -> str | None:
    """ABC trend rating. Cherry-picked from existing codebase.
    A = EMA10 > EMA20 > SMA50 (strong uptrend)
    C = EMA10 < EMA20 < SMA50 (downtrend)
    B = mixed (transitioning)
    """
    try:
        ema10 = calculate_ema(hist_data, 10)
        ema20 = calculate_ema(hist_data, 20)
        sma50 = calculate_sma(hist_data, 50)
        if ema10 is None or ema20 is None or sma50 is None:
            return None
        if ema10 > ema20 and ema20 > sma50:
            return "A"
        if ema10 < ema20 and ema20 < sma50:
            return "C"
        return "B"
    except Exception:
        return None


# ══════════════════════════════════════════════════════════════════════════════
# Adapter class
# ══════════════════════════════════════════════════════════════════════════════

class YfinanceAdapter(BaseAdapter):
    """Secondary adapter for ETF/macro data and VCP OHLC lookups."""

    def fetch_universe(self) -> pd.DataFrame:
        raise NotImplementedError("Use FinvizAdapter for full universe")

    def fetch_etf_data(self, tickers: list[str] = None) -> pd.DataFrame:
        """Fetch ETF data with performance + RRS calculations.
        Uses batch download (not per-ticker) for speed.
        """
        if tickers is None:
            tickers = list({t for group in STOCK_GROUPS.values() for t in group})

        # Ensure SPY is included for RRS calculation
        if 'SPY' not in tickers:
            tickers = ['SPY'] + tickers

        # Single batch download — much faster than per-ticker
        logger.info(f"Downloading {len(tickers)} tickers via yfinance batch...")
        data = yf.download(tickers, period='1y', group_by='ticker',
                           progress=False, threads=True)

        spy_hist = None
        if 'SPY' in data.columns.get_level_values(0):
            spy_hist = data['SPY'][['High', 'Low', 'Close']].dropna()

        results = []
        for ticker in tickers:
            try:
                if len(tickers) == 1:
                    hist = data.dropna()
                else:
                    hist = data[ticker].dropna()

                if len(hist) < 20:
                    continue

                close = float(hist['Close'].iloc[-1])
                atr = calculate_atr(hist)
                sma50 = calculate_sma(hist, 50)
                atr_pct = (atr / close) * 100 if atr and close else None
                # The ATR Matrix, one implementation with the ticker badge and
                # the universe column. The inline formula this replaces was
                # dist*close/atr (no (1+dist)) and nulled an exact zero.
                dist_sma50_atr = atr_multiple_from_levels(close, atr, sma50)

                # ABC Rating
                abc = calculate_abc_rating(hist)

                # RRS vs SPY — a SELF-percentile, not a cross-sectional one.
                #
                # `recent_21` is this ETF's own last 21 readings, so the score
                # answers "where does today sit inside this fund's own recent
                # month" — improvement against its own baseline. It does NOT
                # answer "how strong is this fund against the others", which is
                # what the letters RRS and the UI column header both suggest.
                #
                # Measured 2026-08-09, 11 sector ETFs: the score ranks against
                # the underlying RRS *level* at Spearman +0.075 — the two are
                # effectively unrelated. XLK was the strongest sector on the
                # week (+3.52pp over SPY) and scored 5, the bottom bucket,
                # because a fund that has been strong for months is rarely at
                # an extreme within its own trailing 21 days. Same reason the
                # score runs *negative* against perf_3m (-0.193).
                #
                # Kept as-is deliberately: "improvement against own baseline"
                # is a real second-order momentum reading, and perf_1w/perf_1m
                # already answer the strength question elsewhere on the page.
                # Do not sort a "who is strongest" list by this column.
                #
                # Two properties that follow from the construction and will
                # look like bugs if you don't expect them: values are quantised
                # to multiples of 5 ((k-1)/20 x 100 over 21 ranks), and the
                # scale is bounded 0..100 by definition rather than empirically.
                rs_score = None
                rrs_windows = {}
                if spy_hist is not None and ticker != 'SPY':
                    rrs_data = calculate_rrs(
                        hist[['High', 'Low', 'Close']], spy_hist
                    )
                    if rrs_data is not None and len(rrs_data) >= 21:
                        recent_21 = rrs_data['rollingRRS'].iloc[-21:]
                        ranks = rankdata(recent_21, method='average')
                        rs_score = ((ranks[-1] - 1) / (len(recent_21) - 1)) * 100

                    # Same construction over three lookbacks, so a card can show
                    # whether strength is arriving or leaving. There is no
                    # one-day window: a percentile needs something to rank
                    # against, and a single point ranks against nothing.
                    if rrs_data is not None:
                        series = rrs_data['rollingRRS']
                        for label, n in (('1w', 5), ('1m', 21), ('3m', 63)):
                            if len(series) < n:
                                rrs_windows[f'rrs_{label}'] = None
                                continue
                            window = series.iloc[-n:]
                            r = rankdata(window, method='average')
                            rrs_windows[f'rrs_{label}'] = round(
                                ((r[-1] - 1) / (len(window) - 1)) * 100)

                # Leveraged ETF mapping
                long_etfs, short_etfs = get_leveraged_etfs(ticker)

                # Sparkline: last 20 days normalized to first day
                sparkline = []
                if len(hist) >= 20:
                    spark_data = hist['Close'].iloc[-20:]
                    base = float(spark_data.iloc[0])
                    if base > 0:
                        sparkline = [round(float(v) / base, 4) for v in spark_data]

                results.append({
                    'ticker': ticker,
                    'close': close,
                    'change_pct': float((close - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]) if len(hist) >= 2 else None,
                    'intraday_pct': float((close - hist['Open'].iloc[-1]) / hist['Open'].iloc[-1]),
                    'perf_1w': float((close - hist['Close'].iloc[-5]) / hist['Close'].iloc[-5]) if len(hist) >= 5 else None,
                    'perf_1m': float((close - hist['Close'].iloc[-21]) / hist['Close'].iloc[-21]) if len(hist) >= 21 else None,
                    'perf_3m': float((close - hist['Close'].iloc[-63]) / hist['Close'].iloc[-63]) if len(hist) >= 63 else None,
                    'high_52w_dist': float((close - hist['Close'].max()) / hist['Close'].max()),
                    'atr_pct': round(atr_pct, 1) if atr_pct else None,
                    'dist_sma50_atr': round(dist_sma50_atr, 2) if dist_sma50_atr is not None else None,
                    # Not comparable with the stock-side rs_* columns. This is
                    # the 21-day percentile of a *rolling ATR-normalised
                    # relative-strength ratio* vs SPY; the stock columns are
                    # cross-sectional percentiles of raw returns. Same three
                    # letters, different construction, different scale.
                    # `is not None`, not truthiness: 0.0 is the most informative
                    # reading this column has — today sits at the bottom of the
                    # fund's own trailing month — and a falsy test deleted it.
                    # Eight of the nine nulls on 2026-08-09 (XTN EWY EWT TAN EEM
                    # ICLN WGMI BLOK) were genuine zeros with 251 bars each, so
                    # the published distribution was truncated at its left edge:
                    # the minimum observed value was 5, never 0.
                    'rrs_rank': round(rs_score, 0) if rs_score is not None else None,
                    # 1w/1m/3m percentiles of the same rolling RRS series.
                    **rrs_windows,
                    'abc': abc,
                    'sparkline': sparkline,
                    'long_etfs': long_etfs,
                    'short_etfs': short_etfs,
                })
            except Exception as e:
                logger.warning(f"Error processing {ticker}: {e}")

        logger.info(f"Processed {len(results)}/{len(tickers)} tickers successfully")
        return pd.DataFrame(results)

    @staticmethod
    def _fetch_spy_close() -> pd.Series | None:
        """SPY closes for rs_line_pctl. Separate so tests can stub it."""
        try:
            _spy = yf.download('SPY', period='1y', auto_adjust=True, progress=False)
            if isinstance(_spy.columns, pd.MultiIndex):
                _spy.columns = _spy.columns.get_level_values(0)
            return _spy['Close'].dropna()
        except Exception as e:  # noqa: BLE001
            logger.warning("SPY download for rs_line_pctl failed: %s", e)
            return None

    def enrich_universe(self, universe: pd.DataFrame,
                        batch_size: int = 500,
                        expected_session=None) -> pd.DataFrame:
        """Add performance/technical columns to a Finviz-sourced universe.

        Finviz free tier only provides Overview columns (ticker, sector,
        industry, market_cap, close, change_pct, volume).  This method
        batch-downloads 1-year OHLC from yfinance and computes the missing
        STANDARD_COLUMNS: perf_*, sma*_dist, atr, rel_volume, avg_volume,
        high_52w, low_52w.
        """
        tickers = universe['ticker'].dropna().unique().tolist()
        logger.info(f"Enriching {len(tickers)} tickers with yfinance data...")

        all_data: dict = {}

        def sweep(symbols: list, size: int, tag: str) -> None:
            """One pass of batched downloads into `all_data`."""
            for i in range(0, len(symbols), size):
                batch = symbols[i:i + size]
                logger.info(f"  yfinance {tag} batch {i // size + 1}: "
                            f"{len(batch)} tickers")
                try:
                    data = yf.download(batch, period='1y', group_by='ticker',
                                       progress=False, threads=True)
                    if data.empty:
                        continue
                    for t in batch:
                        try:
                            if len(batch) == 1:
                                hist = _flatten_yf_columns(data).dropna()
                            else:
                                hist = data[t].dropna()
                            if len(hist) >= 20:
                                all_data[t] = hist
                        except Exception:
                            pass
                except Exception as e:
                    logger.warning(f"  Batch download failed: {e}")

        sweep(tickers, batch_size, "pass 1")

        # One pass is not enough on a rate-limited egress. Yahoo throttles the
        # GitHub runner's shared IP, and when it does, the misses arrive in
        # blocks — whole batches return empty, not scattered names. Measured:
        # 2.0% missing from a residential IP, 8.2% and then 22.4% from CI, and
        # the 22.4% night knocked three screeners over at once. The tickers a
        # throttled batch dropped are recoverable the same minute; they just
        # have to be asked for again, smaller and slower.
        #
        # Retries target only what is still missing, in quarter-size batches
        # after a pause. The loop stops early when a round recovers nothing —
        # the residue at that point is delisted symbols and unit tickers, which
        # no amount of retrying converts into price history. ~2% of the
        # universe is the healthy floor, not a failure.
        # 2026-08-18: two rounds (20 s + 40 s) were not enough -- 1,047 missing
        # after pass 1, 348 after retry 1, and retry 2's every batch came back
        # 429 (340 left, 8.8% of the file: quality "degraded"). Yahoo's
        # throttle window is longer than 40 s; four rounds with a growing
        # pause cost <= 4 more minutes of a 45-minute budget.
        for attempt in (1, 2, 3, 4):
            missing = [t for t in tickers if t not in all_data]
            if len(missing) <= max(1, int(0.03 * len(tickers))):
                break
            logger.warning(
                "  %d/%d tickers still missing after %s pass(es) — retrying "
                "in smaller batches", len(missing), len(tickers), attempt)
            time.sleep(20 * attempt)
            before = len(all_data)
            sweep(missing, max(50, batch_size // 4), f"retry {attempt}")
            if len(all_data) == before:
                logger.warning("  retry %d recovered nothing — stopping", attempt)
                break

        final_missing = len(tickers) - len(all_data)
        logger.info(f"  Got OHLC for {len(all_data)}/{len(tickers)} tickers "
                    f"({final_missing} missing, "
                    f"{final_missing / max(1, len(tickers)) * 100:.1f}%)")

        # SPY closes for the RS-line self-percentile (rs_line_pctl). One
        # download; a failure leaves the column null rather than the run dead.
        spy_close = self._fetch_spy_close()

        # --- Bar consistency: retry the stale ones once, then tag ---------
        # The session this run is labelled with. A premarket run labels the
        # previous session (last_completed_session), so "newest bar before the
        # session" is a genuine hole, not the clock.
        if expected_session is None:
            expected_session = _expected_session()
        vendor_close = {}
        if 'close' in universe.columns:
            vendor_close = universe.set_index('ticker')['close'].to_dict()
        verdict: dict[str, tuple[str, str | None]] = {
            t: bar_consistency(h, expected_session, vendor_close.get(t)) for t, h in all_data.items()}
        stale = [t for t, (st, _) in verdict.items() if st == 'stale']
        if stale:
            logger.info(f"  {len(stale)} tickers missing their newest bar — retrying singly")
            # the stale list is mostly the tail of the same throttle; asking
            # again in the same second gets the same 429
            time.sleep(30)
            for i in range(0, len(stale), 50):
                batch = stale[i:i + 50]
                try:
                    data = yf.download(batch, period='1y', group_by='ticker',
                                       auto_adjust=True, progress=False, threads=True)
                except Exception:
                    continue
                for t in batch:
                    try:
                        h = data[t].dropna() if len(batch) > 1 else data.dropna()
                    except KeyError:
                        continue
                    if len(h) and bar_consistency(h, expected_session, vendor_close.get(t))[0] == 'ok':
                        all_data[t] = h
                        verdict[t] = ('ok', str(h.index[-1].date()))
        n_stale = sum(1 for st, _ in verdict.values() if st == 'stale')
        n_scale = sum(1 for st, _ in verdict.values() if st == 'scale_mismatch')
        logger.info(f"  bar consistency: {n_stale} stale after retry, {n_scale} scale-mismatched "
                    f"(session {expected_session}); their derived columns are nulled")

        # Compute columns for each ticker
        enriched: dict[str, dict] = {}
        for ticker, hist in all_data.items():
            status, bar_date = verdict.get(ticker, ('ok', None))
            if status != 'ok':
                # Publish the fact, not a number that is a session late or a
                # split off. Finviz-sourced columns on the row are untouched.
                enriched[ticker] = {'bar_date': bar_date, 'bars_stale': status == 'stale',
                                    'bar_scale_mismatch': status == 'scale_mismatch'}
                continue
            try:
                close = float(hist['Close'].iloc[-1])
                n = len(hist)

                sma20 = float(hist['Close'].rolling(20).mean().iloc[-1])
                sma50 = float(hist['Close'].rolling(50).mean().iloc[-1]) if n >= 50 else None
                sma40 = float(hist['Close'].rolling(40).mean().iloc[-1]) if n >= 40 else None
                sma200 = float(hist['Close'].rolling(200).mean().iloc[-1]) if n >= 200 else None

                atr = calculate_atr(hist)
                avg_vol = float(hist['Volume'].rolling(20).mean().iloc[-1])
                vol = float(hist['Volume'].iloc[-1])

                # --- New fields ---
                last_open = float(hist['Open'].iloc[-1])
                last_high = float(hist['High'].iloc[-1])
                last_low = float(hist['Low'].iloc[-1])
                ema21_series = hist['Close'].ewm(span=21, adjust=False).mean()
                ema21 = float(ema21_series.iloc[-1])
                # MA reclaim (2026-08-19, from the scanner validation): the
                # close crossed UP through the 21EMA / 50SMA today (yesterday's
                # close below yesterday's MA, today's close at or above today's).
                # MU / SNDK / NBIS / RBRK's August starts from 14-28% under the
                # 50 were the one thing every trend panel is defined not to see;
                # this event was the only early footprint. Detection fields;
                # the watchlist panel adds the volume clause.
                sma50_series = hist['Close'].rolling(50).mean()
                cross_ema21_up = _crossed_up(hist['Close'], ema21_series) if n >= 22 else None
                cross_sma50_up = _crossed_up(hist['Close'], sma50_series) if n >= 51 else None
                rs_line_pctl_21 = rs_line_pctl(hist['Close'], spy_close) if spy_close is not None else None
                # Longer windows of the same self-percentile (2026-08-19, from
                # the oratnek 08-18 diff): all eleven names on his Momentum 97
                # had the RS line at a 21/42/63/126-session high, and none of
                # ours did at 126. Detection fields for the hypothesis that
                # his "97" is a long-window RS-line percentile, not 1W perf.
                rs_line_pctl_63 = rs_line_pctl(hist['Close'], spy_close, 63) if spy_close is not None else None
                rs_line_pctl_126 = rs_line_pctl(hist['Close'], spy_close, 126) if spy_close is not None else None
                # Volatility compression, same self-percentile shape as above
                # (2026-08-23 tightness study: the only tightness reading that
                # separated outcomes; see atr_pctl's docstring for the numbers
                # and the two conditions on using it).
                atr_pctl_252 = atr_pctl(hist, 252)
                atr_pctl_63 = atr_pctl(hist, 63)
                range5_pctl_252 = range5_pctl(hist, 252)
                # Phase 1: additional EMAs for trailing-stop UI
                ema10 = float(hist['Close'].ewm(span=10, adjust=False).mean().iloc[-1])
                ema20 = float(hist['Close'].ewm(span=20, adjust=False).mean().iloc[-1])
                weekly_closes_for_ema = hist['Close'].resample('W-FRI').last().dropna()
                wk_ema10 = float(weekly_closes_for_ema.ewm(span=10, adjust=False).mean().iloc[-1]) if len(weekly_closes_for_ema) >= 1 else None
                wk_ema20 = float(weekly_closes_for_ema.ewm(span=20, adjust=False).mean().iloc[-1]) if len(weekly_closes_for_ema) >= 1 else None

                # From Open %: intraday move from open
                from_open_pct = (close - last_open) / last_open if last_open > 0 else None
                # perf_5d: five SESSIONS, from bars. Finviz's perf_1w is a
                # calendar week and on 2026-08-14 (a Friday) held only four
                # sessions (FSLY 7.9% vs 30.4% over five) -- oratnek's "Weekly
                # 20%+" reads the weekly candle, i.e. five sessions.
                perf_5d = float(close / hist['Close'].iloc[-6] - 1) if n >= 6 and hist['Close'].iloc[-6] > 0 else None

                # DCR%: Daily Closing Range (close - low) / (high - low)
                hl_range = last_high - last_low
                dcr_pct = (close - last_low) / hl_range if hl_range > 0 else None

                # Pocket Pivot: green candle + vol > max(prior 10 bars vol)
                pp = None
                pp_count = None
                pp_count_10 = None
                v10 = v10_count_10 = v10_count_30 = None
                if n >= 11:
                    closes = hist['Close'].values
                    opens = hist['Open'].values
                    vols = hist['Volume'].values
                    # Same implementation as the counts (NaN-tolerant, None
                    # when unmeasured) -- an inline max() here once said
                    # False while the count said 1 on the same bar.
                    pp = pocket_pivot_today(closes, opens, vols)
                    # Two windows off one implementation: 30 is what we
                    # already shipped, 10 is the window oratnek screens on
                    # ("a day within the last 10 sessions that posted the
                    # highest volume in 10 days along with a green candle").
                    pp_count = pocket_pivot_count(closes, opens, vols, 30)
                    pp_count_10 = pocket_pivot_count(closes, opens, vols, 10)
                    v10 = vol10_green_today(closes, opens, vols)
                    v10_count_10 = vol10_green_count(closes, opens, vols, 10)
                    v10_count_30 = vol10_green_count(closes, opens, vols, 30)

                # Trend Base: price > 50SMA AND 10WMA > 30WMA
                trend_base = False
                if sma50 is not None and close > sma50:
                    # Resample to weekly for WMA
                    weekly = hist['Close'].resample('W').last().dropna()
                    if len(weekly) >= 30:
                        wma10 = float(weekly.rolling(10).mean().iloc[-1])
                        wma30 = float(weekly.rolling(30).mean().iloc[-1])
                        trend_base = bool(wma10 > wma30)

                # VCS
                vcs = calculate_vcs(hist)

                # Structure Pivot (oratnek's Advanced Structure Pivot, ported;
                # golden-checked against the chart on five names 2026-08-17).
                # One dict of sp_* fields, or all-None on short history.
                sp_row = structure_pivot_row(hist)
                sb = stockbee_ratios(hist)
                af = accumulation_flow(hist)

                # 21EMA Low Dist%: how far today's low is from 21EMA
                ema21_low_dist = (last_low - ema21) / ema21 if ema21 > 0 else None

                # Sugar Babies breakout counts: days with vol >= 9M AND change >= 4%.
                # Pradeep's literal rule for habitual big-volume movers.
                closes = hist['Close'].values
                vols = hist['Volume'].values
                bo_1m = bo_3m = bo_6m = bo_1y = 0
                if n >= 2:
                    prev_close = closes[:-1]
                    today_close = closes[1:]
                    chg = (today_close - prev_close) / prev_close
                    today_vol = vols[1:]
                    is_bo = (today_vol >= 9_000_000) & (chg >= 0.04)
                    bo_1y = int(is_bo.sum())
                    bo_6m = int(is_bo[-126:].sum()) if n - 1 >= 126 else bo_1y
                    bo_3m = int(is_bo[-63:].sum()) if n - 1 >= 63 else min(bo_1y, int(is_bo.sum()))
                    bo_1m = int(is_bo[-21:].sum()) if n - 1 >= 21 else min(bo_1y, int(is_bo.sum()))

                enriched[ticker] = {
                    # Belt for the Finviz 'Change %' rename: with a second
                    # source, a header change upstream degrades this column to
                    # ~2% missing instead of 100%. Fill-only merge, so Finviz
                    # still wins when it parses.
                    'change_pct': (close / float(hist['Close'].iloc[-2]) - 1) if n >= 2 else None,
                    'perf_1w': (close / float(hist['Close'].iloc[-5]) - 1) if n >= 5 else None,
                    'perf_1m': (close / float(hist['Close'].iloc[-21]) - 1) if n >= 21 else None,
                    'perf_34d': (close / float(hist['Close'].iloc[-35]) - 1) if n >= 35 else None,
                    'perf_3m': (close / float(hist['Close'].iloc[-63]) - 1) if n >= 63 else None,
                    'perf_6m': (close / float(hist['Close'].iloc[-126]) - 1) if n >= 126 else None,
                    'perf_1y': (close / float(hist['Close'].iloc[0]) - 1) if n >= 200 else None,
                    'perf_ytd': None,  # Would need calendar-year start
                    'sma20_dist': (close - sma20) / sma20 if sma20 else None,
                    'sma50_dist': (close - sma50) / sma50 if sma50 else None,
                    'sma40_dist': (close - sma40) / sma40 if sma40 else None,
                    'sma200_dist': (close - sma200) / sma200 if sma200 else None,
                    'atr': atr,
                    'rel_volume': vol / avg_vol if avg_vol > 0 else None,
                    'avg_volume': avg_vol,
                    'high_52w': (close / float(hist['High'].max()) - 1),
                    # sessions since the 52w-high bar (2026-08-20, Andy: "特别是
                    # 出新52wh后回撤的" -- the high-after-pullback archetype needs
                    # to know the high is FRESH, which the distance alone cannot say)
                    'days_since_52wh': int(n - 1 - int(hist['High'].values.argmax())),
                    # tightness family (2026-08-20 study: every variant carries
                    # positive edge; weekly tight = offense, daily coil = defense)
                    'wk_tight_3': (lambda w: bool(len(w) >= 3 and (w.iloc[-3:].max() - w.iloc[-3:].min()) / w.iloc[-1] <= 0.015))(hist['Close'].resample('W-FRI').last().dropna()),
                    'range5_pct': float((hist['High'].iloc[-5:].max() - hist['Low'].iloc[-5:].min()) / close * 100) if n >= 5 and close else None,
                    'dist_hi20_pct': float((close / hist['Close'].iloc[-20:].max() - 1) * 100) if n >= 20 else None,
                    'low_52w': (close / float(hist['Low'].min()) - 1),
                    'from_open_pct': from_open_pct,
                    'perf_5d': perf_5d,
                    'dcr_pct': dcr_pct,
                    'pocket_pivot': pp,
                    'pp_count_30d': pp_count,
                    'pp_count_10d': pp_count_10,
                    'vol10_green': v10,
                    'vol10_green_count_10d': v10_count_10,
                    'vol10_green_count_30d': v10_count_30,
                    'trend_base': trend_base,
                    'vcs': vcs,
                    **sp_row,
                    'ti65': sb['ti65'], 'mdt': sb['mdt'], 'min_vol_3d': sb['min_vol_3d'],
                    'ad_ratio_20': af['ad_ratio_20'], 'cmf21': af['cmf21'],
                    'ema21_low_dist': ema21_low_dist,
                    'ema21': ema21,
                    'rs_line_pctl_21': rs_line_pctl_21,
                    'rs_line_pctl_63': rs_line_pctl_63,
                    'rs_line_pctl_126': rs_line_pctl_126,
                    'atr_pctl_252': atr_pctl_252,
                    'atr_pctl_63': atr_pctl_63,
                    'range5_pctl_252': range5_pctl_252,
                    'cross_ema21_up': cross_ema21_up,
                    'cross_sma50_up': cross_sma50_up,
                    'bar_date': bar_date, 'bars_stale': False, 'bar_scale_mismatch': False,
                    'ema10': ema10,
                    'ema20': ema20,
                    'wk_ema10': wk_ema10,
                    'wk_ema20': wk_ema20,
                    'bo_count_1m': bo_1m,
                    'bo_count_3m': bo_3m,
                    'bo_count_6m': bo_6m,
                    'bo_count_1y': bo_1y,
                }
            except Exception as e:
                logger.debug(f"  Enrich failed for {ticker}: {e}")

        logger.info(f"  Enriched {len(enriched)}/{len(all_data)} tickers")

        # Merge enriched data back into universe
        enrich_df = pd.DataFrame.from_dict(enriched, orient='index')
        enrich_df.index.name = 'ticker'
        enrich_df = enrich_df.reset_index()

        # Update: only overwrite columns that are currently None/NaN
        for col in enrich_df.columns:
            if col == 'ticker':
                continue
            if col in universe.columns:
                # Merge on ticker, fill missing values from enrichment
                mapping = enrich_df.set_index('ticker')[col]
                mask = universe[col].isna()
                universe.loc[mask, col] = universe.loc[mask, 'ticker'].map(mapping)
            else:
                universe[col] = universe['ticker'].map(
                    enrich_df.set_index('ticker')[col]
                )

        return universe

    def fetch_ma_data(self, tickers: list[str] = None, return_history: bool = False,
                      history_period: str = '1y'):
        """Calculate MA data for Power 3 Signal and Trend Status.
        Per plan.md §2.4 fetch_ma_data.

        With ``return_history=True`` returns ``(signals, histories)`` where
        ``histories`` maps ticker -> full downloaded OHLC DataFrame covering
        ``history_period``.
        """
        if tickers is None:
            tickers = ['SPY', 'QQQ', 'IWM', 'RSP', '^GSPC']

        signals = {}
        histories = {}
        for ticker in tickers:
            try:
                hist = _flatten_yf_columns(yf.download(ticker, period=history_period, progress=False))
                if len(hist) < 200:
                    logger.warning(f"{ticker}: insufficient history ({len(hist)} rows)")
                    continue
                histories[ticker] = hist

                close = float(hist['Close'].iloc[-1])

                ema8 = float(hist['Close'].ewm(span=8).mean().iloc[-1])
                ema21 = float(hist['Close'].ewm(span=21).mean().iloc[-1])
                sma50 = float(hist['Close'].rolling(50).mean().iloc[-1])
                sma200 = float(hist['Close'].rolling(200).mean().iloc[-1])
                sma20 = float(hist['Close'].rolling(20).mean().iloc[-1])

                # Power 3 Signal: EMA8 > EMA21 > SMA50 (and all above SMA200)
                power_3 = ema8 > ema21 > sma50 > sma200

                if power_3:
                    signal, color = "POWER_3", "green"
                elif ema8 > ema21 and close > sma200:
                    signal, color = "CAUTION", "yellow"
                elif close > sma200:
                    signal, color = "WARNING", "orange"
                else:
                    signal, color = "RISK_OFF", "red"

                # 52-week fields must stay 52-week regardless of how much
                # history the caller asked for. run_all now requests '3y' so the
                # replay book has depth; anchoring on the last 252 sessions keeps
                # the meaning of this field independent of history_period.
                close_52w = hist['Close'].tail(252)
                high_52w = float(close_52w.max())

                signals[ticker] = {
                    'signal': signal,
                    'color': color,
                    'close': close,
                    'ema8': ema8,
                    'ema21': ema21,
                    'sma50': sma50,
                    'sma200': sma200,
                    'sma20': sma20,
                    # Oratnek's Power Trend checks
                    'power_trend': {
                        '3d_gt_20sma': bool(hist['Close'].iloc[-3:].min() > sma20),
                        '3d_gt_50sma': bool(hist['Close'].iloc[-3:].min() > sma50),
                        '3d_gt_200sma': bool(hist['Close'].iloc[-3:].min() > sma200),
                        '20sma_gt_50sma': bool(sma20 > sma50),
                        '50sma_gt_200sma': bool(sma50 > sma200),
                    },
                    # Trend Status (Oratnek style)
                    'trend_status': {
                        '9ema_dist': round(float((close - hist['Close'].ewm(span=9).mean().iloc[-1]) / close * 100), 2),
                        '21ema_dist': round(float((close - ema21) / close * 100), 2),
                        '50sma_dist': round(float((close - sma50) / close * 100), 2),
                        '200sma_dist': round(float((close - sma200) / close * 100), 2),
                        '52w_high_dist': round(float((close - high_52w) / high_52w * 100), 2),
                    },
                }
            except Exception as e:
                logger.warning(f"Error fetching MA data for {ticker}: {e}")

        if return_history:
            return signals, histories
        return signals

    def fetch_ohlc(self, tickers: list[str], period: str = '90d') -> dict:
        """Fetch OHLC for VCP Layer 2 detection."""
        result = {}
        logger.info(f"Fetching OHLC for {len(tickers)} tickers, period={period}")

        data = yf.download(tickers, period=period, group_by='ticker',
                           progress=False, threads=True)

        for ticker in tickers:
            try:
                if len(tickers) == 1:
                    df = _flatten_yf_columns(data)
                    result[ticker] = df[['Open', 'High', 'Low', 'Close', 'Volume']]
                else:
                    df = data[ticker][['Open', 'High', 'Low', 'Close', 'Volume']].dropna()
                    result[ticker] = df
            except Exception:
                pass

        logger.info(f"Got OHLC for {len(result)}/{len(tickers)} tickers")
        return result
