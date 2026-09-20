"""Tests for pipeline/discord/data_alerts.py (T-0921-08).

No webhook URL exists anywhere in this file or the module under test — every
build_* function is pure (payload in, payload out) and _post() only prints
when the env var is unset, which is the default in CI.
"""
import json

from pipeline.discord import data_alerts as da


# -------- 名单变化: shortlist ------------------------------------------------


def test_previous_seat_row_picks_the_latest_date_before_today():
    rows = [
        {"date": "2026-09-17", "seat": "burning", "ticker": "MSFT"},
        {"date": "2026-09-18", "seat": "burning", "ticker": "LUXE"},
    ]
    assert da.previous_seat_row(rows, "2026-09-19") == {"burning": "LUXE"}
    assert da.previous_seat_row(rows, "2026-09-17") == {}


def test_shortlist_alert_none_when_every_seat_unchanged():
    current = [{"seat": "burning", "ticker": "LUXE", "why": "x"}]
    prev = {"burning": "LUXE"}
    assert da.build_shortlist_alert(current, prev) is None


def test_shortlist_alert_lists_only_the_seats_that_changed():
    current = [
        {"seat": "burning", "ticker": "LUXE", "why": "heat top"},
        {"seat": "coiling", "ticker": "MSFT", "why": "tight"},
    ]
    prev = {"burning": "MRNA", "coiling": "MSFT"}
    payload = da.build_shortlist_alert(current, prev)
    body = json.dumps(payload, ensure_ascii=False)
    assert "MRNA" in body and "LUXE" in body
    assert "MSFT" not in body  # coiling seat unchanged, shouldn't appear at all
    assert payload["embeds"][0]["title"] == "名单变化 · Shortlist Seats"


def test_shortlist_alert_marks_a_newly_filled_empty_seat():
    current = [{"seat": "asset", "ticker": "QQQ", "why": "rs"}]
    prev = {}
    payload = da.build_shortlist_alert(current, prev)
    assert "(空)" in json.dumps(payload, ensure_ascii=False)


# -------- 状态变化: market_light ---------------------------------------------


def test_previous_light_reads_tail_first():
    lines = [
        json.dumps({"market_light": {"light": "yellow"}}),
        json.dumps({"market_light": {"light": "red"}}),
    ]
    assert da.previous_light(lines) == "red"


def test_previous_light_skips_records_without_market_light():
    lines = [
        json.dumps({"market_light": {"light": "green"}}),
        json.dumps({"session": "2026-09-18"}),  # no market_light key
    ]
    assert da.previous_light(lines) == "green"


def test_previous_light_none_on_empty_ledger():
    assert da.previous_light([]) is None


def test_state_alert_none_when_light_unchanged():
    assert da.build_state_change_alert("spy", "red", {"n": 7}, "red") is None


def test_state_alert_none_when_no_prior_light():
    assert da.build_state_change_alert("spy", "red", {"n": 7}, None) is None


def test_state_alert_fires_on_a_real_transition():
    payload = da.build_state_change_alert(
        "spy", "green", {"n": 3, "label_zh": "踩下去"}, "red"
    )
    assert payload is not None
    body = json.dumps(payload, ensure_ascii=False)
    assert "red" in body and "green" in body and "踩下去" in body


# -------- 闸的告警: gate ------------------------------------------------------


def test_gate_alert_labels_c_gate_distinctly_from_infra():
    c_gate = da.build_gate_alert({"klass": "C_gate", "why": "闸挡了", "evidence": {}}, "123")
    infra = da.build_gate_alert({"klass": "A_infra", "why": "没留记录", "evidence": {}}, "456")
    assert c_gate["embeds"][0]["title"] != infra["embeds"][0]["title"]
    assert "C_gate" in c_gate["embeds"][0]["title"]
    assert "run_id" in c_gate["embeds"][0]["description"] or "123" in c_gate["embeds"][0]["description"]


def test_gate_alert_includes_evidence_for_debugging():
    verdict = {"klass": "B_vendor", "why": "上游拒绝", "evidence": {"tradeable_ratio": 0.003}}
    payload = da.build_gate_alert(verdict, "789")
    assert "0.003" in payload["embeds"][0]["fields"][0]["value"]


# -------- _post: dry-run-by-default safety -----------------------------------


def test_post_prints_instead_of_posting_when_env_var_unset(monkeypatch, capsys):
    monkeypatch.delenv("DISCORD_DOES_NOT_EXIST_WEBHOOK", raising=False)
    ok = da._post({"hello": "world"}, "DISCORD_DOES_NOT_EXIST_WEBHOOK")
    assert ok is False
    out = capsys.readouterr().out
    assert "hello" in out


def test_no_webhook_url_is_hardcoded_in_the_module():
    src = open(da.__file__, encoding="utf-8").read()
    assert "discord.com/api/webhooks/" not in src
