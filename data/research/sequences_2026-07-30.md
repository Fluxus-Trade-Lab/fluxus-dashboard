# Sequence mining — as of 2026-07-30

## Read this before the table

- **One regime.** 89 archive sessions across a single market environment. A sequence that works here may only be describing that environment.
- **Multiple comparisons.** 42 sequences were tested against this one sample; some will look excellent by chance. Every number in the ranking table is reported **net of a random-entry baseline** drawn from *the same sequence's tickers* and the same dates — so it measures timing, not which companies keep clearing screeners. The baseline is the mean of 20 independent redraws; its own spread is in `baseline_sd_median_excess` — where that is comparable to the net edge, the net edge is noise.
- **The stability filter is weak.** Under pure noise two half-samples agree in sign about **50%** of the time. Observed: **46%** of the 39 adequately-powered sequences passed (18 of 39). A pass rate near 50% means the filter is not discriminating — it is removing coin flips, not identifying edge.
- **Instances are not independent.** Sequences fire in clusters: many names confirm on the same session, and those outcomes share one day of market. The `distinct_signal_dates` column is a much better guide to effective sample size than `n`.
- **Survivorship.** Prices were fetched today, so delisted and renamed tickers are missing (44 of 3872 tickers). Those failures skew toward losers, so the surviving numbers are, if anything, flattering. Per-sequence instances lost to missing prices are in the `lost` column.
- **The tail is unmeasurable.** The price panel ends with the archive, and the longest horizon needs 21 forward sessions, so the last signal date that can be measured at all is **2026-06-30** — 12 of 89 archive sessions contribute zero instances. This makes the half-sample split **asymmetric**: 45/45 measurable sessions in the first half vs 32/44 in the second. That is not a 50/50 split, and the second half is the thinner one, so the stability check leans on less data exactly where the market is most recent.
- **Window.** 10 archive sessions. The archive omits non-session and untrustworthy days, so an N-session gap spans more calendar time than N days.
- Ranked on `net_median_excess_10`; `--min-n 20`, `--seed 42`.

## Survived the guards (stability + power — NOT a profitability test)

Passing here means a sequence had enough instances and did not flip sign between the two half-samples. It says nothing about whether the sequence made money. Sequences below are split by whether their net edge is actually positive.

### Positive net edge (0)

_None. Nothing that survived the guards beat its own random-entry baseline._

### Negative net edge (18) — stable losers

| Sequence | n | distinct dates | lost | net median excess (10d) | baseline sd | net median MFE (R) | net median MAE (R) | net win rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| vol_up_gainers -> gainers_4pct | 2385 | 76 | 583 | -0.4% | 0.3% | +0.16 (raw 1.68) | -0.23 (raw -1.40) | -2pp (raw 47%) |
| ema21_watch -> healthy_charts | 3475 | 76 | 347 | -1.1% | 0.2% | -0.28 (raw 1.46) | -0.29 (raw -1.46) | -5pp (raw 48%) |
| healthy_charts -> ema21_watch | 3746 | 76 | 471 | -1.1% | 0.2% | -0.28 (raw 1.46) | -0.30 (raw -1.45) | -5pp (raw 48%) |
| gainers_4pct -> vol_up_gainers | 2416 | 76 | 508 | -1.5% | 0.3% | +0.07 (raw 1.61) | -0.42 (raw -1.58) | -4pp (raw 45%) |
| vol_up_gainers -> ema21_watch | 347 | 70 | 70 | -1.8% | 0.7% | -0.42 (raw 1.47) | -0.24 (raw -1.40) | -7pp (raw 49%) |
| vol_up_gainers -> vcp | 60 | 41 | 5 | -2.0% | 1.1% | +0.03 (raw 1.79) | -0.37 (raw -1.51) | -9pp (raw 43%) |
| momentum_97 -> ema21_watch | 653 | 76 | 123 | -2.1% | 0.5% | -0.29 (raw 1.59) | -0.20 (raw -1.33) | -7pp (raw 49%) |
| episodic_pivot -> gainers_4pct | 282 | 70 | 18 | -2.4% | 1.0% | -0.05 (raw 1.69) | -0.29 (raw -1.41) | -7pp (raw 46%) |
| gainers_4pct -> vcp | 286 | 71 | 20 | -2.6% | 0.7% | -0.29 (raw 1.51) | -0.38 (raw -1.49) | -11pp (raw 43%) |
| momentum_97 -> healthy_charts | 1990 | 76 | 201 | -2.7% | 0.4% | -0.18 (raw 1.67) | -0.39 (raw -1.54) | -8pp (raw 47%) |
| ema21_watch -> vcp | 404 | 75 | 76 | -2.8% | 0.5% | -0.26 (raw 1.46) | -0.27 (raw -1.42) | -14pp (raw 41%) |
| vcp -> healthy_charts | 389 | 76 | 26 | -3.0% | 0.5% | -0.28 (raw 1.46) | -0.42 (raw -1.59) | -13pp (raw 43%) |
| healthy_charts -> vcp | 408 | 76 | 35 | -3.6% | 0.6% | -0.30 (raw 1.47) | -0.42 (raw -1.54) | -15pp (raw 40%) |
| vol_up_gainers -> episodic_pivot | 137 | 58 | 12 | -3.8% | 1.4% | -0.04 (raw 1.81) | -0.69 (raw -1.79) | -12pp (raw 44%) |
| gainers_4pct -> episodic_pivot | 247 | 67 | 25 | -3.8% | 1.2% | +0.00 (raw 1.77) | -0.69 (raw -1.78) | -12pp (raw 43%) |
| vcp -> vol_up_gainers | 74 | 39 | 7 | -3.9% | 1.3% | -0.61 (raw 1.21) | -0.56 (raw -1.70) | -21pp (raw 36%) |
| episodic_pivot -> vol_up_gainers | 173 | 62 | 4 | -4.1% | 1.1% | -0.07 (raw 1.78) | -0.50 (raw -1.62) | -12pp (raw 43%) |
| momentum_97 -> vcp | 73 | 46 | 8 | -5.4% | 2.0% | -0.48 (raw 1.37) | -0.52 (raw -1.69) | -21pp (raw 36%) |

## Excluded — unstable across half-samples

| Sequence | n | net median excess |
|---|---:|---:|
| gainers_4pct -> ema21_watch | 1558 | -0.9% |
| ema21_watch -> gainers_4pct | 1633 | -1.1% |
| ema21_watch -> momentum_97 | 534 | -1.4% |
| vcp -> momentum_97 | 52 | -1.4% |
| healthy_charts -> gainers_4pct | 2831 | -1.5% |
| gainers_4pct -> momentum_97 | 2622 | -1.6% |
| healthy_charts -> episodic_pivot | 74 | -1.8% |
| gainers_4pct -> healthy_charts | 3099 | -1.8% |
| vol_up_gainers -> momentum_97 | 939 | -1.9% |
| vol_up_gainers -> healthy_charts | 983 | -2.0% |
| momentum_97 -> gainers_4pct | 2053 | -2.0% |
| vcp -> ema21_watch | 400 | -2.2% |
| vcp -> gainers_4pct | 246 | -2.2% |
| episodic_pivot -> healthy_charts | 168 | -2.3% |
| healthy_charts -> vol_up_gainers | 696 | -2.4% |
| healthy_charts -> momentum_97 | 1742 | -2.5% |
| ema21_watch -> episodic_pivot | 36 | -2.7% |
| momentum_97 -> vol_up_gainers | 571 | -2.7% |
| ema21_watch -> vol_up_gainers | 383 | -2.8% |
| episodic_pivot -> momentum_97 | 169 | -2.9% |
| momentum_97 -> episodic_pivot | 62 | -5.3% |

## Excluded — fewer than 20 instances

| Sequence | n | net median excess |
|---|---:|---:|
| episodic_pivot -> ema21_watch | 18 | -1.7% |
| vcp -> episodic_pivot | 4 | -5.1% |
| episodic_pivot -> vcp | 2 | -6.1% |
