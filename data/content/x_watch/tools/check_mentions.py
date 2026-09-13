#!/usr/bin/env python3
"""mentions.csv 公箱自检 —— 按键比对，不数减号。

为什么不用 `git diff | grep '^-'`：mentions.csv 被要求**就地回填 stance 列**。
回填一行在 diff 里是「删一行、加一行」，grep 数出来的是改行数，不是丢行数。
09-09、09-10、09-11 三班连续报红、三班都要人工解释 —— 三次律，升成这个脚本。
(09-11 实测：grep 数出 35，和当班 stance 回填条数逐字相等，丢行是 0。)

比对 base（默认 origin/main 那份）和 head（工作区那份），键 = (date, ticker, handle, post_id)：

  丢行              base 有、head 没有                      → 失败
  非 stance 列被改   同键，date/ticker/handle/post_id 之外、
                    stance 之外的列不同（views/bookmarks）   → 失败（fetch.py 规定已存在的行整行保留）
  已有 stance 被改   base 的 stance 非空，head 与之不同        → 失败（那是人工判断，不许静默覆盖）
  新增              head 有、base 没有                      → 只报数
  stance 空→值      base 空、head 非空                      → 只报数

读 CSV 走 csv 模块、newline=""，所以 CRLF 行尾（mentions.csv 就是 CRLF）不会被当成改动。

用法:
    python3 data/content/x_watch/tools/check_mentions.py            # base=origin/main
    python3 data/content/x_watch/tools/check_mentions.py --base-ref HEAD~1
退出码 0 = 安全；1 = 有丢行 / 改列 / 改 stance。
"""
from __future__ import annotations
import argparse, csv, io, subprocess, sys
from pathlib import Path

REL = "data/content/x_watch/mentions.csv"
KEY = ("date", "ticker", "handle", "post_id")


def read_rows(text: str) -> dict[tuple, dict]:
    out = {}
    for r in csv.DictReader(io.StringIO(text, newline="")):
        out[tuple(r.get(c, "") for c in KEY)] = r
    return out


def compare(base: dict[tuple, dict], head: dict[tuple, dict]) -> dict:
    lost = [k for k in base if k not in head]
    added = [k for k in head if k not in base]
    changed, stance_changed, stance_filled = [], [], []
    for k in base.keys() & head.keys():
        b, h = base[k], head[k]
        cols = (set(b) | set(h)) - set(KEY) - {"stance"}
        if any((b.get(c) or "") != (h.get(c) or "") for c in cols):
            changed.append(k)
        bs, hs = (b.get("stance") or ""), (h.get("stance") or "")
        if bs and bs != hs:
            stance_changed.append(k)
        elif not bs and hs:
            stance_filled.append(k)
    return {"lost": lost, "changed": changed, "stance_changed": stance_changed,
            "added": added, "stance_filled": stance_filled,
            "ok": not (lost or changed or stance_changed)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-ref", default="origin/main")
    ap.add_argument("--head", default=None, help="默认：仓库根下的 mentions.csv")
    a = ap.parse_args()
    root = Path(subprocess.run(["git", "rev-parse", "--show-toplevel"],
                               capture_output=True, text=True, check=True).stdout.strip())
    base_txt = subprocess.run(["git", "-C", str(root), "show", f"{a.base_ref}:{REL}"],
                              capture_output=True, text=True)
    if base_txt.returncode != 0:
        print(f"base 读不到（{a.base_ref}:{REL}）—— 首次提交无可比对，放行")
        return 0
    head_path = Path(a.head) if a.head else root / REL
    r = compare(read_rows(base_txt.stdout), read_rows(head_path.read_text(encoding="utf-8")))
    print(f"丢行 {len(r['lost'])} · 非 stance 列被改 {len(r['changed'])} · "
          f"已有 stance 被改 {len(r['stance_changed'])} · 新增 {len(r['added'])} · "
          f"stance 空→值 {len(r['stance_filled'])}")
    for name in ("lost", "changed", "stance_changed"):
        for k in r[name][:5]:
            print(f"  ✗ {name}: {k}")
    print("✅ 安全" if r["ok"] else "⛔ 不许提交")
    return 0 if r["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
