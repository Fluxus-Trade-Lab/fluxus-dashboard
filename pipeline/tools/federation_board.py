# -*- coding: utf-8 -*-
"""联邦只读看板 v0 —— 全部数据来自 git（origin/main 权威版），只读，零依赖。
用法: python3 federation_board.py <repo> <out.html>
"""
import subprocess, sys, json, html, re, datetime

REPO = sys.argv[1]
OUT = sys.argv[2]

def git(*args):
    return subprocess.run(["git", "-C", REPO] + list(args), capture_output=True, text=True).stdout

def show(path):
    return git("show", "origin/main:" + path)

LANES = [  # (线名, commit message 关键词启发式)
    ("DATA ALEX", ["feat(", "fix(watchlist", "fix(schema", "data(", "chore: market", "fix(ohlc", "screener"]),
    ("UI Claire", ["frontend", "ui(", "fix(front", "feat(ui"]),
    ("RND Linda", ["regime", "gex", "risk(", "lamp"]),
    ("Studio Q", ["studio", "draft", "substack(", "mrna", "letter"]),
    ("Marketing Steve", ["research(steve", "contract(steve", "material(", "post", "fix(posts", "brief"]),
    ("Nighty Zac", ["night(", "prereg(", "collect(", "preview(", "tests(", "adr-floor", "vcp", "amplitude", "stockbee"]),
    ("Plumber Joe", ["joe(", "audit", "contracts(§", "plumb"]),
    ("Growth Gary", ["growth", "product:", "tool(post"]),
    ("OPS Fable", ["ops(", "rules(", "verdict(", "task(zac", "rescue(", "projects(", "growth: PayPal", "team"]),
]

log = git("log", "origin/main", "--since=7 days ago", "--format=%h|%ad|%s", "--date=format:%m-%d %H:%M")
commits = [l.split("|", 2) for l in log.splitlines() if l.count("|") >= 2]

def lane_of(msg):
    m = msg.lower()
    for name, keys in LANES:
        for k in keys:
            if k.lower() in m:
                return name
    return "其他"

lane_last = {}
lane_today = {}
now = datetime.datetime.now()
for h, ad, s in commits:
    ln = lane_of(s)
    if ln not in lane_last:
        lane_last[ln] = (ad, s, h)
    day = ad.split(" ")[0]
    if day == now.strftime("%m-%d"):
        lane_today.setdefault(ln, []).append((h, s))

# --- Kanban 数据 ---
contracts = show("data/reference/DATA_CONTRACTS.md")
todo = []
blocked = []
for line in contracts.splitlines():
    if re.match(r"^- \[\d{2,4}-", line) or re.match(r"^- \[08-", line):
        if "✅" in line or "~~" in line:
            continue
        head = re.sub(r"\*\*", "", line)[:110]
        if "待 Andy" in line or "Andy 拍板" in line and "已" not in line[:40]:
            blocked.append(head)
        elif "→" in line[:60]:
            todo.append(head)
todo = todo[:12]
blocked = blocked[:8]

# 门铃待按（最新晨报）
reports = sorted(re.findall(r"night_reports/(2026-\d\d-\d\d)\.md", git("ls-tree", "-r", "--name-only", "origin/main", "data/research/night_reports/")))
bells = []
if reports:
    latest = show("data/research/night_reports/%s.md" % reports[-1])
    sec = re.search(r"门铃待按[^\n]*\n(.*?)(\n## |\Z)", latest, re.S)
    if sec:
        for row in re.findall(r"\| *\*?\*?([^|*]+?)\*?\*? *\| *([^|]+?) *\|", sec.group(1)):
            if "收件人" in row[0] or "---" in row[0]:
                continue
            bells.append("%s ← %s" % (row[0].strip(), row[1].strip()[:80]))

# 待合分支（远端非 auto-archive 的、领先 main 的）
branches = []
for b in git("branch", "-r", "--no-merged", "origin/main").splitlines():
    b = b.strip()
    if not b or "HEAD" in b or "archive/" in b:
        continue
    n = git("rev-list", "--count", "origin/main.." + b).strip()
    if n and n != "0":
        branches.append("%s (+%s commit)" % (b.replace("origin/", ""), n))
branches = branches[:10]

done24 = [(h, s) for h, ad, s in commits if (now - datetime.datetime.strptime("2026-" + ad, "%Y-%m-%d %H:%M")).total_seconds() < 86400][:20]
doing = [(ln, c) for ln, cs in lane_today.items() for c in cs][:15]

# NOW.md 关卡
nowmd = show("NOW.md")
gate = re.search(r"🎮[^\n]*\n(?:[^\n]*\n){0,6}", nowmd)
gate_txt = html.escape(gate.group(0)[:300]) if gate else "（NOW.md 无关卡节）"

def card(txt, cls=""):
    return '<div class="card %s">%s</div>' % (cls, html.escape(txt))

def col(title, items, cls, empty="（空）"):
    inner = "".join(card(i, cls) for i in items) or '<div class="empty">%s</div>' % empty
    return '<div class="col"><div class="colh %s">%s <span class="n">%d</span></div>%s</div>' % (cls, title, len(items), inner)

lanes_html = ""
for name, _ in LANES:
    last = lane_last.get(name)
    today_n = len(lane_today.get(name, []))
    dot = "🟢" if today_n else ("🟡" if last else "⚪")
    lastline = ("%s · %s" % (last[0], last[1][:60])) if last else "近 7 天无落地"
    lanes_html += '<div class="lane"><span class="dot">%s</span><b>%s</b> <span class="tn">%s</span><div class="ll">%s</div></div>' % (
        dot, name, ("今日 %d 单" % today_n) if today_n else "", html.escape(lastline))

claim_items = ["【门铃】" + b for b in bells] + ["【待合】" + b for b in branches] + ["【契约】" + t for t in todo]

htmldoc = """<!doctype html><html lang="zh"><head><meta charset="utf-8">
<title>Fluxus 联邦看板 v0</title>
<style>
:root{--bg:#faf9f6;--ink:#1a1a1a;--mut:#8a8578;--line:#e8e4da;--card:#fff;
--todo:#8a6d1f;--doing:#1f5c8a;--block:#a33;--done:#2a6e4f}
*{box-sizing:border-box;margin:0}body{background:var(--bg);color:var(--ink);
font:14px/1.55 -apple-system,"PingFang SC",sans-serif;padding:28px}
h1{font-size:20px;letter-spacing:.02em}h2{font-size:13px;color:var(--mut);
text-transform:uppercase;letter-spacing:.12em;margin:26px 0 10px}
.meta{color:var(--mut);font-size:12px;margin-top:4px}
.lanes{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
.lane{background:var(--card);border:1px solid var(--line);padding:10px 12px;border-radius:6px}
.lane .dot{margin-right:6px}.lane .tn{color:var(--done);font-size:12px;margin-left:6px}
.lane .ll{color:var(--mut);font-size:12px;margin-top:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.board{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;align-items:start}
.col{background:#f3f1ea;border:1px solid var(--line);border-radius:8px;padding:10px}
.colh{font-weight:600;font-size:13px;margin-bottom:8px}.colh .n{color:var(--mut);font-weight:400}
.card{background:var(--card);border:1px solid var(--line);border-left:3px solid var(--mut);
border-radius:5px;padding:8px 10px;margin-bottom:8px;font-size:12.5px;word-break:break-all}
.card.todo{border-left-color:var(--todo)}.card.doing{border-left-color:var(--doing)}
.card.block{border-left-color:var(--block)}.card.done{border-left-color:var(--done)}
.colh.todo{color:var(--todo)}.colh.doing{color:var(--doing)}.colh.block{color:var(--block)}.colh.done{color:var(--done)}
.empty{color:var(--mut);font-size:12px;padding:6px}
.gate{background:var(--card);border:1px solid var(--line);border-radius:6px;padding:12px;white-space:pre-wrap;font-size:12.5px}
footer{margin-top:26px;color:var(--mut);font-size:11.5px}
</style></head><body>
<h1>Fluxus 联邦看板 <span style="color:var(--mut);font-weight:400">v0 · 只读</span></h1>
<div class="meta">生成 %(ts)s · 数据源 = origin/main（git 为唯一权威）· 分线归属为 v0 关键词启发式</div>
<h2>八线心跳（近 7 天）</h2><div class="lanes">%(lanes)s</div>
<h2>🎮 关卡</h2><div class="gate">%(gate)s</div>
<h2>任务四列</h2>
<div class="board">%(c1)s%(c2)s%(c3)s%(c4)s</div>
<footer>待认领列 = 门铃待按 + 待合分支 + §七/§12 未勾契约行 三处归一（挂单不挂人：各线开工先来认领自己的）。观察席只读，修改请走各自文件边界。</footer>
</body></html>""" % dict(
    ts=now.strftime("%Y-%m-%d %H:%M JST"),
    lanes=lanes_html, gate=gate_txt,
    c1=col("待认领（挂单板）", claim_items, "todo"),
    c2=col("进行中（今日已落 main）", ["[%s] %s" % (l, c[1][:80]) for l, c in doing], "doing"),
    c3=col("受阻 · 待 Andy", blocked, "block"),
    c4=col("已完成（24h 合 main）", ["%s %s" % (h, s[:80]) for h, s in done24], "done"),
)
open(OUT, "w", encoding="utf-8").write(htmldoc)
print("board -> %s | 挂单 %d · 进行 %d · 受阻 %d · 完成 %d" % (OUT, len(claim_items), len(doing), len(blocked), len(done24)))
