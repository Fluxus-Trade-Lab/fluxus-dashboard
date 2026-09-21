"""Discord webhook alerts for data-pipeline events — T-0921-08.

Andy 09-21: "把数据端的一些内容，通过webhook发到discord上...把系统和流程里的一些
事情拆分，在discord里呈现出来。" Same shape as pipeline/discord/premarket_digest.py:
one env var per channel, dry-run (print to stdout) when the webhook isn't set, so this
module is safe to run in CI/tests with zero configuration.

Each alert reads one existing pipeline output/ledger field — no new state is invented:
  名单变化   shortlist  data/output/shortlist.json .seats
             vs data/history/shortlist_seat_log.csv (prior logged date)
  状态变化   market_light  data/output/market_light.json .<symbol>.light
             vs data/history/run_ledger.jsonl (prior run's market_light.light)
  闸的告警   gate  pipeline/tools/failure_class.classify() verdict for one run_id

Design table (channels, webhook URLs, member visibility) is pending Andy's sign-off:
see data/reference/discord_webhook_channels.md — none of that is hardcoded here.

Env vars (all optional — each alert degrades to a stdout print when unset):
  DISCORD_SHORTLIST_WEBHOOK : 名单变化 channel
  DISCORD_STATE_WEBHOOK     : 状态变化 channel
  DISCORD_GATE_WEBHOOK      : 闸的告警 channel

Usage:
  python -m pipeline.discord.data_alerts shortlist [--dry-run]
  python -m pipeline.discord.data_alerts state [--symbol spy] [--dry-run]
  python -m pipeline.discord.data_alerts gate --run-id <id> [--dry-run]
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import os
from pathlib import Path
from typing import Any

import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("discord_data_alerts")

REPO_ROOT = Path(__file__).resolve().parents[2]
SHORTLIST_PATH = REPO_ROOT / "data" / "output" / "shortlist.json"
SEAT_LOG_PATH = REPO_ROOT / "data" / "history" / "shortlist_seat_log.csv"
MARKET_LIGHT_PATH = REPO_ROOT / "data" / "output" / "market_light.json"
RUN_LEDGER_PATH = REPO_ROOT / "data" / "history" / "run_ledger.jsonl"

SEAT_LABELS = {
    "burning": "🔥 Burning",
    "new_leader": "🆕 New Leader",
    "entry": "🚪 Entry",
    "v_reversal": "↩️ V-Reversal",
    "coiling": "🌀 Coiling",
    "asset": "💎 Asset",
}

LIGHT_COLOR = {"red": 0xdc2626, "yellow": 0xd97706, "green": 0x16a34a}

GATE_TITLE = {
    "A_infra": "🔴 A_infra · 排程被丢弃",
    "B_vendor": "🟠 B_vendor · 上游拒绝",
    "C_gate": "🟡 C_gate · 闸拦住了好数据",
    "D_code": "🔴 D_code · 管线抛异常",
}


def _post(payload: dict[str, Any], env_var: str) -> bool:
    """Post to the webhook named by env_var; print to stdout if it isn't set."""
    url = os.environ.get(env_var)
    if not url:
        logger.info("%s not set — printing payload to stdout", env_var)
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return False
    try:
        r = requests.post(url, json=payload, timeout=15)
        if r.ok or r.status_code == 204:
            logger.info("Posted to Discord OK (%s)", env_var)
            return True
        logger.error("Discord POST failed: %s %s", r.status_code, r.text[:300])
        return False
    except Exception as e:
        logger.error("Discord POST exception: %s", e)
        return False


# -------- 名单变化: shortlist seats ------------------------------------------


def previous_seat_row(rows: list[dict[str, str]], before_date: str) -> dict[str, str]:
    """{seat: ticker} logged on the most recent date strictly before before_date."""
    dates = sorted({r["date"] for r in rows if r["date"] < before_date})
    if not dates:
        return {}
    prev_date = dates[-1]
    return {r["seat"]: r["ticker"] for r in rows if r["date"] == prev_date}


def build_shortlist_alert(
    current_seats: list[dict[str, str]], previous_by_seat: dict[str, str]
) -> dict[str, Any] | None:
    """Diff today's shortlist.json seats against the prior logged day. None if unchanged."""
    changes = []
    for row in current_seats:
        seat, ticker, why = row.get("seat", ""), row.get("ticker", ""), row.get("why", "")
        prev = previous_by_seat.get(seat)
        if prev != ticker:
            label = SEAT_LABELS.get(seat, seat)
            changes.append(f"{label}：`{prev or '(空)'}` → `{ticker}`\n     ↳ {why}")
    if not changes:
        return None
    return {
        "username": "Fluxus Data Desk",
        "embeds": [
            {
                "title": "名单变化 · Shortlist Seats",
                "description": "\n".join(changes)[:4000],
                "color": 0x2563EB,
                "footer": {
                    "text": "出处 data/output/shortlist.json .seats · "
                    "对比 data/history/shortlist_seat_log.csv 前一日"
                },
            }
        ],
    }


def run_shortlist(dry_run: bool = False) -> int:
    if not SHORTLIST_PATH.exists() or not SEAT_LOG_PATH.exists():
        logger.error("shortlist.json or shortlist_seat_log.csv missing")
        return 1
    data = json.loads(SHORTLIST_PATH.read_text())
    seats = data.get("seats") or []
    today = data.get("date") or ""
    with SEAT_LOG_PATH.open() as f:
        rows = list(csv.DictReader(f))
    prev = previous_seat_row(rows, today)
    payload = build_shortlist_alert(seats, prev)
    if payload is None:
        logger.info("No seat changes vs prior day — nothing to post")
        return 0
    if dry_run:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0
    return 0 if _post(payload, "DISCORD_SHORTLIST_WEBHOOK") else 1


# -------- 状态变化: market_light ---------------------------------------------


def previous_light(run_ledger_lines: list[str]) -> str | None:
    """Most recent market_light.light logged in run_ledger.jsonl, tail-first."""
    for line in reversed(run_ledger_lines):
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        ml = rec.get("market_light")
        if isinstance(ml, dict) and ml.get("light"):
            return ml["light"]
    return None


def build_state_change_alert(
    symbol: str, current_light: str, current_gear: dict[str, Any], prev_light: str | None
) -> dict[str, Any] | None:
    if prev_light is None or prev_light == current_light:
        return None
    # `gear` retired from market_light.json 2026-09-20 (course deleted
    # L6B.2) -- run_state() now always passes {}. Only print the suffix
    # when a caller still has a real gear reading (e.g. old ledger replay).
    gear_n = (current_gear or {}).get('n')
    gear_suffix = (f"（gear {gear_n} · {current_gear.get('label_zh', '')}）"
                   if gear_n is not None else "")
    return {
        "username": "Fluxus Data Desk",
        "embeds": [
            {
                "title": f"状态变化 · Market Light ({symbol.upper()})",
                "description": f"`{prev_light}` → `{current_light}`" + gear_suffix,
                "color": LIGHT_COLOR.get(current_light, 0x64748B),
                "footer": {
                    "text": "出处 data/output/market_light.json .<symbol>.light · "
                    "对比 data/history/run_ledger.jsonl 上一条 market_light.light"
                },
            }
        ],
    }


def run_state(symbol: str = "spy", dry_run: bool = False) -> int:
    if not MARKET_LIGHT_PATH.exists():
        logger.error("market_light.json missing")
        return 1
    data = json.loads(MARKET_LIGHT_PATH.read_text())
    sym = data.get(symbol)
    if not sym:
        logger.error("symbol %s not in market_light.json", symbol)
        return 1
    lines = RUN_LEDGER_PATH.read_text().splitlines() if RUN_LEDGER_PATH.exists() else []
    prev = previous_light(lines)
    payload = build_state_change_alert(symbol, sym["light"], sym.get("gear", {}), prev)
    if payload is None:
        logger.info("No light change vs prior run — nothing to post")
        return 0
    if dry_run:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0
    return 0 if _post(payload, "DISCORD_STATE_WEBHOOK") else 1


# -------- 闸的告警: failure_class verdict ------------------------------------


def build_gate_alert(verdict: dict[str, Any], run_id: str) -> dict[str, Any]:
    klass = verdict.get("klass", "?")
    return {
        "username": "Fluxus Data Desk",
        "embeds": [
            {
                "title": GATE_TITLE.get(klass, f"闸的告警 · {klass}"),
                "description": f"run_id `{run_id}`\n{verdict.get('why', '')}",
                "color": 0xDC2626 if klass in ("A_infra", "D_code") else 0xD97706,
                "fields": [
                    {
                        "name": "读数",
                        "value": "```"
                        + json.dumps(verdict.get("evidence", {}), ensure_ascii=False, indent=2)[:1000]
                        + "```",
                        "inline": False,
                    }
                ],
                "footer": {
                    "text": "出处 pipeline/tools/failure_class.classify() · "
                    "发送时机：分诊判完非 OK 立即发，不等下一班"
                },
            }
        ],
    }


def run_gate(run_id: str, dry_run: bool = False) -> int:
    from pipeline.tools.failure_class import classify, find_run, load_ledger

    records = load_ledger(RUN_LEDGER_PATH)
    if not records:
        logger.error("run_ledger.jsonl empty or missing — cannot classify")
        return 1
    rec = find_run(records, run_id)
    verdict = classify(rec, failed=True)
    payload = build_gate_alert(verdict, run_id)
    if dry_run:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0
    return 0 if _post(payload, "DISCORD_GATE_WEBHOOK") else 1


# -------- Main ---------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="alert", required=True)

    p_shortlist = sub.add_parser("shortlist", help="名单变化 · shortlist seats")
    p_shortlist.add_argument("--dry-run", action="store_true")

    p_state = sub.add_parser("state", help="状态变化 · market_light")
    p_state.add_argument("--symbol", default="spy")
    p_state.add_argument("--dry-run", action="store_true")

    p_gate = sub.add_parser("gate", help="闸的告警 · failure_class verdict")
    p_gate.add_argument("--run-id", required=True)
    p_gate.add_argument("--dry-run", action="store_true")

    args = ap.parse_args(argv)

    if args.alert == "shortlist":
        return run_shortlist(dry_run=args.dry_run)
    if args.alert == "state":
        return run_state(symbol=args.symbol, dry_run=args.dry_run)
    if args.alert == "gate":
        return run_gate(args.run_id, dry_run=args.dry_run)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
