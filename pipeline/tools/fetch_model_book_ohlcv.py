"""
Fetch ~18 months of OHLCV data for each model book entry and save as
lightweight-charts-compatible JSON.

Usage:
    python -m pipeline.tools.fetch_model_book_ohlcv

Reads  : frontend/public/data/modelbooks/index.json
Writes : frontend/public/data/modelbooks/ohlcv/{entry-id}.json
         frontend/public/data/modelbooks/ohlcv/spy-{year}.json
Updates: index.json with ohlcv_file, gain_pct, duration_days per entry
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import yfinance as yf

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[2]
INDEX_PATH = ROOT / "frontend" / "public" / "data" / "modelbooks" / "index.json"
OHLCV_DIR = ROOT / "frontend" / "public" / "data" / "modelbooks" / "ohlcv"

# Map model-book tickers to yfinance symbols where possible.
# Many historical tickers (Chrysler, Houston Oil, PeopleSoft, AccuStaff, JDSU)
# are no longer on yfinance — they will simply be skipped.
TICKER_MAP: dict[str, str | None] = {
    "Chrysler": None,       # Delisted, acquired by Fiat
    "Houston Oil": None,    # Acquired 1980s
    "PeopleSoft": None,     # Acquired by Oracle 2005
    "AccuStaff": None,      # Now MPS Group, long delisted
    "JDSU": "VIAV",         # Renamed to Viavi Solutions (but year 1998 data unavailable)
    # Modern tickers map to themselves
}

# T-0925-63: entries whose default (auto_adjust=True, 2dp) fetch collapses
# into flat_share > 50% bars — decades of splits back-adjust their 1980s-era
# cent-level prices into sub-penny noise that rounds to a single value on
# most sessions (see flag-modelbook-outliers.mjs LOW RESOLUTION rule).
# auto_adjust=False (nominal traded price, no dividend/split back-adjustment)
# plus 4dp instead of 2dp recovers real intraday range for both — verified
# against yfinance directly: MSFT 1986 and CSCO 1990 go from 67-82% flat to
# 0% flat. HD 1982 improves (92% -> 79%) but stays above the threshold even
# at full float precision — its 1981-82 Yahoo bars record O=H=L=C on most
# sessions regardless of adjustment or rounding, which is a genuine gap in
# the underlying source for that era, not a rounding artifact.
# NOT the default for every entry: a ticker with a real split *inside* its
# fetch window would show a fake price-cliff under auto_adjust=False (a stock
# doesn't 10x jump — the JUMP_MAX rule would wrongly exclude it). HD/MSFT/CSCO
# have no splits inside their 18-month windows (first splits: HD 1983-08,
# MSFT 1987-09, CSCO 1991) so this is safe for exactly these three.
UNADJUSTED_PRECISE_IDS: set[str] = {"oneil-home-1982", "oneil-msft-1986", "oneil-csco-1990"}


def _yf_symbol(ticker: str) -> str | None:
    """Return the yfinance-downloadable symbol, or None if unavailable."""
    if ticker in TICKER_MAP:
        return TICKER_MAP[ticker]
    return ticker  # Assume modern ticker is valid as-is


def _flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Flatten yfinance MultiIndex columns (single-ticker downloads)."""
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df


def _fetch_ohlcv(symbol: str, start: str, end: str, auto_adjust: bool = True) -> pd.DataFrame | None:
    """Download OHLCV from yfinance. Returns a cleaned DataFrame or None."""
    try:
        df = yf.download(symbol, start=start, end=end, auto_adjust=auto_adjust, progress=False)
        if df is None or df.empty:
            return None
        df = _flatten_columns(df)
        df = df[["Open", "High", "Low", "Close", "Volume"]].dropna()
        if len(df) < 10:
            return None
        return df
    except Exception as e:
        logger.warning(f"  yfinance error for {symbol}: {e}")
        return None


def _df_to_lw_records(df: pd.DataFrame, precision: int = 2) -> list[dict]:
    """Convert OHLCV DataFrame to lightweight-charts format."""
    records = []
    for ts, row in df.iterrows():
        records.append({
            "time": ts.strftime("%Y-%m-%d"),
            "open": round(float(row["Open"]), precision),
            "high": round(float(row["High"]), precision),
            "low": round(float(row["Low"]), precision),
            "close": round(float(row["Close"]), precision),
            "volume": int(row["Volume"]),
        })
    return records


def _compute_gain_and_duration(records: list[dict]) -> tuple[float | None, int | None]:
    """Compute gain_pct (min-close to max-close-after-min) and duration_days.

    This measures the best trough-to-peak move in the data window,
    which approximates the stock's big move for model book purposes.
    """
    if len(records) < 2:
        return None, None

    closes = [r["close"] for r in records]
    dates = [r["time"] for r in records]

    # Find the index of the minimum close
    min_idx = 0
    min_close = closes[0]
    for i, c in enumerate(closes):
        if c < min_close:
            min_close = c
            min_idx = i

    # Find the maximum close AFTER the minimum
    max_close = min_close
    max_idx = min_idx
    for i in range(min_idx, len(closes)):
        if closes[i] > max_close:
            max_close = closes[i]
            max_idx = i

    if min_close <= 0 or max_idx == min_idx:
        return None, None

    gain_pct = round((max_close - min_close) / min_close * 100, 1)

    d_min = datetime.strptime(dates[min_idx], "%Y-%m-%d")
    d_max = datetime.strptime(dates[max_idx], "%Y-%m-%d")
    duration_days = (d_max - d_min).days

    return gain_pct, duration_days


def _date_range_for_year(year: int) -> tuple[str, str]:
    """Return ~18-month window centered around the entry year.
    Start: Jul 1 of prior year.  End: Dec 31 of entry year.
    """
    start = f"{year - 1}-07-01"
    end = f"{year}-12-31"
    return start, end


def main() -> None:
    if not INDEX_PATH.exists():
        logger.error(f"index.json not found at {INDEX_PATH}")
        sys.exit(1)

    OHLCV_DIR.mkdir(parents=True, exist_ok=True)

    with open(INDEX_PATH) as f:
        entries = json.load(f)

    logger.info(f"Loaded {len(entries)} model book entries")

    # Collect unique years for SPY fetching
    spy_years: set[int] = set()
    updated = False

    for entry in entries:
        entry_id = entry["id"]
        ticker = entry["ticker"]
        year = entry["year"]
        spy_years.add(year)

        ohlcv_path = OHLCV_DIR / f"{entry_id}.json"

        # Skip if already fetched (idempotent)
        if ohlcv_path.exists():
            logger.info(f"  SKIP {entry_id} — OHLCV file already exists")
            # Ensure index fields are set even for pre-existing files
            if "ohlcv_file" not in entry:
                entry["ohlcv_file"] = f"ohlcv/{entry_id}.json"
                with open(ohlcv_path) as f:
                    records = json.load(f)
                gain_pct, duration_days = _compute_gain_and_duration(records)
                entry["gain_pct"] = gain_pct
                entry["duration_days"] = duration_days
                updated = True
            continue

        symbol = _yf_symbol(ticker)
        if symbol is None:
            logger.warning(f"  SKIP {entry_id} — no yfinance symbol for '{ticker}'")
            continue

        start, end = _date_range_for_year(year)
        precise = entry_id in UNADJUSTED_PRECISE_IDS
        logger.info(f"  FETCH {entry_id}: {symbol} {start} → {end}" + ("  [unadjusted/4dp]" if precise else ""))

        df = _fetch_ohlcv(symbol, start, end, auto_adjust=not precise)
        if df is None:
            logger.warning(f"  FAIL {entry_id} — no data returned for {symbol}")
            continue

        records = _df_to_lw_records(df, precision=4 if precise else 2)
        with open(ohlcv_path, "w") as f:
            json.dump(records, f, separators=(",", ":"))
        logger.info(f"  SAVED {entry_id}: {len(records)} bars → {ohlcv_path.name}")

        # Compute stats
        gain_pct, duration_days = _compute_gain_and_duration(records)
        entry["ohlcv_file"] = f"ohlcv/{entry_id}.json"
        entry["gain_pct"] = gain_pct
        entry["duration_days"] = duration_days
        updated = True

    # Fetch SPY for each unique year
    for year in sorted(spy_years):
        spy_path = OHLCV_DIR / f"spy-{year}.json"
        if spy_path.exists():
            logger.info(f"  SKIP SPY-{year} — already exists")
            continue

        start, end = _date_range_for_year(year)
        logger.info(f"  FETCH SPY-{year}: {start} → {end}")

        df = _fetch_ohlcv("SPY", start, end)
        if df is None:
            logger.warning(f"  FAIL SPY-{year} — no data returned")
            continue

        records = _df_to_lw_records(df)
        with open(spy_path, "w") as f:
            json.dump(records, f, separators=(",", ":"))
        logger.info(f"  SAVED spy-{year}.json: {len(records)} bars")

    # Write updated index.json
    if updated:
        with open(INDEX_PATH, "w") as f:
            json.dump(entries, f, indent=2)
            f.write("\n")
        logger.info("Updated index.json with ohlcv_file / gain_pct / duration_days")

    logger.info("Done.")


if __name__ == "__main__":
    main()
