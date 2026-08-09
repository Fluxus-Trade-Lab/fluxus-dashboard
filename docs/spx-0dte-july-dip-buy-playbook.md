# SPX / SPY Short-Dated Options — July 1–17 Seasonal Dip-Buy Playbook

*Built 2026-07-01. Entry reference: SPX 7,499 (June 30 close). Backtested on 21 years of SPY 5-min data (2005–2025) + 26 years of daily S&P.*

---

## 1. The thesis (two forces stack)

**Seasonality** — July 1–17 is one of the most bullish windows of the year, with a mid-month peak (~July 17). **Gamma regime** — spot sits just below a positive-gamma shelf, so the *base case* is a grind up into it; below the shelf, dealers *amplify rebounds* off dips.

→ You **buy stabilized morning dips with slightly-ITM short-dated calls**, hold into the afternoon, and manage out before the close.

---

## 2. What the backtest proved (real data, not vibes)

**Daily (26 yrs, S&P):**
- July 1→17 window closes **green 73%** of years (avg +1.08%, median +1.56%).
- **Day 1 of July up 85%** — the strongest single tell.
- A dip ≥0.5% below the entry appears **69%** of years; when it does, still green by the 17th **70%** of the time.
- Path grinds up, **accelerating into days 8–10 (~July 11–15)**. Worst year 2002: −8.46% (tail risk is violent when it fails).

**Intraday (21 yrs, SPY 5-min):**
- Morning dips **reverse** — but the naked 0DTE ATM call is a **break-even lottery** (+2%/trade, median −60%) because the premium + theta hurdle eats the modest bounce. *Being right on direction ≠ making money on a 0DTE.*
- Fix #1 — **go slightly ITM** (delta ~0.6): flips 0DTE median from −60% → +30%.
- Fix #2 — **use 1DTE** (if holding overnight): doubler rate 29% → 42%, avg +22%/trade.
- **OTM calls LOSE** (−4% to −9%/trade, ~32% win) — never buy OTM here.
- Implied daily move (0.97%) ≈ intraday **range** (1.02%) → vol is **fairly priced**; premium selling only looks good if you ignore the path.

**Intraday shape (the whole day's +0.10% drift is earned in the afternoon):**
- Morning 9:30–11:00: **flat/choppy** — this is where the **low forms** (50% of daily lows in the first hour).
- Climb starts ~11:30; **day's high clusters at 3pm** (32%).
- Power hour 15:30–close **fades** (only 47% positive).

---

## 3. The two strategies — pick by overnight tolerance

### A) Flat-by-close (no overnight) → **0DTE, slightly ITM, exit ~3:30pm**
- **Entry:** a **0.5%+ flush** off the day's open, in the **9:30–10:30** window (let the dip come — don't chase the open).
- **Strike:** call **~0.3–0.5% ITM** (delta ~0.6–0.7). *Never ATM/OTM.*
- **Exit:** **3:30pm** (captures the afternoon push, skips the power-hour fade), or TP/stop first.
- **Backtest:** ~55% win, **+13%/trade**, median +15%, 24% double.

### B) Overnight OK → **1DTE, slightly ITM (~0.3%), hold toward next-day expiry**
- Same 0.5% flush entry, same ITM strike.
- Hold through the overnight drift + next-day continuation (that's the edge), manage with TP/stop.
- **Backtest:** ~55% win, **+22%/trade**, median +52%, **42% double**.
- **Caveat:** the edge *is* the overnight gap — your stop can't protect a gap-down. Higher variance.

> **One-line rule:** *Slightly ITM, always. Same-day → 0DTE exit 3:30. Overnight OK → 1DTE to expiry. Never OTM. Never hold a same-day 1DTE (you pay for time you don't use).*

---

## 4. Entry trigger, sizing, exits
- **Trigger:** intraday drop of **≥0.5%** below the day's open, morning session. Buy the flush directly — the *reclaim filter tested WORSE* (−9%), so don't wait for confirmation.
- **Size small, defined risk** (max loss = premium). Cap ~2–3 attempts/day + a daily stop.
- **Manage:** scale half at **+50–60%**, hold the rest toward **+100%**, stop ~**−60%**.
- **Time exit:** ~**3:00–3:30pm** for the same-day version.

---

## 5. Gamma regime — match the structure to the regime
Reference levels (from the June 30 gamma profile; **refresh daily**, they shift with spot):
- **Below ~7,524 (negative gamma):** dealers amplify → **BUY premium** (the dip-buy calls). Prime zone.
- **Inside 7,524–7,637 (positive gamma), peak pin ~7,585:** dealers suppress range → **the only place to SELL premium** (0DTE iron fly centered ~7,585). Situational, not a standalone edge.
- **Above 7,637 (negative gamma again), max-neg ~7,812:** momentum fuel, but max instability — tight stops.

**Premium selling verdict:** at VIX 16–17 the credit is thin (condors collect 28–41% of width; put spreads 14–20%) and vol is fairly priced vs the path. Sell an iron fly **only** when spot sits inside the positive-gamma pocket; otherwise skip it.

---

## 6. Kill switch & aggression calendar
- **Kill switch:** if **7,440 breaks and holds**, the edge inverts (neg-gamma air pocket lower) — stop buying calls. Stand down into scheduled events (CPI/jobs/FOMC); pins don't hold through them.
- **Most aggressive days:** **July 1** (85% up) and the **mid-window ramp (July 11–15)**. Days 2–4 (post-July-4 lull) are the choppiest — where *the* buyable flush usually forms.

---

## 7. Live-levels translation (SPX 7,499)
- 0.5% flush ≈ **37 pts → dip to ~7,462**.
- Buy the **~0.3% ITM call**: SPX **7,475** strike / XSP **747.5** / SPY ~ the delta-0.6 line. Delta ~0.6.

---

## 8. Tooling & data (this repo)
- `scripts/ibkr_intraday_download.py` — pull SPY/ES intraday July windows from IBKR (used for this backtest).
- `scripts/ibkr_daily_option_plan.py` — **daily forward planner**: today's + tomorrow's option chain, IV, deltas, and put/call walls (support/resistance). Run each morning.
- `ibkr_SPY_5mins_julywindows.csv` — the 21-yr backtest dataset.
- Backtest scripts were run inline; re-derive from the CSV.
- `pipeline/gex/` — **GEX engine** (daily 8am ET auto-run): SPX+QQQ dealer-gamma
  structure (3 tenors: front 0–2DTE · swing 5–14DTE · monthly OPEX) →
  `data/gex/latest.json` + HTML brief. Manual run: `.venv/bin/python -m pipeline.gex.engine`.
  See `docs/plans/2026-07-11-gex-engine-design.md` and `docs/gex-engine-setup.md`.

---

## 9. Honest limitations
- IV modeled from IBKR's daily-IV field (×√252 → annualized); not the exact 0DTE/1DTE surface. Directionally sound, not penny-precise.
- No transaction costs modeled — SPY penny spreads are fine; **SPX/XSP spreads are wider, shave a few % off expectancy**.
- Small-sample slices (day-of-window, hour buckets) are suggestive, not proven — don't over-tune.
- Everything here is a **tendency with a tail**. Size for the 2002/2008-style failure, not just the base case.

---

## 10. Live worked example (July 1, 2026) & $5,000 sizing

**Live read (from `ibkr_daily_option_plan.py`):** spot ~7478; 0DTE expected move ±34 pts (0.46%); ATM IV ~19.5%. Support (put walls) **7450 / 7440 / 7400**; resistance (call walls) **7500 / 7570**. 7500 is a battleground (heavy call *and* put OI + round number). 1DTE (Jul 2): spot ~7485, IV ~16%, expected move ±56 pts, support 7450/7400/7350, resistance 7500/7550.

**Capital reality:** on SPX, **$5,000 = 1 contract** (~$3,200–4,600 premium depending on strike/time). SPX is coarse — you can't fine-tune size with $5k. Accept it or use SPY for granularity (user declined XSP).

### The core trade card — 0DTE 0.5% flush → 0.6Δ call

| | |
|---|---|
| **Setup** | July window, spot below the shelf, morning session |
| **Trigger** | 0.5% flush off the open → **~7441**, into the 7440–7450 put-wall support, that **holds** (buy the flush, no reclaim wait) |
| **Strike** | **~0.6Δ 0DTE call** (slightly ITM); at a 7441 entry ≈ the **7419–7430** strike |
| **Size** | $5,000 → **1 contract** (~$4,600 at risk), ~$60 per SPX point, rising as it goes ITM |
| **Targets** | **7500** (call wall / recover the dip + push) → **7525** (good-day) |
| **Stop** | ~−60% of premium; hard invalidation if **7400 breaks and holds** |
| **Time exit** | ~3:30pm (afternoon strength peaks ~3pm; power hour fades) |

**$5k P&L (entry ~7441, exit ~2h later, IV crush 21%→18%):**

| Exit SPX | Move from entry | P&L | Return |
|---|---|---|---|
| 7441 (flat) | +0 | −$1,077 | −23% |
| 7465 (break-even ~here) | +24 | +$659 | +14% |
| **7500 (target)** | +59 | **+$3,679** | +80% |
| 7515 | +74 | +$5,086 | +110% |
| **7525 (target)** | +84 | **+$6,047** | +131% |
| 7550 | +109 | +$8,496 | +184% |
| Downside / −60% stop | — | **−$2,776** | −60% |

*The dip entry is the edge: buying the 7441 flush and targeting the 7500 recovery is a +59-pt move, vs only +25 pts if you buy at 7475. Same target, far bigger payoff — but 1 SPX contract puts ~$4,600 at risk, which is NOT "small."*

### 0DTE vs 1DTE ($5k, buy 7475 call on the dip, realistic exit)

| Exit | 0DTE (same-day ~2h) | 1DTE (next-day ~300min left) |
|---|---|---|
| 7500 | +$727 (+23%) | +$668 (+19%) |
| 7525 | +$2,541 (+79%) | +$2,451 (+72%) |
| Hit target LATE | 7500 = **−$191** (theta death) | 7500 = **+$668** (time value survives) |
| Expiry cliff | n/a (same day) | ≤ strike at Jul-2 close = **−100%** |

**Rule of thumb:** 0DTE = be right *today* and reasonably fast, flat by 3:30. 1DTE = the move gets *room + time* (expected move ±56 vs ±34, so 7525 is ~0.9σ vs 1.5σ), forgives slow/overnight moves, but manage out before the expiry cliff and carry overnight gap risk. Backtest expectancy: 0DTE +13%/trade, 1DTE +22%/trade.

---

## 11. Pre-holiday window (July 2–3) & the 5DTE-ES variant

**Verified seasonals (2000–2025):** 1st trading day of July up **85%**; July 1 up 78%; **July 2 is the SOFT spot** (up 61% daily, only **54% intraday**, avg −0.16%); **July 3 up 81%** (2nd-best day — but historically a half-day). Edge = **buy July 2 weakness, the pre-holiday bid pays into July 3** — not day-trading July 2 in isolation.

**2026 wrinkle:** July 3 has **equities fully CLOSED** (July 4 = Saturday → observed Fri), only a thin shortened ES futures session. So (a) the pre-holiday bid likely **pulls forward into July 2** (last liquid session), and (b) the July 3 ES session is thin/wide — **don't hold options into Friday afternoon**. Favor **flat by Thursday July 2 close**, or exit only early-Friday.

**5DTE-ES structure (user's account can only trade 5DTE ES):** buy the **July-6 expiry** ES option on a July 2 dip, **flat before the weekend** → a ~2–4 DTE option (lower theta, cleaner P&L than 0DTE on the same move) that never carries weekend theta or gap. Same dip-buy logic, but it's a swing (low gamma, more vega) riding the pre-holiday drift, not the intraday reversal.

**Tooling:** `scripts/ibkr_es_option_plan.py` — ES options-on-futures planner (spot, expected move, top-3 OI walls, ~0.6Δ call) for a given `--expiry` (e.g. 20260706). Works live. Note: a July-6 option's IV reads artificially low (~9%) because it's annualized over the dead July-4 weekend — real trading-window vol is ~18–20%; favorable if you exit before the weekend (cheap premium, no weekend theta). `scripts/es_overnight_watch.py` — quick on-demand ES globex re-pull (current price, overnight high/low + time, distance to levels). `scripts/ibkr_intraday_download.py --rth 0` pulls full-session ES (overnight).

**ES overnight behavior (recent 31 sessions, current regime — NOT seasonal):** ≥0.3% overnight dip 55% of nights (avg −0.41%); buying the overnight low → next RTH close green 61%, +0.33%. Overnight low forms in the US-evening/Asia session (16:00–20:00 ET, ~49%) or pre-open (~09:00, 13%). → mild support for a dip-buy-then-recover play; overnight is a directional-scalp env (thin premium), not for selling theta.

**Executed plan (July 2):** dip-buy-then-recovery via 0.6Δ July-6 ES call. Enter on an overnight flush into ~7525–7537 support (or the cash-open/morning flush) that holds; ride the recovery; flat by Thursday close (early-Friday only if liquid); kill if support breaks & holds. Small size (account at $8k — keep dollar risk flat).

**Risk note:** account ran $5k→$8k (+60%) on 2026-07-01 — that was the right tail of a high-variance long-premium cluster, NOT the +13–22%/trade baseline edge. Keep dollar risk flat as the account grows; don't scale size into variance.
