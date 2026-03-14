"""
Finviz data adapter — primary source for stock universe screening.
Strategy:
  1. Try CSV export (requires Finviz Elite)
  2. Fall back to scraping free HTML screener tables
Per plan.md §2.3.
"""
import io
import logging
import time
import re

import pandas as pd
import requests
from bs4 import BeautifulSoup

from .base_adapter import BaseAdapter, STANDARD_COLUMNS
from .utils import retry, parse_pct_string, parse_market_cap

logger = logging.getLogger(__name__)

# Finviz column name -> standard column name mapping
FINVIZ_COL_MAP = {
    'Ticker': 'ticker',
    'Price': 'close',
    'Change': 'change_pct',
    'Perf Week': 'perf_1w',
    'Perf Month': 'perf_1m',
    'Perf Quart': 'perf_3m',
    'Perf Half': 'perf_6m',
    'Perf Year': 'perf_1y',
    'Perf YTD': 'perf_ytd',
    'SMA20': 'sma20_dist',
    'SMA50': 'sma50_dist',
    'SMA200': 'sma200_dist',
    'ATR': 'atr',
    'Relative Volume': 'rel_volume',
    'Average Volume': 'avg_volume',
    'Volume': 'volume',
    'Market Cap': 'market_cap',
    'Sector': 'sector',
    'Industry': 'industry',
    '52W High': 'high_52w',
    '52W Low': 'low_52w',
    'EPS next Y': 'eps_growth_next_y',
    'EPS this Y': 'eps_growth_this_y',
    'Sales past 5Y': 'revenue_growth',
    # HTML scraper may use slightly different names
    'Rel Volume': 'rel_volume',
    'Avg Volume': 'avg_volume',
    'EPS next Y': 'eps_growth_next_y',
}

PCT_COLUMNS = [
    'change_pct', 'perf_1w', 'perf_1m', 'perf_3m',
    'perf_6m', 'perf_1y', 'perf_ytd', 'sma20_dist',
    'sma50_dist', 'sma200_dist', 'high_52w', 'low_52w',
    'eps_growth_next_y', 'eps_growth_this_y', 'revenue_growth',
]


class FinvizAdapter(BaseAdapter):
    """Primary data adapter using Finviz CSV or HTML scraping."""

    CSV_URL = "https://finviz.com/export.ashx"
    SCREENER_URL = "https://finviz.com/screener.ashx"
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                       'AppleWebKit/537.36 (KHTML, like Gecko) '
                       'Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }

    def fetch_universe(self) -> pd.DataFrame:
        """Fetch stock universe. Tries CSV export first, then HTML scraping."""
        # Strategy 1: CSV export (Finviz Elite)
        try:
            df = self._fetch_csv()
            if df is not None and len(df) > 100:
                logger.info(f"Finviz CSV export succeeded: {len(df)} rows")
                df = self._normalize(df)
                self.validate(df)
                return df
        except Exception as e:
            logger.info(f"Finviz CSV export unavailable (likely needs Elite): {e}")

        # Strategy 2: Scrape HTML screener tables (free tier)
        logger.info("Falling back to Finviz HTML scraping...")
        df = self._fetch_html_screener()
        if df is not None and len(df) > 0:
            logger.info(f"Finviz HTML scraping got {len(df)} rows")
            df = self._normalize(df)
            # Relax validation for HTML scraping (may get fewer rows per page)
            if len(df) >= 20:
                return df

        raise RuntimeError(
            "Finviz data unavailable. Both CSV export and HTML scraping failed. "
            "Pipeline will use yfinance fallback universe."
        )

    def _fetch_csv(self) -> pd.DataFrame | None:
        """Try CSV export endpoint (requires Finviz Elite)."""
        params = {'v': '152', 'f': 'cap_1.0to,ind_stocksonly', 'ft': '4'}
        resp = requests.get(self.CSV_URL, params=params,
                            headers=self.HEADERS, timeout=30)
        resp.raise_for_status()

        content_type = resp.headers.get('Content-Type', '')
        if 'text/html' in content_type or resp.text.strip().startswith('<!DOCTYPE'):
            return None  # Got HTML instead of CSV

        return pd.read_csv(io.StringIO(resp.text))

    def _fetch_html_screener(self) -> pd.DataFrame | None:
        """Scrape Finviz Overview (v=111) for ticker universe with basic info.

        Note: Performance (v=151) and Technical (v=161) views are JavaScript-
        rendered; their HTML always returns Overview columns regardless of the
        v= parameter.  Performance/technical data is enriched via yfinance in
        the pipeline orchestrator instead.

        Pages are 20 rows each; we paginate until no more rows.
        """
        base_params = {
            'f': 'cap_1.0to,ind_stocksonly',
            'ft': '4',
        }
        max_pages = 150  # safety cap (~3000 stocks)

        session = requests.Session()
        session.headers.update(self.HEADERS)

        df = self._scrape_view(session, '111', base_params, max_pages)
        if df is not None and len(df) > 0:
            logger.info(f"Overview (v=111): scraped {len(df)} rows")
        return df

    # -----------------------------------------------------------------
    #  Helper: scrape one Finviz view across all pages
    # -----------------------------------------------------------------
    def _scrape_view(
        self,
        session: requests.Session,
        view_id: str,
        base_params: dict,
        max_pages: int,
    ) -> pd.DataFrame | None:
        """Scrape all pages for a single Finviz screener view.

        Returns a DataFrame with raw Finviz column names (including 'Ticker').
        The 'No.' column is dropped automatically.
        """
        all_rows: list[dict] = []
        headers: list[str] | None = None
        page = 1

        while page <= max_pages:
            params = {**base_params, 'v': view_id, 'r': (page - 1) * 20 + 1}
            try:
                resp = session.get(self.SCREENER_URL, params=params, timeout=30)
                resp.raise_for_status()
            except requests.RequestException as e:
                logger.warning(
                    f"Scraping view {view_id}: page {page} request failed: {e}"
                )
                if page == 1:
                    return None
                break

            soup = BeautifulSoup(resp.text, 'html.parser')
            table = self._find_screener_table(soup)

            if table is None:
                if page == 1:
                    logger.warning(
                        f"Could not find screener table for view {view_id}"
                    )
                    return None
                break  # no more pages

            rows = table.find_all('tr')
            if len(rows) <= 1:
                break  # header only, no data

            # Extract headers from the first row on the first page
            if headers is None:
                header_row = rows[0]
                headers = [
                    th.get_text(strip=True)
                    for th in header_row.find_all(['th', 'td'])
                ]

            # Extract data rows
            page_rows = 0
            for row in rows[1:]:
                cells = row.find_all('td')
                if len(cells) < 3:
                    continue
                values = [cell.get_text(strip=True) for cell in cells]
                if len(values) == len(headers):
                    all_rows.append(dict(zip(headers, values)))
                    page_rows += 1

            logger.info(
                f"Scraping view {view_id}: page {page}, {len(all_rows)} rows so far"
            )

            if page_rows < 20:
                break  # last page

            page += 1
            time.sleep(0.2)  # be polite to Finviz

        if not all_rows:
            return None

        df = pd.DataFrame(all_rows)

        # Drop the row-number column that Finviz puts first
        if 'No.' in df.columns:
            df = df.drop(columns=['No.'])

        return df

    # -----------------------------------------------------------------
    #  Helper: locate the screener data table in the HTML
    # -----------------------------------------------------------------
    @staticmethod
    def _find_screener_table(soup: BeautifulSoup):
        """Return the <table> element containing screener data rows.

        Finviz pages have many tables; we look for known class/id first,
        then fall back to heuristics (table whose first row contains
        'Ticker' or 'No.' headers).
        """
        # Try well-known identifiers first
        table = (
            soup.find('table', class_='screener_table')
            or soup.find('table', id='screener-views-table')
        )
        if table is not None:
            return table

        # Heuristic: find a table whose header row mentions Ticker / No.
        for t in soup.find_all('table'):
            rows = t.find_all('tr')
            if len(rows) > 2:
                header_texts = [
                    th.get_text(strip=True)
                    for th in rows[0].find_all(['th', 'td'])
                ]
                if 'Ticker' in header_texts or 'No.' in header_texts:
                    return t

        return None

    def _normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert Finviz columns to standard schema."""
        # Drop 'No.' column if present (row number from HTML)
        if 'No.' in df.columns:
            df = df.drop(columns=['No.'])

        df = df.rename(columns=FINVIZ_COL_MAP)

        # Parse percentage strings: "3.50%" -> 0.035
        for col in PCT_COLUMNS:
            if col in df.columns:
                df[col] = df[col].apply(parse_pct_string)

        # Parse market cap: "1.5B" -> 1_500_000_000
        if 'market_cap' in df.columns:
            df['market_cap'] = df['market_cap'].apply(parse_market_cap)

        # Parse numeric columns
        for col in ['close', 'atr', 'rel_volume', 'avg_volume', 'volume']:
            if col in df.columns:
                df[col] = pd.to_numeric(
                    df[col].astype(str).str.replace(',', ''),
                    errors='coerce'
                )

        # Ensure all standard columns exist (fill missing with None)
        for col in STANDARD_COLUMNS:
            if col not in df.columns:
                df[col] = None

        return df[STANDARD_COLUMNS]

    def fetch_etf_data(self, tickers: list[str] = None) -> pd.DataFrame:
        raise NotImplementedError("Finviz doesn't support ETF lookup by ticker")

    def fetch_ohlc(self, tickers: list[str] = None, period: str = '90d') -> dict:
        raise NotImplementedError("Finviz doesn't provide OHLC history")
