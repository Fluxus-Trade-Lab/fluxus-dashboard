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


def bs_charm(S, K, T, sigma, right="C", r=0.0, q=0.0):
    """Delta decay PER CALENDAR DAY: how far delta drifts if nothing else moves.

    Sign convention is the trap here. This returns d(delta)/dt where t is
    calendar time moving FORWARD, so it is the negative of d(delta)/dT (T =
    time to expiry, which shrinks as t advances). Consequences worth stating:
      * ITM -> charm > 0 (delta climbs toward ±1 as expiry approaches)
      * OTM -> charm < 0 (delta bleeds toward 0)

    Calls and puts are identical only when q == 0; a dividend yield splits them
    because put delta is then -e^(-qT)N(-d1), not call delta minus a constant.

    Why it matters: gamma forces dealers to re-hedge when SPOT moves; charm
    forces them to re-hedge when TIME passes. Two independent drivers, which is
    why their peaks coinciding on a strike is a stronger pin read than either
    alone. Returns None if inputs invalid.
    """
    if not (S > 0 and K > 0 and T > 0 and sigma > 0):
        return None
    srt = sigma * math.sqrt(T)
    d1 = (math.log(S / K) + (r - q + 0.5 * sigma * sigma) * T) / srt
    dd1_dT = (-math.log(S / K) / (2 * sigma * T ** 1.5)
              + (r - q + 0.5 * sigma * sigma) / (2 * srt))
    disc = math.exp(-q * T)
    drift = -disc * _norm_pdf(d1) * dd1_dT
    if q == 0.0:
        return drift / 365.0
    carry = (q * disc * _norm_cdf(d1) if right == "C"
             else -q * disc * _norm_cdf(-d1))
    return (drift + carry) / 365.0


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


def bs_vanna(S, K, T, sigma, r=0.0, q=0.0):
    """Vanna = d(delta)/d(sigma) = d(vega)/d(spot), PER ONE VOL POINT.

    The third dealer-hedging force, and the one that explains the days neither
    of the others can. Gamma fires when spot moves. Charm fires when time
    passes. **Vanna fires when implied volatility moves and spot does not** —
    a vol-crush morning, an event repricing, a Friday afternoon bleed.

    Sign, pinned by a test because I got it backwards on the first pass. For an
    out-of-the-money call K > S, so log(S/K) < 0 and **d2 < 0**, making vanna
    POSITIVE: an OTM option gains delta as vol rises, because rising vol makes
    finishing in the money more likely. An ITM call is the mirror — its delta
    falls back toward 0.5 as vol rises, so vanna is negative.

    The dealer reading follows. Dealers are typically SHORT the OTM calls
    customers buy, so they are short positive vanna: **as IV rises their delta
    goes more negative and they must buy**. That is the squeeze that starts with
    the vol bid rather than with the tape, and neither gamma nor charm sees it.

    Units follow ``bs_vega``: divided by 100, so the number is the delta change
    for a **one-point** move in IV (18% -> 19%), not for sigma going 0.18 -> 1.18.
    Reading it per unit sigma would overstate every hedging estimate 100x, which
    is the error this project already made once with vega.
    """
    if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
        return 0.0
    srt = sigma * math.sqrt(T)
    d1 = (math.log(S / K) + (r - q + 0.5 * sigma * sigma) * T) / srt
    d2 = d1 - srt
    return -math.exp(-q * T) * _norm_pdf(d1) * d2 / sigma / 100.0


def bs_vomma(S, K, T, sigma, r=0.0, q=0.0):
    """Vomma = d(vega)/d(sigma), per one vol point. Vega's own convexity.

    Reported alongside vanna because a book with large vomma re-prices its vega
    non-linearly: the same one-point IV move costs a different amount depending
    on where IV already is.

    The /100 below is NOT redundant with the one inside ``bs_vega``. That one
    makes vega per vol point; this one makes the DIFFERENTIATION per vol point.
    Omitting it returns a per-sigma number that is 100x too large — the exact
    error this module's vega docstring warns about, which I committed here on
    the first pass and a numerical test caught.
    """
    if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
        return 0.0
    srt = sigma * math.sqrt(T)
    d1 = (math.log(S / K) + (r - q + 0.5 * sigma * sigma) * T) / srt
    d2 = d1 - srt
    return bs_vega(S, K, T, sigma, r) * d1 * d2 / sigma / 100.0
