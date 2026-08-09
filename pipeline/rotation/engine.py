"""Rotation engine -- the line, the ribbon, and the sentence at the end.

Three objects, each answering a different question about the same baskets:

* **line**   -- five disjoint two-week excesses against SPY. Descriptive. It
  shows the *shape* of a rotation: how fast it turned and how far it went,
  which is exactly what a quadrant plot flattens away.
* **ribbon** -- one four-state label per two-week step, so ten weeks of state
  reads as a single row without anyone parsing numbers.
* **verdict** -- three independent cuts vote risk-on or risk-off.

**The two-week grid is the drawing, not the judgment.** Our own window testing
(`pipeline/themes/FOUR_STATE_DESIGN.md`, section 6) found that every scheme
with a near bucket of two weeks or less flipped sign between half samples --
one went from -2.10% to +0.62%. So the line is drawn on two-week steps because
that is the resolution the eye needs, while every *state* on the ribbon is
computed on the month-scale V4 windows that survived. The grid controls where
we stand; it does not control what we measure from there.

Pure functions: no I/O, no clock. Every series is passed in ascending by date
and read only up to the anchor, so a truncated history replays unchanged.
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Sequence

from pipeline.themes.rs_engine import classify, safe_round

# Trading sessions, not calendar days -- a calendar fortnight straddles a
# variable number of sessions, which would make bucket widths uneven and the
# line's slope meaningless.
STEP = 10        # two weeks
STEPS = 5        # ten weeks of line and ribbon
NEAR = 21        # one month, the V4 near window
LEVEL = 63       # three months, the V4 level window


def _ret(closes: Sequence[float], end: int, span: int) -> Optional[float]:
    """Simple return over `span` sessions ending at index `end` (inclusive).

    Returns None rather than 0.0 when the history is too short. A missing
    window that reads as flat would place a basket in a state it did not earn.
    """
    start = end - span
    if start < 0 or end >= len(closes):
        return None
    a, b = closes[start], closes[end]
    if a is None or b is None or a <= 0:
        return None
    return b / a - 1.0


def _excess(basket: Sequence[float], bench: Sequence[float],
            end: int, span: int) -> Optional[float]:
    r, rb = _ret(basket, end, span), _ret(bench, end, span)
    return None if r is None or rb is None else r - rb


def anchors(n: int, steps: int = STEPS, step: int = STEP) -> List[int]:
    """Index of the last session in each two-week bucket, oldest first."""
    last = n - 1
    return [last - step * (steps - 1 - k) for k in range(steps)]


def line_series(basket: Sequence[float], bench: Sequence[float],
                steps: int = STEPS, step: int = STEP) -> List[Optional[float]]:
    """Excess return in each disjoint two-week bucket, oldest first.

    Disjoint, not cumulative: bucket k covers only its own fortnight, so a big
    move six weeks ago stops inflating every later point. A cumulative line
    would slope by construction and hide the turn.
    """
    return [_excess(basket, bench, a, step) for a in anchors(len(basket), steps, step)]


def state_at(basket: Sequence[float], bench: Sequence[float],
             end: int) -> Dict[str, Any]:
    """Four-state label as of session `end`, on the month-scale V4 windows.

    level = cumulative three-month excess; accel = last month's excess against
    the excess of the two months before it. Identical definition to
    `rs_engine.score_row`, computed from bars instead of Finviz columns.
    """
    level = _excess(basket, bench, end, LEVEL)
    near = _excess(basket, bench, end, NEAR)
    prior = _excess(basket, bench, end - NEAR, LEVEL - NEAR)
    accel = None if near is None or prior is None else near - prior
    state = None if level is None or accel is None else classify(level, accel)
    return {
        "state": state,
        "level": safe_round(level),
        "accel": safe_round(accel),
    }


def ribbon(basket: Sequence[float], bench: Sequence[float],
           steps: int = STEPS, step: int = STEP) -> List[Dict[str, Any]]:
    """One state per two-week step, oldest first."""
    return [state_at(basket, bench, a) for a in anchors(len(basket), steps, step)]


# ── the sentence ─────────────────────────────────────────────────────

def _side_excess(closes: Mapping[str, Sequence[float]], bench: Sequence[float],
                 tickers: Sequence[str], end: int, span: int) -> Optional[float]:
    """Equal-weighted mean excess across a cut's tickers.

    Equal weight because a cut is a question, not a portfolio -- cap-weighting
    would let one large ETF answer on behalf of the others.
    """
    vals = [_excess(closes[t], bench, end, span)
            for t in tickers if t in closes]
    vals = [v for v in vals if v is not None]
    return sum(vals) / len(vals) if vals else None


def _vote(spread: Optional[float]) -> Optional[str]:
    if spread is None or spread == 0:
        return None
    return "risk_on" if spread > 0 else "risk_off"


def cut_reading(closes: Mapping[str, Sequence[float]], bench: Sequence[float],
                cut: Mapping[str, Any], step: int = STEP) -> Dict[str, Any]:
    """One cut, read at two horizons, plus the speed of the turn.

    `spread` is the long side's excess minus the short side's, both against SPY
    over the same window. Two windows are reported, and that is the point:

    * **fortnight** -- what the market did most recently
    * **month**     -- whether it has been doing it long enough to be a regime

    A fortnight reading on its own is exactly the window our own testing found
    unreliable, so it is never published alone. When the two horizons agree the
    rotation is established; when they disagree the fortnight is a turn that
    has not yet earned the name. `delta` -- this fortnight's spread against the
    previous fortnight's -- is the speed, the reading a quadrant plot cannot
    give: it shows direction and position, never how fast the turn came.
    """
    n = len(bench)

    def spread(end: int, span: int) -> Optional[float]:
        lo = _side_excess(closes, bench, cut["long"], end, span)
        sh = _side_excess(closes, bench, cut["short"], end, span)
        return None if lo is None or sh is None else lo - sh

    s_now = spread(n - 1, step)
    s_prev = spread(n - 1 - step, step)
    s_month = spread(n - 1, NEAR)

    return {
        "key": cut["key"],
        "label": cut["label"],
        "question": cut["question"],
        "long": list(cut["long"]),
        "short": list(cut["short"]),
        "spread": safe_round(s_now),
        "delta": safe_round(None if s_now is None or s_prev is None else s_now - s_prev),
        "month_spread": safe_round(s_month),
        "vote": _vote(s_now),
        "month_vote": _vote(s_month),
    }


_WORD = {"risk_on": "risk on", "risk_off": "risk off"}


def _tally(readings: Sequence[Mapping[str, Any]], field: str
           ) -> tuple[Optional[str], int, int]:
    """(call, votes for it, votes cast) at one horizon."""
    votes = [r[field] for r in readings if r.get(field)]
    on, off = votes.count("risk_on"), votes.count("risk_off")
    call = "risk_on" if on > off else "risk_off" if off > on else None
    return call, max(on, off), on + off


def verdict(readings: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    """The one line, with the vote count and both horizons attached.

    The cuts are not statistically independent -- IVW and SPHB share large-cap
    tech names -- so this reports how many agreed and never converts that into
    a confidence. Three of three is a stronger sentence than two of three
    because more instruments had to move the same way, not because of any
    distributional claim.

    Two horizons produce three kinds of sentence, and the distinction is the
    whole value of the object:

    * **established** -- fortnight and month agree. A regime.
    * **turning**     -- the fortnight has flipped and the month has not. This
      is the reading that is worth something and the one most easily mistaken
      for the first, because a chart of the last two weeks looks the same in
      both cases.
    * **split**       -- the cuts disagree with each other. No call.
    """
    call, agree, counted = _tally(readings, "vote")
    m_call, m_agree, m_counted = _tally(readings, "month_vote")

    out: Dict[str, Any] = {
        "call": call, "agree": agree, "of": counted,
        "month_call": m_call, "month_agree": m_agree, "month_of": m_counted,
    }

    if not counted:
        return {**out, "phase": None,
                "sentence": "not enough history to read the rotation"}

    if call is None:
        return {**out, "phase": "split",
                "sentence": ("the cuts disagree with each other — there is no "
                             "rotation to call")}

    word = _WORD[call]
    lead = (f"every way we cut it, {word} — all {counted} agree"
            if agree == counted else f"{agree} of {counted} cuts read {word}")

    # Magnitude belongs in the sentence: "risk on" at 0.1pp and at 6pp are
    # different claims, and only one of them is worth acting on.
    sized = [r for r in readings if r["vote"] == call and r["spread"] is not None]
    if sized:
        widest = max(sized, key=lambda r: abs(r["spread"]))
        lead += (f", widest on {widest['label'].lower()} at "
                 f"{widest['spread']*100:+.1f}pp over the fortnight")

    if m_call == call:
        phase, tail = "established", f"; the month agrees — this is the regime"
    elif m_call is None:
        phase, tail = "turning", "; the month has no call yet — a turn, not a regime"
    else:
        phase = "turning"
        tail = (f"; the month still reads {_WORD[m_call]} "
                f"({m_agree} of {m_counted}) — a turn, not yet a regime")

    return {**out, "phase": phase, "sentence": lead + tail}
