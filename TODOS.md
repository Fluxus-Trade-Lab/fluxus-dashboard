# TODOS

## Before Layer 1

### Archive existing fluxus-capital.com content
Save testimonials, FAQ, founder story, and pricing details to `docs/archived-site-content.md`.
**Why:** Full redesign will replace the current site. These assets (especially testimonials) are reusable.
**How:** WebFetch the current site content and save as markdown. Do this BEFORE pointing DNS to Vercel.

## Layer 1 Polish (review later)

### Landing page dark hero refinement
- Background dots feel static — consider subtle CSS animation or more organic placement
- Stats numbers (72%, 2.1R, 340+) are sample data — replace with real numbers from pipeline
- Testimonial section is thin — add 2-3 more real testimonials from archived content
- "Who is Fluxus?" bio may need your voice pass — reads a bit third-person/generic

### Method page data-art
- Pillar dot compositions are CSS-positioned — may need tuning on different screen sizes
- Consider making dots slightly animated (gentle float/pulse) to feel alive, not static
- Pillar copy is placeholder-quality — needs your voice, especially the "Select" and "Read" sections

### Results page
- All data is sample/hardcoded — wire up to real `performance.json` from pipeline
- No equity curve chart yet (was in the plan) — add Recharts line chart
- Monthly table and recent trades need real data

### Pricing page
- $99/month and $79/year are placeholder prices — confirm with your actual Whop tiers
- Whop links both point to generic `whop.com/fluxus-trade-lab/` — may need separate free vs paid URLs
- Feature lists (Free vs Member) need your review — some items may be wrong

### Brief preview page
- Sample briefs are fabricated — wire up to real `briefs.json` from pipeline
- Consider showing only 3 briefs instead of 5 (less is more)

### Global polish
- Mobile responsive pass needed on all public pages
- Dark mode pass — dark hero section looks the same in both modes (intentional?)
- No page transitions — feels abrupt when navigating between public pages
- Footer is minimal — may want to add Discord link, email, or legal links

## Content Engine Pipeline (Phase 0-2)

### Phase 0: Prerequisites
Set up Discord bot token (Tao owns the server → create Application + Bot in Discord Developer Portal). Create the Fluxus voice prompt template (`pipeline/content/prompts/fluxus_voice.py`). Add `anthropic` SDK to `pipeline/requirements.txt`.
**Why:** Unblocks Phase 1. The bot token is just for API auth — no hosted bot needed.
**How:** Discord Developer Portal → New Application → Bot → copy token → store in `.env` and GitHub Actions secrets. Write the voice prompt as a Python module with composable system prompt + format-specific instructions.
**Depends on:** Nothing. Can start immediately.

### Phase 1: Discord → Twitter pipeline
Build `pipeline/content/discord_to_thread.py` — fetches Tao's Discord messages for a given day, sends to Claude API with Fluxus voice prompt, outputs a formatted Twitter thread (text file). Manual trigger: `python -m pipeline.content.discord_to_thread --channel <id> --date today`.
**Why:** This is the minimum viable content distribution. Tao's daily Discord reads become public Twitter threads.
**How:** Discord HTTP API (GET /channels/{id}/messages with bot token), filter by author + date, Claude API for formatting, split output into ≤280 char tweets.
**Depends on:** Phase 0 (bot token + prompt template).

### Phase 2: Pre-market audio → Daily brief
Build `pipeline/content/audio_to_brief.py` — transcribes pre-market talk audio via Whisper API, sends transcript to Claude with brief-specific prompt, outputs JSON matching existing `briefs.json` schema.
**Why:** Tao already does a 20-30 min pre-market talk daily. This converts it into a website brief + Twitter post automatically.
**How:** Whisper API (openai SDK) for transcription, Claude API for summarization + formatting, append to `data/output/briefs.json`.
**Depends on:** Phase 0 + Phase 1 patterns established.

### Content pipeline tests
Full test suite: mock Discord API responses, mock Claude API, test prompt composition, test Twitter thread splitting (280 char boundary), test brief JSON schema matches existing format. ~8-10 test cases in `pipeline/tests/test_content_pipeline.py`.
**Why:** Tests document expected API behavior and catch formatting regressions.
**Depends on:** Phase 1 code written.

## After Layer 1

### SEO + Open Graph meta tags
Add `<meta>` tags (title, description, OG image) to public pages so social shares show rich previews.
**Why:** Sharing fluxus-capital.com on Twitter/Discord currently shows a blank card. Rich previews are critical for organic discovery.
**How:** Use `react-helmet-async` or inject tags into `index.html`. Create a branded OG image (1200x630).
**Depends on:** Layer 1 public pages being built.

### Automate trade history export
Replace manual CSV export with automated pipeline step that pulls trade data from Google Sheets.
**Why:** The performance_stats.py pipeline requires trades.csv. Currently Tao must manually export from Sheets.
**How:** The GAS endpoint already supports `?action=pull` returning trades as JSON. Add a pipeline step that hits this endpoint, transforms to CSV, and writes `data/trades.csv`. Or add a new GAS endpoint that returns CSV directly.
**Depends on:** Layer 1 performance pipeline being built.

### Layer 2 engineering review — auth + payments + member gating
Run `/plan-eng-review` for Layer 2: Supabase Auth + Stripe Checkout + gating dashboard pages behind login.
**Why:** Once Layer 1 drives traffic, the dashboard tools need to be behind a paywall.
**Context:** Supabase Auth (free tier) + Stripe Checkout. Gate `#/dashboard`, `#/screener`, `#/portfolio`, etc. behind login. Layer 1 learnings may change the approach.
**Depends on:** Layer 1 being live + initial traffic data.
