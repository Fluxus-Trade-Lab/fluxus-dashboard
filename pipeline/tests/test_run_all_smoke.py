"""End-to-end smoke for the orchestrator -- DATA_RELIABILITY §六.0.

Why this exists: run_all.main() is ~650 lines of control flow and had zero
tests. Every stage is wrapped in its own try/except so that one broken vendor
cannot cost the whole night -- which is right, and which also means a stage can
fail SILENTLY. On 2026-08-19 an `else:` re-bound to an inserted `if` and
breadth.json shipped for a whole night without regime/state_board/verdict/
conditions; nothing failed loudly, so nothing noticed (incident case study in
data/reference/incidents/2026-08-19_breadth_blackout).

So this test asserts two things a "does it crash" smoke would miss:

  1. every file in quality.REQUIRED_BLOCKS is written AND carries its blocks
     (the 08-19 bug is caught here: breadth.json existed, its four blocks did
     not);
  2. no stage logged an exception. The try/except walls swallow the traceback
     into a log line, so the log IS the failure channel. A stage that starts
     throwing turns this red instead of passing quietly.

The universe is a 152-row pre-scoring fixture (pipeline/tests/fixtures/
smoke_universe.json, rebuilt by pipeline.tools.make_smoke_fixture). Every
network call is stubbed; price series are deterministic synthetic walks
anchored on the fixture's own closes. Nothing here asserts a market number --
the subject is the orchestrator's control flow and the shape of what it writes.
"""
from __future__ import annotations

import json
import logging
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).resolve().parent / "fixtures"
FIXTURE = FIXTURES / "smoke_universe.json"
ETF_FIXTURE = FIXTURES / "smoke_etf_data.json"
SIGNALS_FIXTURE = FIXTURES / "smoke_signals.json"

# Copied into the sandbox so the run starts from a realistic archive state.
SEED_DIRS = ("data/reference", "data/history", "data/output/baskets")
SEED_FILES = ("frontend/public/data/screener-presets.json",)

MA_TICKERS = ["SPY", "QQQ", "IWM", "RSP", "^GSPC", "BTC-USD", "^VIX"]

# Stages whose failure is tolerated by design would still be a finding here;
# there is deliberately no allowlist. If a stage must be allowed to fail in
# the sandbox, stub it above instead of excusing it below.


def _synth_bars(seed: int, last_close: float, n: int = 800) -> pd.DataFrame:
    """A deterministic OHLCV walk ending at ``last_close``.

    Business-day index, positive volume, High/Low bracketing Close -- enough
    shape for the MA/ATR/RS machinery downstream. The numbers are synthetic on
    purpose: no assertion in this file reads them.
    """
    rng = np.random.default_rng(seed)
    steps = rng.normal(0.0004, 0.011, n)
    walk = np.exp(np.cumsum(steps))
    close = walk / walk[-1] * last_close
    idx = pd.bdate_range(end="2026-08-19", periods=n)
    high = close * (1 + np.abs(rng.normal(0, 0.004, n)))
    low = close * (1 - np.abs(rng.normal(0, 0.004, n)))
    return pd.DataFrame(
        {
            "Open": close * (1 + rng.normal(0, 0.002, n)),
            "High": np.maximum(high, close),
            "Low": np.minimum(low, close),
            "Close": close,
            "Volume": rng.integers(1_000_000, 40_000_000, n).astype(float),
        },
        index=idx,
    )


@pytest.fixture(scope="module")
def module_monkeypatch():
    with pytest.MonkeyPatch.context() as mp:
        yield mp


@pytest.fixture(scope="module")
def sandbox(tmp_path_factory, module_monkeypatch):
    tmp_path = tmp_path_factory.mktemp("run_all_smoke")
    monkeypatch = module_monkeypatch
    """A cwd of its own. Every path in the pipeline is relative to it."""
    for rel in SEED_DIRS:
        src = ROOT / rel
        if src.exists():
            shutil.copytree(src, tmp_path / rel, dirs_exist_ok=True)
    for rel in SEED_FILES:
        src = ROOT / rel
        if src.exists():
            (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, tmp_path / rel)
    (tmp_path / "data" / "output").mkdir(parents=True, exist_ok=True)
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture(scope="module")
def universe_fixture() -> pd.DataFrame:
    rows = json.loads(FIXTURE.read_text())["rows"]
    return pd.DataFrame(rows)


@pytest.fixture(scope="module")
def no_network(module_monkeypatch, universe_fixture):
    monkeypatch = module_monkeypatch
    """Stub every vendor call main() makes, at the seam it calls them through."""
    from pipeline.adapters import fundamentals_store as FS
    from pipeline.adapters.finviz_adapter import FinvizAdapter
    from pipeline.adapters.yfinance_adapter import YfinanceAdapter
    from pipeline.rotation import fetch_baskets
    from pipeline.screeners import asset_signals, name_cards, volume_enrichment
    from pipeline.risk import correction_risk
    from pipeline.screeners import run_all

    closes = dict(zip(universe_fixture["ticker"], universe_fixture["close"]))

    def bars_for(ticker: str) -> pd.DataFrame:
        anchor = float(closes.get(ticker) or 400.0)
        return _synth_bars(abs(hash(ticker)) % 10_000, anchor)

    # --- universe -------------------------------------------------------
    monkeypatch.setattr(FinvizAdapter, "fetch_universe",
                        lambda self: universe_fixture.copy())
    monkeypatch.setattr(YfinanceAdapter, "enrich_universe",
                        lambda self, df, *a, **k: df)
    monkeypatch.setattr(FS, "refresh",
                        lambda store, tickers, **k: {"due": 0, "ok": 0, "failed": 0,
                                                     "walled": False, "store": len(store or {})})

    # --- ETFs and index MAs --------------------------------------------
    # Real snapshots, not hand-written stubs: quality.check_site grades 18 ETF
    # columns and 10 signal keys, so a thin stub makes the site report severe
    # for a reason that has nothing to do with the orchestrator.
    etf = pd.DataFrame(json.loads(ETF_FIXTURE.read_text()))
    monkeypatch.setattr(YfinanceAdapter, "fetch_etf_data", lambda self: etf.copy())

    signal_snapshot = json.loads(SIGNALS_FIXTURE.read_text())

    def fake_ma(self, tickers=None, return_history=False, history_period="1y"):
        tickers = tickers or MA_TICKERS
        histories = {t: bars_for(t) for t in tickers}
        signals = {t: dict(signal_snapshot[t]) for t in tickers if t in signal_snapshot}
        # The walk ends where the snapshot's close is, so the two agree.
        for t, sig in signals.items():
            histories[t] = _synth_bars(abs(hash(t)) % 10_000, float(sig["close"]))
        return (signals, histories) if return_history else signals

    monkeypatch.setattr(YfinanceAdapter, "fetch_ma_data", fake_ma)

    # --- stages that reach for their own bars ---------------------------
    monkeypatch.setattr(run_all, "run_vcp_pipeline",
                        lambda universe, yf_adapter: {"count": 0, "results": []})
    monkeypatch.setattr(volume_enrichment, "enrich_universe",
                        lambda df: df.assign(vol_5d_50d=1.0))
    monkeypatch.setattr(asset_signals, "fetch",
                        lambda tickers=None: {t: bars_for(t) for t in
                                              (tickers or asset_signals.ASSETS)})
    monkeypatch.setattr(name_cards, "fetch_bars",
                        lambda tickers: {t: bars_for(t) for t in list(tickers) + ["SPY"]})
    monkeypatch.setattr(fetch_baskets, "fetch", lambda *a, **k: {})

    spx = bars_for("^GSPC")
    vix = bars_for("^VIX")
    monkeypatch.setattr(correction_risk, "fetch_inputs",
                        lambda with_appendix=False: pd.DataFrame(
                            {"^GSPC": spx["Close"].values, "^VIX": vix["Close"].values},
                            index=spx.index))

    # The premarket guard reads the wall clock; the smoke must run at any hour.
    monkeypatch.setenv("FORCE_INTRADAY_RUN", "1")
    return run_all


class _Capture(logging.Handler):
    def __init__(self):
        super().__init__(level=logging.DEBUG)
        self.records: list[logging.LogRecord] = []

    def emit(self, record):  # noqa: D102
        self.records.append(record)


@pytest.fixture(scope="module")
def smoke_run(sandbox, no_network):
    """main() runs ONCE for the module; every test reads that one run.

    Three separate runs cost 70s and told us nothing three times.
    """
    handler = _Capture()
    root = logging.getLogger()
    root.addHandler(handler)
    prev = root.level
    root.setLevel(logging.INFO)
    try:
        no_network.main()
    finally:
        root.removeHandler(handler)
        root.setLevel(prev)
    return sandbox, handler.records


def test_run_all_writes_every_required_block(smoke_run):
    """The whole chain runs and every REQUIRED_BLOCKS file arrives intact."""
    from pipeline.quality import REQUIRED_BLOCKS, check_required_blocks

    sandbox, _ = smoke_run
    out = sandbox / "data" / "output"
    missing = check_required_blocks(out)
    assert missing == {}, f"outputs written but incomplete: {missing}"

    # check_required_blocks is satisfied by an empty required-list, so pin the
    # two files whose contract is "exists and parses" separately.
    for name in ("signals.json", "etf_data.json"):
        assert json.loads((out / name).read_text()), f"{name} is empty"

    assert set(REQUIRED_BLOCKS) <= {p.name for p in out.glob("*.json")}


def test_no_stage_swallowed_an_exception(smoke_run):
    """Every failure domain logs instead of raising -- so the log is the gate.

    A stage that starts throwing would otherwise pass the block assertions on
    yesterday's file (or on a payload that happens to still be shaped right).
    """
    _, records = smoke_run
    swallowed = [r for r in records if r.exc_info is not None]
    assert not swallowed, (
        "stage(s) failed silently inside their try/except:\n"
        + "\n".join(f"  {r.name}: {r.getMessage()}" for r in swallowed)
    )


def test_universe_scores_are_computed_not_inherited(smoke_run):
    """The fixture ships pre-scoring, so a score in the output was computed here.

    Guards the fixture itself: if a future rebuild leaves rs_*/h_score baked in,
    the chain could stop computing them and this suite would not notice.
    """
    import json as _json

    sandbox, _ = smoke_run
    fixture_cols = set(_json.loads(FIXTURE.read_text())["rows"][0])
    for col in ("rs_1m", "rs_3m", "rs_ibd", "h_score", "tradeable"):
        assert col not in fixture_cols, f"fixture pre-bakes {col}; rebuild it"

    rows = _json.loads((sandbox / "data" / "output" / "universe.json").read_text())["rows"]
    assert rows, "universe.json has no rows"
    assert any(r.get("rs_3m") is not None for r in rows), "rs_3m never computed"
    assert any(r.get("h_score") is not None for r in rows), "h_score never computed"
