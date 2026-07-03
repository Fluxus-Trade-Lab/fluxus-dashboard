# H1 2026 Performance Reports + Chinese i18n Toggle — Design

**Date:** 2026-07-03
**Author:** Andy (Fluxus Capital) w/ Claude
**Status:** Approved (pending spec review)

## Goal

Two independent deliverables for the Fluxus dashboard:

1. **Chinese language toggle** on the Vercel dashboard (upper-right of header), professional
   finance terminology, covering UI/labels across all 8 main nav pages. **Built and shipped first.**
2. **Half-year (H1) 2026 performance reports** — two separate PDF deliverables:
   - **Investor Pitch** for the user's aunt (raise ≥ $1M).
   - **Internal Review** for the user (candid self-improvement).

Data cutoff for both reports: **June 30, 2026** (the 3 July trades are excluded).

## Build order

1. **i18n toggle** → verify → **commit + push first** (user priority).
2. Shared H1 data layer.
3. Investor Pitch PDF.
4. Internal Review PDF.

---

## Workstream 1 — Chinese i18n Toggle

### Approach: lightweight custom context (no new dependency)

Matches the existing `useTheme` hook pattern; avoids pulling in `react-i18next` (overkill for
label-level translation).

### Components
- `frontend/src/hooks/useLanguage.js` — context + hook, `{ lang, setLang, toggle, t }`.
  Persists to `localStorage` (`fluxus-lang`), default `en`.
- `frontend/src/lib/translations/` — one file per page namespace + `common.js` (nav, header,
  shared buttons/badges). Per-namespace files keep the dictionary maintainable and allow
  parallel work without merge conflicts. `index.js` merges them into `{ en: {...}, zh: {...} }`.
- `t('namespace.key')` helper; falls back to the English string if a key is missing so nothing
  ever renders blank.
- **Toggle UI:** compact `EN / 中文` segmented control in `Header.jsx`, immediately left of the
  theme toggle (upper-right). Provider wraps the app in `App.jsx` (or `main.jsx`).

### Scope
- **In scope:** UI chrome only — nav items, page titles, section headings, column/table labels,
  button labels, status badges, empty/loading states, tooltips — across all 8 pages
  (Dashboard, Screener, Portfolio, Trade Journal, AI Coach, Briefing, Breadth, Model Books).
- **Out of scope:** data values (tickers, numbers, prices, dates), long AI-generated prose
  (briefings/coach narratives stay in their source language).

### Terminology (professional finance zh-CN, not literal)
| EN | zh-CN |
|----|-------|
| Open (positions) | 未平仓 |
| Entry / Entry Price | 建仓价 |
| Stop | 止损 |
| Last (price) | 最新价 |
| Unrl% (unrealized) | 未实现盈亏% |
| Rlzd% (realized) | 已实现盈亏% |
| Mkt Val | 市值 |
| WT% (weight) | 仓位权重% |
| RR (risk/reward) | 风险回报比 |
| Win% | 胜率 |
| Return | 收益率 |
| Drawdown | 回撤 |
| P/L | 盈亏 |
| Cash | 现金 |
| Dir (direction) | 方向 · Long 多 / Short 空 |
| Portfolio | 投资组合 |
| Screener | 选股器 |
| Breadth | 市场广度 |

(Full table maintained in `translations/`. Terms reviewed for finance correctness.)

### Verification
Run dev server, toggle EN ↔ 中文, confirm labels switch, data unaffected, persistence across
reload, no console errors, layout doesn't break with wider CJK glyphs. Screenshot proof.

### Testing
Unit test for `t()` fallback + language persistence. Keep light.

---

## Workstream 2 — Shared H1 Data Layer (built before the reports)

`pipeline/portfolio/h1_report.py`:
- Reuses `parse_csv` + `compute_report` from `pipeline/portfolio/analytics.py` (same
  methodology as the dashboard — numbers will match).
- Reads the attached export (`portfolio_2026-07-03.csv`).
- **Cutoff = 2026-06-30:** closed trades with exit ≤ 6/30 are realized; July trades excluded;
  6 open positions carried as open.
- **Unrealized / MTM (required — headline number):** value the 6 open positions
  (NBIS, DOCN, NAIL, SLV ×2, BUG) at their **June 30, 2026 closing prices**. Source June 30
  closes via the pipeline's price adapter / price API. Headline H1 return =
  **realized P&L + unrealized MTM** on $1.0M starting capital.
- Emits `data/output/h1_2026_stats.json`: headline return %, ending equity, realized vs
  unrealized split, monthly table (Jan–Jun: return%, #trades, win%, avg gain/loss, max
  gain/loss), overall win rate, avg R / expectancy, best & worst trades, sector attribution,
  risk stats (Sharpe, Sortino, Calmar, max drawdown), vs-SPY comparison.
- **Both reports read only this JSON** → pitch and internal review can never disagree.

---

## Workstream 3 — The Two Reports (HTML slides → PDF)

Authored as designed HTML/CSS slides (16:9), charts rendered inline, printed to PDF for maximum
design control ("visually strong," hedge-fund style). Output to `reports/`.

### 3a. `Fluxus_H1_2026_Investor_Pitch.pdf` (for the aunt)

**Audience:** aunt — successful wholesale cotton/fabric entrepreneur, ~$3M/yr profit,
detail-oriented, decisive ("fire-type"), high EQ, family-supportive. Little finance knowledge.

**Framing strategy:**
- Speak in **margin/ROI/inventory-turn language she already lives in** (relate returns to
  business margins she understands).
- Lead with the **stunning headline** (H1 return incl. unrealized vs SPY ~9%).
- **Transparency & risk controls** front and center (she's detail-oriented) — stops, position
  sizing, how capital is protected, quarterly statements.
- **Long-term arc / the real ask:** start with a trust-building allocation now → in 5–10 years
  form a **family office for generational wealth** that supports her family for generations.
  This is the emotional spine, not a footnote.
- No jargon; every finance term explained in one line.

**Deck (~10–12 slides):**
1. Cover — "A Private Family Investment Proposal" (personal name placeholder to fill).
2. The result in one number (H1 return incl. unrealized) vs the market.
3. What I actually do — plain language (disciplined stock selection + strict risk rules).
4. Equity curve vs SPY (the chart).
5. Consistency — monthly track record (Jan–Jun).
6. How I protect your capital — stops, sizing, drawdown discipline (detail-oriented reassurance).
7. Why this is different from gambling — process, rules, repeatability.
8. The vision — trust now → family office → generational wealth for the family.
9. **The offer & how you're rewarded** (terms below).
10. What I'm asking for / next steps.
11. Appendix — the numbers, transparency, how she can verify.

**Reward structure (recommended, aunt-friendly):**
- **8% annual preferred return (hurdle):** her capital earns 8% before the manager earns
  anything.
- **Profit share above the hurdle: 80% her / 20% manager** on the excess.
- **No fixed management fee** — manager only earns when she profits.
- Quarterly statements, defined lock-up + redemption terms, high-water mark.
- Side-by-side box showing the industry-standard **"2 & 20"** to demonstrate she's getting
  better-than-market terms.

### 3b. `Fluxus_H1_2026_Internal_Review.pdf` (for the user)

**Audience:** the user. Candid, data-dense, warts included.

**Contents:**
- Full stats dashboard (return, Sharpe/Sortino/Calmar, expectancy, R-distribution).
- What's working (e.g., May +51%; winning setups/sectors).
- What's dragging (Feb/Mar drawdown; the 3 weak July trades; any panic-trim leakage via
  `panic_trim_leak` / exit-style classification).
- Per-trade P&L attribution, top winners/losers, sector attribution.
- Behavioral patterns (revenge-trade clusters, trim discipline).
- Concrete "improve next half" action list.

---

## Risks / open items
- **June 30 open-position prices:** need a reliable source for 6/30 closes (pipeline adapter or
  price API). If unavailable, fall back to nearest trading-day close and note it.
- **Aunt's name:** not provided; cover uses a respectful placeholder to fill in.
- **CJK layout:** verify wider glyphs don't break dense tables (Portfolio page).
