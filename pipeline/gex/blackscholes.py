"""Black-Scholes gamma + implied-vol solver (no dividends, rate r default 0).

Why this exists: IBKR's model greeks are dark pre-open (only the prior settle
`close` price survives). To compute dealer gamma at 8am ET we back out IV from the
settle price and compute gamma ourselves — the SpotGamma approach — instead of
depending on a live greek feed.
"""
import math

_SQRT2PI = math.sqrt(2.0 * math.pi)


def _norm_pdf(x: float) -> float:
    return math.exp(-0.5 * x * x) / _SQRT2PI


def _norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _d1(S, K, T, sigma, r):
    return (math.log(S / K) + (r + 0.5 * sigma * sigma) * T) / (sigma * math.sqrt(T))


def bs_price(S, K, T, sigma, right, r=0.0):
    """European option price. `right` is 'C' or 'P'. Returns None if inputs invalid."""
    if not (S > 0 and K > 0 and T > 0 and sigma > 0):
        return None
    d1 = _d1(S, K, T, sigma, r)
    d2 = d1 - sigma * math.sqrt(T)
    disc = math.exp(-r * T)
    if right == "C":
        return S * _norm_cdf(d1) - K * disc * _norm_cdf(d2)
    return K * disc * _norm_cdf(-d2) - S * _norm_cdf(-d1)


def bs_gamma(S, K, T, sigma, r=0.0):
    """d²price/dS². Same for calls and puts. Returns None if inputs invalid."""
    if not (S > 0 and K > 0 and T > 0 and sigma > 0):
        return None
    d1 = _d1(S, K, T, sigma, r)
    return _norm_pdf(d1) / (S * sigma * math.sqrt(T))


def bs_delta(S, K, T, sigma, right, r=0.0):
    """dprice/dS. Call in (0,1), put in (-1,0). None if inputs invalid."""
    if not (S > 0 and K > 0 and T > 0 and sigma > 0):
        return None
    nd1 = _norm_cdf(_d1(S, K, T, sigma, r))
    return nd1 if right == "C" else nd1 - 1.0


def bs_vega(S, K, T, sigma, r=0.0):
    """dprice/dsigma per ONE VOL POINT (1%), matching how IBKR reports vega.

    Textbook vega is per 1.00 of sigma (i.e. 100 vol points), so it is divided
    by 100 here — mixing the two conventions silently misstates crush P&L by
    two orders of magnitude. Same for calls and puts.
    """
    if not (S > 0 and K > 0 and T > 0 and sigma > 0):
        return None
    return S * _norm_pdf(_d1(S, K, T, sigma, r)) * math.sqrt(T) / 100.0


def implied_vol(price, S, K, T, right, r=0.0, lo=0.005, hi=5.0, tol=1e-4, iters=64):
    """Solve BS implied vol from an option price via bisection.

    Returns None when the price is below intrinsic, outside the [lo,hi] vol bracket,
    or inputs are invalid — callers must treat None as 'can't enrich this strike'.
    """
    if price is None or not (price > 0 and S > 0 and K > 0 and T > 0):
        return None
    intrinsic = max(0.0, (S - K) if right == "C" else (K - S))
    if price < intrinsic - 1e-6:
        return None

    def f(sig):
        p = bs_price(S, K, T, sig, right, r)
        return None if p is None else p - price

    flo, fhi = f(lo), f(hi)
    if flo is None or fhi is None or flo * fhi > 0:
        return None
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        fm = f(mid)
        if fm is None:
            return None
        if abs(fm) < tol:
            return mid
        if flo * fm <= 0:
            hi, fhi = mid, fm
        else:
            lo, flo = mid, fm
    return 0.5 * (lo + hi)
