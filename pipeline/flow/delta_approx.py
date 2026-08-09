"""Moneyness-based delta approximation for 0DTE SPX options.

No Greeks from IBKR needed — uses a linear ramp centered on spot.
Accurate enough for hedging-flow directionality on intraday scales.
"""


def estimate_delta(spot: float, strike: float, right: str,
                   bandwidth: float = 30.0) -> float:
    """Estimate option delta from moneyness.

    Uses a linear ramp: ATM = 0.50, ±bandwidth from spot = 0.05/0.95.

    Parameters
    ----------
    spot : current SPX price
    strike : option strike
    right : "C" or "P"
    bandwidth : half-width of the linear ramp in index points
                (default 30 — roughly 1 straddle for 0DTE SPX)

    Returns
    -------
    float : estimated delta
        Calls: +0.05 to +0.95
        Puts:  -0.95 to -0.05
    """
    if bandwidth <= 0:
        bandwidth = 30.0
    moneyness = (spot - strike) / bandwidth
    call_delta = max(0.05, min(0.95, 0.5 + 0.5 * moneyness))
    if right == "C":
        return call_delta
    return call_delta - 1.0
