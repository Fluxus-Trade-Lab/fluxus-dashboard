"""Recap delivery gates: every gate must first be shown RED on an injected
positive before its green on a real PDF means anything."""
import pytest

from pipeline.content.recap.gates import run_gates

CLEAN_EN = ("Indexes snapped a four-day slide. SPY +0.85% reclaimed its 50-day; "
            "QQQ 714.88. Open R +1.2R, return +12.3%, cash 62%. Don't chase.")
CLEAN_ZH = "指数止住四连跌。SPY +0.85%，收回 50 日线；龙头是 DELL、HPE。个股分化，股票池 5617 只。现金 62%。"


def test_clean_text_passes_all_three():
    for t in (CLEAN_EN, CLEAN_ZH):
        r = run_gates(t)
        assert r["ok"], r


@pytest.mark.parametrize("inject", [
    "today's Revere roundup", "the Rever roundup", "River Asset Management", "River AI 100",
    "the AI 100 Index", "Turbo 12 list", "Turboction", "Growction", "Ted said", "Dan thinks",
    "per Connor", "Todd's chart", "Don sees", "Jackson Naidik here", "ask@example.com",
    "call 212-555-0187",
    "Ted说今天", "主播Jackson认为",  # CJK neighbours: \b would miss these
    # misspellings that really occur in the 2026-09-11 auto-captions
    "we do not call tops at Revier", "grotction up 0.69%", "Gretection was up", "turboction",
    "the 21 over 21 list", "the sweet 17 watch list", "RG8 up 0.94%",
    "a Toddzilla holding", "Ted Zhang here", "Connor Bates", "Okta Grok Tasha holding",
    "855 real wealth", "ted@revereasset.com", "riverasset",
])
def test_banned_gate_goes_red(inject):
    r = run_gates(CLEAN_EN + " " + inject)
    assert r["banned"], inject
    assert not r["ok"]


def test_leadership_gate_goes_red():
    r = run_gates(CLEAN_ZH + "半导体展现领导力")
    assert r["leadership_zh"] == 1 and not r["ok"]


@pytest.mark.parametrize("inject", [
    "bought $12,400 of DELL", "US$ 5,000", "P/L 3,200 USD", "赚了 1.2 万美元", "2k dollars",
    "sold 300 shares", "trimmed 50 sh", "卖出 200 股", "持有 1,500股",
])
def test_money_shares_gate_goes_red(inject):
    r = run_gates(CLEAN_EN + " " + inject)
    assert r["money_shares"], inject
    assert not r["ok"]


@pytest.mark.parametrize("inject", [
    "Andy at 08:33 ET: rates matter", "per andy", "Andy：盯债券", "I do think we can sell off",
    "stops set in place, I'm out", "our book", "we wait", "我在日内模式", "我们等均线收拢",
])
def test_voice_gate_goes_red(inject):
    r = run_gates(CLEAN_EN + " " + inject)
    assert r["voice"], inject
    assert not r["ok"]


def test_voice_gate_spares_tickers_and_ordinary_words():
    # US (country / ticker-ish caps), IWM, "Index", "mega", "Wedge", "ourselves"-free prose
    r = run_gates("US CPI hot · IWM heavy · Index down 4 days · mega caps · memory · weekly · Iran · IBIT · MU −0.2%")
    assert r["voice"] == [], r["voice"]


def test_money_gate_does_not_flag_prices_or_percent_or_cashtag_free_levels():
    r = run_gates("SPX 7,657 · QQQ 715 bull/bear line · +0.86% · 1.66× volume · 股票 · 个股 · 股价")
    assert r["money_shares"] == []


def test_dont_is_not_the_host_name():
    assert run_gates("Don't chase. Don’t chase.")["banned"] == []
