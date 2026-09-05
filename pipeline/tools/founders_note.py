#!/usr/bin/env python3
"""Founders Note 取数 —— 从 Portfolio GAS 的 Meta tab 拉 Andy 手写的笔记。

daily-recap 用：Founders Note 不截图，直接取文本进正文（Andy 2026-09-06:
「founders notes 最新的是有的，以后我们通过 pipeline 可以拿到，可能不需要给它截图」）。

数据形状（见 frontend/src/lib/writingSync.js）：
  Sheet Meta tab 的 key = writing:<kind>:<YYYY-MM>，value = JSON {date: text}
  kind ∈ trading-recap | founders-daily | founders-weekly | premarket-checklist
  founders-weekly 的 date key 是 ISO 周一（weekKey），其余是 YYYY-MM-DD。

凭证：环境变量 GAS_URL / GAS_SYNC_TOKEN，或仓库根 .env（gitignored）。
与浏览器同一 token（localStorage portfolio-v4 的 gasUrl/syncToken）。

用法：
  python3 pipeline/tools/founders_note.py --date 2026-09-04            # 当日 daily
  python3 pipeline/tools/founders_note.py --date 2026-09-04 --weekly   # 该周 weekly
  python3 pipeline/tools/founders_note.py --date 2026-09-04 --kind trading-recap
  python3 pipeline/tools/founders_note.py --month 2026-09 --all        # 整月各条列出
无内容时 exit 3 并打印 [empty]，让调用方能区分「拉通了但他没写」和「拉不通」。
"""
import argparse
import datetime as dt
import json
import os
import re
import sys
import urllib.parse
import urllib.request

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TIMEOUT = 30  # GAS 冷启动要几秒

KINDS = ("trading-recap", "founders-daily", "founders-weekly", "premarket-checklist")


def load_credentials():
    url = os.environ.get("GAS_URL", "").strip()
    token = os.environ.get("GAS_SYNC_TOKEN", "").strip()
    if url and token:
        return url, token
    env_path = os.path.join(REPO_ROOT, ".env")
    if os.path.exists(env_path):
        text = open(env_path).read()
        m_url = re.search(r'^export GAS_URL="?([^"\n]+)"?', text, re.M)
        m_tok = re.search(r'^export GAS_SYNC_TOKEN="?([^"\n]+)"?', text, re.M)
        if m_url and m_tok:
            return m_url.group(1).strip(), m_tok.group(1).strip()
    sys.exit("未配置：需要 GAS_URL 与 GAS_SYNC_TOKEN（环境变量或仓库根 .env）。"
             "值与浏览器 Portfolio 设置里的 gasUrl/syncToken 相同。")


def pull_meta():
    url, token = load_credentials()
    q = f"{url}?action=pull&token={urllib.parse.quote(token)}"
    with urllib.request.urlopen(q, timeout=TIMEOUT) as res:
        data = json.load(res)
    if not data.get("ok"):
        sys.exit(f"GAS 拒绝：{data.get('error', 'unknown')}")
    return data.get("meta") or {}


def week_key(date):
    """ISO 周一，对齐前端 writingStore 的 weekKey。"""
    return (date - dt.timedelta(days=date.weekday())).isoformat()


def entries_for(meta, kind, month):
    raw = meta.get(f"writing:{kind}:{month}")
    if raw is None:
        return {}
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except ValueError:
            return {}
    return raw if isinstance(raw, dict) else {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", help="YYYY-MM-DD（取该日一条）")
    ap.add_argument("--month", help="YYYY-MM（配 --all 列整月）")
    ap.add_argument("--kind", default="founders-daily", choices=KINDS)
    ap.add_argument("--weekly", action="store_true",
                    help="等价 --kind founders-weekly，date 自动折算到 ISO 周一")
    ap.add_argument("--all", action="store_true", help="列出该月该 kind 的全部条目")
    args = ap.parse_args()

    kind = "founders-weekly" if args.weekly else args.kind

    if args.month and args.all:
        meta = pull_meta()
        entries = entries_for(meta, kind, args.month)
        if not entries:
            print("[empty]")
            sys.exit(3)
        for d in sorted(entries):
            print(f"── {d} ──")
            print(entries[d].strip() if isinstance(entries[d], str) else entries[d])
        return

    if not args.date:
        ap.error("要么 --date，要么 --month --all")
    date = dt.date.fromisoformat(args.date)
    key = week_key(date) if kind == "founders-weekly" else date.isoformat()
    meta = pull_meta()
    entries = entries_for(meta, kind, key[:7])
    text = entries.get(key)
    if not text or not str(text).strip():
        print("[empty]")
        sys.exit(3)
    print(str(text).strip())


if __name__ == "__main__":
    main()
