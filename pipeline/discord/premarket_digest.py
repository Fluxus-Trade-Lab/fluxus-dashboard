"""Pre-market gap digest — Phase 1 of Discord automation.

Runs at 8:00am ET on weekdays, posts to #premarket-summary by 8:15am ET.

Pipeline:
  1. Load universe (pipeline/data/output/universe.json) and filter to liquid names
  2. Fetch pre-market quotes via yfinance (prepost=True, 1m bars)
  3. Filter to gappers (|gap| >= 3%, price >= $2, liquidity gates)
  4. Tag with catalyst (earnings calendar + recent news) via Finnhub
  5. Ask Claude to rank candidates and write a one-line rationale each
  6. POST a Discord embed to the configured webhook

Env vars (all optional — script degrades gracefully):
  DISCORD_PREMARKET_WEBHOOK : webhook URL for #premarket-summary channel
  ANTHROPIC_API_KEY         : enables Claude ranking step
  FINNHUB_API_KEY           : enables catalyst tagging
  PREMARKET_DRY_RUN         : if set (any value), print to stdout instead of posting
  PREMARKET_FORCE_RUN       : if set, bypass the "must be 8am ET" guard (for testing)

Usage:
  python -m pipeline.discord.premarket_digest [--dry-run] [--force]
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import requests
import yfinance as yf

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("premarket_digest")

# -------- Configuration ------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[2]
UNIVERSE_PATH = REPO_ROOT / "data" / "output" / "universe.json"
OUTPUT_DIR = REPO_ROOT / "data" / "output"

# Filter thresholds
MIN_PRICE = 2.0
MIN_AVG_VOL = 500_000           # universe-level liquidity filter
MIN_GAP_PCT = 0.03              # +/- 3% gap from prev close
MIN_PREMKT_VOL = 100_000        # OR low-float gate
MAX_LOW_FLOAT_MCAP = 200_000_000  # "low float" upper bound for the OR-gate
TOP_N_PER_SIDE = 10

# yfinance batching
YF_CHUNK = 80
YF_TIMEOUT_S = 45

# Claude
CLAUDE_MODEL = "claude-sonnet-4-20250514"  # match pipeline/content/processor.py + api/coach

ET_TZ = timezone(timedelta(hours=-5))  # EST; we override during EDT


# -------- Data model ---------------------------------------------------------


@dataclass
class Candidate:
    ticker: str
    prev_close: float
    premkt_last: float
    gap_pct: float                  # signed: +0.05 = +5%
    premkt_volume: int
    avg_volume: int
    market_cap: float | None
    sector: str | None
    catalyst: str = "—"             # 'earnings' | 'news' | '—'
    catalyst_note: str = ""         # e.g. headline preview
    priority: str = ""              # filled by Claude: HIGH | MED | LOW | SKIP
    rationale: str = ""

    @property
    def side(self) -> str:
        return "up" if self.gap_pct > 0 else "down"


# -------- DST-aware ET clock -------------------------------------------------


def _now_et() -> datetime:
    """Return current time in US/Eastern, DST-aware (no pytz dependency)."""
    # Python stdlib zoneinfo is available 3.9+
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("America/New_York"))
    except ImportError:
        # Fallback: assume EDT mid-year, EST winter. Good enough as guard.
        return datetime.now(timezone(timedelta(hours=-4)))


def _is_runtime_window() -> bool:
    """True if ET hour is 8 (we want to fire once per day at 8am ET)."""
    return _now_et().hour == 8


# -------- Step 1: universe filter --------------------------------------------


def load_universe_candidates() -> list[dict[str, Any]]:
    """Read universe.json and pre-filter to liquid, priced-up names."""
    if not UNIVERSE_PATH.exists():
        logger.error("Universe file missing: %s", UNIVERSE_PATH)
        return []

    universe = json.loads(UNIVERSE_PATH.read_text())
    rows = universe.get("rows", [])
    logger.info("Universe loaded: %d rows", len(rows))

    filtered = []
    for r in rows:
        close = r.get("close") or 0
        avg_vol = r.get("avg_volume") or 0
        if close < MIN_PRICE:
            continue
        if avg_vol < MIN_AVG_VOL:
            continue
        if not r.get("ticker"):
            continue
        filtered.append(r)

    logger.info(
        "After liquidity filter (price>=$%s, avg_vol>=%dK): %d candidates",
        MIN_PRICE,
        MIN_AVG_VOL // 1000,
        len(filtered),
    )
    return filtered


# -------- Step 2: pre-market scan via yfinance --------------------------------


def _fetch_premkt_chunk(tickers: list[str]) -> dict[str, dict[str, float]]:
    """Fetch pre-market data for a chunk of tickers.

    Returns {ticker: {premkt_last, premkt_volume, prev_close}}.
    Tickers with no usable data are omitted.
    """
    out: dict[str, dict[str, float]] = {}
    try:
        data = yf.download(
            tickers=" ".join(tickers),
            period="2d",
            interval="1m",
            prepost=True,
            group_by="ticker",
            auto_adjust=False,
            progress=False,
            threads=True,
            timeout=YF_TIMEOUT_S,
        )
    except Exception as e:
        logger.warning("yfinance chunk failed (%d tickers): %s", len(tickers), e)
        return out

    if data is None or data.empty:
        return out

    today_et = _now_et().date()
    market_open_et = datetime.combine(
        today_et,
        datetime.min.time(),
        tzinfo=ET_TZ,
    ).replace(hour=9, minute=30)

    for t in tickers:
        try:
            df = data[t] if len(tickers) > 1 else data
            df = df.dropna(subset=["Close"])
            if df.empty:
                continue

            # Convert tz-aware index to ET
            idx_et = df.index.tz_convert("America/New_York") if df.index.tz else df.index

            # Pre-market = today's bars before 9:30 ET
            today_mask = (idx_et.date == today_et) & (idx_et.time < datetime.min.time().replace(hour=9, minute=30).time())
            today_pm = df[today_mask]

            # Previous regular session close = last bar from yesterday between 9:30 and 16:00
            ydy = today_et - timedelta(days=1)
            for back in range(1, 6):  # walk back up to 5 calendar days for weekends/holidays
                ydy_candidate = today_et - timedelta(days=back)
                ydy_mask = (idx_et.date == ydy_candidate)
                ydy_bars = df[ydy_mask]
                if not ydy_bars.empty:
                    ydy = ydy_candidate
                    break
            else:
                ydy_bars = df[df.index < df.index[-1]]

            if today_pm.empty or ydy_bars.empty:
                continue

            premkt_last = float(today_pm["Close"].iloc[-1])
            premkt_vol = int(today_pm["Volume"].fillna(0).sum())
            prev_close = float(ydy_bars["Close"].iloc[-1])
            if prev_close <= 0 or premkt_last <= 0:
                continue

            out[t] = {
                "premkt_last": premkt_last,
                "premkt_volume": premkt_vol,
                "prev_close": prev_close,
            }
        except Exception:
            continue
    return out


def fetch_premarket_data(candidates: list[dict[str, Any]]) -> list[Candidate]:
    """Scan all candidates for pre-market activity."""
    tickers = [r["ticker"] for r in candidates]
    by_ticker = {r["ticker"]: r for r in candidates}

    # Chunk
    chunks = [tickers[i : i + YF_CHUNK] for i in range(0, len(tickers), YF_CHUNK)]
    logger.info("Fetching pre-market data: %d tickers in %d chunks", len(tickers), len(chunks))

    raw: dict[str, dict[str, float]] = {}
    # yfinance already threads internally; running chunks in parallel can rate-limit us
    for i, chunk in enumerate(chunks):
        logger.info("Chunk %d/%d (%d tickers)", i + 1, len(chunks), len(chunk))
        raw.update(_fetch_premkt_chunk(chunk))

    out: list[Candidate] = []
    for t, q in raw.items():
        prev_close = q["prev_close"]
        gap_pct = (q["premkt_last"] - prev_close) / prev_close
        row = by_ticker.get(t, {})
        out.append(
            Candidate(
                ticker=t,
                prev_close=round(prev_close, 4),
                premkt_last=round(q["premkt_last"], 4),
                gap_pct=round(gap_pct, 4),
                premkt_volume=int(q["premkt_volume"]),
                avg_volume=int(row.get("avg_volume") or 0),
                market_cap=row.get("market_cap"),
                sector=row.get("sector"),
            )
        )
    return out


# -------- Step 3: filter to top gappers --------------------------------------


def apply_gap_filter(rows: list[Candidate]) -> list[Candidate]:
    keep = []
    for c in rows:
        if abs(c.gap_pct) < MIN_GAP_PCT:
            continue
        if c.premkt_last < MIN_PRICE:
            continue
        low_float = (c.market_cap or 0) <= MAX_LOW_FLOAT_MCAP
        if not (low_float or c.premkt_volume >= MIN_PREMKT_VOL):
            continue
        keep.append(c)

    ups = sorted([c for c in keep if c.gap_pct > 0], key=lambda c: c.gap_pct, reverse=True)
    downs = sorted([c for c in keep if c.gap_pct < 0], key=lambda c: c.gap_pct)
    logger.info(
        "Post-filter: %d up, %d down (showing top %d each)",
        len(ups),
        len(downs),
        TOP_N_PER_SIDE,
    )
    return ups[:TOP_N_PER_SIDE] + downs[:TOP_N_PER_SIDE]


# -------- Step 4: catalyst tagging via Finnhub -------------------------------


def tag_catalysts(rows: list[Candidate]) -> None:
    """In-place: tag earnings + recent news via Finnhub."""
    key = os.environ.get("FINNHUB_API_KEY")
    if not key:
        logger.info("FINNHUB_API_KEY not set — skipping catalyst tagging")
        return

    today = _now_et().date()
    earnings_tickers: set[str] = set()

    # Earnings calendar — single call covering yesterday + today
    try:
        from_str = (today - timedelta(days=1)).isoformat()
        to_str = today.isoformat()
        r = requests.get(
            "https://finnhub.io/api/v1/calendar/earnings",
            params={"from": from_str, "to": to_str, "token": key},
            timeout=15,
        )
        if r.ok:
            for ev in r.json().get("earningsCalendar", []) or []:
                if ev.get("symbol"):
                    earnings_tickers.add(ev["symbol"])
    except Exception as e:
        logger.warning("Earnings calendar call failed: %s", e)

    # Per-ticker news — recent 24h headline
    def _news(c: Candidate) -> tuple[str, str, str]:
        if c.ticker in earnings_tickers:
            return c.ticker, "earnings", ""
        try:
            r = requests.get(
                "https://finnhub.io/api/v1/company-news",
                params={
                    "symbol": c.ticker,
                    "from": (today - timedelta(days=1)).isoformat(),
                    "to": today.isoformat(),
                    "token": key,
                },
                timeout=10,
            )
            if r.ok:
                items = r.json() or []
                if items:
                    headline = items[0].get("headline", "")[:120]
                    return c.ticker, "news", headline
        except Exception:
            pass
        return c.ticker, "—", ""

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(_news, rows))

    by_ticker = {r.ticker: r for r in rows}
    for t, cat, note in results:
        if t in by_ticker:
            by_ticker[t].catalyst = cat
            by_ticker[t].catalyst_note = note


# -------- Step 5: Claude ranking ---------------------------------------------


SYSTEM_PROMPT = """You are a senior pre-market trading coach for a momentum swing/intraday trader.

You receive a list of pre-market gappers with their gap %, pre-market volume, market cap, sector, and catalyst (earnings/news/none).

Your job: assign each ticker a priority (HIGH / MED / LOW / SKIP) and write a one-line rationale (≤15 words).

Calibration:
- HIGH = strong catalyst + clean technical setup + appropriate size (institutional vol, not a stuffed penny)
- MED = decent gap with some signal, watch for confirmation
- LOW = noise — gap without conviction, low-quality catalyst, or stretched extension
- SKIP = avoid (pump-and-dump tells, illiquid float-stuffed, ticker we should not touch)

Be terse. Trader is reading this at 8:15am with 75 minutes to plan."""


def _rank_payload(rows: list[Candidate]) -> str:
    """Build the structured user message for Claude."""
    lines = ["TICKER | SIDE | GAP% | PMVOL | MCAP$M | SECTOR | CATALYST | NOTE"]
    for c in rows:
        mcap = f"{(c.market_cap or 0)/1e6:,.0f}" if c.market_cap else "?"
        lines.append(
            f"{c.ticker} | {c.side} | {c.gap_pct*100:+.1f}% | "
            f"{c.premkt_volume:,} | {mcap} | {c.sector or '?'} | "
            f"{c.catalyst} | {c.catalyst_note}"
        )
    return "\n".join(lines)


def rank_with_claude(rows: list[Candidate]) -> None:
    """In-place: fill .priority + .rationale via Claude."""
    if not rows:
        return
    if not os.environ.get("ANTHROPIC_API_KEY"):
        logger.info("ANTHROPIC_API_KEY not set — skipping Claude ranking")
        return

    try:
        import anthropic
    except ImportError:
        logger.warning("anthropic SDK not installed — skipping ranking")
        return

    client = anthropic.Anthropic()
    payload = _rank_payload(rows)
    user_msg = (
        f"Rank the following pre-market gappers. Respond with ONE LINE PER TICKER in this exact format:\n"
        f"TICKER|PRIORITY|RATIONALE\n\n"
        f"Example: TSLA|HIGH|Earnings beat + 12% gap on volume, clean breakout setup\n\n"
        f"Data:\n{payload}"
    )

    try:
        resp = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=1500,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_msg}],
        )
        text = resp.content[0].text if resp.content else ""
    except Exception as e:
        logger.warning("Claude call failed: %s", e)
        return

    by_ticker = {r.ticker: r for r in rows}
    for line in text.strip().splitlines():
        line = line.strip()
        if "|" not in line:
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 3:
            continue
        ticker, prio, *rationale = parts
        if ticker in by_ticker and prio.upper() in {"HIGH", "MED", "LOW", "SKIP"}:
            by_ticker[ticker].priority = prio.upper()
            by_ticker[ticker].rationale = "|".join(rationale).strip()


# -------- Step 6: Discord poster ---------------------------------------------


PRIORITY_EMOJI = {"HIGH": "🟢", "MED": "🟡", "LOW": "⚪", "SKIP": "🔴", "": "·"}


def _format_row(c: Candidate) -> str:
    prio = PRIORITY_EMOJI.get(c.priority, "·")
    gap = f"{c.gap_pct*100:+.1f}%"
    pmv = f"{c.premkt_volume/1000:,.0f}K"
    cat = c.catalyst.upper() if c.catalyst != "—" else ""
    line = f"{prio} `{c.ticker:<6}` {gap:>7}  pmvol {pmv:>6}  {cat}"
    if c.rationale:
        line += f"\n     ↳ {c.rationale}"
    return line


def build_embed(rows: list[Candidate], runtime: datetime) -> dict[str, Any]:
    ups = [c for c in rows if c.gap_pct > 0]
    downs = [c for c in rows if c.gap_pct < 0]

    def section(rs: list[Candidate]) -> str:
        if not rs:
            return "_none_"
        return "\n".join(_format_row(c) for c in rs)[:1024]  # Discord field limit

    color = 0x16a34a if sum(c.gap_pct for c in ups) >= abs(sum(c.gap_pct for c in downs)) else 0xdc2626

    return {
        "username": "Fluxus PM Desk",
        "embeds": [
            {
                "title": f"Pre-Market Digest · {runtime.strftime('%a %b %d %Y')}",
                "description": f"Scan window: pre-9:30 ET · {len(rows)} qualifiers · "
                f"🟢 HIGH | 🟡 MED | ⚪ LOW | 🔴 SKIP",
                "color": color,
                "fields": [
                    {"name": f"▲ Gap Up ({len(ups)})", "value": section(ups), "inline": False},
                    {"name": f"▼ Gap Down ({len(downs)})", "value": section(downs), "inline": False},
                ],
                "footer": {
                    "text": f"Posted {runtime.strftime('%H:%M %Z')} · "
                    f"Caveat: 8:30 ET econ data not factored",
                },
                "timestamp": runtime.astimezone(timezone.utc).isoformat(),
            }
        ],
    }


def post_to_discord(payload: dict[str, Any]) -> bool:
    url = os.environ.get("DISCORD_PREMARKET_WEBHOOK")
    if not url:
        logger.info("DISCORD_PREMARKET_WEBHOOK not set — printing payload to stdout")
        print(json.dumps(payload, indent=2))
        return False
    try:
        r = requests.post(url, json=payload, timeout=15)
        if r.ok or r.status_code == 204:
            logger.info("Posted to Discord OK")
            return True
        logger.error("Discord POST failed: %s %s", r.status_code, r.text[:300])
        return False
    except Exception as e:
        logger.error("Discord POST exception: %s", e)
        return False


# -------- Audit trail --------------------------------------------------------


def write_audit(rows: list[Candidate], runtime: datetime) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / f"premarket_{runtime.strftime('%Y-%m-%d')}.json"
    path.write_text(
        json.dumps(
            {
                "runtime_et": runtime.isoformat(),
                "count": len(rows),
                "rows": [asdict(c) for c in rows],
            },
            indent=2,
            default=str,
        )
    )
    logger.info("Audit written: %s", path)


# -------- Main ---------------------------------------------------------------


def run(dry_run: bool = False, force: bool = False) -> int:
    runtime = _now_et()
    logger.info("Pre-market digest run @ %s", runtime.isoformat())

    if not force and not os.environ.get("PREMARKET_FORCE_RUN") and not _is_runtime_window():
        logger.info("Not 8:00am ET (current hour=%d) — skipping. Use --force to override.", runtime.hour)
        return 0

    candidates = load_universe_candidates()
    if not candidates:
        logger.error("No universe candidates — aborting")
        return 1

    scanned = fetch_premarket_data(candidates)
    logger.info("Pre-market scan returned %d quotes", len(scanned))

    top = apply_gap_filter(scanned)
    if not top:
        logger.info("No gappers passed filter — posting an empty digest is fine")

    tag_catalysts(top)
    rank_with_claude(top)
    write_audit(top, runtime)

    payload = build_embed(top, runtime)
    if dry_run or os.environ.get("PREMARKET_DRY_RUN"):
        logger.info("DRY-RUN — payload below")
        print(json.dumps(payload, indent=2))
        return 0

    return 0 if post_to_discord(payload) else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="Print payload, don't post")
    ap.add_argument("--force", action="store_true", help="Bypass 8am ET guard")
    args = ap.parse_args()
    return run(dry_run=args.dry_run, force=args.force)


if __name__ == "__main__":
    sys.exit(main())
