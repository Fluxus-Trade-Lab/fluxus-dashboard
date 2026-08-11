"""Scheduled macro events, so a premise about the calendar can be checked.

Built 2026-08-11, the day a logged view read "CPI day — expect continued chop"
on a day that was not CPI day. July's CPI lands 2026-08-12 at 08:30 ET. The call
may still be right; the *reason* was resting on a fact nobody could check,
because this repo had no macro-event data of any kind.

Two rules this file exists to keep:

  * **A missing event is not an absent event.** If we hold no rows for NFP, the
    answer to "is today NFP?" is `unknown`, never `no`. Coverage is tracked per
    event and per date range, and a question outside that range comes back
    unknown too. This is the same distinction `profile.patterns` draws between
    a failed condition and an unmeasurable one, and it exists for the same
    reason: silence and denial must never look alike.
  * **It reports, it never blocks and never edits.** Human views are written by
    the human alone. A premise that turns out to be wrong is evidence about the
    reasoning, and evidence is only worth keeping if it stays where it fell.

Rows are append-only with provenance, because these dates get rescheduled —
February 2026's CPI moved from the 11th to the 13th — and a store that silently
overwrites cannot tell a correction from a typo. `load()` collapses duplicates
by taking the latest `recorded_at` for each (date, event).
"""
from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path

DEFAULT_LOG = Path("data/reference/events.jsonl")

# Canonical event keys. The alias table is what free text is matched against;
# an event absent from ALIASES cannot be detected in a rationale at all, which
# is a coverage gap of its own and is reported as such rather than assumed away.
ALIASES: dict[str, tuple[str, ...]] = {
    "CPI": ("cpi", "consumer price", "inflation print", "通胀数据", "通胀报告"),
    "PPI": ("ppi", "producer price"),
    "FOMC": ("fomc", "fed decision", "rate decision", "fed meeting", "议息"),
    "NFP": ("nfp", "non-farm", "nonfarm", "payroll", "jobs report", "非农"),
    "PCE": ("pce", "core pce"),
    "OPEX": ("opex", "monthly opex", "quad witching", "triple witching"),
}


def entry(*, date: str, event: str, name: str, source: str,
          time: str | None = None, recorded_at: str | None = None) -> dict:
    """One scheduled event.

    `date` and `time` are ET, matching every other date in this repo. `source`
    is required and is the URL the date was read from — a calendar without
    provenance is a calendar nobody can correct.
    """
    if event not in ALIASES:
        raise ValueError(f"unknown event key {event!r}; add it to ALIASES first")
    dt.date.fromisoformat(date)  # raises on a malformed date rather than storing it
    if not source:
        raise ValueError("source is required — an unsourced date cannot be corrected")
    return {"date": date, "time": time, "event": event, "name": name,
            "source": source, "recorded_at": recorded_at}


def append(row: dict, path: str | Path = DEFAULT_LOG) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def load(path: str | Path = DEFAULT_LOG) -> list[dict]:
    """Every event, deduped on (date, event) with the last row written winning.

    Last-written rather than latest `recorded_at`: the file is append-only, so
    file order IS the correction order, and it stays right even when a row was
    seeded without a timestamp.
    """
    p = Path(path)
    if not p.exists():
        return []
    seen: dict[tuple[str, str], dict] = {}
    for line in p.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        r = json.loads(line)
        seen[(r["date"], r["event"])] = r
    return sorted(seen.values(), key=lambda r: (r["date"], r["event"]))


def coverage(rows: list[dict] | None = None) -> dict[str, dict]:
    """Per event, the date range we actually hold. Everything else is unknown."""
    rows = load() if rows is None else rows
    out: dict[str, dict] = {}
    for r in rows:
        c = out.setdefault(r["event"], {"first": r["date"], "last": r["date"], "n": 0})
        c["first"] = min(c["first"], r["date"])
        c["last"] = max(c["last"], r["date"])
        c["n"] += 1
    return out


def covers(event: str, date: str, rows: list[dict] | None = None) -> bool:
    """Can we answer 'is `date` an `event` day?' at all?

    True only when the date falls inside the span of rows we hold for that
    event. Outside it — or with no rows at all — the honest answer to any
    question about that day is `unknown`, and every caller here respects that.
    """
    c = coverage(rows).get(event)
    return bool(c and c["first"] <= date <= c["last"])


def on(date: str, rows: list[dict] | None = None) -> list[dict]:
    """Events scheduled on that ET date."""
    rows = load() if rows is None else rows
    return [r for r in rows if r["date"] == date]


def upcoming(date: str, within: int = 7, rows: list[dict] | None = None) -> list[dict]:
    """Events from `date` forward, each carrying how many calendar days out."""
    rows = load() if rows is None else rows
    d0 = dt.date.fromisoformat(date)
    out = []
    for r in rows:
        delta = (dt.date.fromisoformat(r["date"]) - d0).days
        if 0 <= delta <= within:
            out.append({**r, "days_out": delta})
    return sorted(out, key=lambda r: (r["days_out"], r["event"]))


def nearest(event: str, date: str, rows: list[dict] | None = None) -> dict | None:
    """The scheduled occurrence of `event` closest to `date`, either side."""
    rows = load() if rows is None else rows
    cands = [r for r in rows if r["event"] == event]
    if not cands:
        return None
    d0 = dt.date.fromisoformat(date)
    r = min(cands, key=lambda r: abs((dt.date.fromisoformat(r["date"]) - d0).days))
    return {**r, "days_out": (dt.date.fromisoformat(r["date"]) - d0).days}


def mentions(text: str) -> list[str]:
    """Which event keys a free-text rationale names.

    Word-boundary matching on the ASCII aliases so "opex" is found in "post-opex
    drift" but "cpi" is not invented out of some longer token. The CJK aliases
    carry no word boundaries and are matched as substrings, which is how those
    scripts work.
    """
    low = (text or "").lower()
    hits = []
    for key, aliases in ALIASES.items():
        for a in aliases:
            found = (a in low if not a.isascii()
                     else re.search(rf"\b{re.escape(a)}\b", low) is not None)
            if found:
                hits.append(key)
                break
    return hits


def check_claim(text: str, date: str, rows: list[dict] | None = None) -> list[dict]:
    """Audit a rationale's calendar premise against the schedule.

    One result per event the text names, with `verdict` in:

      ``confirmed``  the event is on the calendar for that date
      ``mismatch``   we hold that event's schedule for that period, and the
                     date is not one of them — `nearest` says when it is
      ``unknown``    we do not hold enough of that event's schedule to say

    Never raises, never mutates, never returns a bare boolean. A rationale can
    be right for a wrong reason and this is the record of that, not a verdict on
    the trade.
    """
    rows = load() if rows is None else rows
    out = []
    for key in mentions(text):
        if any(r["event"] == key for r in on(date, rows)):
            out.append({"event": key, "verdict": "confirmed", "nearest": None,
                        "note": f"{key} is scheduled for {date}"})
        elif covers(key, date, rows):
            n = nearest(key, date, rows)
            when = (f"{n['date']} ({n['days_out']:+d}d)" if n else "unknown")
            out.append({"event": key, "verdict": "mismatch", "nearest": n,
                        "note": f"{key} is not on {date}; nearest is {when}"})
        else:
            c = coverage(rows).get(key)
            have = (f"we hold {c['n']} {key} dates, {c['first']}..{c['last']}"
                    if c else f"we hold no {key} dates at all")
            out.append({"event": key, "verdict": "unknown", "nearest": None,
                        "note": f"cannot say whether {date} is a {key} day — {have}"})
    return out


def summary(date: str, within: int = 7, rows: list[dict] | None = None) -> str:
    """One line for the brief: what is on today, and what is coming.

    Says which events it can speak for. A calendar line that lists two events
    reads as "those are the only two", and if we only track two that sentence is
    a lie of omission.
    """
    rows = load() if rows is None else rows
    if not rows:
        return "Calendar ......... no event data held"
    cov = coverage(rows)
    today = on(date, rows)
    soon = [r for r in upcoming(date, within, rows) if r["days_out"] > 0]
    head = (", ".join(f"{r['event']} {r['time'] or ''}".strip() for r in today)
            if today else "nothing scheduled")
    tail = ("; next " + ", ".join(f"{r['event']} +{r['days_out']}d" for r in soon[:3])
            if soon else f"; nothing else within {within}d")
    return f"Calendar ......... {head}{tail}  (tracking {'/'.join(sorted(cov))})"
