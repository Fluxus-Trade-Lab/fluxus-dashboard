"""Which RS reading each panel's RS leg uses (RS unify, option B).

Andy 2026-10-04: 「选B，而且务必要做forward testing，至少5天。」
B = switch three legs to `rs_rating`, keep Monthly Leader 97 on `rs_1m`
(its name is "one-month leader"; the backtest found the switch replaced
~73% of its list daily and lowered 20-day excess from +3.77% to +2.47%).
Backtest: data/research/rs_unify/switch_impact.json (74028cef9).

One-key revert: set UNIFIED = False. The pipeline then computes every leg
exactly as before 2026-10-05. The 4% Bullish preset lives in the frontend
(frontend/public/data/screener-presets.json, filter key `rsIbd`); reverting it
means putting `rs21d` back there -- see PRESET_REVERT below.

Forward test: every run writes both readings of each switched leg to
data/history/rs_switch_shadow.csv (pipeline/tools/rs_switch_shadow.py), so the
old and new lists can be compared on real sessions for >= FORWARD_MIN_SESSIONS.
"""

UNIFIED = True
SWITCH_FIRST_SESSION = "2026-10-05"
FORWARD_MIN_SESSIONS = 5

# leg -> (old field, new field). Threshold numbers are unchanged: the
# backtest's size-matched thresholds were 79.75 / 59.25, i.e. the same lists.
LEGS = {
    "liquid_leader": ("rs_3m", "rs_rating"),   # also feeds every liquid_leader-based panel
    "vcs": ("rs_3m", "rs_rating"),
    "industry_rank": ("rs_3m", "rs_rating"),   # median of tradeable members
    "4pct_bullish": ("rs_21d", "rs_rating"),   # frontend preset; logged here for the shadow only
}
NOT_SWITCHED = {"monthly_leader_97": "rs_1m"}

PRESET_REVERT = {"4% Bullish": {"from": "rsIbd", "to": "rs21d", "min": 60, "max": 99}}


def field(leg: str, unified: bool = None) -> str:
    """The column the leg reads now (or under `unified`, for the shadow)."""
    old, new = LEGS[leg]
    use = UNIFIED if unified is None else unified
    return new if use else old
