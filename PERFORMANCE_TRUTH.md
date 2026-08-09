# PERFORMANCE TRUTH — Canonical Verified Numbers

**This file is the single source of truth for Fluxus trading-performance numbers.**
Any external surface that publishes performance — the Squarespace **Track Record**
page, Substack posts, X threads, investor decks — MUST match the figures here.
If another document disagrees, this file wins; fix the other document.

- **Source data:** `data/portfolio/portfolio_YYYY-MM-DD.csv` (latest = truth; git-ignored, local-only)
- **Engine:** `pipeline/portfolio/performance_review.py` + `pipeline/portfolio/mtm.py`
- **Machine-readable copy:** [`performance_truth.json`](performance_truth.json)
- **Regenerate:** `python pipeline/portfolio/performance_review.py --period h1 --label h1_2026`
  then `python pipeline/portfolio/truth_snapshot.py`
- Numbers below are **aggregate only** (no per-trade rows) so this file is safe to
  commit to the public repo.

---

## Period 1 — H1 2026 · 2025-12-31 → 2026-07-22  *(as of export 2026-07-26)*

Account: **$1,000,000 → $1,905,255** · **+90.53%** · 331 closed trades · 100% cash

### Return & edge
| Metric | Value | Verification |
|---|---|---|
| Net realized P&L | **+$905,255** (+90.53%) | **triple-verified**: per-leg engine, independent proceeds−cost, and the dashboard's own React calc all agree to the cent |
| Closed trades | 331 (all fully closed, 0 open) | trim qtys reconcile to original qty on every trade |
| Win rate | 39.9% | 132 W / 181 L / 18 flat |
| Payoff (avg win ÷ avg loss) | 3.40× | avg win $11,490 / avg loss $3,378 |
| Profit factor | 2.48 | |
| Expectancy | +$2,735 / trade (+0.88R) | |
| Total R captured | +290.6R | |
| Avg hold | 7.5 days | swing cadence |
| **Return on deployed capital** | **85.3%** | P&L per $1 actually at risk (vs +90.5% on total capital) |
| Leverage (gross ÷ equity) | avg **0.79×**, peak **1.56×** | mostly under fully-invested; peaked ~1.6× (Reg-T-ish), not 2.5×. (Deployment vs *starting* $1M reads higher — 106%/248% peak — because equity grew; leverage vs current equity is the honest gauge.) |

### Drawdown & risk — **mark-to-market is the reporting standard**
| Metric | Value | Notes |
|---|---|---|
| **Max drawdown (MTM, EOD)** | **−$207,300 · −17.9% of peak** | peak 2026-01-28 → trough 2026-03-19. Daily net-liq incl. open positions; split scale anchored to as-traded fills. **This is the number to publish.** |
| Peak equity | $2,036,318 (+104%) | 2026-06-30 |
| Max drawdown (realized floor) | −$57,300 · −5.4% | closed-trade only; understates true risk — internal use |
| Sharpe / Sortino | 2.61 / 4.65 | annualized, daily returns |
| Ann. volatility | 45.4% | |
| CAGR / Calmar | 206.6% / 11.5 | ⚠ annualized from a 7-month sample — reads high; the honest headline is the **+90.5% actual** period return, not the annualized figure |

> **Max DD = −17.9% (Jan 28 → Mar 19), verified real.** The Jan gains were given
> back in a smooth 7-week slide (biggest day −6.3%), dipping ~5% below the $1M
> start by mid-March — no single-day spike, curve is clean of split artifacts.
> **Correction (2026-08-03):** the previously-published −11.1% was a bug — the
> drawdown routine selected the max *dollar* drop (a June episode on the larger
> ~$2M base) instead of the max *percentage* drop; fixed to select by %. And the
> old "~18% is a split phantom" note was itself wrong: the ~18% was always the
> real Jan–Mar drawdown, not a phantom.

### Monthly realized P&L
| Month | P&L | Return |
|---|---|---|
| 2026-01 | +$43,710 | +4.4% |
| 2026-02 | +$9,569 | +1.0% |
| 2026-03 | +$20,370 | +2.0% |
| 2026-04 | +$141,337 | +14.1% |
| 2026-05 | +$319,907 | +32.0% |
| 2026-06 | +$271,142 | +27.1% |
| 2026-07 (to 22nd) | +$99,220 | +9.9% |

### By direction
| Dir | n | P&L | Win% |
|---|---|---|---|
| Long | 298 | +$819,327 | 39% |
| Short | 33 | +$85,928 | 48% |

### Benchmarks — same window (2025-12-31 → 2026-07-22)
| | Return | Multiple |
|---|---|---|
| **Account** | **+90.5%** | — |
| SPY | **+9.60%** | 9.4× |
| **QQQ** | **+14.82%** | **6.1×** |

- Source: **IBKR** (TWS, daily `TRADES`, RTH). Never TradingView. SPY 681.92 → 747.41; QQQ 614.31 → 705.35.
- Reproduce: `python scripts/benchmark_window.py 2025-12-31 2026-07-22`
- **Price return, not total return** — IBKR's `ADJUSTED_LAST` times out for these ETFs, and price return is the right comparison anyway: the account figure beside it is realized trading P&L, which also excludes dividends. Both sides consistent. (Dividends over this window would add roughly +0.6% to SPY, +0.3% to QQQ.)
- **Publish both.** SPY alone is the soft benchmark; QQQ is the honest yardstick for a momentum/tech book.

---

## Methodology (so any reviewer can reproduce)
- **Realized P&L** per trade: long `Σ(exit−entry)×qty`, short `Σ(entry−exit)×qty`, summed over trim legs. Attributed to the trim/exit date.
- **R** = pnl ÷ (|entry − initial_stop| × original_qty).
- **MTM equity(day)** = capital + realized-to-date + open-position unrealized, marked at the day's close. **Split correction anchors each position's marks to its own as-traded fills** (`median(fill_price / adjusted_close)` per era) — it does NOT trust any split feed (yfinance's split list is unreliable for these ETFs; it missed a 2026-05-26 SOXS split).
- **Max drawdown** = peak-to-trough of the daily curve, as % of the running peak.

*Generated by `truth_snapshot.py`. Do not hand-edit the numbers — regenerate.*
