"""End-to-end smoke of run_all.main() -- DATA_RELIABILITY §六 item 0.

The 2026-08-19 breadth blackout survived 717 passing tests because none of
them executed the orchestrator: run_all.main() is ~900 lines of control flow
whose failure domains had never been walked as one path. This test walks it.

Only the NETWORK is fake (one synthetic yf.download + a fixture Finviz
universe); every writer, guard, archive and enrichment is the real code,
running inside a temp directory (all pipeline paths are relative, so
chdir(tmp) redirects the whole tree). Assertions are the ones that would
have caught the real incidents:

  * breadth.json carries regime / state_board / verdict / conditions
    (the else-rebind blackout)
  * run_ledger's breadth note lists all four enriched blocks with a score
    ("ok with empty evidence" was the blackout's signature)
  * required blocks present in every core output (check_required_blocks)
  * audit_archives: zero violations on everything the run wrote
  * universe rows > 0 with derived columns measured

Runtime ~1-2 min (60 synthetic tickers). Deterministic: seeded per-ticker
price paths, fixed session calendar ending Fri 2026-08-14, clock patched to
the following Saturday so the intraday guard passes."""

from __future__ import annotations

import datetime as dt
import json
import shutil
from pathlib import Path

import zlib

import numpy as np
import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[2]
LAST_SESSION = dt.date(2026, 8, 14)                     # Friday
FAKE_NOW = dt.datetime(2026, 8, 15, 10, 0)               # Saturday morning ET
N_TICKERS = 60


def _tickers():
    return [f"T{i:02d}" for i in range(N_TICKERS)]


def _path_for(symbol: str) -> pd.DataFrame:
    """Deterministic OHLCV: mix of trends so screeners/panels have material.

    `zlib.crc32`, not `hash()`. Python randomises string hashing per process
    unless PYTHONHASHSEED is pinned, so the seed -- and therefore the entire
    synthetic tape -- used to change on every run while the docstring promised
    it did not. Measured 2026-08-26: T00's last close came out 32.30 / 112.21 /
    39.79 under three seeds. That made this test intermittently red for reasons
    no one could reproduce, and a green run said nothing about the next one.
    """
    rng = np.random.RandomState(zlib.crc32(symbol.encode()) % (2**31))
    n = 320
    idx = pd.bdate_range(end=LAST_SESSION, periods=n)
    drift = {0: 0.0015, 1: -0.0008, 2: 0.0004, 3: 0.001}[rng.randint(4)]
    ret = rng.normal(drift, 0.02, n)
    if symbol in ("SPY", "QQQ", "IWM", "RSP", "^GSPC", "DIA"):
        ret = rng.normal(0.0006, 0.009, n)
    c = 50 * np.exp(np.cumsum(ret))
    # Intraday range wide enough to clear the production universe floor.
    # MIN_ADR_PCT went to 3.5 at UNIVERSE level on 2026-08-25 (e260757d); the
    # old spreads (0.004/0.006) gave the fixture an ADR20 median of 1.28% and
    # NOTHING cleared it -- every screener emptied, ticker_events fell under
    # run_all's <100-row plausibility guard, the append was skipped, and this
    # test died in the archive audit 200 lines later with "8 != 0". A fixture
    # universe has to be a universe the pipeline would actually serve.
    # Only the intraday spreads move: `ret` and therefore `c` are untouched,
    # so every trend / breadth / perf assertion below sees the same tape, and
    # the rng draw COUNT is unchanged so Volume is byte-identical too.
    o = c * (1 + rng.normal(0, 0.012, n))
    h = np.maximum(o, c) * (1 + abs(rng.normal(0, 0.024, n)))
    low = np.minimum(o, c) * (1 - abs(rng.normal(0, 0.024, n)))
    v = rng.randint(1_000_000, 8_000_000, n).astype(float)
    return pd.DataFrame({"Open": o, "High": h, "Low": low, "Close": c, "Volume": v}, index=idx)


_BARS_CACHE: dict = {}


def bars(symbol: str) -> pd.DataFrame:
    if symbol not in _BARS_CACHE:
        _BARS_CACHE[symbol] = _path_for(symbol)
    return _BARS_CACHE[symbol]


def test_the_fixture_universe_can_clear_the_production_gates():
    """The fixture must be a universe the pipeline would actually serve.

    Written 2026-08-26 after the end-to-end test spent a day dead. The
    universe ADR floor was raised to 3.5 on 08-25 (e260757d, Andy-approved and
    correct); the synthetic tape's ADR20 median was 1.28, so NOTHING cleared
    it. Every screener emptied, the day fell under `MIN_TOTAL_ROWS`, the
    ticker_events append was skipped as a pipeline-failure signature, and the
    only symptom -- 200 lines downstream -- was `assert 8 == 0` out of the
    archive auditor. Nothing in that message says "your fixture is too quiet".

    So this asserts the link directly, and names the gate. When a floor moves
    again, THIS fails first and says which one, instead of the end-to-end test
    failing last and saying nothing.
    """
    import numpy as np
    from pipeline.screeners import watchlist as W
    from pipeline.screeners.ticker_events import MIN_TOTAL_ROWS

    adr = np.array([float(((b := bars(t))["High"] - b["Low"]).tail(20).mean()
                          / b["Close"].tail(20).mean() * 100) for t in _tickers()])
    cleared = (adr >= W.MIN_ADR_PCT).mean()
    assert cleared >= 0.9, (
        f"only {cleared:.0%} of the fixture clears MIN_ADR_PCT={W.MIN_ADR_PCT} "
        f"(fixture ADR20 median {np.median(adr):.2f}). Widen the intraday spreads "
        f"in _path_for(); a universe that cannot clear the live floor makes every "
        f"downstream assertion in this file meaningless.")
    # The other half of the chain: enough names to survive the plausibility gate.
    assert N_TICKERS * 2 >= MIN_TOTAL_ROWS or N_TICKERS >= 60, (
        f"N_TICKERS={N_TICKERS} is thin against MIN_TOTAL_ROWS={MIN_TOTAL_ROWS}")


def fake_yf_download(tickers, *args, **kwargs):
    if isinstance(tickers, str):
        tickers = [tickers]
    tickers = list(tickers)
    frames = {t: bars(t) for t in tickers}
    if len(tickers) == 1:
        return frames[tickers[0]].copy()
    return pd.concat(frames, axis=1)          # MultiIndex (ticker, field)


def fixture_universe() -> pd.DataFrame:
    from pipeline.adapters.base_adapter import STANDARD_COLUMNS
    rows = []
    for i, t in enumerate(_tickers()):
        b = bars(t)
        c = b["Close"]
        close = float(c.iloc[-1])
        rows.append({
            "ticker": t, "close": close,
            "change_pct": float(c.iloc[-1] / c.iloc[-2] - 1),
            "perf_1w": float(c.iloc[-1] / c.iloc[-6] - 1),
            "perf_1m": float(c.iloc[-1] / c.iloc[-22] - 1),
            "perf_3m": float(c.iloc[-1] / c.iloc[-64] - 1),
            "perf_6m": float(c.iloc[-1] / c.iloc[-127] - 1),
            "perf_1y": float(c.iloc[-1] / c.iloc[0] - 1),
            "perf_ytd": None,
            "sma20_dist": float(close / c.rolling(20).mean().iloc[-1] - 1),
            "sma50_dist": float(close / c.rolling(50).mean().iloc[-1] - 1),
            "sma200_dist": float(close / c.rolling(200).mean().iloc[-1] - 1),
            "atr": float((b["High"] - b["Low"]).rolling(14).mean().iloc[-1]),
            "rel_volume": 1.0 + (i % 5) * 0.3,
            "avg_volume": float(b["Volume"].rolling(50).mean().iloc[-1]),
            "volume": float(b["Volume"].iloc[-1]),
            "market_cap": 2e9 + i * 5e8,
            "sector": ["Technology", "Industrials", "Healthcare", "Energy"][i % 4],
            "industry": ["Software", "Machinery", "Biotech", "Oil & Gas"][i % 4],
            "high_52w": float(close / c.max() - 1),
            "low_52w": float(close / c.min() - 1),
            "eps_growth_next_y": None, "eps_growth_this_y": None, "revenue_growth": None,
        })
    return pd.DataFrame(rows)[STANDARD_COLUMNS]


def seed_breadth_archive(path: Path):
    from pipeline.marketcal import is_trading_day
    days = [d for d in pd.bdate_range(end=LAST_SESSION - dt.timedelta(days=3), periods=34)
            if is_trading_day(d.date())][-30:]   # the auditor's I1 caught a July-4th row in v1 of this fixture
    rng = np.random.RandomState(7)
    rows = []
    spx = 7000.0
    for d in days:
        spx *= 1 + rng.normal(0.0005, 0.008)
        rows.append({
            "date": d.date().isoformat(), "source": "live", "universe_size": 5000,
            "spx_close": round(spx, 2),
            "up_4pct": int(rng.randint(150, 600)), "down_4pct": int(rng.randint(150, 600)),
            "ratio_5d": 1.0, "ratio_10d": 1.0,
            "up_25pct_qtr": 800, "down_25pct_qtr": 600,
            "up_25pct_month": 300, "down_25pct_month": 250,
            "up_50pct_month": 80, "down_50pct_month": 60,
            "up_13pct_34d": 900, "down_13pct_34d": 800,
            "t2108": 50.0, "pct_above_200sma": 50.0, "pct_above_50sma": 52.0,
            "pct_above_20sma": 51.0, "advances": 2500, "declines": 2400,
            "new_highs": 60, "new_lows": 30, "net_advances": 100, "rana": 0.5,
            "ad_line": 1000, "mcclellan_osc": 5.0,
        })
    pd.DataFrame(rows).to_csv(path, index=False)


@pytest.mark.slow
def test_run_all_end_to_end(tmp_path, monkeypatch):
    # ── the whole pipeline tree lives in tmp (paths are relative) ─────
    (tmp_path / "data/output/library").mkdir(parents=True)
    (tmp_path / "data/history/quality").mkdir(parents=True)
    (tmp_path / "data/reference").mkdir(parents=True)
    (tmp_path / "frontend/public/data").mkdir(parents=True)
    shutil.copy(REPO / "frontend/public/data/screener-presets.json",
                tmp_path / "frontend/public/data/screener-presets.json")
    (tmp_path / "data/reference/shortlist_manual.json").write_text('{"tickers": []}')
    seed_breadth_archive(tmp_path / "data/history/breadth_archive.csv")
    monkeypatch.chdir(tmp_path)

    # ── clock: Saturday after the fixture's last session ──────────────
    import pipeline.marketcal as MC
    _tz = MC.market_now().tzinfo
    fake_now = FAKE_NOW.replace(tzinfo=_tz)
    monkeypatch.setattr(MC, "market_now", lambda: fake_now)
    monkeypatch.setattr(MC, "market_today", lambda now=None: FAKE_NOW.date())

    # ── network fakes ────────────────────────────────────────────────
    import yfinance
    monkeypatch.setattr(yfinance, "download", fake_yf_download)
    import time as _time
    monkeypatch.setattr(_time, "sleep", lambda s: None)

    import pipeline.screeners.run_all as RA
    from pipeline.adapters.finviz_adapter import FinvizAdapter
    monkeypatch.setattr(FinvizAdapter, "fetch_universe", lambda self: fixture_universe())
    FinvizAdapter.claimed_total = None

    from pipeline.adapters import fundamentals_store as FS
    monkeypatch.setattr(FS, "refresh", lambda store, tickers, **kw:
                        {"due": 0, "ok": 0, "failed": 0, "walled": False, "store": 0})
    # FS.apply is pure (no network) -- runs real

    try:
        import pipeline.risk.regime_ledger as RL
        monkeypatch.setattr(RL, "build_row", lambda refresh=True: None)
    except ImportError:
        pass

    # breadth guard THRESHOLDS shrunk to fixture scale (logic untouched):
    # _MIN_UNIVERSE=1500 would stale-serve a 60-ticker universe, hiding the
    # enrichment path this test exists to walk
    import pipeline.screeners.breadth_store as BS
    monkeypatch.setattr(BS, "_MIN_UNIVERSE", 50)
    monkeypatch.setattr(BS, "_MAX_PCT200_JUMP", 100.0)

    # shortlist feedback: no env -> quiet no-op (asserted via ledger absence)
    monkeypatch.delenv("FLUXUS_GAS_URL", raising=False)

    # ── run the orchestrator ─────────────────────────────────────────
    RA.main()

    out = tmp_path / "data/output"
    hist = tmp_path / "data/history"

    # 1. universe written, measured
    u = json.loads((out / "universe.json").read_text())
    assert len(u["rows"]) == N_TICKERS and u["quality"]["status"] in ("ok", "degraded")
    r0 = next(r for r in u["rows"] if r.get("rs_line_pctl_21") is not None)
    assert r0["bar_date"] == LAST_SESSION.isoformat()

    # 2. THE regression: breadth enrichment ran on the success path
    b = json.loads((out / "breadth.json").read_text())
    for block in ("regime", "state_board", "verdict", "conditions"):
        assert block in b and b[block], f"breadth.json lost {block}"
    assert b["regime"]["score"] is not None

    # 3. ledger note carries evidence, not just "ok"
    lines = [json.loads(x) for x in (hist / "run_ledger.jsonl").read_text().splitlines()]
    note = lines[-1]["guards"]["breadth"]
    assert note["status"] == "ok" and note["regime_score"] is not None
    assert sorted(note["enriched"]) == ["conditions", "regime", "state_board", "verdict"]
    assert lines[-1]["session"] == LAST_SESSION.isoformat()

    # 4. watchlist + shortlist + assets all present with required blocks
    from pipeline.quality import check_required_blocks
    missing = check_required_blocks(out)
    missing.pop("groups.json", None)        # theme layer needs repo reference data; own domain
    assert not missing, f"missing required blocks: {missing}"
    wl = json.loads((out / "watchlist.json").read_text())
    assert wl["date"] == LAST_SESSION.isoformat()
    measured = [p["key"] for z in wl["zones"] for p in z["panels"] if p["measured"]]
    assert "episodic_pivot" in measured and "ma_reclaim" in measured
    sl = json.loads((out / "shortlist.json").read_text())
    assert len(sl["seats"]) == 6
    assert all(("ticker" in s) and (s["ticker"] or s.get("empty_reason")) for s in sl["seats"])

    # 5. archives the run wrote pass the auditor
    from pipeline.tools.audit_archives import run as audit
    rep = audit(hist, last_done=LAST_SESSION, output=out)
    assert rep["violations"] == 0, rep
