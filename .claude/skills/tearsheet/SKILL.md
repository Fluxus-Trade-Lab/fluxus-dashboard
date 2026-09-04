---
name: tearsheet
description: Synthesizes the AI narrative layer (bull/bear case, trade plan, management commentary, peers, catalysts) for one ticker's tearsheet — the 个股页 AI 段 of a stock's 一页纸 — and writes it back into that ticker's ai_synthesis JSON field. Use when a ticker's L1 numeric data is already fetched and its 个股页 AI 段 needs synthesizing or refreshing, e.g. "写 <SYMBOL> 的 tearsheet" or "刷新这只票一页纸的 AI 叙事段". Uses Max-subscription compute + WebSearch/WebFetch — no paid API tokens.
when_to_use: 触发词：tearsheet、一页纸、个股页 AI 段、bull/bear case、给 <票> 做个 tearsheet、刷新 <票> 的 AI 叙事、写 <票> 的交易计划段。不触发：看 GEX、看 Signal History、跑 run_tickers 拉 L1 数据、改 tearsheet 前端组件、问某个字段怎么算。
allowed-tools: Bash, Read, Edit, Write, WebFetch, WebSearch
---

# /tearsheet — synthesize AI narrative for a ticker's tear-sheet

You are synthesizing the **AI narrative layer** of the per-ticker tear-sheet for the Fluxus Capital dashboard. The user has already fetched yfinance numeric data (Layer 1) via the pipeline. Your job is to add Layer 2 — the analyst-quality narrative.

**Argument:** the ticker symbol, e.g. `AAOI`. If no symbol is given in `$ARGUMENTS`, fail with an instruction asking for one.

## Step-by-step instructions

### Step 1 — Read the existing per-ticker JSON

Read `data/output/tickers/<SYMBOL>.json`. This contains L1 numeric data: `info`, `earnings_history`, `next_earnings`, `quarterly_metrics`, `analyst`, `news`, `options_implied_move`, `technicals`, `ohlc_1y` (last 252 daily bars), `current_price`. Note the existing `ai_synthesis` field — you will REPLACE it.

If the file doesn't exist, fail with `ERROR: ticker not in tracked set. Run python -m pipeline.tickers.run_tickers --tickers <SYMBOL> first.`

### Step 2 — Gather live context via web

Run these in parallel:

- `WebSearch` for `<SYMBOL> recent catalysts 2026` — recent news outside what yfinance has
- `WebSearch` for `<SYMBOL> analyst rating change` — fresh PT moves
- `WebSearch` for `<SYMBOL> earnings call commentary` — management quotes from the last call
- `WebFetch` the top 2-3 news URLs from the JSON's `news[]` array — read actual article content

Skim — don't go deep. The yfinance data is your ground truth for numbers; the web is for narrative color and source citations.

### Step 3 — Synthesize the AI sections

Compose an `ai_synthesis` dict with the following keys. **Be concrete and trader-actionable** — use real prices from `current_price` and `technicals.ma20/ma50/ma200/atr14`, real R-multiples, real earnings dates. The reference is the AAOI tearsheet the user provided; match that tone and density.

```json
{
  "synthesized_at": "<ISO-8601 timestamp now>",
  "management": {
    "commentary": "<1-2 sentence narrative — positioning for 2026, key strategic priorities — sourced from earnings calls / management guidance. Cite footnote refs like [1]>"
  },
  "peers": [
    {"symbol": "...", "name": "...", "focus": "<1-line industry niche>"},
    // 5-7 peers — public competitors in the same sub-industry
  ],
  "bull_case": [
    "<bullet 1: concrete positive — guidance, growth driver, secular tailwind. Cite [n] if from news/analyst.>",
    // 5-7 bullets total
  ],
  "bear_case": [
    "<bullet 1: concrete negative — valuation, execution risk, concentration, profitability. Cite [n] if applicable.>",
    // 5-7 bullets
  ],
  "trade_plan_long": {
    "name": "Trend Continuation",
    "trigger": "<e.g., 'reclaim and hold above $185 with volume; ideal entry is pullback to MA20 ($150-155) or breakout retest of $160 pivot.'>",
    "entry_zone": "<e.g., '$150–$160 (pullback) or >$185 (breakout add)'>",
    "stop": "<e.g., '$138 (below MA20 / 10-day low buffer; ~1× ATR below entry)' — use real numbers from technicals>",
    "targets": [
      "<e.g., 'T1 $192 (52W high)'>",
      "<T2 measured move>",
      "<T3 ambitious / analyst high PT>"
    ],
    "rr_note": "<e.g., 'R:R from $155 entry, $138 stop, $215 target: ≈ 3.5:1'>",
    "sizing_note": "<e.g., 'ATR-based — 1R = $17–$20/share, so a 1% account risk = ~50 shares per $1k risked' — anchor to user's R=$2,500 / 0.25% equity model when possible>"
  },
  "trade_plan_short": {
    "name": "Earnings Disappointment or Trend Break",
    "trigger": "<e.g., 'failed bounce + close below $145 (loss of MA20) on volume, OR post-earnings gap-down through $145 with no reclaim.'>",
    "entry_zone": "<...>",
    "stop": "<above broken pivot>",
    "targets": ["<MA50 zone>", "<consensus PT zone>", "<bear-case low PT>"],
    "rr_note": "<...>",
    "sizing_note": "<note about short borrow / put spread alternatives if applicable>"
  },
  "earnings_risk_note": "<e.g., 'Options-implied move on May 7 print is ±18.4%, average of last 4 post-earnings moves is ±15.7%. Consider trimming size or hedging into the print. ATR(14) of $17.48 means a normal session moves ~10%, so use wider mental stops and ATR-based sizing.' — pull options_implied_move + post_earnings_moves from L1 data>",
  "catalysts": [
    "<bullet 1: dated narrative — 'Mar 9, 2026: First volume order for 1.6T transceivers from a major hyperscale customer totaling more than $200M; shipments early Q3, completing Q4 2026.[1]'>",
    // 5-8 bullets
  ],
  "sources": [
    {"id": 1, "title": "<headline>", "url": "<url>", "source": "<publisher>", "date": "<YYYY-MM-DD>"},
    // numbered, matching [n] refs above
  ]
}
```

### Step 4 — Write back to per-ticker JSON

Read the file, update only the `ai_synthesis` and `ai_synthesized_at` fields, write back. Use the Edit tool (or Python via Bash) — do not clobber the other L1 fields.

### Step 5 — Commit

Single commit:
```
git add data/output/tickers/<SYMBOL>.json
git commit -m "$(cat <<'EOF'
ai(tearsheet): synthesize narrative for <SYMBOL>

- Bull case (N bullets) / Bear case (N bullets)
- Trade Plan: long setup at <entry zone>, short fade setup at <zone>
- Earnings risk note, peers (N), catalysts (N), sources (N)

Sources: <comma-separated source domains>

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

### Step 6 — Confirm to the user

Print a short summary:
- Symbol synthesized
- Counts (N bull bullets, N bear, N peers, N catalysts, N sources)
- Trade Plan headline (long entry zone + stop, short entry zone + stop)
- Earnings risk note (if any)
- "View at #/ticker/<SYMBOL>"

## Quality bar

- **Numbers from L1 only.** Never invent prices, EPS, revenue, ratings. Verify against the JSON's `info`, `technicals`, `analyst`, `earnings_history`, `quarterly_metrics`.
- **Narrative from web + your reasoning.** Bull/Bear, Trade Plan, catalysts narrative — synthesize from the live web context + the L1 facts. Don't hedge into uselessness; be specific.
- **Trade Plan uses ATR-based stops.** Anchor to `technicals.atr14` and the user's R = $2,500 / 0.25% equity sizing model.
- **Cite everything narrative.** Every Bull/Bear bullet and catalyst that draws from news should have a `[n]` footnote ref tying to `sources[]`.
- **Match the AAOI reference density.** Look at `docs/superpowers/specs/2026-05-24-ticker-tearsheet-design.md` if you need a tone reference.

## Refresh policy

If the existing `ai_synthesized_at` is < 7 days old AND no new earnings happened AND price hasn't moved ≥5%, you can short-circuit: print "Already fresh (synthesized <date>), skipping. Pass `--force` to re-synthesize." (Honor `--force` argument if passed.)
