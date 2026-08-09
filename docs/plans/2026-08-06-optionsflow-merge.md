# Is OptionsFlow complementary, and should it merge?

Short answer: **complementary, yes — it is exactly the page we are missing. Fully
merge, no. Merge the maths, leave the process.**

## They are already coupled, in the worst available way

`OptionsFlow/config.toml`:

```toml
[gex]
refresh_s    = 600
sibling_path = "~/Documents/AI-Trading-System/data/gex/latest.json"
lockfile     = "/tmp/gex_pull.lock"
```

The flow engine reads this repo's GEX file across the filesystem by absolute
path, and the two processes coordinate through a lockfile in `/tmp`. Nothing
declares this dependency: no import, no package, no version. Renaming
`latest.json` breaks a program in another repository, silently, at 09:30 the next
morning. `confluence/scorer.py` already grades signals against `call_wall` /
`put_wall` / `flip` — so the join we said we lacked partly exists, just outside
anything either repo's tests can see.

So the question is not whether to couple them. They are coupled. The question is
whether the coupling gets declared.

## What each side actually is

| | this repo | OptionsFlow |
|---|---|---|
| shape | batch — scripts that run and exit | streaming — a long-lived process |
| cadence | premarket / midday / post-close | continuous through RTH |
| failure | a script exits non-zero | a daemon goes stale and nobody notices |
| infra | launchd one-shots | launchd + watchdog + lockfile |
| size | — | 14,290 lines |

That difference is the whole argument. A repo of short-lived scripts and a repo
with a supervised daemon want different tests, different logs, different
restarts. Folding the daemon into a repo that also holds the Substack drafts and
the React dashboard would be putting a live process where nothing else has a
lifecycle.

## Where OptionsFlow fits in the report

nextSignals' four pages map cleanly onto what we now have:

| his page | ours |
|---|---|
| AUCTION MARKET | `pipeline/profile/tpo.py` — built this week |
| OPTIONS CHAIN | `pipeline/gex/` — GEX, charm, dominance |
| **ORDER BOOK** | **OptionsFlow `flow/`** — this is that page |
| DATA SYNTHESIS | `pipeline/profile/synthesis.py` |

"Calls being sold −3.08M net in 750–760", "sold-put zone", "top of bought-put
band" are Lee-Ready classification aggregated per strike in premium. OptionsFlow
already classifies; it just does it for ~30 strikes around the money rather than
the chain, and its output never reaches the brief.

## The split

**Move — `flow/` (620 lines).** `quote_rule`, `enrich`, `aggregate`, `clusters`,
`spreads`, `delta_approx`. Pure functions, no IO, no process, ~6,500 lines of
tests behind them, validated against a golden replay. These belong in
`pipeline/flow/` next to `pipeline/gex/` and `pipeline/profile/`, because the
synthesis layer has to import them and cross-repo imports are how the
`/tmp` lockfile happened.

**Leave — `live/` (1,178), `display/` (2,895), `scripts/` (2,926).** The engine,
the Plotly panes, the CLIs. These stay their own repo and their own process. The
contract between the two becomes explicit: **the engine writes a JSONL tape; the
brief reads the tape.** A file format, versioned, with a reader that fails loudly
on a schema it does not recognise — instead of an absolute path into a sibling
checkout.

**Retire — `confluence/scorer.py` (64 lines).** Its A/B/C grading is a second,
weaker confluence implementation that does not know the independence rule.
Flow becomes a third framework inside `synthesis.reference_map()`, where
"auction + options + flow agree" is countable and "gamma + charm agree" still
does not count as anything.

**Invert the lockfile.** Today the flow engine pauses its subscriptions while the
GEX pull runs, because both compete for IBKR's ~100 market-data lines. That is a
real constraint and the mechanism is fine; what is wrong is that it lives in
`/tmp` with no owner. It becomes a documented protocol in one place, with the
line budget written down, since exhausting it is what silently starved SPY and
QQQ of quotes twice this week.

## Order

1. `pipeline/flow/` — move the pure modules with their tests, no behaviour change
2. Tape format — version it, write the reader, make the reader fail loudly
3. Widen coverage — per-strike premium across the chain, not just the ATM core
4. Third framework — flow into `synthesis.reference_map()`, delete `confluence/`
5. Line-budget protocol — one document, both repos obey it

Step 1 is mechanical and can happen without touching the running engine. Step 3
is the expensive one and is the same "weeks" estimate as before; nothing here
makes it cheaper, but steps 1–2 mean the work lands somewhere the brief can use.

## What this does not fix

Widening the tape to the full chain still costs market-data lines we do not have
spare, and that is the binding constraint on the bought/sold bands — not code
structure. Merging the maths makes the result usable; it does not make the data
affordable.
