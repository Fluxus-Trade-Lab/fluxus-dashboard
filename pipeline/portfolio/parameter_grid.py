"""Define the parameter sweep for the backtest optimizer."""
from __future__ import annotations

from itertools import product

from pipeline.portfolio.simulator import SimParams

TRIM1_TRIGGERS = (2.0, 2.5, 3.0, 3.5, 4.0)
TRIM1_SIZES = (0.30, 0.40, 0.50, 0.60, 0.70)
TRIM2_SIGNALS = ('d_close_lt_10ema', 'wk_close_lt_10ema', 'd_close_lt_13ema', 'd_close_lt_5d_low')
TRIM2_SIZES = (0.50, 0.70, 1.00)
FULL_STOPS = ('d_close_lt_20ema', 'wk_close_lt_20ema', 'd_close_lt_30ema', 'trailing_2atr')
RATCHETS = ('none', '5R_to_3R', '8R_to_5R')
SELL_STRENGTH = ('none', 'trim_30_on_15pct', 'trim_50_on_20pct')


def all_params() -> list[SimParams]:
    """Return the full Cartesian product as SimParams objects."""
    out = []
    for t1t, t1s, t2sig, t2sz, fs, ratch, ss in product(
        TRIM1_TRIGGERS, TRIM1_SIZES, TRIM2_SIGNALS, TRIM2_SIZES,
        FULL_STOPS, RATCHETS, SELL_STRENGTH,
    ):
        out.append(SimParams(
            trim1_trigger_R=t1t, trim1_size_pct=t1s,
            trim2_signal=t2sig, trim2_size_pct=t2sz,
            full_stop_signal=fs,
            gain_ratchet=ratch, sell_strength=ss,
        ))
    return out


def params_to_label(p: SimParams) -> str:
    """Human-readable label for a parameter set."""
    sig_map = {
        'd_close_lt_10ema': 'd10EMA',
        'wk_close_lt_10ema': 'wk10EMA',
        'd_close_lt_13ema': 'd13EMA',
        'd_close_lt_5d_low': 'd5dLow',
    }
    stop_map = {
        'd_close_lt_20ema': 'd20EMA',
        'wk_close_lt_20ema': 'wk20EMA',
        'd_close_lt_30ema': 'd30EMA',
        'trailing_2atr': 'trail2ATR',
    }
    ratch_map = {'none': '∅', '5R_to_3R': 'r5→3', '8R_to_5R': 'r8→5'}
    ss_map = {'none': '∅', 'trim_30_on_15pct': 's30@15%', 'trim_50_on_20pct': 's50@20%'}
    return (f"T1={p.trim1_trigger_R}R/{int(p.trim1_size_pct*100)}% · "
            f"T2={sig_map[p.trim2_signal]}/{int(p.trim2_size_pct*100)}% · "
            f"Stop={stop_map[p.full_stop_signal]} · "
            f"Ratch={ratch_map[p.gain_ratchet]} · "
            f"Strength={ss_map[p.sell_strength]}")
