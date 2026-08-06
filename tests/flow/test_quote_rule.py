from pipeline.flow.quote_rule import classify


def test_at_or_above_ask_is_bot():
    assert classify(price=5.10, bid=5.00, ask=5.10) == "BOT"
    assert classify(price=5.15, bid=5.00, ask=5.10) == "BOT"


def test_at_or_below_bid_is_sold():
    assert classify(price=5.00, bid=5.00, ask=5.10) == "SOLD"
    assert classify(price=4.95, bid=5.00, ask=5.10) == "SOLD"


def test_inside_spread_above_mid_is_bot():
    # spread 5.00 / 5.10, mid 5.05
    assert classify(price=5.07, bid=5.00, ask=5.10) == "BOT"


def test_inside_spread_below_mid_is_sold():
    assert classify(price=5.02, bid=5.00, ask=5.10) == "SOLD"


def test_at_mid_uses_tick_rule():
    assert classify(price=5.05, bid=5.00, ask=5.10, prev_price=5.00) == "BOT"
    assert classify(price=5.05, bid=5.00, ask=5.10, prev_price=5.10) == "SOLD"
    assert classify(price=5.05, bid=5.00, ask=5.10, prev_price=5.05) == "UNKNOWN"
    assert classify(price=5.05, bid=5.00, ask=5.10, prev_price=None) == "UNKNOWN"


def test_missing_or_crossed_quote_is_unknown():
    assert classify(price=5.05, bid=None, ask=5.10) == "UNKNOWN"
    assert classify(price=5.05, bid=5.00, ask=None) == "UNKNOWN"
    # crossed / locked quote (ask <= bid) — refuse to guess
    assert classify(price=5.05, bid=5.10, ask=5.00) == "UNKNOWN"
