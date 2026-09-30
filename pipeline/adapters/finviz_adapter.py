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
    # Finviz renamed this header around 2026-08-07. The map only knew the old
    # name, so the column silently went 100% null for a week: 4% counts read
    # 0/0, three gainers screeners returned nothing, and the thrust vote in
    # the breadth verdict was cast on an empty column. Keep both spellings.
    'Change %': 'change_pct',
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

#: Finviz's HTML screener stops paginating at row 1000.  Any `r` above that
#: returns 403 with `Cf-Mitigated: challenge` -- a Cloudflare managed
#: challenge, i.e. an interstitial we cannot solve from a script.
#:
#: Measured 2026-09-30, after two GitHub runs (36783219599, 36785607847) and a
#: local run all stopped at exactly 1000 of 5613 rows on page 51.  The first
#: reading of that shape was "the runner's IP got throttled"; it was not:
#:
#:   fresh session, FIRST request     r=981  -> 200      r=1001 -> 403
#:   fresh session, FIRST request     r=1021 -> 403      r=3001 -> 403
#:
#: A rate limit cannot be reproduced by a request that is the first one a
#: session makes, and an IP ban cannot be reproduced from three different
#: networks.  The boundary is the row offset, so it is a per-query cap and
#: **backing off and retrying the same page can never clear it** -- the cure
#: is to ask smaller questions.
ROW_CAP = 1000

#: ...which is what this is.  Sector is the partition because it is the one
#: Finviz facet that is provably exhaustive: on 2026-09-30 the 11 slices
#: summed to 5613, exactly the unpartitioned claim, with no name in two
#: sectors and none in neither.  (Market cap bands lose the 41 names Finviz
#: has no cap for; exchange loses 1.)  `_fetch_html_screener` re-checks that
#: sum on every run rather than trusting this paragraph.
SECTOR_FILTERS = (
    'sec_basicmaterials', 'sec_communicationservices', 'sec_consumercyclical',
    'sec_consumerdefensive', 'sec_energy', 'sec_financial', 'sec_healthcare',
    'sec_industrials', 'sec_realestate', 'sec_technology', 'sec_utilities',
)


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

    # Finviz's own Index filter. Verified 2026-09-04: `f=idx_sp500` returns
    # "#1 / 503 Total" -- 503 rather than 500 because of dual-share-class
    # names, which is what StockCharts' $SPX breadth family also carries.
    INDEX_FILTERS = {"sp500": "idx_sp500", "ndx": "idx_ndx", "djia": "idx_dji"}

    def fetch_index_members(self, index: str = "sp500") -> set[str]:
        """Tickers in a named index, for the index-scoped breadth family.

        StockCharts' percent-above-MA indicators are always attached to an
        index -- $SPXA200R is the S&P 500, $NYA200R the NYSE. Ours were
        computed on a 5,630-name Finviz screener universe that corresponds to
        no published index, so they could not be compared with any published
        reading. On 2026-09-03 our full-universe %>200SMA read 53.45 while
        S5TH (S&P 500) read 66.40; our own >=$10B slice read 70.09. Same
        market, three rulers.

        Returns an empty set on any failure -- the caller ships the
        index-scoped columns as NULL rather than falling back to the whole
        universe, which is the substitution that made the readings
        incomparable in the first place.
        """
        f = self.INDEX_FILTERS.get(index)
        if not f:
            raise ValueError(f"unknown index {index!r}; have {sorted(self.INDEX_FILTERS)}")
        try:
            session = requests.Session()
            session.headers.update(self.HEADERS if hasattr(self, "HEADERS") else
                                   {"User-Agent": "Mozilla/5.0"})
            df = self._scrape_view(session, "111", {"f": f}, max_pages=60)
        except Exception as e:
            logger.warning("Finviz index membership (%s) failed: %s", index, e)
            return set()
        if df is None or "Ticker" not in df.columns:
            logger.warning("Finviz index membership (%s): no rows", index)
            return set()
        members = {str(t).strip().upper() for t in df["Ticker"] if str(t).strip()}
        logger.info("Finviz index %s: %d members", index, len(members))
        return members

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

        Pages are 20 rows each.  Since 2026-09-30 a single query only yields
        its first ROW_CAP rows, so the market is asked for one sector at a time
        and the slices are unioned; see ROW_CAP and SECTOR_FILTERS.
        """
        base_filter = 'cap_1.0to,ind_stocksonly'
        # Finviz returns rows alphabetically, so a binding page cap does not
        # sample the market -- it truncates it mid-alphabet.  At 150 pages the
        # universe stopped at LNTH: every ticker from M to Z was missing,
        # including NVDA, MSFT, TSLA and PLTR.  Sized to clear the largest
        # single sector with headroom; _scrape_pages warns loudly if it binds.
        max_pages = 600

        session = requests.Session()
        session.headers.update(self.HEADERS)

        # The unpartitioned claim, asked for once.  This is the denominator the
        # run reconciles against (run_all.py's short-scrape guard), so it has to
        # be the whole market's number and not the sum of the parts -- if the
        # partition itself starts losing a sector, a self-consistent sum would
        # hide exactly the failure we are trying to surface.
        whole_claim = self._claimed_total(session, '111', {'f': base_filter, 'ft': '4'})
        if whole_claim:
            self.claimed_total = whole_claim

        frames: list[pd.DataFrame] = []
        claims: dict[str, int] = {}
        for sector in SECTOR_FILTERS:
            params = {'f': f'{base_filter},{sector}', 'ft': '4'}
            part, claimed = self._scrape_pages(session, '111', params, max_pages)
            if claimed:
                claims[sector] = claimed
            if part is None or part.empty:
                logger.error("Finviz sector %s returned no rows", sector)
                continue
            if claimed and len(part) < claimed:
                logger.error("Finviz sector %s: got %d of %d claimed rows",
                             sector, len(part), claimed)
            frames.append(part)

        if not frames:
            return None

        df = pd.concat(frames, ignore_index=True)
        if 'Ticker' in df.columns:
            # Sectors are disjoint, but head/tail passes inside one sector
            # overlap on purpose (see _scrape_pages), so dedupe is required.
            df = df.drop_duplicates(subset=['Ticker'], keep='first')
            df = df.reset_index(drop=True)

        summed = sum(claims.values())
        if whole_claim and summed != whole_claim:
            # The partition stopped covering the market: Finviz added a sector,
            # renamed one, or started classifying names outside all eleven.
            # Not fatal here -- run_all's short-scrape guard owns that call --
            # but the reason has to be in the log next to the number.
            logger.error(
                "Finviz sector partition does not reconcile: sectors claim %d, "
                "whole universe claims %d (missing %d). SECTOR_FILTERS needs a "
                "new slice.", summed, whole_claim, whole_claim - summed)
        logger.info("Overview (v=111): scraped %d rows across %d sectors "
                    "(sectors claim %d, universe claims %s)",
                    len(df), len(frames), summed, whole_claim)
        return df

    def _claimed_total(
        self, session: requests.Session, view_id: str, base_params: dict,
    ) -> int | None:
        """How many rows Finviz says match a filter, from its "#1 / N Total"."""
        params = {**base_params, 'v': view_id, 'r': 1}
        try:
            resp = session.get(self.SCREENER_URL, params=params, timeout=30)
            resp.raise_for_status()
        except requests.RequestException as e:
            logger.warning("Finviz claimed-total probe failed: %s", e)
            return None
        m = re.search(r'/\s*([\d,]+)\s*Total', resp.text)
        return int(m.group(1).replace(',', '')) if m else None

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
        """Scrape one Finviz view; rows only. See `_scrape_pages`."""
        return self._scrape_pages(session, view_id, base_params, max_pages)[0]

    def _scrape_pages(
        self,
        session: requests.Session,
        view_id: str,
        base_params: dict,
        max_pages: int,
    ) -> tuple[pd.DataFrame | None, int | None]:
        """Scrape all reachable pages for one Finviz screener query.

        Returns `(rows, claimed)` -- a DataFrame with raw Finviz column names
        (including 'Ticker'), and the row count Finviz claims for this query.
        The 'No.' column is dropped automatically.

        Only the first ROW_CAP rows of a query are reachable (see ROW_CAP).
        When the query claims more than that, the rest is read from the other
        end, sorted descending, which reaches rows ROW_CAP+1..2*ROW_CAP. The
        two passes deliberately overlap; the caller dedupes on Ticker. A query
        claiming more than 2*ROW_CAP has an unreachable middle and says so.
        """
        claimed = self._claimed_total(session, view_id, base_params)

        rows_asc, headers = self._scrape_one_direction(
            session, view_id, base_params, max_pages, order=None)
        all_rows = list(rows_asc)

        if claimed and claimed > ROW_CAP:
            if claimed > 2 * ROW_CAP:
                logger.error(
                    "Finviz query claims %d rows; only %d are reachable from "
                    "each end, so rows %d..%d cannot be read at all. Split the "
                    "query further.",
                    claimed, ROW_CAP, ROW_CAP + 1, claimed - ROW_CAP)
            tail_rows, tail_headers = self._scrape_one_direction(
                session, view_id, base_params, max_pages, order='-ticker',
                stop_after=claimed - ROW_CAP)
            if headers is None:
                headers = tail_headers
            all_rows.extend(tail_rows)

        if not all_rows:
            return None, claimed

        df = pd.DataFrame(all_rows)

        # Drop the row-number column that Finviz puts first
        if 'No.' in df.columns:
            df = df.drop(columns=['No.'])

        return df, claimed

    def _scrape_one_direction(
        self,
        session: requests.Session,
        view_id: str,
        base_params: dict,
        max_pages: int,
        order: str | None = None,
        stop_after: int | None = None,
    ) -> tuple[list[dict], list[str] | None]:
        """Page through one query in one sort order, up to ROW_CAP rows.

        `stop_after` stops early once that many rows are in hand -- the tail
        pass only needs the overflow, not another full ROW_CAP of rows.
        """
        all_rows: list[dict] = []
        headers: list[str] | None = None
        page = 1

        while page <= max_pages:
            offset = (page - 1) * 20 + 1
            if offset > ROW_CAP:
                # Requesting this would earn a Cloudflare challenge, not rows.
                break
            params = {**base_params, 'v': view_id, 'r': offset}
            if order:
                params['o'] = order
            try:
                resp = session.get(self.SCREENER_URL, params=params, timeout=30)
                resp.raise_for_status()
            except requests.RequestException as e:
                logger.warning(
                    f"Scraping view {view_id}: page {page} request failed: {e}"
                )
                if page == 1:
                    return [], None
                break

            soup = BeautifulSoup(resp.text, 'html.parser')
            table = self._find_screener_table(soup)

            if table is None:
                if page == 1:
                    logger.warning(
                        f"Could not find screener table for view {view_id}"
                    )
                    return [], None
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
            ticker_idx = headers.index('Ticker') if 'Ticker' in headers else None
            page_rows = 0
            for row in rows[1:]:
                cells = row.find_all('td')
                if len(cells) < 3:
                    continue
                values = [cell.get_text(strip=True) for cell in cells]
                # Finviz's ticker cell now embeds a logo <img>, so get_text()
                # prepends a stray character (e.g. "A" -> "AA"), which invalidates
                # every symbol and breaks yfinance enrichment. The <td> carries a
                # clean data-boxover-ticker attribute — use it.
                if ticker_idx is not None and ticker_idx < len(cells):
                    clean = cells[ticker_idx].get('data-boxover-ticker')
                    if clean:
                        values[ticker_idx] = clean.strip()
                if len(values) == len(headers):
                    all_rows.append(dict(zip(headers, values)))
                    page_rows += 1

            logger.info(
                "Scraping view %s%s: page %d, %d rows so far",
                view_id, ' (desc)' if order else '', page, len(all_rows),
            )

            if page_rows < 20:
                break  # last page

            if stop_after is not None and len(all_rows) >= stop_after:
                break  # the tail pass has the overflow; the rest is overlap

            page += 1
            time.sleep(0.2)  # be polite to Finviz
        else:
            # Loop exhausted max_pages without hitting a short page: the cap is
            # binding and the universe is silently truncated mid-alphabet.
            # This went unnoticed once and cost every ticker from M to Z.
            logger.error(
                "Finviz page cap (%d) bound at %d rows - universe is TRUNCATED. "
                "Last ticker: %s. Raise max_pages.",
                max_pages, len(all_rows),
                all_rows[-1].get('Ticker') if all_rows else 'n/a',
            )

        return all_rows, headers

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
