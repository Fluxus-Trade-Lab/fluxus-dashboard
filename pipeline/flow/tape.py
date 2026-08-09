"""The tape — the declared seam between the live flow engine and this repo.

Until now the two repos were coupled by an absolute sibling path and a lockfile
in /tmp: the engine read `~/Documents/AI-Trading-System/data/gex/latest.json`,
and nothing declared the dependency, so renaming a file here silently broke a
process there at the next open. This module replaces that arrangement in the
other direction — the engine WRITES a versioned line format, and this repo READS
it through a single function that fails loudly on anything it does not
recognise.

The rules, all of which exist because their absence has already cost us:

* **Every line carries `v`.** A reader that guesses at an unversioned schema is
  a reader that keeps working incorrectly after the writer changes.
* **Unknown versions are an error, not a warning.** Skipping them silently would
  under-count premium and the number would still look plausible.
* **Legacy (unversioned) lines are readable only when the caller says so** —
  `allow_legacy=True` is a statement that you know the file predates the
  contract, not a default.
* **A malformed line names its line number.** "invalid tape" without a position
  is a message to a person who now has to bisect a million-line file.
"""
from __future__ import annotations

import json
from pathlib import Path

TAPE_VERSION = 1

# One classified 2-minute bar for one side of the book. This is the shape
# aggregate_2min() produces plus identity fields the engine adds.
BAR_REQUIRED = frozenset({"time_bin", "side", "premium_total", "bot_premium",
                          "sold_premium", "net_premium", "n_prints"})

KINDS = ("bar",)


def line(kind: str, payload: dict) -> str:
    """Serialise one tape line at the current version.

    The writer half of the contract. The engine adopting this function is the
    moment the sibling-path coupling can be deleted.
    """
    if kind not in KINDS:
        raise ValueError(f"kind must be one of {KINDS}")
    if kind == "bar":
        missing = BAR_REQUIRED - payload.keys()
        if missing:
            raise ValueError(f"bar payload missing {sorted(missing)}")
    return json.dumps({"v": TAPE_VERSION, "kind": kind, **payload},
                      sort_keys=True, default=str)


def read_tape(path: str | Path, *, allow_legacy: bool = False) -> list[dict]:
    """Read one session's tape, validating every line.

    Returns the payload dicts (with `v` and `kind` retained). Raises ValueError
    with the offending line number on: unparseable JSON, a version this reader
    does not know, a kind it does not know, or a bar missing required fields.
    Blank lines are permitted — an append-only file ends with one.
    """
    p = Path(path)
    out: list[dict] = []
    for i, raw in enumerate(p.read_text().splitlines(), start=1):
        if not raw.strip():
            continue
        try:
            row = json.loads(raw)
        except json.JSONDecodeError as e:
            raise ValueError(f"{p.name}:{i}: not JSON ({e.msg})") from None
        if "v" not in row:
            if allow_legacy:
                out.append({"v": 0, "kind": "bar", **row})
                continue
            raise ValueError(
                f"{p.name}:{i}: unversioned line — a pre-contract tape. Pass "
                f"allow_legacy=True only if you know this file predates v1.")
        if row["v"] != TAPE_VERSION:
            raise ValueError(f"{p.name}:{i}: tape version {row['v']!r}, reader "
                             f"knows {TAPE_VERSION}. Refusing to guess.")
        if row.get("kind") not in KINDS:
            raise ValueError(f"{p.name}:{i}: unknown kind {row.get('kind')!r}")
        if row["kind"] == "bar":
            missing = BAR_REQUIRED - row.keys()
            if missing:
                raise ValueError(f"{p.name}:{i}: bar missing {sorted(missing)}")
        out.append(row)
    return out


def per_strike_premium(bars: list[dict]) -> dict[float, dict]:
    """Net classified premium per strike — the input the reference map wants.

    Only bars that carry a strike participate; session-level bars (no strike)
    are skipped rather than pooled into a fake strike 0. Signs follow the
    aggregation: positive net = buyer-initiated dominates at that strike.
    """
    acc: dict[float, dict] = {}
    for b in bars:
        k = b.get("strike")
        if not isinstance(k, (int, float)):
            continue
        s = acc.setdefault(float(k), {"net_premium": 0.0, "premium_total": 0.0,
                                      "n_prints": 0})
        s["net_premium"] += float(b.get("net_premium") or 0.0)
        s["premium_total"] += float(b.get("premium_total") or 0.0)
        s["n_prints"] += int(b.get("n_prints") or 0)
    return acc
