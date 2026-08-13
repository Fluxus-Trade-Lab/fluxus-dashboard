"""Every rule we tried, and how it ended. The denominator.

    "17 volatility signals died. A leverage overlay died. Eight alternative base
     assets lost to plain SPY."   — @TailThatWagsDog, 2026-08-12

That count is the point of this file. A surviving rule from a search of unknown
size is not evidence: twenty independent probes at alpha .05 throw at least one
false positive 64% of the time, and forty-two throw one 88% of the time — which
is exactly how this project produced a `+4.4%` sequence finding that turned out
to be nothing. See `pipeline.reference.power.family_error`.

So the log is append-only and records **deaths as carefully as survivals**. A
rule deleted from the codebase still has a row here; that is the difference
between a research record and a highlight reel.

`survivors()` refuses to report a survival rate without the denominator beside
it, and `family_error_now()` prices the whole search so far.
"""
from __future__ import annotations

import json
from pathlib import Path

DEFAULT_LOG = Path("data/book/kill_log.jsonl")

VERDICTS = ("survived", "killed", "undecided")


def entry(result: dict, *, hypothesis: str, computed_from: str,
          date: str, note: str = "") -> dict:
    """One tested rule.

    `computed_from` is required and is a plain-English statement of which
    session's data the `active` series was built from. Lookahead is the failure
    the kill test cannot detect for you, so the claim that there is none has to
    be written down where a later reader can check it against the code.
    """
    if result.get("verdict") not in VERDICTS:
        raise ValueError(f"verdict must be one of {VERDICTS}")
    if not hypothesis:
        raise ValueError("a rule without a stated hypothesis cannot be killed "
                         "or credited — say what it was supposed to do")
    if not computed_from:
        raise ValueError("computed_from is required: name the session whose "
                         "data the signal was built from, or lookahead is "
                         "unfalsifiable")
    adv = result.get("advantage") or {}
    return {
        "date": date, "rule": result["rule"], "verdict": result["verdict"],
        "hypothesis": hypothesis, "computed_from": computed_from,
        "n_days": result.get("n_days"), "n_oos_days": result.get("n_oos_days"),
        "n_fired_oos": result.get("n_fired_oos"),
        "advantage": adv.get("advantage"),
        "ci": [adv.get("ci_low"), adv.get("ci_high")] if adv else None,
        "block": adv.get("block"), "draws": adv.get("draws"),
        "note": note or result.get("note", ""),
    }


def append(row: dict, path: str | Path = DEFAULT_LOG) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def read(path: str | Path = DEFAULT_LOG) -> list[dict]:
    p = Path(path)
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]


def counts(rows: list[dict] | None = None) -> dict:
    rows = read() if rows is None else rows
    out = {v: 0 for v in VERDICTS}
    for r in rows:
        if r.get("verdict") in out:
            out[r["verdict"]] += 1
    out["tested"] = len(rows)
    return out


def family_error_now(rows: list[dict] | None = None, alpha: float = 0.05) -> dict:
    """What the search so far costs in false-positive risk.

    Counts every DECIDED test — a survival and a kill are both a look at the
    data. Undecided tests are counted too and said so separately, because an
    undecided test still consumed a look even though it returned nothing.
    """
    from pipeline.reference.power import family_error
    rows = read() if rows is None else rows
    c = counts(rows)
    # Distinct HYPOTHESES, not runs. A timing-shuffled control is part of
    # testing one idea, not a second idea about the market, and counting it
    # would inflate the search. The run count is kept beside it because a
    # control is still a look at the data and the two numbers answer different
    # questions.
    k = len({r.get("hypothesis") for r in rows if r.get("hypothesis")})
    return {"tested": c["tested"], "hypotheses": k,
            **{v: c[v] for v in VERDICTS},
            "p_at_least_one_false_survivor": round(family_error(k, alpha), 4),
            "alpha": alpha,
            "note": (f"{c['tested']} runs over {k} distinct hypotheses; at "
                     f"alpha {alpha} a search of {k} throws at least one false "
                     f"survivor {family_error(k, alpha):.0%} of the time")}


def survivors(rows: list[dict] | None = None) -> dict:
    """Survivors, always beside the count of everything that was tried.

    Returning the list alone would be the highlight reel this file exists to
    prevent, so the denominator is part of the return value and not an optional
    extra a caller may drop.
    """
    rows = read() if rows is None else rows
    c = counts(rows)
    return {"survivors": [r for r in rows if r["verdict"] == "survived"],
            **c,
            "survival_rate": (c["survived"] / c["tested"]) if c["tested"] else None,
            **family_error_now(rows)}


def report(rows: list[dict] | None = None) -> str:
    rows = read() if rows is None else rows
    if not rows:
        return "kill log empty — nothing has been tested yet"
    c = counts(rows)
    lines = [f"{c['tested']} rules tested   "
             f"{c['survived']} survived   {c['killed']} killed   "
             f"{c['undecided']} undecided", ""]
    for r in rows:
        adv = (f"{r['advantage'] * 100:+.1f}pt" if r.get("advantage") is not None
               else "   —  ")
        lines.append(f"  [{r['verdict']:<9}] {r['rule']:<34} {adv}  "
                     f"fired {r.get('n_fired_oos', '?')} of "
                     f"{r.get('n_oos_days', '?')} OOS days")
    fe = family_error_now(rows)
    lines += ["", f"  {fe['note']}"]
    return "\n".join(lines)
