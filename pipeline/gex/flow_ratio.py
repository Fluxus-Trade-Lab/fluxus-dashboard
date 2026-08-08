"""Today's flow against standing positioning, per strike.

From @TailThatWagsDog, 2026-03-24: he screens "top 100 SPX assets preloaded with
a high **GEX-Volume ratio**." Not two columns side by side — a ratio, used as a
filter. We built the volume-weighted series and left it as a second column,
which is the part that carries no signal.

The quantity: open interest is what is *positioned*, today's volume is what is
*being done*. A strike where today's flow is far out of proportion to the
standing book is a strike where something new is happening, and that is
invisible in either series alone.

Why a share ratio and not a plain one. Both series are signed and cross zero, so
`gex_vol / gex_oi` is nonsense at any strike where the denominator is small or
the signs differ — it explodes, or it reports a negative "ratio" that means
nothing. Each strike's **share of its own series' total absolute magnitude** is
sign-safe, scale-free, and comparable across days when the whole book grows or
shrinks. Sign agreement is then reported separately, because "more flow than
positioning" and "flow in the opposite direction to positioning" are different
findings and collapsing them loses the interesting one.
"""
from __future__ import annotations

# Below this share of its series, a strike is rounding error and its ratio is an
# artefact of a tiny denominator rather than a fact about flow.
MIN_SHARE = 0.005
# A strike carrying this many times its positioning share is doing something.
HOT = 2.0


def flow_ratio(gex_oi: dict[float, float], gex_vol: dict[float, float],
               min_share: float = MIN_SHARE) -> list[dict]:
    """Per strike: share of today's flow vs share of standing positioning.

    Strikes below `min_share` in BOTH series are dropped — not because they are
    uninteresting but because their ratio is undefined in practice, and a table
    that reports 40x on a rounding error trains the reader to ignore the column.
    """
    shared = sorted(set(gex_oi) & set(gex_vol))
    if not shared:
        return []
    tot_oi = sum(abs(gex_oi[k]) for k in shared)
    tot_vol = sum(abs(gex_vol[k]) for k in shared)
    if tot_oi <= 0 or tot_vol <= 0:
        return []

    out = []
    for k in shared:
        s_oi = abs(gex_oi[k]) / tot_oi
        s_vol = abs(gex_vol[k]) / tot_vol
        if s_oi < min_share and s_vol < min_share:
            continue
        ratio = (s_vol / s_oi) if s_oi >= min_share else None
        out.append({
            "strike": k,
            "gex_oi": gex_oi[k], "gex_volume": gex_vol[k],
            "share_oi": round(s_oi, 5), "share_volume": round(s_vol, 5),
            "ratio": round(ratio, 3) if ratio is not None else None,
            "same_sign": gex_oi[k] * gex_vol[k] > 0,
            "note": (None if ratio is not None else
                     "positioning share below the floor — ratio would be an artefact"),
        })
    return out


def hot_strikes(rows: list[dict], hot: float = HOT) -> list[dict]:
    """Strikes where today's flow is `hot`x its positioning share, biggest first.

    Split by sign agreement, because the two cases read differently:
      same sign  — today is ADDING to what is already there
      opposed    — today is trading AGAINST the standing book
    """
    live = [r for r in rows if r["ratio"] is not None and r["ratio"] >= hot]
    return sorted(live, key=lambda r: -r["ratio"])


def summary(rows: list[dict], hot: float = HOT) -> dict:
    h = hot_strikes(rows, hot)
    return {
        "n_strikes": len(rows),
        "n_hot": len(h),
        "hot_threshold": hot,
        "adding": [r["strike"] for r in h if r["same_sign"]],
        "opposing": [r["strike"] for r in h if not r["same_sign"]],
        "hottest": h[0] if h else None,
    }
