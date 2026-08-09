"""Side-classified option flow — the order-book framework.

Moved verbatim from ~/Documents/OptionsFlow/flow/ (commit history lives there).
These are the PURE pieces: Lee-Ready classification, trade/quote enrichment,
2-minute aggregation, cluster labelling, spread netting, delta approximation,
and ATM-core strike selection. No IO, no process, no IBKR — the live engine
stays in the OptionsFlow repo and talks to this repo through the tape format
defined in pipeline/flow/tape.py, not through a sibling path.
"""
