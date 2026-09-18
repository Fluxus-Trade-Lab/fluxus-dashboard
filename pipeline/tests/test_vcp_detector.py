"""VCP: Minervini's two constituent conditions are FILTERS, not flags.

Andy 2026-09-18: 「全部按原文」. Audit 09-18 #43: `volume_declining` and
`ratios_healthy` were computed and shipped but never gated -- 27 names on
vcp.json that day, 4 met both. Minervini (Trade Like a Stock Market Wizard,
ch. 10): the contractions tighten, each "contained to about half (plus or
minus a reasonable amount) of the previous", typically two to four and "as
many as five or six", and volume contracts with them.
"""
import numpy as np
import pandas as pd

from pipeline.screeners.vcp_detector import layer2_detect_vcp


def _bars(legs, vols):
    """Piecewise-linear closes through `legs` (price anchors), `vols[i]` the
    volume on leg i. High/Low = close so swings sit exactly on the anchors."""
    closes, volume = [], []
    for i in range(len(legs) - 1):
        seg = np.linspace(legs[i], legs[i + 1], 12, endpoint=False)
        closes.extend(seg)
        volume.extend([vols[i]] * len(seg))
    closes.append(legs[-1])
    volume.append(vols[-1])
    idx = pd.bdate_range("2026-03-02", periods=len(closes))
    c = pd.Series(closes, index=idx, dtype=float)
    return pd.DataFrame({"Open": c, "High": c, "Low": c, "Close": c,
                         "Volume": pd.Series(volume, index=idx, dtype=float)})


# three contractions 20% -> 10% -> 5%, ending just under the last high
LEGS = [80, 100, 80, 100, 90, 100, 95, 99]


def test_positive_halving_contractions_on_falling_volume():
    h = _bars(LEGS, [9e5, 9e5, 7e5, 7e5, 5e5, 5e5, 3e5, 3e5])
    r = layer2_detect_vcp(h, "VCPX")
    assert r is not None
    assert r["volume_declining"] is True and r["ratios_healthy"] is True


def test_negative_volume_not_contracting_is_not_a_vcp():
    # same price path, volume RISING into each tighter contraction
    h = _bars(LEGS, [3e5, 3e5, 5e5, 5e5, 7e5, 7e5, 9e5, 9e5])
    assert layer2_detect_vcp(h, "VOLUP") is None


def test_negative_contraction_not_near_half_is_not_a_vcp():
    # shallower each time (monotone), but 20% -> 19% -> 18%: not "about half"
    legs = [80, 100, 81, 100, 82, 100, 95, 99]
    h = _bars(legs, [9e5, 9e5, 7e5, 7e5, 5e5, 5e5, 3e5, 3e5])
    assert layer2_detect_vcp(h, "FLAT") is None


def test_negative_more_than_six_contractions_is_not_a_vcp():
    # seven contractions: Minervini's range tops out at "five or six"
    legs = [60, 100, 60, 100, 70, 100, 80, 100, 85, 100, 90, 100, 95, 100, 97.5, 100, 98.75, 99.5]
    vols = list(np.linspace(1e6, 2e5, len(legs)))
    h = _bars(legs, vols)
    assert layer2_detect_vcp(h, "SEVEN") is None
