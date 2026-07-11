# tests/gex/test_render.py
from pipeline.gex.render import render_brief
from tests.gex.test_schema import tenor_stub

def make_doc(stale=False):
    from pipeline.gex.schema import build_document
    return build_document(
        asof="2026-07-11T08:00:00-04:00", stale=stale,
        stale_reason="pull failed" if stale else None,
        opex={"date": "2026-07-17", "dte": 6, "within_week": False},
        instruments={"SPX": {"spot": 7543.6, "basis": {"ES": 53.0},
                             "tenors": {"front": tenor_stub(),
                                        "swing": tenor_stub(),
                                        "monthly": tenor_stub()}}},
        read={"regime": "positive",
              "bull": ["floor held"], "bear": ["extended"],
              "plan": ["Line in the sand: 7590"]},
        strategy_fit=[{"name": "bull_put_spread", "rating": "favored",
                       "why": "floor + regime on-side"}])

def test_render_contains_key_values():
    html = render_brief(make_doc())
    # NOTE: the n0 filter renders thousands separators — assert "7,650" not "7650"
    for token in ("7543.6", "7,650", "7,550", "bull_put_spread", "favored",
                  "positive", "Line in the sand: 7590", "2026-07-17"):
        assert token in html, f"missing {token}"

def test_render_stale_banner():
    assert "STALE" in render_brief(make_doc(stale=True))
    assert "STALE" not in render_brief(make_doc(stale=False))
