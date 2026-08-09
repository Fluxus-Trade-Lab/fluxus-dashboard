"""Internal learning log — claims, errors and method changes, with how each dies.

The scorecard answers "were the levels right". This answers the slower question:
**are we getting better, and how do we tend to be wrong.**

Every entry carries a `falsifier`: the observation that would show the entry was
mistaken. An entry without one is an opinion, and the writer refuses them — that
is the whole discipline this file exists to enforce.

Error entries also carry a `class`, because the pattern across errors is more
useful than any single error. From the first five logged, four were not
arithmetic mistakes: the maths was right and the *input or definition* was wrong,
which is an argument for cross-checks and provenance over more unit tests.
"""
from __future__ import annotations

import json
from pathlib import Path

DEFAULT_LOG = Path("data/reference/learning_log.jsonl")

KINDS = ("error", "hypothesis", "method_change")

# Observed failure modes. Extend deliberately — a class that catches everything
# catches nothing.
ERROR_CLASSES = (
    "unit_convention",      # right maths, wrong units
    "wrong_reference",      # right formula, wrong input (spot vs forward)
    "free_parameter",       # output dominated by a constant we chose
    "conflated_quantity",   # two different things sharing a name
    "non_simultaneous",     # comparing observations from different moments
    "arithmetic",           # actually wrong maths
    "plumbing",             # computed correctly, never reached the output
)


def entry(kind: str, claim: str, falsifier: str, *,
          error_class: str | None = None, status: str = "open",
          outcome: str | None = None, ref: str | None = None,
          date: str | None = None) -> dict:
    if kind not in KINDS:
        raise ValueError(f"kind must be one of {KINDS}")
    if error_class and error_class not in ERROR_CLASSES:
        raise ValueError(f"unknown error class {error_class!r}")
    if not falsifier.strip():
        raise ValueError("every entry needs a falsifier — what would show this is wrong?")
    return {"date": date, "kind": kind, "claim": claim, "falsifier": falsifier,
            "class": error_class, "status": status, "outcome": outcome, "ref": ref}


def append(e: dict, path: Path | str = DEFAULT_LOG) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a") as fh:
        fh.write(json.dumps(e, sort_keys=True) + "\n")


def read(path: Path | str = DEFAULT_LOG) -> list[dict]:
    p = Path(path)
    if not p.exists():
        return []
    out = []
    for line in p.read_text().splitlines():
        if line.strip():
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def error_pattern(rows: list[dict]) -> dict:
    """Which failure modes recur — the thing worth acting on."""
    counts: dict[str, int] = {}
    for r in rows:
        if r.get("kind") == "error" and r.get("class"):
            counts[r["class"]] = counts.get(r["class"], 0) + 1
    total = sum(counts.values())
    return {"counts": dict(sorted(counts.items(), key=lambda kv: -kv[1])),
            "total": total,
            "top": max(counts, key=counts.get) if counts else None}


def open_items(rows: list[dict]) -> list[dict]:
    """Hypotheses still awaiting the observation that would settle them."""
    return [r for r in rows if r.get("status") == "open" and r.get("kind") == "hypothesis"]
