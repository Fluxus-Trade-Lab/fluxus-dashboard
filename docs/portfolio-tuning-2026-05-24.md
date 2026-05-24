# Portfolio Tuning Report — 2026-05-24T12:09:35

_255 closed trades · 46 multi-day-trim · 37,800 param sets · 1,738,800 simulations_

## TL;DR — Key takeaways

- **Total opportunity**: +93.82R of additional R was left on the table across 46 multi-day-trim trades (+80.4% lift over actual).
- **Recommended Trim 1**: **+4.0R / 30%** of original. Then Trim 2 = `weekly close < 10EMA`, size 30% of remaining.
- **Trim 3 ladder rung adds value**: target `price reaches +8R`, trim **100%** of what's left. Validates your stated practice of using a 3-rung R-target ladder rather than relying on a single signal-based exit.
- **Full stop**: `weekly close < 20EMA` — the patient runner-exit signal the optimizer keeps selecting across buckets.
- **Swing (>8d) trades have the biggest lift potential**: +68.00R of additional R available on 19 swing trades — the optimizer wants weekly-EMA-based exits and a smaller Trim 1 to let trends mature.
- **Single biggest gap: MU entered 2026-04-12** — actual +10.36R vs optimal +48.91R (+38.55R miss). Review the chart: this is the canonical example of premature trim on a runner.
- **Pyramiding is net positive**: +101.56R of total lift across 50 multi-layer campaigns (28 added R, 22 subtracted). When you pyramid INTO a winning trend you're adding real edge.
- **Best pyramid: AXTI** (7 layers, 2026-03-23 → 2026-03-31) — actual +144.01R vs first-layer-alone +4.54R = **+139.47R added by the adds.**
- **Worst pyramid: SNXX** (2 layers) — actual +7.63R vs first-layer-alone +58.05R = **-50.42R drag.** Check whether you were adding to strength (real pyramid) or averaging down (loser-doubling).
- **Result is robust**: all top-5 parameter sets agree on Trim 1 = **+4.0R / 30%**. The recommendation is not a fragile peak.

## Headline

- **Actual total R** (across 46 multi-day trades): **+116.69R**
- **Best simulated total R**: **+210.51R** (lift: +80.4%)
- Largest gap came from premature exits on multi-day winners — optimizer held longer with a wider EMA-based stop

## Recommended parameter set — Overall

| Parameter | Value |
|---|---|
| Trim 1 trigger | **+4.0R** |
| Trim 1 size | **30%** of original position |
| Trim 2 trigger | **weekly close < 10EMA** |
| Trim 2 size | **30%** of remaining |
| Trim 3 trigger | **price reaches +8R**, trim **100%** of remaining |
| Full stop | **weekly close < 20EMA** |
| Gain ratchet | **none** |
|  |  |
| Simulated total R | **+210.51R** |
| Mean R per trade | +4.58R |
| Sharpe-adj R | 3.22 |
| Trade count | 46 |


## By ATR bucket

| ATR% | # trades | Actual R | Optimal R | Best params |
|---|---:|---:|---:|---|
| **<3%** | 1 | -4.23R | +4.45R | T1=4.0R/30% · T2=+6R/70% · T3=— · Stop=d20EMA · Ratch=r5→3 |
| **3-5%** | 7 | +20.61R | +24.09R | T1=4.0R/30% · T2=+6R/30% · T3=+12R/100% · Stop=wk20EMA · Ratch=r8→5 |
| **5-7%** | 16 | +40.83R | +91.99R | T1=4.0R/30% · T2=wk10EMA/30% · T3=— · Stop=wk20EMA · Ratch=∅ |
| **7-10%** | 15 | +35.59R | +47.94R | T1=4.0R/30% · T2=+8R/70% · T3=— · Stop=trail2ATR · Ratch=∅ |
| **10%+** | 7 | +23.89R | +64.76R | T1=2.5R/30% · T2=wk10EMA/30% · T3=— · Stop=d30EMA · Ratch=∅ |

## By hold archetype

Tactical (1-3d) trades = positions stopped or scaled out within 3 business days. Core (4-8d) = the main two-leg system trades. Swing (>8d) = extended trend-followers.

| Archetype | # trades | Actual R | Optimal R | Best params |
|---|---:|---:|---:|---|
| **tactical (1-3d)** | 13 | +16.10R | +32.62R | T1=4.0R/30% · T2=wk10EMA/30% · T3=— · Stop=wk20EMA · Ratch=∅ |
| **core (4-8d)** | 14 | +37.12R | +56.36R | T1=4.0R/30% · T2=+8R/70% · T3=+8R/100% · Stop=d30EMA · Ratch=∅ |
| **swing (>8d)** | 19 | +63.46R | +131.47R | T1=4.0R/30% · T2=wk10EMA/30% · T3=+8R/100% · Stop=wk20EMA · Ratch=∅ |

## By entry market regime

Bull regime = SPY closed above its 21EMA on the trade entry day. Pullback = SPY below 21EMA. Use this to gauge whether aggressive sell-into-strength rules help in strong tape vs defensive EMA-break rules help when the market is correcting.

| Regime | # trades | Actual R | Optimal R | Best params |
|---|---:|---:|---:|---|
| **bull** | 33 | +76.42R | +148.59R | T1=4.0R/30% · T2=wk10EMA/30% · T3=+8R/100% · Stop=wk20EMA · Ratch=r8→5 |
| **pullback** | 13 | +40.26R | +68.52R | T1=4.0R/30% · T2=d5dLow/70% · T3=— · Stop=wk20EMA · Ratch=∅ |

## Biggest missed-gain trades

Trades where the optimizer's exit chain produced significantly more R than the actual exit.

| Ticker · Entry | Actual R | Optimal R | Δ R |
|---|---:|---:|---:|
| MU · 2026-04-12 | +10.36R | +48.91R | **+38.55R** |
| SNXX · 2026-04-21 | +2.68R | +31.43R | **+28.75R** |
| MRVL · 2026-03-31 | +5.72R | +16.30R | **+10.57R** |
| AAOI · 2026-02-18 | +2.13R | +12.24R | **+10.11R** |
| NBIS · 2026-04-05 | +5.94R | +15.27R | **+9.33R** |
| DOCN · 2026-03-15 | +6.34R | +15.36R | **+9.02R** |
| NOK · 2026-04-29 | +4.11R | +12.95R | **+8.85R** |
| BABA · 2026-01-11 | -4.23R | +3.44R | **+7.67R** |
| NVTS · 2026-05-10 | +4.24R | +9.99R | **+5.75R** |
| DXYZ · 2026-04-30 | +7.30R | +12.23R | **+4.93R** |
| AMDL · 2026-03-17 | +0.10R | +4.89R | **+4.79R** |
| BE · 2026-04-08 | +7.33R | +11.86R | **+4.52R** |
| ARM · 2026-03-30 | +0.58R | +4.53R | **+3.95R** |
| GEV · 2026-01-15 | -0.54R | +2.93R | **+3.47R** |
| KLIC · 2026-04-08 | +1.88R | +4.82R | **+2.94R** |

## Pyramid campaigns

Same-ticker, same-direction trades opened within 60 business days of each other are grouped as a pyramid campaign. 
`Counterfactual R` = first layer simulated alone under the optimal Phase-3 rules, out to the campaign's final exit. 
`Δ R = Actual − Counterfactual`: positive means pyramiding added value, negative means the additional layers were a drag vs holding the first layer alone with the patient rules.

| Ticker · # layers | First → Last entry | Actual R | Counterfactual R | Δ R |
|---|---|---:|---:|---:|
| **AXTI** · 7 layers (short) | 2026-03-23 → 2026-03-31 | +144.01R | +4.54R | **+139.47R** |
| **DOCN** · 3 layers (long) | 2026-03-15 → 2026-05-19 | +26.84R | +15.36R | **+11.48R** |
| **MU** · 3 layers (long) | 2026-01-14 → 2026-04-12 | +13.52R | +5.42R | **+8.11R** |
| **NVTS** · 3 layers (long) | 2026-03-15 → 2026-05-10 | +10.95R | -2.84R | **+13.79R** |
| **BE** · 15 layers (long) | 2026-02-10 → 2026-05-19 | +10.00R | -1.80R | **+11.80R** |
| **SOXS** · 4 layers (long) | 2026-05-06 → 2026-05-17 | +7.70R | -4.97R | **+12.67R** |
| **SNXX** · 2 layers (long) | 2026-04-21 → 2026-04-21 | +7.63R | +58.05R | **-50.42R** |
| **NBIS** · 9 layers (long) | 2026-04-05 → 2026-05-18 | +7.17R | +15.27R | **-8.11R** |
| **NMAX** · 4 layers (long) | 2026-04-21 → 2026-04-21 | +3.79R | -0.37R | **+4.16R** |
| **NOK** · 3 layers (long) | 2026-04-29 → 2026-05-10 | +3.76R | +12.95R | **-9.19R** |
| **ARM** · 5 layers (long) | 2026-01-20 → 2026-04-15 | +3.53R | -1.38R | **+4.91R** |
| **USAR** · 2 layers (long) | 2026-04-29 → 2026-05-04 | +3.13R | -4.40R | **+7.53R** |
| **ALAB** · 5 layers (long) | 2026-05-10 → 2026-05-18 | +2.42R | +9.64R | **-7.22R** |
| **CIFR** · 2 layers (long) | 2026-04-23 → 2026-05-04 | +2.20R | -1.71R | **+3.91R** |
| **FLY** · 2 layers (long) | 2026-01-06 → 2026-01-06 | +2.04R | +0.57R | **+1.48R** |
| **METU** · 3 layers (long) | 2026-02-08 → 2026-05-05 | +1.99R | -1.95R | **+3.94R** |
| **APA** · 3 layers (short) | 2026-03-30 → 2026-03-30 | +1.94R | +4.06R | **-2.12R** |
| **AAOI** · 2 layers (long) | 2026-02-18 → 2026-04-29 | +1.86R | +12.24R | **-10.39R** |
| **CRWV** · 2 layers (long) | 2026-01-13 → 2026-01-26 | +1.44R | +1.18R | **+0.26R** |
| **NAIL** · 2 layers (long) | 2026-02-02 → 2026-02-26 | +1.39R | -1.00R | **+2.39R** |
| **PL** · 12 layers (long) | 2026-02-17 → 2026-05-07 | +1.29R | +9.78R | **-8.50R** |
| **APLD** · 3 layers (long) | 2026-01-06 → 2026-01-25 | +1.26R | -1.00R | **+2.26R** |
| **VG** · 2 layers (long) | 2026-03-18 → 2026-03-19 | +1.02R | -1.74R | **+2.76R** |
| **VRT** · 3 layers (long) | 2026-02-23 → 2026-03-16 | +0.91R | -1.64R | **+2.55R** |
| **ARKK** · 8 layers (short) | 2026-02-10 → 2026-04-05 | +0.49R | -1.02R | **+1.52R** |
| **FIG** · 2 layers (long) | 2026-05-14 → 2026-05-18 | +0.28R | -0.23R | **+0.51R** |
| **FSLY** · 5 layers (long) | 2026-03-01 → 2026-05-03 | +0.10R | +1.47R | **-1.37R** |
| **PLTR** · 8 layers (short) | 2026-01-07 → 2026-03-24 | +0.08R | +5.70R | **-5.62R** |
| **GLW** · 6 layers (long) | 2026-02-22 → 2026-05-10 | +0.04R | -1.61R | **+1.65R** |
| **TSLL** · 2 layers (long) | 2026-05-10 → 2026-05-20 | -0.32R | -1.00R | **+0.68R** |
| **META** · 2 layers (long) | 2026-02-04 → 2026-02-04 | -0.94R | -1.22R | **+0.28R** |
| **RKLB** · 2 layers (long) | 2026-01-14 → 2026-03-16 | -1.02R | +0.84R | **-1.87R** |
| **CIEN** · 2 layers (long) | 2026-03-23 → 2026-04-15 | -1.16R | -1.80R | **+0.65R** |
| **RCAT** · 2 layers (long) | 2026-03-13 → 2026-03-23 | -1.24R | -1.78R | **+0.53R** |
| **SLV** · 2 layers (long) | 2026-05-07 → 2026-05-14 | -1.37R | -1.00R | **-0.37R** |
| **DDOG** · 2 layers (long) | 2026-05-14 → 2026-05-14 | -1.38R | +4.81R | **-6.20R** |
| **ACMR** · 3 layers (long) | 2026-04-21 → 2026-05-20 | -1.39R | -1.00R | **-0.39R** |
| **CCJ** · 2 layers (long) | 2026-02-23 → 2026-04-14 | -1.41R | -2.16R | **+0.75R** |
| **CRCL** · 2 layers (long) | 2026-05-10 → 2026-05-14 | -1.49R | -1.87R | **+0.37R** |
| **CSIQ** · 2 layers (long) | 2026-01-22 → 2026-01-25 | -1.57R | -1.45R | **-0.11R** |
| **NOWL** · 2 layers (long) | 2026-05-18 → 2026-05-19 | -1.78R | -0.21R | **-1.56R** |
| **ONDS** · 4 layers (long) | 2026-04-23 → 2026-04-30 | -1.87R | -1.16R | **-0.71R** |
| **SNDK** · 2 layers (long) | 2026-02-22 → 2026-02-22 | -2.05R | -1.48R | **-0.58R** |
| **OUST** · 2 layers (long) | 2026-05-14 → 2026-05-14 | -2.08R | -2.13R | **+0.05R** |
| **SOLS** · 3 layers (long) | 2026-03-01 → 2026-03-17 | -2.45R | -1.60R | **-0.86R** |
| **ERO** · 2 layers (long) | 2026-02-22 → 2026-02-24 | -2.69R | -1.73R | **-0.96R** |
| **OPEN** · 4 layers (long) | 2026-04-20 → 2026-05-04 | -2.93R | -1.56R | **-1.36R** |
| **CAR** · 5 layers (short) | 2026-04-06 → 2026-04-20 | -3.29R | -11.00R | **+7.71R** |
| **CWEB** · 2 layers (long) | 2026-04-16 → 2026-05-12 | -3.96R | -1.29R | **-2.67R** |
| **BABA** · 5 layers (long) | 2026-01-05 → 2026-02-02 | -24.51R | +1.52R | **-26.03R** |

**Net pyramid impact**: 28 campaigns added R, 22 subtracted. Total Δ = +101.56R.


## Sensitivity — top-5 parameter sets (by total R)

Tight cluster around similar rules = robust recommendation. Scattered = fragile.

1. T1=4.0R/30% · T2=wk10EMA/30% · T3=+8R/100% · Stop=wk20EMA · Ratch=∅ → **+210.51R**
2. T1=4.0R/30% · T2=wk10EMA/50% · T3=+8R/100% · Stop=wk20EMA · Ratch=∅ → **+209.58R**
3. T1=4.0R/30% · T2=wk10EMA/30% · T3=+8R/50% · Stop=wk20EMA · Ratch=∅ → **+209.37R**
4. T1=4.0R/30% · T2=wk10EMA/50% · T3=+8R/50% · Stop=wk20EMA · Ratch=∅ → **+208.77R**
5. T1=4.0R/30% · T2=wk10EMA/70% · T3=+8R/100% · Stop=wk20EMA · Ratch=∅ → **+208.66R**

---

_Report generated by `pipeline.portfolio.backtest_optimizer`. Re-run any time after exporting a fresh CSV into `data/portfolio/`._
