---
name: Fluxus Capital
description: A market instrument that turns data into a reviewable judgement — a library, not a casino.
colors:
  bg: "#12110F"
  bg-light: "#e2e0d6"
  surface: "#232120"
  surface-light: "#f2f0e9"
  surface-raised: "#32302f"
  border: "#423f3e"
  border-light: "#2b2a29"
  text: "#e6e5e5"
  text-bold: "#ffffff"
  text-secondary: "#b7b6b5"
  text-muted: "#979594"
  took: "#77b4fb"
  took-light: "#194371"
  refused: "#ef5442"
  refused-light: "#b5342c"
  untested: "#c2c0bf"
  accent: "#6a97bd"
  accent-light: "#2d5f8a"
  profit: "#77b4fb"
  loss: "#ef5442"
  slot-1: "#e0e9f2"
  slot-2: "#85cd83"
  slot-3: "#c48658"
typography:
  verdict:
    fontFamily: "PlexCond, Plex, sans-serif"
    fontSize: "clamp(3.25rem, 9vw, 5.5rem)"
    fontWeight: 700
    lineHeight: 0.86
    letterSpacing: "-0.018em"
  title:
    fontFamily: "Plex, sans-serif"
    fontSize: "46px"
    fontWeight: 600
  display:
    fontFamily: "Plex, sans-serif"
    fontSize: "26px"
    fontWeight: 600
  lead:
    fontFamily: "Plex, sans-serif"
    fontSize: "17px"
    fontWeight: 600
  prose:
    fontFamily: "Plex, sans-serif"
    fontSize: "14px"
    lineHeight: 1.45
  body:
    fontFamily: "Plex, sans-serif"
    fontSize: "12.5px"
  meta:
    fontFamily: "Plex, sans-serif"
    fontSize: "11px"
  label:
    fontFamily: "PlexMono, ui-monospace, monospace"
    fontSize: "10px"
    letterSpacing: "0.14em"
rounded:
  hair: "1px"
  chip: "3px"
  sm: "4px"
  panel: "12px"
  card: "24px"
  pill: "9999px"
spacing:
  xs: "4px"
  sm: "6px"
  md: "8px"
  lg: "12px"
  xl: "16px"
components:
  card:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.card}"
    padding: "20px 24px"
  scan-card:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.panel}"
    padding: "8px 12px"
  scan-card-quiet:
    backgroundColor: "transparent"
    rounded: "{rounded.panel}"
    padding: "7px 12px"
  chip-menu-trigger:
    textColor: "{colors.text-bold}"
    typography: "{typography.body}"
  ticker-atr-chip:
    rounded: "{rounded.chip}"
    padding: "1px 4px"
    typography: "{typography.body}"
---

# Fluxus Design System — v3

*v3 written 2026-08-19 **from the running code**, not from intentions.*
*The v2 document is preserved verbatim at [`DESIGN.v2.md`](DESIGN.v2.md) — its ΔE tables,
greyscale evidence and refusal trigger rates are one-off measurements that cost a round
each and cannot be re-derived from the build. Look there for the history; change the
system here.*

## Overview

> **Make the reasoning legible, not the numbers visible.**

Anti-dopamine. No neon green, no rockets, no "10x". **A library, not a casino.**
Anti-dopamine does not mean voiceless — the voice lives in the interpretation layer and
is always typographically separated from the measurement layer. That separation is what
makes having a position safe.

Every surface answers one question: **could a stranger reach the conclusion themselves?**
A paying subscriber is the second reader, so provenance, recipe and threshold are
mandatory furniture, not optional footnotes.

## Colors

Two grounds, and every value is written explicitly in both. **Partial coverage is silent
inheritance, and silent inheritance is a token that quietly fails in the other theme** —
that is how `took` and `untested` once came out 0.8 ΔE apart in dark mode while sitting
42 apart in light.

| role | dark | light |
|---|---|---|
| ground | `#12110F` | `#e2e0d6` |
| surface | `#232120` | `#f2f0e9` |
| raised | `#32302f` | `#dcd9ce` |
| border | `#423f3e` | `#cbc6b8` |
| hairline | `#2b2a29` | `#dbd7cb` |
| text | `#e6e5e5` | `#1c1917` |
| text bold | `#ffffff` | `#292524` |
| text secondary | `#b7b6b5` | `#4b453e` |
| text muted | `#979594` | `#655e55` |

### The encoding pair

| | dark | light |
|---|---|---|
| `took` — the market gave and it was taken | `#77b4fb` | `#194371` |
| `refused` — it was given and refused | `#ef5442` | `#b5342c` |
| `untested` — not measured, out of the scale | `#c2c0bf` | `#b0aaa2` |

**No channel carries rank alone.** Fill says which side; the empty cell is the
denominator; area says "partial"; 45° hatching marks failure; a dashed outline means
unmeasured and leaves the colour scale; position says how many are filled. The three
non-colour channels are the load-bearing ones — they are theme-independent, and
**greyscale is the only column that must always pass**, because this brand's real
condition is being screenshotted and printed.

### Encoding colour belongs to graphics

`took` / `refused` are **fills**. A number borrows them only when it labels its own
graphic. Verdict words and prose never wear them — a coloured figure with no bar to
belong to has degraded into decoration.

`accent` is **chrome**, never data: links, focus rings, sort arrows, the "you are here"
rule, the step bar. It answers "the interface is pointing here", never "the data says
this".

### Three sets that never mix

- **Market layer** — `took` / `refused`. Response quality, never price direction.
- **Money layer** — `profit` / `loss`. P&L only, never market state. Long is not profit:
  colouring direction as P&L implies long is good.
- **Expression set** — poster and Substack only. **Never on the instrument.** Break it
  once and blue/red stop meaning anything.

### A continuous reading may take a ramp, under one law

The ATR position (how far a name has run from its 50-day) is painted as the ticker's own
ground rather than printed as a figure: it is the reading that decides whether you can
still get on, and it should land before anything has been read.

**The ramp must be monotonic in lightness.** Hue alone dies in greyscale. Dark rises
`L* 44.9 → 57` as the reading warms; light falls `75.1 → 61`. The directions differ
because the grounds do — on ink the alarming end is the luminous one, on paper the heavy
one — and a screenshot is taken inside one theme.

Three rules the measurements forced, none of them visible by eye:

1. **Interpolate the ground, choose the ink.** Blending the foreground alongside the
   background drives it through mid-grey on a mid-lightness fill — measured 1.61:1. Pick
   whichever ink the computed ground can carry. Pure white/black, not the page's
   near-inks: the worst point measured 4.40 with those, and a fill in the middle of a
   lightness range is the hardest ground there is.
2. **Correct each mix to its target lightness.** Straight RGB interpolation between a
   blue and an orange dips on the way (44.9 at ATR 4, 44.6 at 4.5 — the greyscale
   briefly running backwards). Pull every mix to the linearly-interpolated `L*` so
   monotonicity is a property of the construction, not of the anchors lining up.
3. **Off the scale means off the scale.** Below the 50-day is not "very un-extended", it
   is a different situation: no fill, ordinary ink.

## Typography

**IBM Plex**, self-hosted, OFL, no CDN. Three families from one source.

| use | family |
|---|---|
| body · UI | IBM Plex Sans |
| verdicts · page titles · key names | IBM Plex Sans Condensed *(condensed only works in English)* |
| numbers · codes · timestamps | IBM Plex Mono |
| Chinese | PingFang SC — **never in the mono face**, it collapses |

### The ladder, as built

| px | rung | what it does |
|---|---|---|
| 10 | label | mono, uppercase, tracked — column heads, section labels, menu carets |
| 11 | meta | notes, footnotes, denominators, timestamps |
| 12.5 | body | table rows, controls, the numbers you read |
| 14 | prose | sentences — the reading line, guidance, HowToRead |
| 17 | lead | a card's headline number, a panel's own h2 |
| 26 | display | a page's principal figure |
| 46 | title | page name (PageHeader only) |
| clamp(52 → 88) | verdict | the market verdict, Plex Cond Bold, `line-height .86`, `-.018em` |

**Nothing renders below 10px anywhere**, including SVG text and chart axis ticks. An
SVG's declared size is not its rendered size: a figure inside a `1000`-unit viewBox at
`900px` renders 11px type at 9.9. Give such a figure a floor width equal to its viewBox
so one unit is one pixel.

**Measured drift, recorded rather than hidden** (2026-08-19 sweep of the four market
pages): `10.5` ×13, `11.5` ×17, `12` ×45, `13` ×5, `15` ×4 are in use off the ladder.
They are legible and none breaks the floor, but they are drift and the next typography
pass should either absorb or remove them.

## Layout

- **Content width `1800px`**, centred, `px-3 py-4`. (v2 specified 1360; the build has
  been 1800 since the market pages were rebuilt.)
- Base spacing unit **4px**; the common gaps measured are 4 / 6 / 8 / 12 / 16.
- Every wide or tall object scrolls **inside its own box** — tables on both axes, the
  theme field horizontally, the screener's ten-row window vertically. **The document
  scrolls on neither axis at any width**, verified at 375 / 1512 / 2000.
- A sticky table header outranks nothing by default: an open menu in the control bar
  must have a higher stacking context than the table's own sticky `thead`, or it paints
  underneath it.

### Size is the fourth channel

The three morning pages share one skeleton — a matrix of cards whose inside always reads
**change → strength → names** — and **the cards are not equal. Size says what the page is
for, and each page spends it differently.**

| page | largest | middle | small |
|---|---|---|---|
| Dashboard | the verdict and the condition that ends it | market cycle · the founder's own words | what moved, at four grains |
| Themes | the four-state field (leading × accelerating) | the strength curve over time | the ranking, members, full table |
| Screener / Today's List | the scan field | the chart card and the shortlist beside it | the names |

Two rules that came out of using it:

- **A fixed card does not resize on selection.** Sizing the chart to the selection was
  proposed and rejected: a click that reflows the page loses the reader's place in the
  grid they were reading.
- **The largest card must survive being cropped out on its own.** The top third of every
  page is how this work is distributed, so a claim and its exit condition belong in one
  card, not two.

## Elevation & Depth

Depth is nearly absent by design. Cards are separated by **ground, not by fences** —
`24px` corners, no border, the page's radial ground showing between them.

- `--lift`: `0 1px 2px rgba(0,0,0,.30), 0 10px 28px -14px rgba(0,0,0,.55)` — offset and
  soft blur, used sparingly.
- `--glass` + `--glass-blur` for the one sticky control bar.
- `--ground`: a single wide radial tint, `rgba(59,130,196,.10)` on dark.

## Shapes

| radius | where |
|---|---|
| `1px` | encoding cells, hairline marks |
| `3px` | the ATR chip under a ticker |
| `4px` | small controls, menu rows |
| `12px` | scan cards |
| `24px` | page cards |
| pill | theme toggle, nav affordances |

## Components

- **Verdict card** — change line, the word at `clamp(52→88)`, twelve vote glyphs, then
  the falsification sentence in the *expected* register. Never coloured by side.
- **Vote glyph** — fill = which side, rule = the line it flips at, height = distance in
  its own unit, dashed = could not be counted, ring = sitting on its line. **Heights are
  normalised inside each vote's own range and never compared across two.**
- **Four-state field** — `classify(excess_3m, rs_accel)` drawn as its own definition:
  two axes cut at zero, so a dot's quadrant *is* its state. **Therefore nothing on it is
  coloured by state** — position already said it. Dot size is `persistence`.
- **Fixed chart card** — same place, same size, never empty; opens on the first name out
  of a named screen and says which. The widget takes the ground it stands on, read from
  the DOM, so it has no edge of its own.
- **Step bar** — five ordered steps, the chosen one carrying three lines: what it looks
  for, what it is used with, and **how it is misread**. The third line is the one worth
  the ink.
- **Scan card, quiet** — a scan off the current step keeps its title and count on one
  line and gives up its names until clicked. Quiet, not hidden; and what opens by hand
  closes by hand.
- **Shortlist tray** — each entry freezes the readings it was taken at and remembers
  which screen it came off, because the question worth asking about an old shortlist is
  whether the call was good on the day it was made.

## Do's and Don'ts

**Do**

- Print both denominators when two instruments are on one card, and say they are different.
- Count the rows you are showing, not a precomputed total that describes rows you do not hold.
- Report what a filter excluded, in the same sentence as the filter.
- Say "not measured" — never `0` — and keep *not measured*, *found none* and *blocked by a
  threshold* looking different from each other.
- State the selection mechanism of any list ordered by outcome.
- Verify by driving the built page: hit-test it, measure computed styles, disable
  transitions first, and confirm the page actually rendered — **a white screen passes
  every colour audit.**

**Don't**

- Rank a 6-name thesis against a 1,579-name size bucket on one pair of axes.
- Let a control go one way only. An expander with no collapse is not a control.
- Put two selectors over the same set of objects.
- Colour by a property the position already encodes.
- Trust an SVG's declared font size, a summary's totals, or a screenshot that predates
  the change you are testing.

---

## Weirdness 1–5, and what each surface is allowed

Each level is defined by **what the reader has to pay**, not by how decorated it is.

| level | | cost | example |
|---|---|---|---|
| 1 | none | zero | an ordinary chart |
| 2 | **one mark** | zero, but remembered | a `NOT A CALL` stamp · a deliberately empty cell |
| 3 | **the form is rewritten** | accept an unfamiliar container | an instruction card · a rule certificate |
| 4 | **refuses to be the subject** | accept that "no content" is content | `NOTHING TO REPORT` · an empty-day receipt |
| 5 | **category violation** | ask "what is this" first | the Du Bois edition · the character portrait |

Instrument surfaces (dashboard, themes, screener, today's list, course) sit at **2**.
The letter's interior is 2 and its cover 4; X is 3–4; the poster is the only 5.

## Eight refusals

Each must point at a specific number, or it may not ship.

1. There must be something to say every day → `NOTHING TO REPORT` (measured trigger rate 2.3%).
2. This is advice → the `NOT A CALL` stamp.
3. Fill the blank cell → the rates cell stays empty; the pipeline has no bond feed.
4. Smooth the gap → archive breaks are drawn, not interpolated (13 sessions).
5. Only show the wins → null results ship (sequence mining 0/42; the 52-week-high filter's negative alpha).
6. The chart always proves the headline → when it refutes the headline, the refutation stays.
7. Predict the price → report only "the market gave / it was taken or refused".
8. The content treadmill → the number only increments when there is a reading.

**Three promoted to general rules**

- If a thing cannot be drawn honestly, print it as a number.
- Any list ordered by outcome must disclose its own selection mechanism.
- **Absent ≠ empty.** Data that was never connected is drawn as absent; an empty lane
  claims it did not happen.

## The four registers — typographically visible

| register | mark | example |
|---|---|---|
| **measurement** | plain, unmarked | `523 names −25% on the quarter` |
| **reading** | **solid left rule** | `Megacaps repaired.` |
| **expected** | **dashed left rule** | `Five-day ratio needs to clear 1.0` |
| **action** | reversed block / large condensed | `WAIT FOR FTD` |

Weight and colour alone are not enough — they do not survive a screenshot. Every layer
needs a structural mark.
