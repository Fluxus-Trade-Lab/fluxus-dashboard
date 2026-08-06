"""Rolling one-sidedness labels for 2-min aggregate bars.

A bar earns a "BOT" or "SOLD" cluster_label when a centered window of
`window_min` around it shows aggressor-classified premium concentrated on
one side (share > `dominance`) AND the window's total classified premium
is non-trivial relative to the busiest window in the session — so dead
tape can't get labeled.

These are the axis labels on the reference's flow panels: marking sustained
regimes, not per-print aggressor.
"""
import pandas as pd

MIN_SESSION_SCALE_FRAC = 0.05  # window must have ≥5% of the session's peak classified premium


def label_clusters(agg: pd.DataFrame,
                   window_min: int = 10,
                   dominance: float = 0.55) -> pd.DataFrame:
    out = agg.copy()
    if len(out) == 0:
        out["cluster_label"] = pd.Series(dtype="object")
        return out

    # Centered rolling window in bars: window_min minutes / 2 minutes per bar
    win_bars = max(1, window_min // 2)
    bot = out["bot_premium"].rolling(win_bars, center=True, min_periods=1).sum()
    sold = out["sold_premium"].rolling(win_bars, center=True, min_periods=1).sum()
    classified = bot + sold
    session_peak = float(classified.max()) if classified.max() > 0 else 0.0
    scale_floor = MIN_SESSION_SCALE_FRAC * session_peak

    labels = []
    for b, s, tot in zip(bot, sold, classified):
        if tot < scale_floor or tot == 0:
            labels.append("")
            continue
        bot_share = b / tot
        if bot_share >= dominance:
            labels.append("BOT")
        elif (1 - bot_share) >= dominance:
            labels.append("SOLD")
        else:
            labels.append("")
    out["cluster_label"] = labels
    return out
