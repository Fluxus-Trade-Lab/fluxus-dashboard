from pipeline.flow.atm_core import select_core


def test_budget_binds_when_sigma_wide():
    # spot 7550, 5-pt strikes 7400..7700, budget 62 (31 strikes) — expect 31
    # strikes centered on 7550 = 7475..7625 (both inclusive, 15 above + ATM + 15 below)
    strikes = [7400 + 5 * i for i in range(61)]  # 7400..7700
    picked = select_core(spot=7550, chain_strikes=strikes,
                         budget_contracts=62, max_sigma=1.0,
                         daily_sigma_pct=0.01)  # 1σ = 75 pts
    assert len(picked) == 31
    assert 7550 in picked
    # symmetric around ATM
    assert 7475 in picked and 7625 in picked


def test_sigma_binds_when_high_vol():
    # spot 7550, VIX-40 sigma ~2.5% ≈ 189pts → wide sigma bound, budget binds
    strikes = [7400 + 5 * i for i in range(61)]
    picked = select_core(spot=7550, chain_strikes=strikes,
                         budget_contracts=200, max_sigma=1.0,
                         daily_sigma_pct=0.005)  # narrow sigma: 1σ ≈ 38 pts
    # 1σ upper = 7588; 1σ lower = 7512 → strikes in [7515, 7585] (7515,7520,...,7585)
    # (7510 is 40pts below spot, slightly beyond the 38-pt band; 7515 is 35pts, inside)
    assert max(picked) <= 7590
    assert min(picked) >= 7510
    # tighter than the 200-contract budget would have chosen
    assert len(picked) < 100


def test_asymmetric_chain_still_works():
    # spot 7550 but chain only extends to 7600 above — should saturate that side
    strikes = [7400 + 5 * i for i in range(41)]  # 7400..7600
    picked = select_core(spot=7550, chain_strikes=strikes,
                         budget_contracts=60, max_sigma=2.0,
                         daily_sigma_pct=0.01)
    assert max(picked) == 7600
    # remaining budget spent expanding downward
    assert len(picked) <= 30


def test_sorted_ascending_no_dupes():
    strikes = [7400 + 5 * i for i in range(61)]
    picked = select_core(spot=7550, chain_strikes=strikes,
                         budget_contracts=60, max_sigma=1.0,
                         daily_sigma_pct=0.01)
    assert picked == sorted(picked)
    assert len(picked) == len(set(picked))
