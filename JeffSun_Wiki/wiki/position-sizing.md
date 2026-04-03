---
title: "Position Sizing"
aliases: [sizing, risk per trade, R-multiple sizing]
category: "Risk & Sizing"
tags: [risk-management, position-sizing]
sources:
  - "[[sources/notion/complete-guide-snapshot]]"
  - "[[sources/notion/risk-and-position-management-snapshot]]"
related:
  - "[[3-stop-strategy]]"
  - "[[risk-management-philosophy]]"
  - "[[entry-rules]]"
  - "[[adr-percent]]"
notion_ref: "26b5bc7910f780168d6fdeb6944c60c8"
created: 2026-04-03
updated: 2026-04-03
---

# Position Sizing

> [!summary]
> Jeff uses fixed percentage risk relative to equity to define position size, with the R-multiple as the universal unit of measurement. He adjusts capital allocation based on ADR%, designs re-entries to stay within -1R total risk, and frames the entire system as a "printing machine" built on math over 1,000+ trades.

## Core Concept

The **R-multiple** is the foundation of Jeff's sizing framework. R represents the initial risk on a trade — the dollar distance between entry price and stop-loss, multiplied by share count. Every trade outcome is then expressed as a multiple of this initial R amount, allowing objective evaluation of performance regardless of position size or stock price.

> "The 'R' in R-Multiple represents the **initial risk** on a trade, defined by the difference between the entry price and the stop-loss level. An R-Multiple then expresses the profit or loss of a trade as a multiple of this initial 'R' amount."

Jeff maintains a **fixed % risk relative to equity** for every trade. This means as equity grows, absolute dollar risk scales proportionally — and as equity shrinks during drawdowns, risk automatically decreases, protecting capital.

## Rules / Details

**Fixed % Risk to Equity**
- Each new position risks a fixed percentage of current total equity
- The [[3-stop-strategy]] further reduces actual losses to -0.6 to -0.8R per trade instead of -1R
- Re-entries after being stopped out are sized so that combined risk still stays within -1R total [[sources/tweets/jfsrev-pedma7]]

**Capital Allocation by ADR%**
- Higher ADR% securities require less capital allocation to achieve the same R-risk, because wider daily ranges mean the stop distance captures more potential move per dollar risked [[sources/tweets/jfsrev-1856232860107350147]]
- Jeff published a ballpark estimate of % capital allocation needed for executing securities based on different ADR% levels [[sources/tweets/jfsrev-1939966489475547529]]

**The Effects of 1,000 Trades**
- Jeff visualizes the compounding effect of fixed % risk over 1,000 trades — demonstrating the gradual decline of equity during losing streaks and parabolic growth during winning streaks [[sources/tweets/jfsrev-1866778428709671171]]
- This graphic is one of his 6 key internalization charts (Chapter 9)

## How Jeff Applies It

Jeff frames the outcome of disciplined sizing as building a **"printing machine"**:

> "If You Designed Exit Rules That Lift Your Average R, You've Built Yourself A Printing Machine" — LoneStockTrader, shared by Jeff [[sources/tweets/jfsrev-LoneStockTrader-1973958399663747244]]

His 2024 results demonstrate the power of this approach: a win rate as low as 31.6% in his worst month, yet trades reaching 51R (max), four trades at 20R+, and eleven at 10R+. The math works because sizing is consistent and losses are mechanically capped.

> "One trade to more than cover 13 losing streaks is my style." [[sources/tweets/jfsrev-1749460835662225835]]

A companion example: 27% win rate compounding to 114% annualized return, achieved through controlled R-losses and letting winners run [[sources/tweets/jfsrev-1940818944228839430]].

## Related Concepts

- [[3-stop-strategy]] — The mechanism that reduces average R-loss below -1R
- [[risk-management-philosophy]] — The "best loser is long-term winner" framework
- [[adr-percent]] — How ADR% affects capital allocation per position
- [[drawdown-management]] — What happens during losing streaks with fixed % sizing
- [[entry-rules]] — Tight execution amplifies R-returns parabolically

## Sources

- Chapter 6: Design of Entry, Stop, % Risk to Equity [[sources/notion/complete-guide-snapshot]]
- Chapter 9: 6 graphics to internalize [[sources/notion/complete-guide-snapshot]]
- Kyna Kosling's risk management compilation [[sources/notion/risk-and-position-management-snapshot]]
