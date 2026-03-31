# Model Book V2 — Design Document

## Overview
Upgrade model books from 50 hand-curated entries to 1,500+ by importing Will's Big Movers dataset. Add three-panel layout, Trading Gym game, and stats improvements. Design: Research Terminal (A) + Trading Journal touch (B).

## 1. Data Import — Will's Big Movers
- Pipeline script downloads `big_movers_result.csv` (1,495 entries) + 928 OHLCV CSVs from GitHub
- Converts CSVs to lightweight-charts JSON, saves to `frontend/public/data/modelbooks/ohlcv/`
- Merges into `index.json`: Will's entries get `source: "Big Movers"`, empty patterns/lessons
- Existing 50 curated entries preserved with their tags/lessons
- Result: ~1,545 entries, ~930 OHLCV files

## 2. Three-Panel Layout (Filter | Chart | Notes)
- Desktop: 22% | 48% | 30% columns
- Left: compact table (drop Duration column, abbreviate Source)
- Center: chart + toolbar (D/W, LIN/LOG, SPY, MA legend)
- Right: journal-style notes panel
  - Ticker name (slightly larger, editorial weight), year, source subtitle
  - Pattern badges
  - Gain + Duration compact stat row
  - Key Lessons as margin notes (italic, left-border blockquote style)
  - "Your Notes" section (TBD — user will provide instructions)
  - Outcome as quiet conclusion
- Tablet: left panel collapses to ticker strip
- Mobile: stacks vertically
- Per-ticker drill-down: click ticker name → pre-fills search, filters to all setups for that symbol

## 3. Trading Gym — "Guess the Move"
- 4th tab: Browse | Study Mode | Stats | Gym
- Random chart loads, 70% revealed (up to breakout point)
- Three buttons: Buy (green) / Pass (gray) / Fade (red)
- After choosing, remaining 30% animates bar-by-bar (~100ms per bar)
- Result card: actual gain/loss %, correct/wrong
- Running score: streak counter, session accuracy
- Correct = Buy+20%gain, Pass+<20%, Fade+loss
- No timer, relaxed study feel
- Streak animation on correct
- Session stats in localStorage (best streak, total rounds)
- Difficulty: Easy (100%+ gainers) | Mixed (all) | Hard (include fakeouts)

## 4. Stats Improvements
- Time period filter: All Time | 2020s | 2010s | 2000s
- Source filter reused from browse
- Untagged count shown: "847 untagged setups"
