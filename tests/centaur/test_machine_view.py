"""The machine's half of the pairing — deterministic, or absent."""
from pipeline.centaur.machine_view import machine_direction


def snap(spot, flip, va_low=None, va_high=None, confluent=0):
    rows = []
    if va_high is not None:
        rows.append({"confluence": False, "members": [
            {"name": "value area high", "price": va_high}]})
    if va_low is not None:
        rows.append({"confluence": False, "members": [
            {"name": "value area low", "price": va_low}]})
    for i in range(confluent):
        rows.append({"confluence": True, "members": [{"name": f"x{i}", "price": 0}]})
    return {"gex": {"spot": spot, "zero_gamma_flip": flip}, "reference_map": rows}


def test_positive_gamma_inside_value_is_balance():
    v = machine_direction(snap(7710, 7600, 7700, 7730))
    assert v["direction"] == "range"


def test_the_same_location_in_negative_gamma_is_not_balance():
    # Below the flip, "inside value" is a coiled spring, not a range. The view
    # must decline rather than reuse the positive-gamma answer.
    v = machine_direction(snap(7550, 7600, 7500, 7580))
    assert v["direction"] == "stand_aside"


def test_accepted_above_value_in_positive_gamma_is_up():
    assert machine_direction(snap(7800, 7600, 7700, 7730))["direction"] == "up"


def test_below_value_below_the_flip_is_down():
    assert machine_direction(snap(7400, 7600, 7500, 7580))["direction"] == "down"


def test_conviction_comes_from_cross_framework_agreement():
    assert machine_direction(snap(7710, 7600, 7700, 7730, confluent=0))["conviction"] == 1
    assert machine_direction(snap(7710, 7600, 7700, 7730, confluent=2))["conviction"] == 3
    # capped: five agreements are not five times the evidence
    assert machine_direction(snap(7710, 7600, 7700, 7730, confluent=5))["conviction"] == 3


def test_missing_inputs_yield_no_view_rather_than_a_guess():
    assert machine_direction({"gex": {}}) is None
    assert machine_direction({"gex": {"spot": 7700}}) is None


def test_no_value_area_still_produces_a_regime_read_at_low_conviction():
    v = machine_direction(snap(7710, 7600))
    assert v["direction"] == "range" and v["conviction"] == 1


def test_every_view_carries_its_reasoning():
    v = machine_direction(snap(7710, 7600, 7700, 7730))
    assert "flip" in v["rationale"] and "7,710" in v["rationale"]
