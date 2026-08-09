"""Market Profile — the auction half of the read.

Everything here is one of two things: a count of *time* at a price (TPO), or a
count of *volume* at a price. Steidlmayer's insight, formalised at the CBOT from
the 1960s-70s and released publicly in 1985, is that price alone says nothing
about whether the market accepted a level — time at price does.

**Sources and how far each is trusted**

* J. Peter Steidlmayer / CBOT — originator. "Market Profile" is a CME Group mark.
* James Dalton, *Mind Over Markets* (2nd ed.) — the practitioner standard. Its
  appendix carries the TPO value-area calculation, and its definitions of the
  initial balance ("the first two time periods") and of tails ("at least two
  TPOs to be significant") are the ones implemented here.
* Vendor docs (CQG, Sierra Chart, TradingView) — authoritative for what a given
  chart will *show*, not for theory, and they do not agree with each other.

**The disagreement you must know about.** There are two value-area algorithms in
circulation and they can return different boundaries on the same profile:

  ``pair``   Dalton/CBOT manual method — compare the SUM of the two prices above
             the current area against the SUM of the two below, and absorb the
             larger PAIR. This is the default here.
  ``single`` CQG's published method — expand ONE price at a time, choosing the
             direction by the single adjacent price.

This is a free parameter, not a fact, so it is named in the result rather than
buried. Two vendors' VAH differing by a tick is this choice, not a bug.

What is deliberately NOT implemented: "time diversity". The phrase appears in
some practitioners' writing but is not in the Steidlmayer/Dalton lexicon, and we
do not adopt vocabulary we cannot source. The measurable quantity it points at —
a price holding heavy volume but few TPOs — is available as
``volume_without_time``.
"""
from __future__ import annotations

import math
import string

# A-Z then a-z: the CBOT half-hour bracket letters, 52 periods = 26 hours.
LETTERS = string.ascii_uppercase + string.ascii_lowercase

VALUE_AREA_COVERAGE = 0.70          # ~1 standard deviation, per the CBOT convention
VALUE_AREA_METHODS = ("pair", "single")


def price_buckets(low: float, high: float, tick: float) -> list[float]:
    """Every tick-aligned price the range [low, high] touches, ascending.

    Aligned to the tick grid rather than to `low`, so two bars that overlap in
    price share bucket identities — otherwise no price ever accumulates a second
    TPO and the whole profile is flat.
    """
    if tick <= 0:
        raise ValueError("tick must be positive")
    lo = math.floor(low / tick + 1e-9)
    hi = math.ceil(high / tick - 1e-9)
    return [round(i * tick, 10) for i in range(lo, hi + 1)]


def build_profile(bars: list[dict], tick: float) -> dict[float, str]:
    """{price: letters} — which brackets touched each price.

    `bars` are period bars in chronological order, each {high, low, ...}. One bar
    is one letter; feed 30-minute bars for the standard profile. A price touched
    twice in the same bracket still earns one letter: TPO counts time *periods*,
    not trades.
    """
    prof: dict[float, str] = {}
    for i, b in enumerate(bars):
        letter = LETTERS[i] if i < len(LETTERS) else LETTERS[-1]
        for p in price_buckets(b["low"], b["high"], tick):
            prof[p] = prof.get(p, "") + letter
    return prof


def tpo_counts(profile: dict[float, str]) -> dict[float, int]:
    return {p: len(v) for p, v in profile.items()}


def poc(counts: dict[float, int]) -> float | None:
    """Point of control — most TPOs.

    Ties resolve to the price nearest the middle of the range, which is CQG's
    published rule and the only tie-break anyone states explicitly. Without it,
    the POC would depend on dict ordering.
    """
    if not counts:
        return None
    best = max(counts.values())
    tied = [p for p, c in counts.items() if c == best]
    if len(tied) == 1:
        return tied[0]
    mid = (min(counts) + max(counts)) / 2.0
    return min(tied, key=lambda p: (abs(p - mid), p))


def value_area(counts: dict[float, int], coverage: float = VALUE_AREA_COVERAGE,
               method: str = "pair") -> dict | None:
    """The band holding `coverage` of all TPOs, grown outward from the POC.

    Returns low, high, the POC it grew from, the fraction actually covered, and
    the method — because the method changes the answer and a value area quoted
    without it is not reproducible.

    Ties between the two sides go UP. Neither Dalton nor CQG states a rule for
    that case; the choice is ours and is recorded here rather than left implicit.
    """
    if method not in VALUE_AREA_METHODS:
        raise ValueError(f"method must be one of {VALUE_AREA_METHODS}")
    if not counts:
        return None
    prices = sorted(counts)
    total = sum(counts.values())
    target = total * coverage
    c = poc(counts)
    i = j = prices.index(c)                      # inclusive window [i, j]
    acc = counts[c]
    step = 2 if method == "pair" else 1

    while acc < target and (i > 0 or j < len(prices) - 1):
        up = [prices[k] for k in range(j + 1, min(j + 1 + step, len(prices)))]
        dn = [prices[k] for k in range(max(i - step, 0), i)]
        up_sum = sum(counts[p] for p in up)
        dn_sum = sum(counts[p] for p in dn)
        # An exhausted side must never win, even at 0 == 0.
        if up and (not dn or up_sum >= dn_sum):
            j += len(up)
            acc += up_sum
        else:
            i -= len(dn)
            acc += dn_sum
    return {"low": prices[i], "high": prices[j], "poc": c,
            "covered": acc / total if total else 0.0,
            "method": method, "coverage_target": coverage}


def single_prints(profile: dict[float, str]) -> list[float]:
    """Prices touched in exactly one bracket — where the auction moved too fast
    to build acceptance."""
    return sorted(p for p, v in profile.items() if len(v) == 1)


def tails(profile: dict[float, str], min_length: int = 2) -> dict:
    """Buying and selling tails: unbroken runs of single prints at the extremes.

    Dalton requires at least two TPOs for a tail to be significant, so a
    one-tick single print at the high is reported as a run of length 1 and
    flagged `significant: False` rather than silently dropped — the reader
    should see the near-miss.
    """
    if not profile:
        return {"buying": None, "selling": None}
    prices = sorted(profile)
    singles = set(single_prints(profile))

    def run(seq):
        out = []
        for p in seq:
            if p in singles:
                out.append(p)
            else:
                break
        return sorted(out)

    low_run = run(prices)                    # upward from the low  -> buying tail
    high_run = run(reversed(prices))         # downward from the high -> selling tail

    def pack(r):
        if not r:
            return None
        return {"low": r[0], "high": r[-1], "length": len(r),
                "significant": len(r) >= min_length}
    return {"buying": pack(low_run), "selling": pack(high_run)}


def poor_extremes(profile: dict[float, str], min_tpos: int = 2) -> dict:
    """A 'poor' high or low: the extreme price itself carries multiple TPOs.

    The auction stopped without excess — it ran out of time, not out of buyers —
    which is why poor extremes are read as unfinished business.
    """
    if not profile:
        return {"poor_high": False, "poor_low": False}
    prices = sorted(profile)
    return {"poor_high": len(profile[prices[-1]]) >= min_tpos,
            "poor_low": len(profile[prices[0]]) >= min_tpos,
            "high": prices[-1], "low": prices[0],
            "high_tpos": len(profile[prices[-1]]),
            "low_tpos": len(profile[prices[0]])}


def initial_balance(bars: list[dict], periods: int = 2) -> dict | None:
    """The range of the first two brackets — Dalton's definition exactly."""
    head = bars[:periods]
    if not head:
        return None
    return {"low": min(b["low"] for b in head), "high": max(b["high"] for b in head),
            "periods": len(head)}


def volume_at_price(bars: list[dict], tick: float) -> dict[float, float]:
    """Volume per price, APPROXIMATED by spreading each bar's volume evenly
    across the prices it spans.

    True volume-at-price needs the trade tape. This is the standard
    reconstruction from bars, and it is only as good as the bars are fine: on
    1-minute bars the error is small, on 30-minute bars it is not. Callers that
    report a VPOC from this must say where it came from — a VPOC quoted as if it
    were tape-derived is the kind of provenance slip that has cost us before.
    """
    vap: dict[float, float] = {}
    for b in bars:
        pts = price_buckets(b["low"], b["high"], tick)
        if not pts:
            continue
        share = (b.get("volume") or 0.0) / len(pts)
        for p in pts:
            vap[p] = vap.get(p, 0.0) + share
    return vap


def vpoc(vap: dict[float, float]) -> float | None:
    """Price with the most volume. Ties resolve toward the middle, as for POC."""
    if not vap:
        return None
    best = max(vap.values())
    tied = [p for p, v in vap.items() if v == best]
    if len(tied) == 1:
        return tied[0]
    mid = (min(vap) + max(vap)) / 2.0
    return min(tied, key=lambda p: (abs(p - mid), p))


def volume_without_time(vap: dict[float, float], counts: dict[float, int],
                        vol_pct: float = 0.80, tpo_pct: float = 0.50) -> list[float]:
    """Prices in the top `vol_pct` of volume but the bottom `tpo_pct` of TPOs.

    Heavy trade that never earned time — a level the market transacted at but did
    not accept. Both thresholds are free parameters and are in the signature so
    they can be swept rather than argued about.
    """
    if not vap or not counts:
        return []
    vs = sorted(vap.values())
    ts = sorted(counts.values())
    vcut = vs[min(int(vol_pct * len(vs)), len(vs) - 1)]
    tcut = ts[min(int(tpo_pct * len(ts)), len(ts) - 1)]
    return sorted(p for p in vap
                  if vap[p] >= vcut and counts.get(p, 0) <= tcut)


# A price holding less than this share of the profile's peak volume is a
# low-volume node. Steidlmayer's own framing is that volume marks acceptance;
# its absence marks a price the auction passed through without agreeing on.
LVN_FRAC = 0.25


def low_volume_nodes(vap: dict[float, float], frac: float = LVN_FRAC,
                     min_separation: int = 1) -> list[dict]:
    """Prices the auction moved through without building acceptance.

    From @TailThatWagsDog, 2025-10-01: *"If you're a fan of auction market
    profile … or Wyckoff and Volume-Spread-Analysis … you know that LOW volume
    points are often key levels … key decision points."*

    We had the opposite half only. VPOC and the value area find where volume
    PILED UP; this finds where it did not. The reading is different in kind: a
    high-volume node is where price is comfortable and tends to rotate, a
    low-volume node is where it is not and tends to travel — so an LVN is a
    place to expect speed, not support.

    A node qualifies when it is a local minimum, sits below `frac` of the
    profile's peak, and has genuine volume on BOTH sides. That last condition is
    what distinguishes an LVN from the thin tails at the edges of the profile,
    which are not decision points — they are just where the day ended.
    """
    if not vap or frac <= 0:
        return []
    prices = sorted(vap)
    if len(prices) < 3:
        return []
    peak = max(vap.values())
    if peak <= 0:
        return []
    cut = frac * peak

    out = []
    for i in range(min_separation, len(prices) - min_separation):
        p = prices[i]
        v = vap[p]
        if v > cut:
            continue
        lo = prices[max(0, i - min_separation):i]
        hi = prices[i + 1:i + 1 + min_separation]
        if not lo or not hi:
            continue
        # A local minimum, and flanked by real volume on both sides — otherwise
        # this is the edge of the profile rather than a gap inside it.
        if v > min(vap[q] for q in lo) or v > min(vap[q] for q in hi):
            continue
        left_peak = max(vap[q] for q in prices[:i]) if i else 0.0
        right_peak = max(vap[q] for q in prices[i + 1:])
        if left_peak <= cut or right_peak <= cut:
            continue
        out.append({"price": p, "volume": v,
                    "share_of_peak": round(v / peak, 4),
                    "left_peak": left_peak, "right_peak": right_peak,
                    "note": "expect speed here, not support — the auction passed "
                            "through without agreeing"})
    return sorted(out, key=lambda r: r["share_of_peak"])


def profile_gaps(vap: dict[float, float]) -> list[dict]:
    """Every INTERIOR local minimum with its depth, threshold-free.

    The near-miss discipline, applied to nodes. `low_volume_nodes` answers "what
    qualified"; this answers "and how close did the rest come", so a session that
    produced nothing can be distinguished from a threshold that was set too tight.

    Measured on 2026-08-07 the three interior dips came in at 37.8%, 39.2% and
    50.1% of peak against a 25% cut — nothing qualified, and the day genuinely
    had no gap rather than the setting being wrong. Without this the two cases
    look identical, and the temptation is to lower the cut until something
    appears, which is how a free parameter becomes a finding.
    """
    if not vap or len(vap) < 3:
        return []
    prices = sorted(vap)
    peak = max(vap.values()) or 1.0
    cut_free = []
    for i in range(1, len(prices) - 1):
        p_, v = prices[i], vap[prices[i]]
        if not (v < vap[prices[i - 1]] and v < vap[prices[i + 1]]):
            continue
        left = max(vap[q] for q in prices[:i])
        right = max(vap[q] for q in prices[i + 1:])
        cut_free.append({
            "price": p_, "volume": v, "share_of_peak": round(v / peak, 4),
            "left_peak_share": round(left / peak, 4),
            "right_peak_share": round(right / peak, 4),
            # A dip with nothing but tail on one side is where the day ended,
            # not a gap the auction crossed.
            "interior": left > 0.25 * peak and right > 0.25 * peak,
        })
    return sorted(cut_free, key=lambda r: r["share_of_peak"])
