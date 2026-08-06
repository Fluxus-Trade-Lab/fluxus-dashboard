"""Join options TRADES with the contemporaneous NBBO for aggressor classification.

Each trade gets the most-recent BID_ASK tick within `max_lookback_ms` via
pandas.merge_asof (backward, tolerance). No match → bid/ask are NaN and the
downstream classifier returns "UNKNOWN".
"""
import pandas as pd


def enrich_trades(trades: pd.DataFrame,
                  quotes: pd.DataFrame,
                  max_lookback_ms: int = 5000) -> pd.DataFrame:
    if trades.empty:
        out = trades.copy()
        for c in ("bid", "ask", "prev_price"):
            out[c] = pd.Series(dtype="float64")
        return out
    t = trades.sort_values("time").reset_index(drop=True)
    t["time"] = t["time"].dt.as_unit("ns")
    t_tz = t["time"].dt.tz
    if not quotes.empty:
        q = quotes.sort_values("time").reset_index(drop=True)
        if q["time"].dt.tz != t_tz and t_tz is not None:
            q["time"] = q["time"].dt.tz_convert(t_tz)
        q["time"] = q["time"].dt.as_unit("ns")
    else:
        tz_str = str(t_tz) if t_tz else "UTC"
        q = pd.DataFrame({"time": pd.Series(dtype=f"datetime64[ns, {tz_str}]"),
                          "bid": pd.Series(dtype="float64"),
                          "ask": pd.Series(dtype="float64")})
    merged = pd.merge_asof(
        t, q, on="time", direction="backward",
        tolerance=pd.Timedelta(milliseconds=max_lookback_ms),
    )
    merged["prev_price"] = merged["price"].shift(1)
    return merged
