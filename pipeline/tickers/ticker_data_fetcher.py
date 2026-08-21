"""Fetch per-ticker fundamentals + analyst + earnings data via yfinance.

Writes one JSON file per ticker to data/output/tickers/<SYM>.json.

This is Layer 1 (numeric, deterministic). Layer 2 (AI narrative synthesis —
Bull/Bear, Trade Plan, Management commentary) is handled separately by the
/tearsheet Claude Code slash command.

yfinance is rate-limited and sometimes returns missing/stale fields. We
gracefully fall back to None for missing data rather than crashing.
"""
from __future__ import annotations

import json
import logging
import math
from datetime import datetime, date
from pathlib import Path
from typing import Any, Optional

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)

OUTPUT_DIR = Path('data/output/tickers')


# ── helpers ────────────────────────────────────────────────────────────────

def _safe(value: Any) -> Any:
    """Convert pandas/numpy types to JSON-safe primitives. NaN → None."""
    if value is None:
        return None
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return float(value)
    if isinstance(value, (int, bool, str)):
        return value
    if isinstance(value, (pd.Timestamp, datetime, date)):
        return value.isoformat() if hasattr(value, 'isoformat') else str(value)
    try:
        # numpy scalars
        return value.item()
    except (AttributeError, ValueError):
        return str(value)


def _get(d: dict, key: str, default=None):
    v = d.get(key, default) if isinstance(d, dict) else default
    return _safe(v)


# ── info / valuation snapshot ──────────────────────────────────────────────

def fetch_info(tk: yf.Ticker) -> dict:
    """Return the curated subset of yfinance .info we care about."""
    info = {}
    try:
        info = tk.info or {}
    except Exception as e:  # noqa: BLE001
        logger.warning(f"info fetch failed: {e}")
        return {}

    return {
        'symbol': info.get('symbol'),
        'longName': info.get('longName') or info.get('shortName'),
        'sector': info.get('sector'),
        'industry': info.get('industry'),
        'exchange': info.get('exchange') or info.get('fullExchangeName'),
        'country': info.get('country'),
        'city': info.get('city'),
        'website': info.get('website'),
        'fullTimeEmployees': _get(info, 'fullTimeEmployees'),
        'marketCap': _get(info, 'marketCap'),
        'enterpriseValue': _get(info, 'enterpriseValue'),
        'trailingPE': _get(info, 'trailingPE'),
        'forwardPE': _get(info, 'forwardPE'),
        'priceToSalesTrailing12Months': _get(info, 'priceToSalesTrailing12Months'),
        'enterpriseToRevenue': _get(info, 'enterpriseToRevenue'),
        'priceToBook': _get(info, 'priceToBook'),
        'grossMargins': _get(info, 'grossMargins'),
        'operatingMargins': _get(info, 'operatingMargins'),
        'profitMargins': _get(info, 'profitMargins'),
        'returnOnEquity': _get(info, 'returnOnEquity'),
        'totalCash': _get(info, 'totalCash'),
        'totalDebt': _get(info, 'totalDebt'),
        'totalRevenue': _get(info, 'totalRevenue'),
        'freeCashflow': _get(info, 'freeCashflow'),
        'debtToEquity': _get(info, 'debtToEquity'),
        'currentRatio': _get(info, 'currentRatio'),
        'fiftyTwoWeekHigh': _get(info, 'fiftyTwoWeekHigh'),
        'fiftyTwoWeekLow': _get(info, 'fiftyTwoWeekLow'),
        'averageVolume': _get(info, 'averageVolume'),
        'averageVolume10days': _get(info, 'averageVolume10days'),
        'beta': _get(info, 'beta'),
        'sharesOutstanding': _get(info, 'sharesOutstanding'),
        'sharesFloat': _get(info, 'floatShares'),
        'companyOfficers': _safe_officers(info.get('companyOfficers') or []),
    }


def _safe_officers(officers: list) -> list:
    """Subset of officer info for the Management section."""
    out = []
    for o in officers[:6]:
        out.append({
            'name': o.get('name'),
            'title': o.get('title'),
            'age': o.get('age'),
            'yearBorn': o.get('yearBorn'),
        })
    return out


# ── earnings ───────────────────────────────────────────────────────────────

def fetch_earnings_history(tk: yf.Ticker) -> list:
    """Last 4-8 reported quarters with actual vs estimate for Rev + EPS."""
    out: list = []
    try:
        hist = tk.earnings_history
        if hist is None or hist.empty:
            return out
        # earnings_history columns vary by yf version; try common ones
        for ts, row in hist.iterrows():
            r = {'period_end': _safe(ts)}
            for col_target, col_candidates in [
                ('eps_actual', ['epsActual', 'EPSActual']),
                ('eps_estimate', ['epsEstimate', 'EPSEstimate']),
                ('eps_surprise_pct', ['surprisePercent', 'epsDifference']),
            ]:
                for c in col_candidates:
                    if c in row.index:
                        r[col_target] = _safe(row[c]); break
            out.append(r)
        out.sort(key=lambda x: x.get('period_end') or '', reverse=True)
        return out[:8]
    except Exception as e:  # noqa: BLE001
        logger.debug(f"earnings_history fetch failed: {e}")
        return out


def fetch_next_earnings(tk: yf.Ticker) -> dict:
    """Upcoming earnings date + revenue/EPS estimate range if available."""
    out: dict = {}
    try:
        cal = tk.calendar
        if cal is None:
            return out
        if isinstance(cal, pd.DataFrame):
            d = {col: cal[col].iloc[0] for col in cal.columns}
        else:
            d = dict(cal)
        # common keys: 'Earnings Date', 'EPS Estimate', 'Revenue Estimate'
        for k, target in [
            ('Earnings Date', 'date'),
            ('EPS Estimate', 'eps_estimate'),
            ('Revenue Estimate', 'revenue_estimate'),
            ('Revenue Low', 'revenue_low'),
            ('Revenue High', 'revenue_high'),
        ]:
            if k in d:
                v = d[k]
                if isinstance(v, list) and v:
                    v = v[0]
                out[target] = _safe(v)
        return out
    except Exception as e:  # noqa: BLE001
        logger.debug(f"calendar fetch failed: {e}")
        return out


# ── quarterly financials ───────────────────────────────────────────────────

def fetch_quarterly_metrics(tk: yf.Ticker, n: int = 5) -> list:
    """Last N quarters: Revenue, YoY %, Gross Profit, GM%, Op Inc, EPS,
    Cash (balance sheet), Op CF (cash flow)."""
    out: list = []
    try:
        qf = tk.quarterly_financials
        qbs = tk.quarterly_balance_sheet
        qcf = tk.quarterly_cashflow
        if qf is None or qf.empty:
            return out
        # qf columns = periods (most recent first)
        periods = list(qf.columns)[:n + 4]  # extra for YoY lookup
        quarters: list[dict] = []
        for i, p in enumerate(periods):
            rev = qf.at['Total Revenue', p] if 'Total Revenue' in qf.index else None
            gp = qf.at['Gross Profit', p] if 'Gross Profit' in qf.index else None
            opinc = qf.at['Operating Income', p] if 'Operating Income' in qf.index else None
            eps = qf.at['Diluted EPS', p] if 'Diluted EPS' in qf.index else (
                qf.at['Basic EPS', p] if 'Basic EPS' in qf.index else None
            )
            cash = qbs.at['Cash And Cash Equivalents', p] if (
                qbs is not None and not qbs.empty and 'Cash And Cash Equivalents' in qbs.index and p in qbs.columns
            ) else None
            opcf = qcf.at['Operating Cash Flow', p] if (
                qcf is not None and not qcf.empty and 'Operating Cash Flow' in qcf.index and p in qcf.columns
            ) else None
            quarters.append({
                'period_end': _safe(p),
                'revenue': _safe(rev),
                'gross_profit': _safe(gp),
                'operating_income': _safe(opinc),
                'eps': _safe(eps),
                'cash': _safe(cash),
                'operating_cashflow': _safe(opcf),
                'gross_margin_pct': (
                    float(gp) / float(rev) * 100 if rev and gp and float(rev) > 0 else None
                ),
            })
        # Compute YoY (4 quarters back)
        for i in range(min(n, len(quarters))):
            cur = quarters[i]
            yoy_idx = i + 4
            if yoy_idx < len(quarters) and quarters[yoy_idx]['revenue'] and cur['revenue']:
                cur['yoy_pct'] = (cur['revenue'] / quarters[yoy_idx]['revenue'] - 1) * 100
            else:
                cur['yoy_pct'] = None
            out.append(cur)
        return out
    except Exception as e:  # noqa: BLE001
        logger.debug(f"quarterly_metrics fetch failed: {e}")
        return out


# ── analyst sentiment ──────────────────────────────────────────────────────

def fetch_analyst(tk: yf.Ticker) -> dict:
    """Consensus, ratings split, price targets, recent rating changes."""
    out: dict = {}
    try:
        rec = tk.recommendations
        if rec is not None and not rec.empty:
            # Most recent row aggregated
            latest = rec.iloc[-1] if hasattr(rec, 'iloc') else None
            if latest is not None and 'strongBuy' in latest.index:
                strong_buy = int(latest.get('strongBuy', 0) or 0)
                buy = int(latest.get('buy', 0) or 0)
                hold = int(latest.get('hold', 0) or 0)
                sell = int(latest.get('sell', 0) or 0)
                strong_sell = int(latest.get('strongSell', 0) or 0)
                total = strong_buy + buy + hold + sell + strong_sell
                consensus = None
                if total > 0:
                    score = (strong_buy * 5 + buy * 4 + hold * 3 + sell * 2 + strong_sell * 1) / total
                    consensus = ('Strong Buy' if score >= 4.5 else
                                 'Buy' if score >= 3.5 else
                                 'Hold' if score >= 2.5 else
                                 'Sell' if score >= 1.5 else 'Strong Sell')
                out['consensus'] = consensus
                out['total_ratings'] = total
                out['bullish'] = strong_buy + buy
                out['neutral'] = hold
                out['bearish'] = sell + strong_sell
    except Exception as e:  # noqa: BLE001
        logger.debug(f"recommendations fetch failed: {e}")

    try:
        pt = tk.analyst_price_targets
        if pt is not None:
            if isinstance(pt, dict):
                out['avg_price_target'] = _safe(pt.get('mean'))
                out['high_price_target'] = _safe(pt.get('high'))
                out['low_price_target'] = _safe(pt.get('low'))
                out['current_price'] = _safe(pt.get('current'))
    except Exception as e:  # noqa: BLE001
        logger.debug(f"analyst_price_targets fetch failed: {e}")

    # Recent rating changes (last 60d)
    try:
        upgrades = tk.upgrades_downgrades
        if upgrades is not None and not upgrades.empty:
            recent = upgrades.head(10)
            out['recent_rating_changes'] = [
                {
                    'date': _safe(row.name) if hasattr(row, 'name') else _safe(ts),
                    'firm': row.get('Firm') or row.get('firm'),
                    'to_grade': row.get('ToGrade') or row.get('toGrade'),
                    'from_grade': row.get('FromGrade') or row.get('fromGrade'),
                    'action': row.get('Action') or row.get('action'),
                }
                for ts, row in recent.iterrows()
            ]
    except Exception as e:  # noqa: BLE001
        logger.debug(f"upgrades_downgrades fetch failed: {e}")

    return out


# ── news ───────────────────────────────────────────────────────────────────

def fetch_news(tk: yf.Ticker, n: int = 10) -> list:
    """Most recent news headlines + URLs."""
    out: list = []
    try:
        news = tk.news or []
        for item in news[:n]:
            content = item.get('content', item)
            pub = content.get('pubDate') or content.get('providerPublishTime')
            if isinstance(pub, (int, float)):
                pub = datetime.fromtimestamp(pub).isoformat()
            out.append({
                'date': _safe(pub),
                'title': content.get('title'),
                'url': (
                    content.get('canonicalUrl', {}).get('url')
                    if isinstance(content.get('canonicalUrl'), dict)
                    else content.get('link')
                ),
                'source': (
                    content.get('provider', {}).get('displayName')
                    if isinstance(content.get('provider'), dict)
                    else content.get('publisher')
                ),
            })
    except Exception as e:  # noqa: BLE001
        logger.debug(f"news fetch failed: {e}")
    return out


# ── options-implied move (for next earnings) ───────────────────────────────

def fetch_options_implied_move(tk: yf.Ticker, current_price: Optional[float]) -> Optional[float]:
    """Approximate implied move using nearest-expiry ATM straddle / spot."""
    if not current_price or current_price <= 0:
        return None
    try:
        expiries = list(tk.options or [])
        if not expiries:
            return None
        nearest = expiries[0]
        chain = tk.option_chain(nearest)
        calls = chain.calls
        puts = chain.puts
        if calls.empty or puts.empty:
            return None
        # nearest ATM strike
        calls = calls.assign(diff=(calls['strike'] - current_price).abs())
        puts = puts.assign(diff=(puts['strike'] - current_price).abs())
        atm_call = calls.loc[calls['diff'].idxmin()]
        atm_put = puts.loc[puts['diff'].idxmin()]
        # Use lastPrice; fall back to mid if needed
        c_price = atm_call.get('lastPrice') or 0
        p_price = atm_put.get('lastPrice') or 0
        straddle = float(c_price) + float(p_price)
        if straddle <= 0:
            return None
        return straddle / current_price
    except Exception as e:  # noqa: BLE001
        logger.debug(f"options_implied_move fetch failed: {e}")
        return None


# ── OHLC + computed technicals ─────────────────────────────────────────────

def fetch_ohlc_and_technicals(tk: yf.Ticker) -> dict:
    """Fetch 1y daily OHLC + compute key technical fields.

    Returns:
        {
          'ohlc': [{date, open, high, low, close, volume}, ...],
          'rsi14': float | None,
          'ma20': float | None,
          'ma50': float | None,
          'ma200': float | None,
          'high_20d': float, 'high_52w': float,
          'low_5d': float, 'low_10d': float, 'low_52w': float,
          'atr14_pct': float | None,
          'position_in_52w_range_pct': float | None,
        }
    """
    out: dict = {'ohlc': []}
    try:
        # Fetch 2y so point-in-time 200-SMA is computable at entries up to ~1y old
        # (powers the Diagnosis case-study cards). Technical *fields* below are still
        # computed on the trailing ~1y so 52w-range / MA / ATR semantics are unchanged.
        hist = tk.history(period='2y', auto_adjust=True)
        if hist is None or hist.empty:
            return out
        # Full 2y OHLC records (rounded to keep files compact)
        def _round(v):
            r = _safe(v)
            return round(r, 4) if isinstance(r, float) else r
        records = []
        for ts, row in hist.iterrows():
            records.append({
                'date': ts.date().isoformat(),
                'open': _round(row.get('Open')),
                'high': _round(row.get('High')),
                'low': _round(row.get('Low')),
                'close': _round(row.get('Close')),
                'volume': _safe(row.get('Volume')),
            })
        out['ohlc'] = records

        # Trailing ~1y window for the derived technical fields
        h = hist.iloc[-252:]
        closes = h['Close']
        highs = h['High']
        lows = h['Low']
        last_close = float(closes.iloc[-1])

        # Moving averages (use simple MAs to match TradingView/Stockbee convention)
        if len(closes) >= 20:
            out['ma20'] = float(closes.rolling(20).mean().iloc[-1])
        if len(closes) >= 50:
            out['ma50'] = float(closes.rolling(50).mean().iloc[-1])
        if len(closes) >= 200:
            out['ma200'] = float(closes.rolling(200).mean().iloc[-1])

        # RSI(14) — Wilder's smoothing
        delta = closes.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(alpha=1/14, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/14, adjust=False).mean()
        rs = avg_gain / avg_loss.replace(0, float('nan'))
        rsi = 100 - 100 / (1 + rs)
        out['rsi14'] = _safe(rsi.iloc[-1])

        # Recent highs / lows
        if len(highs) >= 20:
            out['high_20d'] = float(highs.iloc[-20:].max())
        if len(lows) >= 5:
            out['low_5d'] = float(lows.iloc[-5:].min())
        if len(lows) >= 10:
            out['low_10d'] = float(lows.iloc[-10:].min())
        out['high_52w'] = float(highs.max())
        out['low_52w'] = float(lows.min())

        # ATR(14) — TR-based, %
        tr1 = highs - lows
        tr2 = (highs - closes.shift(1)).abs()
        tr3 = (lows - closes.shift(1)).abs()
        import pandas as _pd  # noqa: F401
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(14, min_periods=1).mean().iloc[-1]
        if last_close > 0:
            out['atr14'] = float(atr)
            out['atr14_pct'] = float(atr / last_close * 100)

        # Position in 52W range (%)
        h52 = float(highs.max()); l52 = float(lows.min())
        if h52 > l52:
            out['position_in_52w_range_pct'] = (last_close - l52) / (h52 - l52) * 100
    except Exception as e:  # noqa: BLE001
        logger.debug(f"ohlc_and_technicals fetch failed: {e}")
    return out


# ── main entry ─────────────────────────────────────────────────────────────

def fetch_ticker_data(symbol: str) -> dict:
    """Fetch all L1 numeric data for one ticker. Returns the JSON dict."""
    logger.info(f"Fetching ticker data for {symbol}")
    tk = yf.Ticker(symbol)
    info = fetch_info(tk)
    current_price = None
    try:
        current_price = float(tk.fast_info.get('lastPrice') or tk.fast_info.get('regularMarketPrice') or 0)
    except Exception:
        pass

    technicals = fetch_ohlc_and_technicals(tk)
    out = {
        'ticker': symbol.upper(),
        'fetched_at': datetime.utcnow().isoformat(timespec='seconds') + 'Z',
        '_schema': 'v2',
        'current_price': current_price,
        'info': info,
        'earnings_history': fetch_earnings_history(tk),
        'next_earnings': fetch_next_earnings(tk),
        'quarterly_metrics': fetch_quarterly_metrics(tk),
        'analyst': fetch_analyst(tk),
        'news': fetch_news(tk),
        'options_implied_move': fetch_options_implied_move(tk, current_price),
        'technicals': {
            k: v for k, v in technicals.items() if k != 'ohlc'
        },
        'ohlc_2y': technicals.get('ohlc', []),
        'ohlc_1y': technicals.get('ohlc', [])[-252:],
        # Layer 2 (AI synthesis) goes here under 'ai_synthesis' when
        # /tearsheet <SYM> Claude Code slash command runs.
        'ai_synthesis': None,
        'ai_synthesized_at': None,
    }
    return out


def write_ticker_json(symbol: str, data: dict, output_dir: Path = OUTPUT_DIR) -> Optional[Path]:
    """A file with no bars must never be written: an empty shell overwrote
    MRNA's 501 bars twice (3a27e96 -> 71aae5a; DATA_CONTRACTS §七 [08-20]).
    No price data -> no write, whatever else was fetched -- the previous
    file (if any) stays, and the caller counts it as skipped."""
    if not data.get('ohlc_2y'):
        logger.warning(f"  {symbol}: no OHLC fetched — NOT writing (empty shells have no overwrite rights)")
        return None
    output_dir.mkdir(parents=True, exist_ok=True)
    safe = symbol.upper().replace('/', '_').replace('^', '_')
    path = output_dir / f'{safe}.json'
    with open(path, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    return path
