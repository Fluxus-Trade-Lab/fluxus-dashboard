"""Lee–Ready quote-rule aggressor classification for options prints.

References:
- Lee, C.M.C. and Ready, M.J. (1991), Inferring Trade Direction from Intraday Data.
- Ellis, K., Michaely, R., and O'Hara, M. (2000) refinements (mid → tick rule).

Called for every options TRADE print with the contemporaneous NBBO on the same
contract. Returns "BOT" | "SOLD" | "UNKNOWN".
"""


def classify(price, bid, ask, prev_price=None):
    if bid is None or ask is None:
        return "UNKNOWN"
    if ask <= bid:                     # crossed or locked — refuse to guess
        return "UNKNOWN"
    if price >= ask:
        return "BOT"
    if price <= bid:
        return "SOLD"
    mid = (bid + ask) / 2.0
    if price > mid:
        return "BOT"
    if price < mid:
        return "SOLD"
    # exactly at mid — fall back to tick rule
    if prev_price is None:
        return "UNKNOWN"
    if price > prev_price:
        return "BOT"
    if price < prev_price:
        return "SOLD"
    return "UNKNOWN"
