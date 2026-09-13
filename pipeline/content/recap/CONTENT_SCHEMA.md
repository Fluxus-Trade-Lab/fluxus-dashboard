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
| `led` / `lagged` | array | rows `[name, chg_string, note]`; `chg_string` starts with `+` / `−` |
| `sentiment` | string \| null | optional paragraph |
| `tomorrow` | array of strings | next-session (weekly: next-week) watch items; checked by R2 |
| `rules` | array of 7 strings | 1–6 written for this issue; 7 **must start with** `Never serious trouble until S&P breaks the 200-day` / `标普不破 200 日线，谈不上真正的麻烦`, followed by the issue's read. 1–6 may not repeat the 09-04 set (stale gate) and are checked by R2 |
| `education` | object | see below |
| `portfolio_note` | string | one neutral sentence; R and % only |
| `labels` | object | section and column labels for this language (copy from the previous issue) |
| `x_posts` | object | **EN dailies only**: `{"v1": {"text", "fields"}, "v2": {"text", "fields"}}` — v1 judgment first (the day's character, 1–2 readings, 2–4 leader cashtags on the last line), v2 structure first (the main structural event, what it means using only judgments already in this file, same cashtags). ≤ 280 X characters, no hashtags / emoji / links / calls to action, every number must appear verbatim elsewhere in this file; `fields` lists the fields the post draws on. Gate P1 in `xpost.py`; missing → a plain fallback marked `auto` |
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
- R1 turns red if A or B repeats a concept, or a title (≥ 0.6 similar), used in the last 20 sessions or
  among spec §5's eight topics; a weekly A may not repeat a concept used by a daily A of the same week.
- Member PDFs show only the chosen option's title, body and figure. The topic cards and reasons appear
  only in `preview.html` and `delivery.md`.
