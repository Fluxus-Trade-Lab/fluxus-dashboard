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
MIN_MARKET_CAP = 3e8
MIN_DOLLAR_VOLUME = 2e6


def is_tradeable(row) -> bool:
    """True if a universe row clears the theme-tracking liquidity floor."""
    cap = row.get("market_cap") or 0
    dollar_vol = (row.get("avg_volume") or 0) * (row.get("close") or 0)
    return cap >= MIN_MARKET_CAP and dollar_vol >= MIN_DOLLAR_VOLUME
