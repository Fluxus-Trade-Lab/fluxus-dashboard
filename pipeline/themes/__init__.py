"""Theme layer: the tradeable-universe view of industries and themes.

The liquidity floor below defines what "tradeable" means for *theme tracking
only*.  It is not a filter on the universe or the screener -- those keep every
name Finviz returns.  A $90M company with $440k of daily volume is a perfectly
legitimate screener hit; it is just not something whose price should be
allowed to shape a theme's reading, because its prints are stale and a real
position in it could not be built in a day at the sizes this account uses.

Changing these two numbers changes what every theme means, so they live here
rather than inside whichever module happened to need them first.
"""

# Applied to theme and industry aggregation. NOT applied to universe.json.
#
# Raised from $300M to $1B on 2026-08-10. Measured through a real build on that
# session's universe, not estimated: 2,991 tradeable names to 2,379 (-20.5%),
# 126 industries to 118, 73 themes to 72.
#
# The eight industries that fall out are the small-cap-heavy ones -- Luxury
# Goods, Broadcasting, Mortgage Finance and similar -- which lose members below
# the five a group needs to be scored at all.
#
# One theme dies by definition rather than by liquidity: Microcaps. A floor of
# $1B removes the thing it is built to track. If it is ever wanted back it needs
# its own floor, not this one.
#
# ETF-backed themes are untouched. Their members are funds, which never appear
# in universe.json, so this filter has never applied to them -- a proxy theme
# holding one ETF reads exactly as before.
MIN_MARKET_CAP = 1e9
MIN_DOLLAR_VOLUME = 2e6

# The window `avg_volume` is measured over. Finviz never labels it and the
# code never said it either, while every standard liquidity definition found
# declares its window explicitly. Measured 2026-09-05 against raw (unadjusted)
# volume with the dates aligned to the universe's own bar_date: 58 of 58
# sampled names matched a 20-session mean to 0.0000 relative error, against
# 15.9% for 50 sessions and 18.1% for 63. Declared here so the next reader
# does not have to re-derive it. (First attempt at this measurement used
# split-adjusted volume and a window ending one session late, and reported a
# 1.93% median error -- the alignment is the whole measurement.)
AVG_VOLUME_WINDOW_SESSIONS = 20

# Security types the standard liquidity screens exclude. Same list the breadth
# new-high/new-low counts use (NYSE/Nasdaq/Arca publish theirs common-stock
# only). Finviz already keeps ETFs, closed-end funds, preferreds and warrants
# out of our universe; the SPAC/shell bucket is the one it does not, and it is
# labelled `industry == "Shell Companies"` -- 331 names on 2026-08-28, of which
# 58 were being counted as 52-week new highs.
#
# Added here 2026-09-05 because leaving it out was the SAME defect in a second
# place: on 2026-08-31 the new-high count was fixed by a type filter while
# `is_tradeable` went on betting that the vendor would not hand us funds.
EXCLUDED_INDUSTRIES = frozenset({"Shell Companies"})


def is_tradeable(row) -> bool:
    """True if a universe row clears the theme-tracking liquidity floor.

    THREE DECLARED DEVIATIONS from the standard (S&P's Float-Adjusted
    Liquidity Ratio, `methodology-sp-us-indices.pdf`: annual dollar value
    traded / float-adjusted market cap >= 0.1):

    1. ABSOLUTE, NOT A RATIO. FALR is a turnover measure and would reject
       names like BRK -- low turnover, trivially tradeable. We are asking
       something else: can an account of our size build a position in a day.
       Absolute dollar floors have vendor precedent (Trade-Ideas, Deepvue).
       The cost is that $1B and $2M drift out of calibration as the market
       moves, the same weakness the raw new-high counts had before Record
       High Percent replaced them with a ratio.
    2. THE TWO CONSTANTS WERE NEVER ALIGNED WITH EACH OTHER. $1B market cap is
       stricter than S&P SmallCap 600's floor; $2M dollar volume is roughly
       1.7x looser than the matching liquidity requirement. They were each
       picked on their own.
    3. THE WINDOW WAS UNDECLARED until 2026-09-05 (it is 20 sessions; see
       AVG_VOLUME_WINDOW_SESSIONS). Every standard definition states its own.

    `falr_252` ships beside this as a REPORTED value so the standard reading
    is visible without gating on it.
    """
    industry = row.get("industry")
    if industry in EXCLUDED_INDUSTRIES:
        return False
    cap = row.get("market_cap") or 0
    dollar_vol = (row.get("avg_volume") or 0) * (row.get("close") or 0)
    return cap >= MIN_MARKET_CAP and dollar_vol >= MIN_DOLLAR_VOLUME


def falr(row, sessions_per_year: int = 252) -> float | None:
    """S&P's Float-Adjusted Liquidity Ratio, REPORTED not enforced.

        annual dollar value traded / float-adjusted market cap

    S&P requires >= 0.1 for a new constituent. We approximate the numerator
    from `avg_volume * close * 252` -- their own definition is the average
    closing price times historical volume over the trailing 365 calendar days,
    and our average volume covers 20 sessions, so this extrapolates a month to
    a year and will be wrong for a name whose volume has changed. The
    denominator is full market cap, not float-adjusted, because we do not
    carry a float factor.

    Both approximations are why this is a reading and not a gate. It exists so
    the standard measure is on the row next to our own, which is the thing
    that was missing when the two could not be compared at all.
    """
    cap = row.get("market_cap") or 0
    dv = (row.get("avg_volume") or 0) * (row.get("close") or 0)
    if not cap or cap <= 0 or dv <= 0:
        return None
    return round(dv * sessions_per_year / cap, 4)
