"""
Import big movers data from Will's GitHub project and convert to
lightweight-charts-compatible JSON for the model books page.

Downloads:
  - big_movers_result.csv  (master list of big moves)
  - collected_stocks/*.csv  (OHLCV data per symbol)
  - SPY Historical Data.csv (SPY benchmark)

Writes:
  - frontend/public/data/modelbooks/ohlcv/{symbol}-{year}.json
  - frontend/public/data/modelbooks/ohlcv/spy-{year}.json
  - Merges entries into frontend/public/data/modelbooks/index.json

Usage:
    python -m pipeline.tools.import_big_movers
"""

import csv
import io
import json
import logging
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from pathlib import Path

import requests

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[2]
INDEX_PATH = ROOT / "frontend" / "public" / "data" / "modelbooks" / "index.json"
OHLCV_DIR = ROOT / "frontend" / "public" / "data" / "modelbooks" / "ohlcv"

REPO_RAW = "https://raw.githubusercontent.com/willhjw/big_movers/main"
REPO_API = "https://api.github.com/repos/willhjw/big_movers"

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "fluxus-import"})


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _business_days(start_str: str, end_str: str) -> int:
    """Count business days between two YYYY-MM-DD date strings."""
    start = datetime.strptime(start_str, "%Y-%m-%d")
    end = datetime.strptime(end_str, "%Y-%m-%d")
    count = 0
    current = start
    while current <= end:
        if current.weekday() < 5:
            count += 1
        current += timedelta(days=1)
    return count


def _parse_date(s: str) -> datetime:
    """Parse date string in YYYY-MM-DD format."""
    return datetime.strptime(s.strip(), "%Y-%m-%d")


def _parse_spy_date(s: str) -> datetime:
    """Parse SPY date string in MM/DD/YYYY format."""
    return datetime.strptime(s.strip(), "%m/%d/%Y")


def _ohlcv_to_lw(rows: list[dict]) -> list[dict]:
    """Convert parsed CSV rows to lightweight-charts records."""
    records = []
    for row in rows:
        try:
            records.append({
                "time": row["date"],
                "open": round(float(row["open"]), 4),
                "high": round(float(row["high"]), 4),
                "low": round(float(row["low"]), 4),
                "close": round(float(row["close"]), 4),
                "volume": int(float(row["volume"])),
            })
        except (ValueError, KeyError):
            continue
    return records


# ---------------------------------------------------------------------------
# Download functions
# ---------------------------------------------------------------------------

def fetch_big_movers_csv() -> list[dict]:
    """Download and parse big_movers_result.csv."""
    url = f"{REPO_RAW}/big_movers_result.csv"
    logger.info(f"Downloading big_movers_result.csv ...")
    resp = SESSION.get(url, timeout=30)
    resp.raise_for_status()

    # Handle BOM
    text = resp.text.lstrip("\ufeff")
    reader = csv.DictReader(io.StringIO(text))
    entries = []
    for row in reader:
        try:
            entries.append({
                "year": int(row["year"]),
                "symbol": row["symbol"].strip(),
                "gain_pct": round(float(row["gain_pct"]), 1),
                "low_date": row["low_date"].strip(),
                "high_date": row["high_date"].strip(),
                "low_price": float(row["low_price"]),
                "high_price": float(row["high_price"]),
            })
        except (ValueError, KeyError) as e:
            logger.warning(f"  Skipping malformed row: {e}")
    logger.info(f"  Parsed {len(entries)} big mover entries")
    return entries


def fetch_available_csvs() -> set[str]:
    """Get the set of available CSV filenames in collected_stocks/ via GitHub API."""
    logger.info("Fetching repo tree for collected_stocks/ file list ...")
    url = f"{REPO_API}/git/trees/main?recursive=1"
    resp = SESSION.get(url, timeout=30)
    resp.raise_for_status()
    tree = resp.json()["tree"]
    files = set()
    for item in tree:
        path = item["path"]
        if path.startswith("collected_stocks/") and path.endswith(".csv"):
            # Extract just the filename without extension
            fname = path.split("/")[-1]
            symbol = fname.replace(".csv", "")
            files.add(symbol)
    logger.info(f"  Found {len(files)} OHLCV CSVs available")
    return files


def download_stock_csv(symbol: str) -> str | None:
    """Download a single stock CSV. Returns raw text or None on failure."""
    url = f"{REPO_RAW}/collected_stocks/{symbol}.csv"
    try:
        resp = SESSION.get(url, timeout=30)
        if resp.status_code == 200:
            return resp.text
        return None
    except requests.RequestException:
        return None


def parse_stock_csv(text: str, start_date: str, end_date: str) -> list[dict]:
    """Parse a collected_stocks CSV and filter to date range.

    CSV format: Unnamed: 0, DateTime, Open, High, Low, Close, Volume
    """
    reader = csv.DictReader(io.StringIO(text))
    rows = []
    for row in reader:
        try:
            dt = row["DateTime"].strip()
            d = _parse_date(dt)
            if start_date <= dt <= end_date:
                rows.append({
                    "date": dt,
                    "open": row["Open"],
                    "high": row["High"],
                    "low": row["Low"],
                    "close": row["Close"],
                    "volume": row["Volume"],
                })
        except (ValueError, KeyError):
            continue
    # Sort by date
    rows.sort(key=lambda r: r["date"])
    return rows


def download_spy_csv() -> str | None:
    """Download SPY Historical Data CSV."""
    url = f"{REPO_RAW}/SPY%20Historical%20Data.csv"
    logger.info("Downloading SPY Historical Data.csv ...")
    try:
        resp = SESSION.get(url, timeout=30)
        if resp.status_code == 200:
            logger.info(f"  SPY CSV: {len(resp.text)} bytes")
            return resp.text
        logger.warning(f"  SPY download failed: HTTP {resp.status_code}")
        return None
    except requests.RequestException as e:
        logger.warning(f"  SPY download error: {e}")
        return None


def parse_spy_csv(text: str) -> dict[str, list[dict]]:
    """Parse SPY CSV and group by year.

    SPY CSV format: DateTime (MM/DD/YYYY), Open, High, Low, Close, Volume
    Returns dict: year_str -> list of {date, open, high, low, close, volume}
    """
    reader = csv.DictReader(io.StringIO(text))
    by_year: dict[str, list[dict]] = {}
    for row in reader:
        try:
            dt = _parse_spy_date(row["DateTime"])
            date_str = dt.strftime("%Y-%m-%d")
            year_str = str(dt.year)
            if year_str not in by_year:
                by_year[year_str] = []
            by_year[year_str].append({
                "date": date_str,
                "open": row["Open"],
                "high": row["High"],
                "low": row["Low"],
                "close": row["Close"],
                "volume": row["Volume"],
            })
        except (ValueError, KeyError):
            continue
    # Sort each year
    for year in by_year:
        by_year[year].sort(key=lambda r: r["date"])
    return by_year


# ---------------------------------------------------------------------------
# Batch downloader
# ---------------------------------------------------------------------------

def batch_download_stocks(
    symbols: list[str], max_workers: int = 20
) -> dict[str, str]:
    """Download multiple stock CSVs in parallel. Returns {symbol: csv_text}."""
    results = {}
    total = len(symbols)
    done = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_sym = {
            executor.submit(download_stock_csv, sym): sym for sym in symbols
        }
        for future in as_completed(future_to_sym):
            sym = future_to_sym[future]
            done += 1
            try:
                text = future.result()
                if text:
                    results[sym] = text
                if done % 50 == 0 or done == total:
                    logger.info(f"  Downloaded {done}/{total} CSVs ({len(results)} successful)")
            except Exception as e:
                logger.warning(f"  Error downloading {sym}: {e}")

    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    OHLCV_DIR.mkdir(parents=True, exist_ok=True)

    # Load existing index
    if INDEX_PATH.exists():
        with open(INDEX_PATH) as f:
            existing_entries = json.load(f)
    else:
        existing_entries = []

    # Build set of existing ticker+year combos (to avoid overwriting curated entries)
    existing_keys: set[str] = set()
    for entry in existing_entries:
        key = f"{entry['ticker'].upper()}-{entry['year']}"
        existing_keys.add(key)
    logger.info(f"Existing index has {len(existing_entries)} entries ({len(existing_keys)} unique ticker-year combos)")

    # 1. Download big_movers_result.csv
    big_movers = fetch_big_movers_csv()

    # 2. Get list of available CSVs
    available_csvs = fetch_available_csvs()

    # 3. Determine which symbols we need to download
    # Group big_movers entries by symbol for efficient downloading
    symbols_needed: dict[str, list[dict]] = {}
    skipped_existing = 0
    skipped_no_csv = 0

    for bm in big_movers:
        symbol = bm["symbol"]
        year = bm["year"]
        entry_key = f"{symbol.upper()}-{year}"

        # Skip if curated entry already exists with this ticker+year
        if entry_key in existing_keys:
            skipped_existing += 1
            continue

        # Skip if no OHLCV CSV available
        if symbol not in available_csvs:
            skipped_no_csv += 1
            continue

        ohlcv_filename = f"{symbol.lower()}-{year}.json"
        ohlcv_path = OHLCV_DIR / ohlcv_filename

        # Skip if OHLCV already downloaded (idempotent)
        if ohlcv_path.exists():
            # Still need to add to index if not there yet
            entry_id = f"bigmovers-{symbol.lower()}-{year}"
            if entry_id not in {e["id"] for e in existing_entries}:
                duration = _business_days(bm["low_date"], bm["high_date"])
                existing_entries.append({
                    "id": entry_id,
                    "ticker": symbol,
                    "year": year,
                    "source": "Big Movers",
                    "patterns": [],
                    "key_lessons": [],
                    "outcome": f"{bm['gain_pct']}% in {duration} days",
                    "gain_pct": bm["gain_pct"],
                    "duration_days": duration,
                    "ohlcv_file": f"ohlcv/{ohlcv_filename}",
                })
            continue

        if symbol not in symbols_needed:
            symbols_needed[symbol] = []
        symbols_needed[symbol].append(bm)

    logger.info(f"Skipped {skipped_existing} entries (existing curated match)")
    logger.info(f"Skipped {skipped_no_csv} entries (no OHLCV CSV available)")
    logger.info(f"Need to download {len(symbols_needed)} unique symbol CSVs")

    # 4. Batch download all needed CSVs
    if symbols_needed:
        csv_data = batch_download_stocks(list(symbols_needed.keys()), max_workers=20)
        logger.info(f"Successfully downloaded {len(csv_data)} CSVs")
    else:
        csv_data = {}

    # 5. Process each big mover entry
    new_entries = 0
    ohlcv_files_created = 0
    failures = 0

    for symbol, bm_list in symbols_needed.items():
        if symbol not in csv_data:
            failures += len(bm_list)
            continue

        raw_csv = csv_data[symbol]

        for bm in bm_list:
            year = bm["year"]
            entry_id = f"bigmovers-{symbol.lower()}-{year}"
            ohlcv_filename = f"{symbol.lower()}-{year}.json"
            ohlcv_path = OHLCV_DIR / ohlcv_filename

            # Compute date range: 6 months before low_date to 3 months after high_date
            low_dt = _parse_date(bm["low_date"])
            high_dt = _parse_date(bm["high_date"])
            start_dt = low_dt - timedelta(days=180)
            end_dt = high_dt + timedelta(days=90)
            start_str = start_dt.strftime("%Y-%m-%d")
            end_str = end_dt.strftime("%Y-%m-%d")

            rows = parse_stock_csv(raw_csv, start_str, end_str)
            if len(rows) < 10:
                logger.warning(f"  SKIP {entry_id}: only {len(rows)} bars in range")
                failures += 1
                continue

            records = _ohlcv_to_lw(rows)
            with open(ohlcv_path, "w") as f:
                json.dump(records, f, separators=(",", ":"))
            ohlcv_files_created += 1

            duration = _business_days(bm["low_date"], bm["high_date"])
            existing_entries.append({
                "id": entry_id,
                "ticker": symbol,
                "year": year,
                "source": "Big Movers",
                "patterns": [],
                "key_lessons": [],
                "outcome": f"{bm['gain_pct']}% in {duration} days",
                "gain_pct": bm["gain_pct"],
                "duration_days": duration,
                "ohlcv_file": f"ohlcv/{ohlcv_filename}",
            })
            new_entries += 1

    logger.info(f"Created {ohlcv_files_created} OHLCV files, {new_entries} new index entries, {failures} failures")

    # 6. SPY data for all unique years
    spy_years_needed: set[int] = set()
    for entry in existing_entries:
        y = entry.get("year")
        if y:
            spy_path = OHLCV_DIR / f"spy-{y}.json"
            if not spy_path.exists():
                spy_years_needed.add(y)

    if spy_years_needed:
        logger.info(f"Need SPY data for years: {sorted(spy_years_needed)}")
        spy_text = download_spy_csv()
        if spy_text:
            spy_by_year = parse_spy_csv(spy_text)
            spy_created = 0
            for year in sorted(spy_years_needed):
                spy_path = OHLCV_DIR / f"spy-{year}.json"
                year_str = str(year)

                # For SPY, we want the full year + 6 months before
                # Gather data from prior year July through end of year
                prior_year = str(year - 1)
                rows = []
                if prior_year in spy_by_year:
                    rows.extend(
                        r for r in spy_by_year[prior_year]
                        if r["date"] >= f"{year - 1}-07-01"
                    )
                if year_str in spy_by_year:
                    rows.extend(spy_by_year[year_str])
                rows.sort(key=lambda r: r["date"])

                if len(rows) < 10:
                    logger.warning(f"  SKIP spy-{year}: only {len(rows)} bars")
                    continue

                records = _ohlcv_to_lw(rows)
                with open(spy_path, "w") as f:
                    json.dump(records, f, separators=(",", ":"))
                spy_created += 1
                logger.info(f"  SAVED spy-{year}.json: {len(records)} bars")
            logger.info(f"Created {spy_created} SPY files")
        else:
            logger.warning("Could not download SPY data, skipping SPY files")

    # 7. Write updated index.json
    # Sort: curated sources first, then big movers by gain_pct descending
    source_order = {"O'Neil": 0, "Minervini": 1, "Zanger": 2, "General": 3, "Big Movers": 4}
    existing_entries.sort(
        key=lambda e: (
            source_order.get(e.get("source", ""), 5),
            -(e.get("gain_pct") or 0),
        )
    )

    with open(INDEX_PATH, "w") as f:
        json.dump(existing_entries, f, indent=2)
        f.write("\n")
    logger.info(f"Wrote {len(existing_entries)} total entries to index.json")
    logger.info("Done.")


if __name__ == "__main__":
    main()
