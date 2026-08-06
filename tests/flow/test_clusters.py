import pandas as pd
from pipeline.flow.clusters import label_clusters


def _mk_agg(bots, solds):
    """bots and solds are per-2min-bar premium; bars start at 12:00 ET, 2min apart."""
    n = len(bots)
    times = pd.date_range("2026-07-15 12:00", periods=n, freq="2min", tz="America/New_York")
    return pd.DataFrame({
        "time_bin": times,
        "premium_total": [b + s for b, s in zip(bots, solds)],
        "bot_premium": bots,
        "sold_premium": solds,
        "net_premium": [b - s for b, s in zip(bots, solds)],
        "n_prints": [1] * n,
        "n_prints_over_threshold": [0] * n,
        "top_prints": [[]] * n,
    })


def test_strong_bot_run_labeled_bot():
    # 15 bars, 12 BOT-heavy then 3 mixed → the BOT run should be labeled
    agg = _mk_agg(bots=[1e6] * 12 + [1e5, 1e5, 1e5],
                  solds=[1e5] * 12 + [1e5, 1e5, 1e5])
    out = label_clusters(agg, window_min=10)
    # bars in the middle of the BOT run must be labeled BOT
    assert out.iloc[5]["cluster_label"] == "BOT"
    assert out.iloc[8]["cluster_label"] == "BOT"


def test_strong_sold_run_labeled_sold():
    agg = _mk_agg(bots=[1e5] * 12 + [1e5, 1e5, 1e5],
                  solds=[1e6] * 12 + [1e5, 1e5, 1e5])
    out = label_clusters(agg, window_min=10)
    assert out.iloc[5]["cluster_label"] == "SOLD"
    assert out.iloc[8]["cluster_label"] == "SOLD"


def test_balanced_flow_unlabeled():
    agg = _mk_agg(bots=[5e5] * 20, solds=[5e5] * 20)
    out = label_clusters(agg, window_min=10)
    for lbl in out["cluster_label"]:
        assert lbl == ""


def test_dead_bar_not_labeled_even_if_one_sided():
    # 20 quiet BOT-only bars ($1 each) alongside no other activity — total premium
    # is tiny relative to a busy session; without a "big enough" bars nearby, dead
    # tape should NOT get a cluster label.
    # We simulate this by making bar 0 huge (setting the session scale), then 20
    # micro bars that are 100% BOT but total ~0.
    agg = _mk_agg(bots=[1e9] + [1.0] * 20,
                  solds=[1e9] + [0.0] * 20)
    out = label_clusters(agg, window_min=10)
    # micro BOT bars should not get a label — session-relative gate prunes them
    assert out.iloc[10]["cluster_label"] == ""
