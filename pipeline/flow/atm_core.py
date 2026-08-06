"""Budget-first ATM-core strike selection for the 0DTE options core.

Expand from the strike nearest to spot outward, alternating up/down, stopping
when either (a) the contract budget is spent (each strike = call + put) or
(b) the next strike would fall outside +/- max_sigma * daily_sigma_pct of spot.
This gives a VIX-adaptive core: low vol → budget binds; high vol → sigma binds.
"""


def select_core(spot: float,
                chain_strikes: list[float],
                budget_contracts: int = 60,
                max_sigma: float = 1.0,
                daily_sigma_pct: float = 0.01) -> list[float]:
    if not chain_strikes:
        return []
    strikes_sorted = sorted(chain_strikes)
    # ATM = strike closest to spot
    atm = min(strikes_sorted, key=lambda k: abs(k - spot))
    atm_idx = strikes_sorted.index(atm)

    max_strikes = budget_contracts // 2
    hi_bound = spot * (1 + max_sigma * daily_sigma_pct)
    lo_bound = spot * (1 - max_sigma * daily_sigma_pct)

    picked = {atm}
    up_i, dn_i = atm_idx + 1, atm_idx - 1
    while len(picked) < max_strikes and (up_i < len(strikes_sorted) or dn_i >= 0):
        # go up if the next up strike is inside the sigma bound
        if up_i < len(strikes_sorted) and strikes_sorted[up_i] <= hi_bound:
            picked.add(strikes_sorted[up_i])
            up_i += 1
            if len(picked) >= max_strikes:
                break
        else:
            up_i = len(strikes_sorted)  # disable further up-expansion
        # then down
        if dn_i >= 0 and strikes_sorted[dn_i] >= lo_bound:
            picked.add(strikes_sorted[dn_i])
            dn_i -= 1
        else:
            dn_i = -1  # disable further down-expansion
    return sorted(picked)
