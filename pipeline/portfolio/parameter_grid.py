"""Define the parameter sweep for the backtest optimizer (v2)."""
from __future__ import annotations

from itertools import product

from pipeline.portfolio.simulator import SimParams

TRIM1_TRIGGERS = (2.0, 2.5, 3.0, 3.5, 4.0)
TRIM1_SIZES = (0.30, 0.40, 0.50, 0.60, 0.70)
# T2 trigger can be a signal OR an R-target
TRIM2_TRIGGERS = (
    'd_close_lt_10ema',
    'wk_close_lt_10ema',
    'd_close_lt_5d_low',
    'r_5',
    'r_6',
    'r_8',
)
TRIM2_SIZES = (0.30, 0.50, 0.70)
# T3 is always R-target (or none)
TRIM3_TRIGGERS = ('none', 'r_8', 'r_10', 'r_12')
TRIM3_SIZES = (0.50, 1.00)
FULL_STOPS = ('d_close_lt_20ema', 'wk_close_lt_20ema', 'd_close_lt_30ema', 'trailing_2atr')
RATCHETS = ('none', '5R_to_3R', '8R_to_5R')


def all_params() -> list[SimParams]:
    """Return the full Cartesian product as SimParams objects.

    Skips redundant combinations (e.g., T3 = none with any T3 size > 50%).
    """
    out = []
    for t1t, t1s, t2t, t2sz, t3t, t3sz, fs, ratch in product(
        TRIM1_TRIGGERS, TRIM1_SIZES, TRIM2_TRIGGERS, TRIM2_SIZES,
        TRIM3_TRIGGERS, TRIM3_SIZES, FULL_STOPS, RATCHETS,
    ):
        # When T3 is 'none', T3 size doesn't matter — only emit one variant
        if t3t == 'none' and t3sz != TRIM3_SIZES[0]:
            continue
        out.append(SimParams(
            trim1_trigger_R=t1t, trim1_size_pct=t1s,
            trim2_trigger=t2t, trim2_size_pct=t2sz,
            trim3_trigger=t3t, trim3_size_pct=t3sz,
            full_stop_signal=fs,
            gain_ratchet=ratch,
        ))
    return out


def params_to_label(p: SimParams) -> str:
    """Human-readable label for a parameter set."""
    t2_map = {
        'd_close_lt_10ema': 'd10EMA',
        'wk_close_lt_10ema': 'wk10EMA',
        'd_close_lt_5d_low': 'd5dLow',
        'r_5': '+5R',
        'r_6': '+6R',
        'r_8': '+8R',
    }
    t3_map = {'none': '—', 'r_8': '+8R', 'r_10': '+10R', 'r_12': '+12R'}
    stop_map = {
        'd_close_lt_20ema': 'd20EMA',
        'wk_close_lt_20ema': 'wk20EMA',
        'd_close_lt_30ema': 'd30EMA',
        'trailing_2atr': 'trail2ATR',
    }
    ratch_map = {'none': '∅', '5R_to_3R': 'r5→3', '8R_to_5R': 'r8→5'}
    t3_part = (
        f"T3=—"
        if p.trim3_trigger == 'none'
        else f"T3={t3_map[p.trim3_trigger]}/{int(p.trim3_size_pct*100)}%"
    )
    return (f"T1={p.trim1_trigger_R}R/{int(p.trim1_size_pct*100)}% · "
            f"T2={t2_map[p.trim2_trigger]}/{int(p.trim2_size_pct*100)}% · "
            f"{t3_part} · "
            f"Stop={stop_map[p.full_stop_signal]} · "
            f"Ratch={ratch_map[p.gain_ratchet]}")
