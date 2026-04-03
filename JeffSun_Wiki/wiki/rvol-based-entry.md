---
title: "RVOL-Based Entry"
aliases: ["relative volume entry", "RVOL confirmation", "volume entry"]
category: "Entry & Execution"
tags: ["glossary-term", "RVOL", "volume", "ORH", "execution"]
sources: ["https://x.com/jfsrev", "Complete Guide Chapters 2 & 6"]
related: ["entry-rules", "execution-quality", "lod-atr-rule"]
notion_ref: "26b5bc7910f780168d6fdeb6944c60c8"
created: 2026-04-03
updated: 2026-04-03
---

# RVOL-Based Entry

> [!summary]
> Relative Volume (RVOL) is Jeff Sun's primary confirmation signal for trade entry. RVOL on Opening Range High (ORH) reclaims has a proven statistical edge, and RVOL-based entry rules have saved Jeff from countless unnecessary stop losses year after year.

## Core Concept

RVOL measures current volume relative to the average volume over a lookback period (typically 50-day sessions). It answers one question: **is institutional participation present right now?**

Jeff treats RVOL as a hard gate for entry. Without substantial relative volume, price action fades -- moves lack the conviction to sustain breakouts, and positions drift into stop losses. This principle is codified as Hard Rule #4 in the [[entry-rules]]:

> Hard rule: I do not enter trade if there's no substantial RVOL -- stocks outside of mega cap liquid watchlist and liquid ETFs -- because price always fades outside of RVOL.

The exception is mega cap liquid names and liquid ETFs, which have sufficient baseline volume to sustain directional moves.

## RVOL on ORH: Statistical Edge

RVOL-based entry on Opening Range High (ORH) reclaims has a proven statistical edge in the market. The ORH represents the high of the initial trading range established in the first minutes of the session. When a stock reclaims its ORH on elevated RVOL, it signals that buyers are willing to pay above the opening range with conviction -- a setup Jeff references frequently:

> "RVOL based entry on ORH have proven statistical edge in the market."

The M30 Re-ORH variant (30-minute reclaim of the opening range high) adds a time filter, waiting for the initial noise to settle before confirming the ORH reclaim with volume.

## The KC Trade: +180% in 6 Weeks

Jeff's KC trade -- which returned +180% in approximately 6 weeks -- exemplifies RVOL-based entry in action. The strong volume run-rate served as the first proof of strong buying, confirming the setup before entry. The trade began with a screening process that identified KC's chart structure, but the final execution trigger was the RVOL confirmation on the breakout day.

> "Using RVOL for entry confirmation: Strong volume run-rate as first proof of strong buying for exceptional short term return."

## Saving From Unnecessary Stops

Jeff explicitly credits RVOL-based entry rules with protecting capital over multiple years:

> "RVOL based entry rules have saved me from countless unnecessary stop losses year after year."

The logic: a breakout without volume confirmation is more likely to fail. By requiring RVOL before entering, Jeff filters out the majority of false breakouts that would otherwise produce -1R (or -0.67R under the [[three-stop-strategy]]) losses. Over hundreds of trades, this filter meaningfully improves the profit factor.

## Adam H. Grimes on RVOL

Jeff credits Adam H. Grimes with explaining RVOL concepts better than anyone else, referencing Grimes' 2015 work on the subject. In 2025, Grimes wrote an additional piece on RVOL after Jeff's own tweet on the topic caught his attention -- a cross-pollination that Jeff highlighted as validation of the concept's importance from a respected market researcher.

## Defining "High RVOL" in Practice

One of the practical challenges with RVOL is defining what qualifies as "high." Jeff offers a concrete heuristic using the Simple Volume with Pocket Pivots indicator by @finallynitin:

> "If you find it hard to define what qualifies as high RVOL, use Projected Volume in the script with a 50% haircut."

This means: take the indicator's projected end-of-day volume based on the current run-rate, then apply a 50% discount. If the result still qualifies as elevated volume, the RVOL signal is genuine. The haircut accounts for the common pattern where volume is front-loaded at the open and decays throughout the session.

## How Jeff Applies It

Jeff's live market setup includes dedicated RVOL monitoring:

1. **Pre-market**: Two live market screeners on TradingView -- one for Focus List names, one for pre-market gappers -- both filtered for RVOL
2. **At open**: Monitors RVOL run-rate across Focus List names, looking for extreme readings that justify entry within the first 30 minutes (overriding Hard Rule #5)
3. **Post-30 minutes**: Standard RVOL confirmation required on ORH reclaims or breakout levels
4. **Throughout session**: If RVOL decays, the entry thesis weakens -- no new positions without volume conviction

## Related Concepts

- [[entry-rules]] -- RVOL is Hard Rule #4
- [[execution-quality]] -- RVOL as part of tight entry framework
- [[lod-atr-rule]] -- Complementary intraday filter
- [[focus-list]] -- Where RVOL monitoring begins

## Sources

- [RVOL on ORH statistical edge](https://x.com/jfsrev/status/1809139555041518052)
- [KC trade: +180% with RVOL confirmation](https://x.com/jfsrev/status/1946777562648383700)
- [RVOL rules saving from unnecessary stops](https://x.com/jfsrev/status/1955826518644678725)
- [Adam H. Grimes explains RVOL (2015)](https://x.com/AdamHGrimes/status/1957795316066873464)
- [Adam H. Grimes 2025 RVOL piece](https://x.com/AdamHGrimes/status/1958884198430703784)
- [Defining high RVOL with 50% haircut](https://x.com/jfsrev/status/1950202147787977058)
- [Live market mainframe with RVOL monitoring](https://x.com/jfsrev/status/1946214673482969302)
