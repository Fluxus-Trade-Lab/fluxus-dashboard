# Recap content file schema — `content_EN.json` / `content_ZH.json`

The scheduled writing session produces these two files in the issue's pack directory
(`$FLUXUS_RECAP_ROOT/YYYY-MM/<issue>/pack/`, default root `~/Documents/Trading/01_Market_Reports_Daily`;
issue = `YYYY-MM-DD` for dailies, `YYYY-Www` for weeklies; the five 2026-09 samples keep `YYYY-MM/samples/pack_<issue>/`),
after `run.py fetch` has written `pack.json` and `transcript.md`. **Numbers are not typed here**:
index closes, breadth, votes, groups, R and % all render from `pack.json` / the archives.
The files never enter git.

Then:

```bash
python3 -m pipeline.content.recap.run check  --date 2026-09-11      # R1/R2 + rules, no rendering
~/.venvs/fluxus-recap/bin/python -m pipeline.content.recap.run render --date 2026-09-11 [--edu B]
python3 -m pipeline.content.recap.run ledger-add --date 2026-09-11
```

A red `check` means rewrite, not force. `render` runs `check` again and refuses to print on red.

## Voice and data rules (enforced by gates on the rendered text)

- No proprietary names from the source video (channel, products, hosts, lists, contacts).
- No 「领导力」 in ZH (use 龙头). No dollar amounts, no share counts, anywhere.
- Never the word “Andy”, never first person (I / we / our / me / my / us / 我). Restate his Discord
  judgments as neutral sentences; English quotes allowed without attribution or timestamps.
- ZH is a rewrite, not a translation; ZH cells carry no English duplicates (「多空线」, not
  「多空线 / bull/bear line」). Tickers, metric names and group names stay as they are.
- `◇` marks anything from outside the data layer (transcript, news, external index levels).
- **No “week” shorthand** (Andy 09-13: “theme week” reads as “theme weak”). Write
  `−10.5% over the week (theme)` or `1-week −9.4%`, never `theme week`, `IBIT week;` or a note opening
  with `week −9.4%`. ZH writes 本周 / 一周. Gate W1 (`wording.py`) blocks `check` and `render`.
- “Grow” (a source trend-gauge state) is a proprietary name; growth / grow in ordinary prose are fine.
- Rich text: `<b>…</b>` is the only markup allowed inside strings.

## Top-level fields (both languages)

| field | type | notes |
|---|---|---|
| `lang` | `"EN"` \| `"ZH"` | |
| `tone` | `"up"` \| `"down"` \| `"range"` | title bar colour |
| `title` | string | paraphrased, never the video title; `—` / `——` splits the B-layout headline |
| `subtitle` | string | 2–3 keywords · date |
| `big_picture` | string | one paragraph; transcript narrative leads, Discord sharpens (Andy 09-13). First sentence is checked by R2 |
| `index_notes` | object | `{"SPY": [technical_event, level_or_note], "QQQ": …, "RSP": …, "DIA": …, "IWM": …}`; events only (reclaimed / lost), never “above X” |
| `extra_index_rows` | array | optional rows not in the data layer: `[name, close, chg, vol, event, note]`, mark `◇` |
| `state_line` | string | one sentence under the market-state strip |
| `founders_note` | string \| null | Founders Note text if GAS returned one; null → the section is not rendered |
| `led` / `lagged` | array | rows `[name, chg_string, note]`; `chg_string` starts with `+` / `−`. **`note` should name the tickers driving the group** (Andy 09-15: 「主题和行业的领涨落后要写上ticker名字」) — omit only when the row is genuinely group-only (a state change with no single name to point at) |
| `sentiment` | string \| null | optional paragraph |
| `session_commentary` | array of strings \| omitted | Discord `#live-commentary` observations made **during the covered session** that are not next-session watch items — a rejection, a level defended, "sellers in control", a name called out mid-tape (Andy 09-15: 「DISCORD内容应该是变成"盘中评论"，而不是"下个交易日看什么"」). Neutral voice, no attribution, same rules as everywhere else. Renders its own section (label `labels.session_commentary`) between Sentiment and Tomorrow; omit the field (or leave it empty) when there is nothing session-specific to say — the section then does not print. Checked by R2 like `tomorrow` |
| `tomorrow` | array of strings | next-session (weekly: next-week) watch items — **forward-looking only** (a level, an event, a follow-through question for the *next* session). Intraday observations about the session just covered belong in `session_commentary`, not here. checked by R2 |
| `rules` | array of 7 strings | 1–6 written for this issue; 7 **must start with** `Never serious trouble until S&P breaks the 200-day` / `标普不破 200 日线，谈不上真正的麻烦`, followed by the issue's read. 1–6 may not repeat the 09-04 set (stale gate) and are checked by R2 |
| `education` | object | see below |
| `portfolio_note` | string | one neutral sentence; R and % only |
| `labels` | object | section and column labels for this language (copy from the previous issue). Since 2026-09-23 the Portfolio table has five columns, so `labels.pos_cols` needs a 5th entry — or leave `pos_cols` at four and add `labels.pos_stop` (EN `Stop R` / ZH `止损 R`); the renderer splices it in as column 4. `labels.legs_title` names the trims/exits list (EN `Trims & exits` / ZH `减仓与平仓`); both fall back to the right language when absent, so a missing label degrades rather than printing English on the ZH page |

### Portfolio: the R ladder (Andy 2026-09-23「以多少R的形式，不出现美元数值」)

`book` in `pack.json` carries the numbers; **no per-share price, dollar amount or share count ever reaches the page.**
entry is the zero point, so a position reads `cost 0R → stop ±X.XR → now +Y.YR`:

| field | meaning |
|---|---|
| `positions[].stop_R` | the **live trailed** stop in R off entry — `sgn · (stop_price − entry_price) / (R_dollars / original_qty)`. The initial stop is `−1.0R` by definition and is only ever the denominator. `null` when `initial_stop` was never recorded (no R scale to state it on) → the cell prints blank, never a guess |
| `legs[]` | TRIM / CLOSE events between `period_start` and D: `{date, ticker, type, pct_of_position, R, R_scope}` |
| `legs[].R_scope` | `leg` for a TRIM (that tranche's R) · `trade` for a CLOSE (the **whole trade's** realized R) |

A trade sold out in several tranches on one day is **one** CLOSE row, not one per tranche (09-22's FSLY went out in three). `pct_of_position` is `qty / original_qty` — a percentage, never a share count.
Guarded by `pipeline/tests/test_recap_r_ladder.py`, whose direction-B control was proven to redden before its green was trusted.
| `x_posts` | object | **EN dailies only** (Andy 09-13: long post = structure sentence + Big Picture): `{"lead": string \| null, "cashtags": ["HPE", …], "why": "one-line reason (optional)"}`. The post is `lead` (if any), then `big_picture` verbatim with `<b></b>` and ` ◇` stripped, then 2–4 cashtags. **Cashtags are names that appear in this issue** — each must be a stand-alone word in `big_picture` / `index_notes` / `led` / `lagged` / `session_commentary` / `tomorrow` / `rules` (gate P3); book tickers are not avoided (Andy 09-13). No Substack link or pointer at the end (P1 flags the word). `lead` is **null when Big Picture's first sentence already states the day's main structural event** (which average was reclaimed / lost, which index split from which); otherwise one structure sentence that only restates this file — no new judgment. The body is never rewritten. Gates in `xpost.py`: P1 (≤ 1,500 X characters, no proprietary names / Andy / first person / dollar amounts / hashtags / emoji / links / calls to action, every number in the file, no leftover `<b>` or ◇, 2–4 cashtags) and P2 (lead vs Big Picture's first sentence, SequenceMatcher ≥ 0.4 → red, set lead to null). Missing → Big Picture only, marked `auto` |
| `weekly_k_names` | array | weekly only: tickers for the weekly-close table, in order |
| `weekly_k_line` | string | weekly only: one sentence under that table |

## `education`

```json
{
  "chosen": "A",
  "options": [
    {"key": "A", "concept": "left_side_of_v", "title": "…", "why": "one line", "body": "one paragraph", "figure": "left_side_of_v"},
    {"key": "B", "concept": "low_volume_breakout", "title": "…", "why": "one line", "body": "one paragraph", "figure": "low_volume_breakout"}
  ]
}
```

- Both options are written in full (title, one-sentence reason, one-paragraph body, figure). Production
  prints A; `render --edu B` prints B from the same file without rewriting.
- `concept` is a short English tag, identical in EN and ZH files; it is what the topic ledger stores.
- `figure` names a builder in `visual_figs.FIGS`; a new concept needs a new builder whose asserts encode
  spec §5's three checks. `concept` and `figure` are usually the same string.
- `picked_by_andy` (optional, per option): Andy's words, verbatim, when he names the topic himself. R1 skips that option — topic choice is his (Andy 2026-09-19「新的教育选题 用 neWS FailIure」). Never set it on a machine-picked topic.
- R1 turns red if A or B repeats a concept, or a title (≥ 0.6 similar), used in the last 20 sessions or
  among spec §5's eight topics; a weekly A may not repeat a concept used by a daily A of the same week.
- Member PDFs show only the chosen option's title, body and figure. The topic cards and reasons appear
  only in `preview.html` and `delivery.md`.
- The lesson may run onto page 5 (Andy 09-13:「教育段可以跨页」,「接受日刊变成5+1的组合」), so a daily prints
  5 pages when it fits and 6 when it spills. Gate L1: every other section ends by page 4, the book owns the
  last page alone, and no page opens mid-sentence — a paragraph, list item, table row and figure each travel
  whole, which is what keeps X image 4 (EN page 4) from cutting inside a sentence.
