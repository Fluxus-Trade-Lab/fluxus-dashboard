# Feature Designs: Options Log, Briefing, AI Coach, Model Books

**Date**: 2026-03-16
**Status**: Approved

---

## 1. Portfolio Options Trade Log

### Goal
Add a simple manual options trade logger as a new tab in the Portfolio page, with its own starting capital and a performance curve.

### Location
New "Options" tab in Portfolio page (Tab index 6, after 3-Stop Sim). Shares the PortfolioContext provider but has its own `optionsCapital` and `optionsTrades[]` state.

### Data Model

Each options trade stored in `state.optionsTrades[]`:

| Field | Type | Example |
|-------|------|---------|
| `id` | string (uuid) | `"abc-123"` |
| `date` | ISO date | `"2026-03-10"` |
| `ticker` | string | `"AAPL"` |
| `strategy` | enum | `call` / `put` / `call_spread` / `put_spread` / `iron_condor` / `straddle` / `strangle` / `other` |
| `strike` | number | `150` |
| `expiry` | ISO date | `"2026-04-18"` |
| `direction` | enum | `long` / `short` |
| `contracts` | number | `5` |
| `premium` | number (per share) | `2.50` |
| `closeDate` | ISO date or null | `"2026-03-14"` |
| `closePremium` | number or null | `4.10` |
| `notes` | string | `"earnings play"` |

**P&L formula**: `(closePremium - premium) * contracts * 100 * (direction === 'long' ? 1 : -1)`

### Tab Layout

```
+-----------------------------------------------------------+
| Options Capital: $25,000    Realized P&L: +$1,240          |
| Open Positions: 3           Win Rate: 62%                  |
+-----------------------------------------------------------+
| [+ New Trade]                                              |
|                                                            |
| -- Open Positions ---------------------------------------- |
| Date  Ticker  Strike  Expiry  Dir  Cts  Premium  Notes     |
| 3/10  AAPL    150C    4/18    L    5    $2.50              |
| ...                                                        |
|                                                            |
| -- Closed Trades ----------------------------------------- |
| Date  Ticker  Strike  Expiry  Dir  Cts  In   Out   P&L    |
| 3/5   TSLA    280P    3/14    L    2    $3.1 $5.2  +$420  |
| ...                                                        |
|                                                            |
| -- Performance ------------------------------------------- |
|  [cumulative realized P&L line chart over time - Recharts] |
+-----------------------------------------------------------+
```

### Storage & Export
- Persisted in localStorage via PortfolioContext reducer
- New reducer actions: `ADD_OPTIONS_TRADE`, `CLOSE_OPTIONS_TRADE`, `DELETE_OPTIONS_TRADE`, `SET_OPTIONS_CAPITAL`
- CSV export/import extended to include options section
- `optionsCapital` stored separately from `startingCapital`

### Performance Chart
- Simple Recharts line (already in bundle) showing cumulative realized P&L by close date
- X-axis: dates, Y-axis: cumulative $

### New/Modified Files
- `frontend/src/components/portfolio/tabs/OptionsTab.jsx` -- new tab component
- `frontend/src/components/portfolio/OptionsTradeForm.jsx` -- trade entry form
- `frontend/src/components/portfolio/context/PortfolioContext.jsx` -- add optionsTrades state + reducer
- `frontend/src/components/portfolio/lib/portfolioFormat.js` -- add "Options" to TABS array
- `frontend/src/components/portfolio/lib/csv.js` -- extend export/import for options
- `frontend/src/components/portfolio/PortfolioLayout.jsx` -- add OptionsTab render

---

## 2. Briefing Page

### Goal
Replace the empty Briefing placeholder with a hybrid page: auto-generated market recaps from external markdown files + personal daily notes.

### Data Sources
- **Recaps**: Markdown files generated from automated video summary pipeline (2 sources). Files stored at `data/briefings/YYYY-MM-DD.md`.
- **Notes**: User's personal daily observations, saved in localStorage keyed by date.

### Architecture

```
data/briefings/
  index.json          <-- list of available dates
  2026-03-16.md       <-- auto-generated recap
  2026-03-15.md
  ...

Frontend:
  1. Fetches /data/briefings/index.json for date list
  2. Loads today's (or selected day's) .md file
  3. Renders markdown client-side (small markdown renderer ~5KB)
  4. Notes section stored in localStorage
```

### Page Layout

```
+-----------------------------------------------------------+
| MARKET BRIEFING                   [< Mar 15]  Mar 16      |
+-----------------------------------------------------------+
|                                                            |
|  [Rendered markdown from video recap source 1]             |
|  [Rendered markdown from video recap source 2]             |
|                                                            |
+-----------------------------------------------------------+
| MY NOTES                                          [Save]   |
|  +------------------------------------------------------+ |
|  | Free-form text editor (localStorage per day)          | |
|  +------------------------------------------------------+ |
+-----------------------------------------------------------+
```

### Features
- Date navigation (prev/next arrows) to browse historical briefings
- Markdown rendered client-side
- Notes section persisted to localStorage keyed by date (`briefing-notes-2026-03-16`)
- Graceful empty state when no recap exists for a date

### New/Modified Files
- `frontend/src/components/briefing/BriefingPage.jsx` -- replace placeholder
- `frontend/src/components/briefing/RecapViewer.jsx` -- fetches + renders markdown
- `frontend/src/components/briefing/DailyNotes.jsx` -- localStorage-backed text editor
- `frontend/src/components/briefing/DateNav.jsx` -- prev/next date navigation
- `data/briefings/index.json` -- auto-generated date index
- Add markdown rendering dependency (e.g., `marked` or `markdown-it`, ~5KB gzipped)

### Pipeline Integration
- User's video recap automation writes .md files to `data/briefings/`
- A small script regenerates `index.json` listing all available dates
- GitHub Actions workflow (or manual commit) pushes new recaps

---

## 3. AI Coach

### Goal
Build a two-part coaching system: rules-based analytics from trade data + LLM-powered strategy-specific coaching loaded with expert knowledge.

### Section A: Rules-Based Analytics (no API needed)

Pulls from Portfolio trade data and computes:
- Win rate by setup/strategy type
- Average R-multiple by strategy
- Average hold time by strategy
- Best/worst performing strategies
- Pattern identification ("Your EP trades avg 2.3R vs 1.1R for VCP")

### Section B: Strategy Coach (Claude API via Vercel serverless)

3-4 strategy-specific coaches, each loaded with a knowledge base:

```
data/coach/
  episodic-pivot.md    <-- strategy rules, ideal criteria, examples, common mistakes
  vcp.md
  breakout.md
  range-breakout.md
```

Architecture:
```
Frontend chat UI
  |
  v
/api/coach (Vercel serverless function)
  <- receives: strategy name, user message, trade context
  <- loads: strategy .md as system prompt context
  <- calls: Claude API
  -> returns: coaching response
```

Use cases:
- **Pre-trade**: "Review this setup: AAPL is forming a 12-week cup with handle, RS new highs..."
- **Post-trade**: "I entered TSLA at 280 on a VCP breakout, got stopped out at 268. Review my execution."

### Page Layout

```
+-----------------------------------------------------------+
| AI COACH                                                   |
| [Analytics]  [Episodic Pivot]  [VCP]  [Breakout]  [Range]  |
+-----------------------------------------------------------+
|                                                            |
| Analytics tab:                                             |
|   Stats cards + patterns from trade data                   |
|                                                            |
| Strategy tabs:                                             |
|   Chat-like interface with the coach                       |
|   System prompt loaded with strategy .md knowledge base    |
|   Pre-trade setup review + post-trade coaching             |
|                                                            |
+-----------------------------------------------------------+
```

### Phasing
- **Phase 1 (now)**: Build UI + rules-based analytics. Strategy tabs show chat interface but stub the API call.
- **Phase 2 (after Vercel deploy)**: Wire up `/api/coach` serverless function with Claude API + strategy .md files.

### New/Modified Files
- `frontend/src/components/journal/JournalPage.jsx` -- replace placeholder
- `frontend/src/components/journal/AnalyticsTab.jsx` -- rules-based stats
- `frontend/src/components/journal/CoachTab.jsx` -- chat interface per strategy
- `frontend/src/components/journal/CoachMessage.jsx` -- chat message component
- `data/coach/episodic-pivot.md` -- strategy knowledge base
- `data/coach/vcp.md`
- `data/coach/breakout.md`
- `data/coach/range-breakout.md`
- `api/coach.js` (Vercel serverless, Phase 2)

---

## 4. Model Books

### Goal
Transform a collection of trading PDFs (annotated chart case studies from O'Neil, TraderLion, etc.) into an indexed, browsable pattern recognition study tool.

### Source Material
- **William O'Neil "America's Greatest Opportunity"** (52MB) -- historical model stocks with annotated weekly charts, one per page
- **TraderLion 2020 Model Book** (9.5MB) -- modern model stocks with annotated daily charts, one per page
- **TraderLion Ultimate Trading Guide** (7.6MB) -- educational content (feeds into AI Coach knowledge base instead)
- Additional PDFs to be added over time

### Extraction Pipeline

```
pipeline/tools/extract_model_books.py

1. Input: PDFs in data/modelbooks/raw/ (gitignored)
2. pdf2image splits each PDF -> one PNG per page
3. Claude Vision reads each PNG and auto-generates metadata:
   {
     "id": "oneil-chrysler-1962",
     "ticker": "Chrysler",
     "year": 1962,
     "source": "O'Neil - America's Greatest Opportunity",
     "patterns": ["cup_with_handle", "flat_base"],
     "key_lessons": [
       "36-week cup with handle",
       "Heavy volume accumulation in base",
       "16 weeks up in a row after breakout",
       "Sell on heavy volume stalling"
     ],
     "buy_points": 3,
     "outcome": "10x",
     "image": "oneil-chrysler-1962.png"
   }
4. User reviews and corrects AI-generated metadata
5. Output:
   public/modelbooks/images/*.png  (~200KB per page)
   data/modelbooks/index.json      (array of all cards)
```

### Pattern Taxonomy

```
cup_with_handle | flat_base | vcp | high_tight_flag |
pocket_pivot | episodic_pivot | range_breakout |
base_on_base | double_bottom | ipo_base |
faulty_base (negative examples!)
```

### Frontend Layout

**Browse Mode:**
```
+-----------------------------------------------------------+
| MODEL BOOKS                       [Browse]  [Study Mode]   |
+-----------------------------------------------------------+
| Filter: [All Patterns v] [All Eras v] [All Sources v]      |
|                                                            |
| +----------+ +----------+ +----------+ +----------+       |
| | chart    | | chart    | | chart    | | chart    |       |
| | thumb    | | thumb    | | thumb    | | thumb    |       |
| |          | |          | |          | |          |       |
| | CRWD '20 | | AMZN '20 | | CHRY '62 | | PSFT '94 |       |
| | CWH, PP  | | CWH, PP  | | CWH, FB  | | CWH,BOB  |       |
| +----------+ +----------+ +----------+ +----------+       |
|                                                            |
| Click card -> full-size view with annotations              |
+-----------------------------------------------------------+
```

**Study Mode (flashcard):**
```
+-----------------------------------------------------------+
| +--------------------------------------+                   |
| |        [chart image]                 |  Ticker: ???      |
| |                                      |  Pattern: ???     |
| |   Can you identify the pattern?      |  Year: ???        |
| |                                      |  [Reveal]         |
| +--------------------------------------+                   |
|              [Next] [Skip] [Mark for review]               |
+-----------------------------------------------------------+
```

### Storage
- Raw PDFs: `data/modelbooks/raw/` (gitignored, too large for repo)
- Extracted images: `public/modelbooks/images/` (committed, ~200KB per page)
- Index: `data/modelbooks/index.json` (committed)
- To add new books: drop PDF in `raw/`, run extraction script, review metadata

### Cross-links
- Educational content (TraderLion Guide) -> extracted as strategy .md files for AI Coach knowledge base
- Pattern tags align with AI Coach strategy tabs (VCP, Episodic Pivot, etc.)

### New/Modified Files
- `pipeline/tools/extract_model_books.py` -- PDF extraction + Claude Vision tagging script
- `data/modelbooks/raw/` -- raw PDFs (gitignored)
- `data/modelbooks/index.json` -- card metadata index
- `public/modelbooks/images/` -- extracted page images
- `frontend/src/components/modelbooks/ModelBooksPage.jsx` -- replace placeholder
- `frontend/src/components/modelbooks/BrowseView.jsx` -- filterable card grid
- `frontend/src/components/modelbooks/StudyMode.jsx` -- flashcard interface
- `frontend/src/components/modelbooks/CardDetail.jsx` -- full-size chart view with metadata

---

## Implementation Priority

| Priority | Feature | Complexity | Dependencies |
|----------|---------|------------|-------------|
| 1 | Options Trade Log | Medium | None (extends existing Portfolio) |
| 2 | Briefing Page | Low | External recap automation (can stub) |
| 3 | Model Books | Medium-High | Claude API for extraction, pdf2image |
| 4 | AI Coach | High | Vercel deploy for LLM, trade data for analytics |

Recommended order: Options Log -> Briefing -> Model Books extraction -> Model Books frontend -> AI Coach analytics -> AI Coach LLM integration
