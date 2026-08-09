"""Was the human's view formed before or after seeing the machine's?

The CDSS deskilling literature says the mitigation for an anchored second
opinion is ordering: the human commits first, then sees the model. Our daily
chain had it backwards — the brief was pushed at 07:30 and a view would be filed
afterwards, having already read it. That is not an independent opinion, and 20
such views would build the merge's weights on a contaminated sample.

**The important part is not enforcing the order — it is measuring it.** I cannot
know whether Andy read a brief. What I can know is when it was pushed, and
whether his view predates that. So every full brief push is recorded, every view
is classified against the record, and the hit rate is reported split by the two.

That turns the anchoring worry from a design assumption into a testable claim:
if independent and anchored views score the same, anchoring is not happening
here and the ordering change is unnecessary ceremony.

A view with no brief on record for its session is `independent` — nothing was
there to anchor to. A view whose session has a push but no usable timestamp is
`unknown`, never quietly counted as clean.
"""
from __future__ import annotations

import json
from pathlib import Path

DEFAULT_LOG = Path("data/centaur/brief_pushes.jsonl")

INDEPENDENT = "independent"
ANCHORED = "anchored"
UNKNOWN = "unknown"


def record_push(session: str, pushed_at: str, kind: str = "full",
                path: Path | str = DEFAULT_LOG) -> bool:
    """Note that a brief for `session` went out at `pushed_at`.

    `kind` distinguishes the prompt-only card — which carries the question but no
    answer, and therefore cannot anchor a direction — from the full brief.
    Only `full` pushes count as exposure.
    """
    p = Path(path)
    key = (session, kind)
    if any((r.get("session"), r.get("kind")) == key for r in read(path)):
        return False
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a") as fh:
        fh.write(json.dumps({"session": session, "pushed_at": pushed_at,
                             "kind": kind}, sort_keys=True) + "\n")
    return True


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


def first_full_push(pushes: list[dict]) -> dict[str, str]:
    """{session: earliest full-brief push time}. Earliest, because the first
    exposure is the one that could have anchored."""
    out: dict[str, str] = {}
    for r in pushes:
        if r.get("kind") != "full":
            continue
        s, t = r.get("session"), r.get("pushed_at")
        if not s or not t:
            continue
        if s not in out or t < out[s]:
            out[s] = t
    return out


def classify(view: dict, pushes: list[dict]) -> str:
    """Was this view filed before the session's full brief went out?"""
    if view.get("source") != "human":
        return INDEPENDENT           # the machine cannot be anchored by itself
    seen = first_full_push(pushes).get(view.get("session"))
    if seen is None:
        return INDEPENDENT           # nothing was published to anchor to
    asof = view.get("asof")
    if not asof:
        return UNKNOWN
    return INDEPENDENT if asof < seen else ANCHORED


def split(rows: list[dict], pushes: list[dict]) -> dict[str, list[dict]]:
    """Human views grouped by whether the brief had gone out first."""
    out: dict[str, list[dict]] = {INDEPENDENT: [], ANCHORED: [], UNKNOWN: []}
    for r in rows:
        if r.get("source") != "human":
            continue
        out[classify(r, pushes)].append(r)
    return out
