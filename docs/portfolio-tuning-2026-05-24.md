# Portfolio Tuning Report — 2026-05-24T04:05:09

_255 closed trades · 46 multi-day-trim · 10,800 param sets · 496,800 simulations_

## TL;DR — Key takeaways

- **Total opportunity**: +17.31R of additional R was left on the table across 46 multi-day-trim trades (+14.8% lift over actual).
- **Move from daily to weekly EMAs**: optimal trim-2 signal is `weekly close < 10EMA` and full stop is `weekly close < 20EMA`. Weekly closes filter out daily whipsaw on high-ATR momentum names.
- **Trim smaller on Trim 1**: optimal is **30%** at **+4.0R** (your stated default is 50%/+2-3R). Leaving more on the table for the runner is worth more than the early lock-in.
- **Pullback-regime entries are the leaky bucket**: optimizer found +19.85R of lift on 13 pullback-regime entries vs -0.74R on 33 bull-regime entries. Bull entries are already near-optimal; pullback entries need tighter stop / wider EMA discipline.
- **Don't replace your tactical discretion with rules**: for 13 tactical (1-3 day) trades you achieved +16.10R vs the rule-based optimizer's +2.24R. Your fast-exit intuition is outperforming any mechanical rule. Keep discretion on these.
- **Swing (>8d) trades have the biggest lift potential**: +51.02R of additional R available on 19 swing trades — the optimizer wants weekly-EMA-based exits and a smaller Trim 1 to let trends mature.
- **Single biggest gap: MU entered 2026-04-12** — actual +10.36R vs optimal +48.91R (+38.55R miss). Review the chart: this is the canonical example of premature trim on a runner.
- **Result is robust**: all top-5 parameter sets agree on Trim 1 = **+4.0R / 30%**. The recommendation is not a fragile peak.

## Headline

- **Actual total R** (across 46 multi-day trades): **+116.69R**
- **Best simulated total R**: **+133.99R** (lift: +14.8%)
- Largest gap came from premature exits on multi-day winners — optimizer held longer with a wider EMA-based stop

## Recommended parameter set — Overall

| Parameter | Value |
|---|---|
| Trim 1 trigger | **+4.0R** |
| Trim 1 size | **30%** of original position |
| Trim 2 signal | **weekly close < 10EMA** |
| Trim 2 size | **100%** of remaining |
| Full stop | **weekly close < 20EMA** |
| Gain ratchet | **none** |
| Sell-into-strength | **none** |
|  |  |
| Simulated total R | **+133.99R** |
| Mean R per trade | +2.91R |
| Sharpe-adj R | 2.37 |
| Trade count | 46 |


## By ATR bucket

| ATR% | # trades | Actual R | Optimal R | Best params |
|---|---:|---:|---:|---|
| **<3%** | 1 | -4.23R | +3.77R | T1=4.0R/70% · T2=wk10EMA/100% · Stop=d20EMA · Ratch=∅ · Strength=∅ |
| **3-5%** | 7 | +20.61R | +6.96R | T1=4.0R/50% · T2=d5dLow/50% · Stop=wk20EMA · Ratch=r8→5 · Strength=s30@15% |
| **5-7%** | 16 | +40.83R | +72.09R | T1=4.0R/30% · T2=wk10EMA/50% · Stop=wk20EMA · Ratch=∅ · Strength=∅ |
| **7-10%** | 15 | +35.59R | +35.59R | T1=3.0R/30% · T2=wk10EMA/50% · Stop=trail2ATR · Ratch=∅ · Strength=∅ |
| **10%+** | 7 | +23.89R | +23.50R | T1=4.0R/30% · T2=wk10EMA/50% · Stop=wk20EMA · Ratch=∅ · Strength=∅ |

## By hold archetype

Tactical (1-3d) trades = positions stopped or scaled out within 3 business days. Core (4-8d) = the main two-leg system trades. Swing (>8d) = extended trend-followers.

| Archetype | # trades | Actual R | Optimal R | Best params |
|---|---:|---:|---:|---|
| **tactical (1-3d)** | 13 | +16.10R | +2.24R | T1=3.0R/70% · T2=d10EMA/50% · Stop=trail2ATR · Ratch=∅ · Strength=∅ |
| **core (4-8d)** | 14 | +37.12R | +24.18R | T1=4.0R/70% · T2=wk10EMA/50% · Stop=trail2ATR · Ratch=∅ · Strength=s30@15% |
| **swing (>8d)** | 19 | +63.46R | +114.48R | T1=4.0R/30% · T2=wk10EMA/100% · Stop=wk20EMA · Ratch=∅ · Strength=∅ |

## By entry market regime

Bull regime = SPY closed above its 21EMA on the trade entry day. Pullback = SPY below 21EMA. Use this to gauge whether aggressive sell-into-strength rules help in strong tape vs defensive EMA-break rules help when the market is correcting.

| Regime | # trades | Actual R | Optimal R | Best params |
|---|---:|---:|---:|---|
| **bull** | 33 | +76.42R | +75.68R | T1=4.0R/30% · T2=d5dLow/50% · Stop=wk20EMA · Ratch=r8→5 · Strength=∅ |
| **pullback** | 13 | +40.26R | +60.11R | T1=4.0R/30% · T2=wk10EMA/50% · Stop=wk20EMA · Ratch=∅ · Strength=∅ |

## Biggest missed-gain trades

Trades where the optimizer's exit chain produced significantly more R than the actual exit.

| Ticker · Entry | Actual R | Optimal R | Δ R |
|---|---:|---:|---:|
| MU · 2026-04-12 | +10.36R | +48.91R | **+38.55R** |
| MRVL · 2026-03-31 | +5.72R | +16.30R | **+10.57R** |
| AAOI · 2026-02-18 | +2.13R | +12.24R | **+10.11R** |
| NBIS · 2026-04-05 | +5.94R | +15.27R | **+9.33R** |
| DOCN · 2026-03-15 | +6.34R | +15.36R | **+9.02R** |
| BABA · 2026-01-11 | -4.23R | +3.44R | **+7.67R** |
| BE · 2026-04-08 | +7.33R | +11.86R | **+4.52R** |
| ARM · 2026-03-30 | +0.58R | +4.53R | **+3.95R** |
| GEV · 2026-01-15 | -0.54R | +2.93R | **+3.47R** |
| KLIC · 2026-04-08 | +1.88R | +4.82R | **+2.94R** |
| PL · 2026-05-07 | +2.02R | +4.48R | **+2.46R** |
| FSLY · 2026-05-03 | -0.68R | +1.20R | **+1.88R** |
| METU · 2026-04-07 | +2.37R | +4.13R | **+1.77R** |
| SLV · 2026-05-07 | -1.23R | -1.00R | **+0.23R** |
| NOWL · 2026-05-18 | -1.14R | -1.00R | **+0.14R** |

## Sensitivity — top-5 parameter sets (by total R)

Tight cluster around similar rules = robust recommendation. Scattered = fragile.

1. T1=4.0R/30% · T2=wk10EMA/100% · Stop=wk20EMA · Ratch=∅ · Strength=∅ → **+133.99R**
2. T1=4.0R/30% · T2=wk10EMA/70% · Stop=wk20EMA · Ratch=∅ · Strength=∅ → **+133.70R**
3. T1=4.0R/30% · T2=wk10EMA/50% · Stop=wk20EMA · Ratch=∅ · Strength=∅ → **+133.50R**
4. T1=4.0R/30% · T2=d5dLow/70% · Stop=wk20EMA · Ratch=∅ · Strength=∅ → **+133.01R**
5. T1=4.0R/30% · T2=d5dLow/50% · Stop=wk20EMA · Ratch=∅ · Strength=∅ → **+133.01R**

---

_Report generated by `pipeline.portfolio.backtest_optimizer`. Re-run any time after exporting a fresh CSV into `data/portfolio/`._
