# Trade Analysis Docs

How to turn a trade log into decisions — the method, the prompts, and the mistakes that shaped both.

| File | What it is |
|---|---|
| [`TRADE_ANALYSIS_GUIDE.en.md`](./TRADE_ANALYSIS_GUIDE.en.md) | **The method.** Beginner tier (what a review must answer, R-multiples, metric glossary, the 3 mistakes that bite first) + advanced tier (SQN's capped N, when Kelly lies, the 3 sizing questions, heat measured three ways, regime attribution, honesty discipline) |
| [`TRADE_ANALYSIS_GUIDE.zh.md`](./TRADE_ANALYSIS_GUIDE.zh.md) | 同上，中文版 |
| [`TRADE_ANALYSIS_PROMPTS.en.md`](./TRADE_ANALYSIS_PROMPTS.en.md) | **Six copy-paste prompts**: full review · behavioural diagnosis · sizing audit · counterfactual · SQN · regime attribution |
| [`TRADE_ANALYSIS_PROMPTS.zh.md`](./TRADE_ANALYSIS_PROMPTS.zh.md) | 同上，中文版 |

`.en` and `.zh` are the same content in two languages, not two different documents.

---

## If you are an AI picking this up

**Start with the prompts file.** Each prompt already carries the requirements that make the output trustworthy; the guide explains why each one exists.

The single most load-bearing idea: **every trade must be expressed as an R-multiple**
(`R = P&L ÷ (|entry − initial stop| × qty)`) before any analysis begins. Without a recorded initial stop, most of what follows is not computable.

Both files end with a table mapping each requirement to the specific bug that taught it. Those are the parts worth trusting most — they were paid for.

## Where the real numbers live

These docs are method, not data. In this repo:

- `PERFORMANCE_TRUTH.md` (repo root) — the canonical, aggregate-only figures for this account. Any published number must reconcile against it.
- `pipeline/portfolio/` — the engine: `performance_review.py` (R + stats), `mtm.py` (mark-to-market curve + drawdown), `analysis.py` (behavioural diagnosis, SQN, regime attribution), `sizing.py` (Kelly + Monte Carlo objectives), `report_html.py` (the shareable report).
- `data/portfolio/reviews/` — generated reports (HTML + PDF). **Contains real trade data — do not publish.**

Regenerate a report:

```bash
python -m pipeline.portfolio.report_html --period h1     # or --all-months
python scripts/html_to_pdf.py                            # HTML → PDF
```
