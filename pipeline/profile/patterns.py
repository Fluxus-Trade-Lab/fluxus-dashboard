"""Named auction patterns, reported condition by condition.

The first is the two-session bullish setup @TailThatWagsDog specified on
2026-08-11, applying Donald Jones' auction market value principles. He gave it
in full — conditions, entry, anchor, objective, invalidation — so it can be
implemented literally rather than paraphrased:

    Day 1, an incomplete auction
      poor high made late, on two or three TPOs
      close at or near the session low, BELOW the TPOC
      no excess at the low — closing on the extreme, no punctuation
    Day 2, the granted probe refused
      opens above Day 1's close and the low holds there
      low holds at or above Day 1's TPOC
      TPOC prints higher than Day 1's — value migrates up
      VPOC and TPOC coincide — volume and time agree at one price
      buying tail from the open, periods 1-2
      close above Day 2's own TPOC but below its high

    entry Day 2's close · anchor Day 1's TPOC · objective Day 1's poor high
    invalid below Day 1's close, or if Day 2's TPOC fails to migrate up

**This returns a checklist, never a verdict.** A boolean would hide that eight
of ten conditions held, which is the interesting case and the one a bare False
throws away. Every condition reports what it needed, what it saw, and whether
that particular input was even measurable.

Nothing here says the pattern works. It is one practitioner's stated structure,
implemented so it can be counted and eventually scored. Our own record says a
published level holds about half the time, and that was measured; this has not
been.
"""
from __future__ import annotations


def _n(x, spec: str = ",.1f") -> str:
    """Format a number, or say it is absent.

    Every `saw` string below reports values that may be missing. Guarding the
    verdict and then formatting the same value unconditionally is how a
    correctly-detected missing input turns into a TypeError — the second time
    this exact shape has bitten, after a CLI that printed a variable bound below
    the branch that returned.
    """
    return format(x, spec) if isinstance(x, (int, float)) else "—"


def _cond(name: str, ok: bool | None, needed: str, saw: str) -> dict:
    """`ok=None` means the input was missing — never silently False."""
    return {"name": name, "ok": ok, "needed": needed, "saw": saw,
            "measurable": ok is not None}


def _t(profile: dict) -> dict:
    return (profile or {}).get("tpo") or {}


def bullish_two_session(day1: dict, day2: dict,
                        late_from: int = 7, poor_max_tpos: int = 3) -> dict:
    """Score the setup across two consecutive session profiles."""
    a, b = _t(day1), _t(day2)
    va, vb = (day1 or {}).get("volume") or {}, (day2 or {}).get("volume") or {}
    C = []

    # ---------------- Day 1: an incomplete auction ----------------
    pe = a.get("poor_extremes") or {}
    hp, tpos = a.get("high_period"), pe.get("high_tpos")
    C.append(_cond(
        "D1 poor high made late",
        None if (hp is None or tpos is None) else
        (bool(pe.get("poor_high")) and hp >= late_from and tpos <= poor_max_tpos),
        f"poor high in period {late_from}+ on <= {poor_max_tpos} TPOs",
        "not measurable" if hp is None else
        f"period {hp}, {tpos} TPOs, poor={pe.get('poor_high')}"))

    cl, lo, tp = a.get("close"), a.get("low"), a.get("tpoc")
    C.append(_cond(
        "D1 closed below its own TPOC",
        None if (cl is None or tp is None) else cl < tp,
        "close < TPOC — the day ended disagreeing with its own value",
        "not measurable" if cl is None else f"close {_n(cl)} vs TPOC {_n(tp)}"))

    rng = (a.get("high") or 0) - (lo or 0)
    C.append(_cond(
        "D1 closed at or near the low",
        None if (cl is None or lo is None or rng <= 0) else (cl - lo) <= 0.25 * rng,
        "close within the lower quarter of the range — still probing at the bell",
        "not measurable" if cl is None else
        f"close {(cl - lo) / rng:.0%} up from the low" if (cl is not None and lo is not None and rng) else "—"))

    buy_tail = (a.get("tails") or {}).get("buying")
    C.append(_cond(
        "D1 no excess at the low",
        None if a.get("tails") is None else
        not (buy_tail and buy_tail.get("significant")),
        "no significant buying tail — the low was never punctuated",
        "not measurable" if a.get("tails") is None else
        ("a significant buying tail exists" if buy_tail and buy_tail.get("significant")
         else "no significant tail")))

    # ---------------- Day 2: the probe refused ----------------
    C.append(_cond(
        "D2 opened above D1's close",
        None if (b.get("open") is None or cl is None) else b["open"] > cl,
        "open > D1 close — the granted probe lower is declined at the bell",
        "not measurable" if b.get("open") is None else
        f"open {_n(b['open'])} vs D1 close {_n(cl)}"))

    C.append(_cond(
        "D2 low held at or above D1's TPOC",
        None if (b.get("low") is None or tp is None) else b["low"] >= tp,
        "D2 low >= D1 TPOC — prior validated value becomes support",
        "not measurable" if b.get("low") is None else
        f"D2 low {_n(b['low'])} vs D1 TPOC {_n(tp)}"))

    C.append(_cond(
        "value migrated up",
        None if (b.get("tpoc") is None or tp is None) else b["tpoc"] > tp,
        "D2 TPOC > D1 TPOC — this one is also the invalidation",
        "not measurable" if b.get("tpoc") is None else
        f"{_n(tp)} -> {_n(b['tpoc'])}"))

    C.append(_cond(
        "D2 VPOC and TPOC coincide",
        vb.get("coincide"),
        "volume and time agree at one price — value validated, not merely transacted",
        "not measurable — needs both on one instrument" if vb.get("coincide") is None
        else f"VPOC {_n(vb.get('vpoc'))} / TPOC {_n(vb.get('tpoc'))}"))

    bt = (b.get("tails") or {}).get("buying")
    C.append(_cond(
        "D2 buying tail from the open",
        None if b.get("tails") is None else bool(bt and bt.get("significant")),
        "responsive buying in the first brackets, never revisited",
        "not measurable" if b.get("tails") is None else
        (f"{bt['length']} ticks at {_n(bt['low'])}" if bt else "none")))

    C.append(_cond(
        "D2 closed above its TPOC but below its high",
        None if (b.get("close") is None or b.get("tpoc") is None
                 or b.get("high") is None) else
        b["tpoc"] < b["close"] < b["high"],
        "above value confirms; short of the extreme leaves the buying auction open",
        "not measurable" if b.get("close") is None else
        f"close {_n(b['close'])} vs TPOC {_n(b.get('tpoc'))} / high {_n(b.get('high'))}"))

    met = [c for c in C if c["ok"] is True]
    failed = [c for c in C if c["ok"] is False]
    unmeasurable = [c for c in C if c["ok"] is None]
    return {
        "pattern": "bullish two-session value migration (Jones / TailThatWagsDog)",
        "sessions": [(day1 or {}).get("date"), (day2 or {}).get("date")],
        "conditions": C,
        "n_met": len(met), "n_failed": len(failed), "n_unmeasurable": len(unmeasurable),
        "n_total": len(C),
        "complete": not failed and not unmeasurable,
        "reference_prices": {
            "entry": b.get("close"),
            "anchor_must_hold": tp,
            "first_objective": (a.get("poor_extremes") or {}).get("high"),
            "invalidation_below": cl,
        },
        "note": "a checklist, not a verdict — and an untested one: this is a "
                "practitioner's stated structure, implemented literally, never "
                "yet scored against outcomes here",
    }
