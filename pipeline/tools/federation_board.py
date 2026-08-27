# -*- coding: utf-8 -*-
"""Fluxus 联邦控制台 v3 —— 侧栏多页应用（单文件），数据源 = origin/main + 本机定时任务目录。只读。
用法: python3 federation_console.py <repo> <out.html>
"""
import subprocess, sys, json, re, html, os, datetime, collections

REPO, OUT = sys.argv[1], sys.argv[2]
E = html.escape

def git(*a):
    return subprocess.run(["git", "-C", REPO] + list(a), capture_output=True, text=True).stdout

def show(p):
    return git("show", "origin/main:" + p)

now = datetime.datetime.now()
TODAY = now.strftime("%m-%d")

ROSTER = [
    ("DATA ALEX", "数据端", "每晚数据管线与 26 个 output；契约 §七 的主要收件人", "data/output · data/history · pipeline/screeners|tickers|adapters", ["feat(", "fix(watchlist", "fix(schema", "data(", "chore: market", "screener", "数据端", "alex", "groups_history"]),
    ("UI Claire", "前端", "Dashboard React 前端；按文件分工不按话题", "frontend/", ["frontend", "claire", "前端", "ui("]),
    ("RND Linda", "模型 R&D", "四盏灯 regime、GEX、量化模型与交易数据分析", "data/history/regime_ledger.csv · 模型研究目录", ["regime", "gex", "lamp", "linda", "风险线"]),
    ("Studio Q", "内容成稿", "课程/视频/Substack 成稿与数据艺术——笔在这条线", "Fluxus_Substack · Fluxus_Brand/templates|record|copybook", ["studio", "draft", "substack", "mrna", "成稿", "letter"]),
    ("Marketing Steve", "创意营销", "调研/五道闸审稿/品牌视觉/X 日常；不写成稿", "Fluxus_Brand/research|voice|ops|visual · data/content", ["steve", "material(", "fix(posts", "brief", "post:", "调研", "research("]),
    ("Nighty Zac", "夜间自学", "04:32 JST 唯一动手窗口：测试/研究/收藏夹/UI 预览稿", "data/research（night_reports/collection/ui_previews）", ["night(", "prereg(", "collect(", "preview(", "tests(", "adr", "vcp", "amplitude", "stockbee", "zac"]),
    ("Plumber Joe", "可靠性巡检", "07:20 JST 数据晨检；全联邦天然的 Gate", "incidents · DATA_RELIABILITY §六 · audit 工具", ["joe", "audit", "contracts(§", "巡检", "plumb"]),
    ("Growth Gary", "增长官", "会员台账/转化率/收入对账/canceling 哨位", "data/growth/", ["growth", "product:", "tool(post", "gary", "增长"]),
    ("OPS Fable", "联邦运维", "宪法/花名册/跨线协调/裁决投递/看板", "TEAM.md · PROJECTS.md · KNOWLEDGE.md · repo_health", ["ops", "rules(", "verdict(", "task(", "rescue(", "projects(", "governance", "board(", "team"]),
]

# ---------- lane 归属（v5：路径优先） ----------
# 路径规则**逐条抄自 TEAM.md 第 12-19 行的「文件边界」列**，不是照错误拟合出来的。
# 顺序 = 从具体到笼统，第一条命中即算该文件的票；owner=None 的是公箱（各线都能写），不投票。
PATH_RULES = [
    ("data/research/repo_health/", "OPS Fable"),
    ("data/research/night_reports/INBOX.md", None),
    ("data/reference/DATA_CONTRACTS.md", None),
    ("data/reference/DATA_RELIABILITY.md", None),
    ("Fluxus_Brand/ops/material_inbox.md", None),
    ("data/reference/incidents/", "Plumber Joe"),
    ("pipeline/tools/audit_", "Nighty Zac"),
    ("data/research/", "Nighty Zac"),
    ("data/growth/", "Growth Gary"),
    ("frontend/", "UI Claire"),
    ("data/history/regime_ledger.csv", "RND Linda"),
    ("pipeline/screeners/", "DATA ALEX"), ("pipeline/tickers/", "DATA ALEX"),
    ("pipeline/adapters/", "DATA ALEX"), ("data/output/", "DATA ALEX"),
    ("data/history/", "DATA ALEX"),
    ("Fluxus_Substack/", "Studio Q"), ("Fluxus_Brand/templates/", "Studio Q"),
    ("Fluxus_Brand/record/", "Studio Q"), ("Fluxus_Brand/copybook/", "Studio Q"),
    ("Fluxus_Brand/", "Marketing Steve"), ("Fluxus_Marketing_Visual_Design/", "Marketing Steve"),
    ("visuals/", "Marketing Steve"), ("data/content/", "Marketing Steve"),
    ("TEAM.md", "OPS Fable"), ("CLAUDE.md", "OPS Fable"), (".claude/agents/", "OPS Fable"),
    ("KNOWLEDGE.md", "OPS Fable"), ("PROJECTS.md", "OPS Fable"), ("NOW.md", "OPS Fable"),
    ("pipeline/tools/federation_board.py", "OPS Fable"),
]

# 「→ 收件人」别名：契约行/门铃的 lane 是**被指派的那条线**，不是写这条行的人。
ARROW_ALIAS = [
    ("UI Claire", "UI Claire"), ("前端", "UI Claire"),
    ("DATA ALEX", "DATA ALEX"), ("数据端", "DATA ALEX"),
    ("RND Linda", "RND Linda"), ("风险线", "RND Linda"),
    ("模型 R&D", "RND Linda"), ("模型R&D", "RND Linda"),
    ("Studio Q", "Studio Q"), ("StudioQ", "Studio Q"),
    ("Marketing Steve", "Marketing Steve"),
    ("Nighty Zac", "Nighty Zac"), ("夜间组", "Nighty Zac"),
    ("Plumber Joe", "Plumber Joe"),
    ("OPS Fable", "OPS Fable"), ("OPS", "OPS Fable"),
    ("Growth Gary", "Growth Gary"), ("增长官", "Growth Gary"),
]


def lane_of_paths(paths):
    """按改动文件投票定线；公箱文件不投票。无票或平票 -> None（交给文本兜底）。"""
    votes = collections.Counter()
    for p in paths or []:
        for pref, owner in PATH_RULES:
            if p.startswith(pref):
                if owner:
                    votes[owner] += 1
                break
    if not votes:
        return None
    top = votes.most_common()
    if len(top) > 1 and top[0][1] == top[1][1]:
        return None
    return top[0][0]


def lane_of_arrow(text):
    """解析「→ X:」「-> X:」，取箭头后的收件人。取不到返回 None。"""
    m = re.search(r"(?:→|->)\s*([^:：\n]{0,40})", text)
    if not m:
        return None
    head = m.group(1)
    hits = [(head.find(a), lane) for a, lane in ARROW_ALIAS if a in head]
    return min(hits)[1] if hits else None


def lane_of(text):
    """兜底：关键词。**按在文本里出现的位置取最早的那个**，不按花名册顺序——
    否则「建议 Joe 认领」「Zac 卡改为…」这类顺带提到的人名会盖过真正的归属方。"""
    t = text.lower()
    best = None
    for name, _, _, _, keys in ROSTER:
        for k in keys:
            i = t.find(k)
            if i >= 0 and (best is None or i < best[0]):
                best = (i, name)
    return best[1] if best else "联邦"


def lane_for(text, paths=None):
    """总入口：路径 > 箭头收件人 > 关键词。"""
    return lane_of_paths(paths) or lane_of_arrow(text) or lane_of(text)

# ---------- git 数据 ----------
# 一次 git log 同时取 commit 元信息与改动路径（不为每个 commit 单独起进程）
_raw = git("log", "origin/main", "--since=14 days ago", "--name-only",
           "--format=%x00%h|%ad|%s", "--date=format:%m-%d %H:%M")
log14, commit_paths, _cur = [], {}, None
for _l in _raw.split("\n"):
    if _l.startswith("\x00"):
        _cur = _l[1:].split("|", 2)
        log14.append(_cur)
        commit_paths[_cur[0]] = []
    elif _l.strip() and _cur:
        commit_paths[_cur[0]].append(_l.strip())
by_day = collections.Counter(ad.split(" ")[0] for _, ad, _ in log14)
lane_7d = collections.Counter()
lane_last, lane_today = {}, collections.Counter()
for h, ad, s in log14:
    ln = lane_for(s, commit_paths.get(h))
    days_ago = (now - datetime.datetime.strptime("2026-" + ad, "%Y-%m-%d %H:%M")).days
    if days_ago < 7:
        lane_7d[ln] += 1
        lane_last.setdefault(ln, (ad, s, h))
    if ad.split(" ")[0] == TODAY:
        lane_today[ln] += 1

cards = []
cid = [0]
def add(col, pri, title, src, lane=None, date="", paths=None):
    cid[0] += 1
    cards.append(dict(id="K%03d" % cid[0], col=col, pri=pri,
                      lane=lane or lane_for(title, paths), t=title.strip()[:170], src=src, d=date))

reports = sorted(re.findall(r"night_reports/(2026-\d\d-\d\d)\.md", git("ls-tree", "-r", "--name-only", "origin/main", "data/research/night_reports/")))
if reports:
    latest = show("data/research/night_reports/%s.md" % reports[-1])
    sec = re.search(r"门铃待按[^\n]*\n(.*?)(\n## |\Z)", latest, re.S)
    if sec:
        for who, what in re.findall(r"\| *\*?\*?([^|*]+?)\*?\*? *\| *([^|]+?) *\|", sec.group(1)):
            if "收件人" in who or "---" in who:
                continue
            add("claim", 1, what.strip(), "晨报门铃 %s" % reports[-1][5:], lane_for(who), reports[-1][5:])

for b in git("branch", "-r", "--no-merged", "origin/main").splitlines():
    b = b.strip()
    if not b or "HEAD" in b or "archive/" in b:
        continue
    n = git("rev-list", "--count", "origin/main.." + b).strip()
    if n and n != "0":
        last = git("log", "-1", "--format=%ad|%s", "--date=format:%m-%d", b).strip().split("|", 1)
        bpaths = git("diff", "--name-only", "origin/main..." + b).split()
        add("claim", 2, "%s（+%s）%s" % (b.replace("origin/", ""), n, ("· " + last[1][:60]) if len(last) > 1 else ""),
            "待合分支", lane_for(b + (last[1] if len(last) > 1 else ""), bpaths), last[0] if last else "")

contracts = show("data/reference/DATA_CONTRACTS.md").splitlines()
for i, line in enumerate(contracts):
    if not re.match(r"^- \[(?:20)?\d\d-", line) or "✅" in line or "~~" in line:
        continue
    # 下一行若是「↳ 已执行/裁决」类回执，视为已办结
    nxt = contracts[i + 1] if i + 1 < len(contracts) else ""
    if "↳" in nxt and ("✅" in nxt or "已执行" in nxt or "裁决" in nxt):
        continue
    date = (re.search(r"\[(?:2026-)?(\d\d-\d\d)\]", line) or [None, ""])[1]
    txt = re.sub(r"[*`]", "", line)
    head = txt[txt.index("]") + 1:].strip()[:150]
    if "待 Andy" in line or ("Andy 拍板" in line and "已" not in line):
        add("blocked", 0, head, "契约行", lane_for(line), date)
    elif "→" in txt[:60]:
        add("claim", 3, head, "契约行", lane_for(txt), date)

nowmd = show("NOW.md")
for line in nowmd.splitlines():
    if "待你" in line and "- [ ]" in line:
        add("blocked", 0, re.sub(r"[*\[\]~]", "", line.replace("- [ ]", "")).strip()[:150], "NOW.md", "OPS Fable", "")

for h, ad, s in log14:
    hrs = (now - datetime.datetime.strptime("2026-" + ad, "%Y-%m-%d %H:%M")).total_seconds() / 3600
    if hrs < 24:
        add("done", 9, s[:150], h, lane_for(s, commit_paths.get(h)), ad)
    if ad.split(" ")[0] == TODAY:
        add("doing", 9, s[:130], h, lane_for(s, commit_paths.get(h)), ad.split(" ")[1])

gate = re.search(r"周关卡[^\n]*?(\d)\s*/\s*5", nowmd)
gate_n = int(gate.group(1)) if gate else None

# ---------- 定时任务 ----------
tasks = []
troot = os.path.expanduser("~/.claude/scheduled-tasks")
if os.path.isdir(troot):
    for d in sorted(os.listdir(troot)):
        sk = os.path.join(troot, d, "SKILL.md")
        if d.startswith("_") or not os.path.isfile(sk):
            continue
        head = open(sk, encoding="utf-8").read(1200)
        desc = (re.search(r"description:\s*(.+)", head) or [None, d])[1].strip()
        when = (re.search(r"(每日|每周[一二三四五六日]|周[一二三四五六日]-?[一二三四五六日]?|每周)[^，·（)]*?(\d\d?:\d\d)\s*(JST)?", desc) or [None])
        sched = when.group(0) if when and when != [None] and hasattr(when, "group") else ""
        tasks.append(dict(name=d, desc=desc[:120], sched=sched, personal=d.startswith("personal") or d.startswith("remind") or "mrna" in d))

# ---------- 知识库计数 ----------
tree = git("ls-tree", "-r", "--name-only", "origin/main").splitlines()
def cnt(prefix):
    return sum(1 for f in tree if f.startswith(prefix))
KB = [
    ("权威层", "规矩与宪法，冲突时以此为准", [("CLAUDE.md 宪法", 1), ("TEAM.md / NOW.md / PROJECTS.md / KNOWLEDGE.md", 4), ("DATA_CONTRACTS 契约", 1), ("DATA_RELIABILITY + RESEARCH_PROTOCOL", 2)]),
    ("结论层", "量过的事实（引用必须带日期）", [("研究结论台账 claims.jsonl", 1), ("研究目录文件", cnt("data/research/")), ("夜间晨报", len(reports))]),
    ("教训层", "防坑账与事故档", [("事故档 incidents/", cnt("data/reference/incidents/")), ("memory 防坑账（会话侧）", "60+")]),
    ("台账层", "append-only 流水", [("posts.csv 发布记录", 1), ("素材箱 material_inbox", 1), ("growth 台账文件", cnt("data/growth/"))]),
    ("资料层", "只读引用区", [("JeffSun_Wiki", cnt("JeffSun_Wiki/")), ("Fluxus_References", cnt("Fluxus_References/")), ("对外 Library", cnt("data/output/library/")), ("品牌目录 Fluxus_Brand", cnt("Fluxus_Brand/"))]),
]

# ---------- infra ----------
last_data = next(((ad, s) for _, ad, s in [(h, a, s) for h, a, s in log14] if "chore: market data" in s), None)
infra = [
    ("数据 cron（GitHub Actions 21:30 UTC）", "最近落数据 %s" % (last_data[0] if last_data else "未见"), "ok" if last_data else "warn"),
    ("Vercel 自动部署", "跟随 main push（本页不直连，状态未测量）", "na"),
    ("GAS / Google Sheets 回拉", "挂 run_all（本页不直连，状态未测量）", "na"),
    ("本机（唯一节点 MacBook）", "定时任务 App 开着才跑", "ok"),
]

counts = {c: sum(1 for k in cards if k["col"] == c) for c in ["claim", "doing", "blocked", "done"]}

# ---------- 生意数据 ----------
def last_nonempty(csv_text, col):
    lines = [l for l in csv_text.splitlines() if l.strip()]
    hdr = lines[0].split(",")
    if col not in hdr:
        return None
    i = hdr.index(col)
    for l in reversed(lines[1:]):
        parts = l.split(",")
        if i < len(parts) and parts[i].strip():
            return parts[i].strip()
    return None

met = show("data/growth/metrics.csv")
BIZ = dict(
    members=last_nonempty(met, "whop_members") or "—",
    mrr=last_nonempty(met, "mrr_usd") or "—",
    discord=last_nonempty(met, "discord_members") or "—",
    followers=last_nonempty(met, "x_followers") or "未测量",
    subs=last_nonempty(met, "substack_subs") or "未测量",
)
posts_csv = show("data/content/posts.csv").splitlines()[1:]
week_start = (now - datetime.timedelta(days=now.weekday())).strftime("%Y-%m-%d")
posts_week = sum(1 for l in posts_csv if len(l.split(",")) > 1 and l.split(",")[1] >= week_start)
views7 = 0
for l in posts_csv:
    p = l.split(",")
    if len(p) > 4 and p[1] >= (now - datetime.timedelta(days=7)).strftime("%Y-%m-%d"):
        try:
            views7 += int(p[4])
        except Exception:
            pass

projmd = show("PROJECTS.md")
PROJS = []
for m in re.finditer(r"^### (P\d) · ([^（(\n]+)[（(]([^）)\n]*)[）)]?([^\n]*)\n((?:(?!^###).*\n)*?)", projmd, re.M):
    pid, pname, prole, pstar, body = m.group(1), m.group(2).strip(), m.group(3).strip(), m.group(4), m.group(5)
    st = (re.search(r"- 状态[：:](.+)", body) or re.search(r"- \*\*状态（?([^\n]+)", body) or [None, ""])[1]
    st = re.sub(r"[*`]", "", st).strip()[:180]
    light = "🟢" if "🟢" in st or "自转" in st else ("🔴" if ("空" in st[:14] or "没落地" in st) else ("⏸" if ("冻结" in st or "未定" in st) else "🟡"))
    PROJS.append((pid, pname, prole, "⭐" in pstar, light, st or "（无状态行）"))

now_main = (re.search(r"## 本周主线[^\n]*\n\n(.+)", nowmd) or [None, ""])[1]
now_main = re.sub(r"[*`]", "", now_main).strip()[:140]
today_one = (re.search(r"## 今天的一件事\s*\n+([^#\n][^\n]*)", nowmd) or [None, ""])[1]
today_one = re.sub(r"[*`]", "", today_one).strip()[:140]

FUNNEL = [
    ("内容", "%d 件 / 本周" % posts_week, "posts.csv"),
    ("流量", "%s views / 7d" % (format(views7, ",") if views7 else "—"), "X"),
    ("引流", "Substack %s" % BIZ["subs"], "站"),
    ("落地", "%s 会员 · MRR $%s" % (BIZ["members"], BIZ["mrr"]), "Whop"),
    ("服务", "Discord %s 人" % BIZ["discord"], "139 频道"),
    ("售后", "canceling 哨位在册", "Gary"),
]

# ================= HTML =================
def kpi(v, label, color=""):
    return '<div class="kpi"><b style="%s">%s</b><span>%s</span></div>' % (("color:" + color) if color else "", v, label)

def section(title, body, extra=""):
    return '<div class="panel"><div class="ph">%s %s</div>%s</div>' % (title, extra, body)

def cardh(c, showlane=True):
    PRI = {0: ("P0", "var(--p0)"), 1: ("P1", "var(--p1)"), 2: ("P2", "var(--p2)"), 3: ("P3", "var(--p3)"), 9: ("", "var(--don)")}
    pl, pc = PRI[c["pri"]]
    return ('<div class="k" style="--pc:%s" data-lane="%s" data-pri="%s"><div class="m">%s<span class="kid">%s</span>%s</div>%s<span class="src">%s%s</span></div>'
            % (pc, E(c["lane"]), c["pri"],
               ('<span class="pid">%s</span>' % pl) if pl else "", c["id"],
               ('<span class="dt">%s</span>' % E(c["d"])) if c["d"] else "",
               E(c["t"]),
               E(c["src"]), (" · " + E(c["lane"])) if showlane else ""))

# --- 页1 今日（生意优先） ---
blocked_cards = [c for c in cards if c["col"] == "blocked"]
today_stream = [c for c in cards if c["col"] == "doing"][:8]
p_home = (
    '<div class="kpis">' + kpi(BIZ["members"], "会员") + kpi("$" + str(BIZ["mrr"]), "MRR") +
    kpi("%d/5" % posts_week, "本周发布") + kpi(format(views7, ",") if views7 else "—", "7d views") +
    kpi(counts["blocked"], "等你拍板", "var(--blk)") + "</div>" +
    section("本周主线", '<div>%s</div><div class="mut" style="margin-top:6px">今天的一件事：%s</div>' % (E(now_main or "（NOW.md 未写）"), E(today_one or "（未写）"))) +
    section("⚠ 等你拍板", "".join(cardh(c) for c in blocked_cards) or '<div class="empty">现在没有等你的事</div>') +
    section("AI 今日已落地（详见任务看板）", "".join(cardh(c) for c in today_stream) or '<div class="empty">今天还没有 commit</div>'))

# --- 页1.5 项目 ---
fun = "".join('<div class="fstage"><div class="fname">%s</div><div class="fval">%s</div><div class="fsrc">%s</div></div><div class="farrow">→</div>' % (n, E(v), E(s)) for n, v, s in FUNNEL)
fun = fun.rsplit('<div class="farrow">', 1)[0]
pcards = ""
for pid, pname, prole, star, light, st in PROJS:
    pcards += ('<div class="agent"><div class="ah">%s <b>%s · %s</b>%s<span class="mut" style="margin-left:8px">%s</span></div>'
               '<div class="ab">%s</div></div>' % (light, pid, E(pname), " ⭐" if star else "", E(prole), E(st)))
p_projects = (section("生意漏斗（内容 → 售后）", '<div class="funnel">%s</div>' % fun) +
              '<div class="mut" style="margin:2px 0 10px">项目档案实时映射自 PROJECTS.md——状态行过期时该修的是档案，不是看板。</div>' +
              '<div class="agrid">%s</div>' % pcards)

# --- 页2 看板 ---
COLS = [("claim", "待认领 · 挂单板"), ("doing", "进行中 · 今日"), ("blocked", "等 Andy 拍板"), ("done", "已完成 · 24h")]
kb_cols = ""
for key, label in COLS:
    items = sorted([c for c in cards if c["col"] == key], key=lambda c: c["pri"])
    inner = ""
    if key == "claim":
        bylane = collections.OrderedDict()
        for c in items:
            bylane.setdefault(c["lane"], []).append(c)
        for ln in bylane:
            inner += '<div class="lgroup">%s · %d</div>' % (E(ln), len(bylane[ln])) + "".join(cardh(c, False) for c in bylane[ln])
    else:
        inner = "".join(cardh(c, False) for c in items)
    kb_cols += '<div class="col"><div class="colh">%s<span class="n">%d</span></div>%s</div>' % (label, len(items), inner or '<div class="empty">（空）</div>')
p_board = ('<div class="ctrl"><input id="q" placeholder="搜索卡片…"><span class="chip pf" data-p="0">P0</span><span class="chip pf" data-p="1">P1</span><span class="chip pf" data-p="2">P2</span><span class="chip pf" data-p="3">P3</span></div>'
           '<div class="board">' + kb_cols + "</div>")

# --- 页3 泳道 ---
rows = ""
for name, role, _, _, _ in ROSTER:
    claims = [c for c in cards if c["col"] == "claim" and c["lane"] == name]
    dones = [c for c in cards if c["col"] == "done" and c["lane"] == name][:3]
    rows += ('<tr><td><b>%s</b><div class="mut">%s</div></td><td>%s</td><td class="num">%s</td><td>%s</td></tr>'
             % (name, role,
                "".join('<span class="tag">%s</span>' % E(c["t"][:46]) for c in claims[:4]) or '<span class="mut">—</span>',
                lane_today.get(name, 0) or "—",
                "".join('<span class="tag don">%s</span>' % E(c["t"][:46]) for c in dones) or '<span class="mut">—</span>'))
p_lanes = section("九线泳道", '<table><thead><tr><th>线</th><th>在手挂单</th><th>今日</th><th>近期完成</th></tr></thead><tbody>%s</tbody></table>' % rows)

# --- 页4 智能体 ---
ag = ""
for name, role, duty, files, _ in ROSTER:
    last = lane_last.get(name)
    t_for = [t for t in tasks if not t["personal"] and (name.split(" ")[1].lower() in t["name"] or name.split(" ")[0].lower() in t["name"] or (name == "Growth Gary" and "growth" in t["name"]) or (name == "OPS Fable" and "fable" in t["name"]))]
    dot = "🟢" if lane_today.get(name) else ("🟡" if last else "⚪")
    ag += ('<div class="agent"><div class="ah">%s <b>%s</b><span class="mut">· %s</span></div>'
           '<div class="ab">%s</div><div class="af">边界：%s</div>%s'
           '<div class="al">%s</div></div>'
           % (dot, name, role, E(duty), E(files),
              "".join('<div class="af">⏰ %s</div>' % E(t["sched"] or t["desc"][:60]) for t in t_for),
              ("最近落地 %s · %s" % (last[0], E(last[1][:56]))) if last else "近 7 天无落地"))
p_agents = '<div class="agrid">%s</div>' % ag

# --- 页5 运营 ---
days = [(now - datetime.timedelta(days=i)).strftime("%m-%d") for i in range(13, -1, -1)]
mx = max([by_day.get(d, 0) for d in days] + [1])
bars = "".join('<div class="bar" title="%s · %d"><i style="height:%d%%"></i><s>%s</s></div>' % (d, by_day.get(d, 0), round(by_day.get(d, 0) / mx * 100), d[3:]) for d in days)
rank = sorted(lane_7d.items(), key=lambda kv: -kv[1])
rank_h = "".join('<tr><td class="num">%d</td><td>%s</td><td class="num">%d</td></tr>' % (i + 1, n, v) for i, (n, v) in enumerate(rank[:9]))
p_ops = (section("14 天吞吐（commit 到 main）", '<div class="chart">%s</div>' % bars) +
         section("7 天完成排行", '<table><thead><tr><th>#</th><th>线</th><th>commit</th></tr></thead><tbody>%s</tbody></table>' % rank_h) +
         (section("🎮 发布关卡", '<div class="gatebar"><div style="width:%d%%"></div></div><div class="mut">本周 %d / 5</div>' % (gate_n * 20, gate_n)) if gate_n is not None else ""))

# --- 页6 知识库 ---
kbh = ""
for layer, sub, items in KB:
    rows_k = "".join('<tr><td>%s</td><td class="num">%s</td></tr>' % (E(str(n)), v) for n, v in items)
    kbh += '<div class="panel"><div class="ph">%s <span class="mut" style="font-weight:400">· %s</span></div><table><tbody>%s</tbody></table></div>' % (layer, sub, rows_k)
p_kb = '<div class="mut" style="margin-bottom:12px">地图版真理索引 · 全文在仓库根 <b>KNOWLEDGE.md</b> · 全文检索不存在（靠 grep + 本图）</div>' + kbh

# --- 页7 基础设施 ---
ti = "".join('<tr><td><b>%s</b><div class="mut">%s</div></td><td>%s</td></tr>' % (t["name"], E(t["desc"][:90]), E(t["sched"] or "—")) for t in tasks if not t["personal"])
inf = "".join('<tr><td>%s</td><td>%s</td><td>%s</td></tr>' % (n, E(d), {"ok": "🟢", "warn": "🟠", "na": "◻︎ 未测量"}[s]) for n, d, s in infra)
p_infra = (section("定时任务（工作线）", '<table><thead><tr><th>任务</th><th>排程</th></tr></thead><tbody>%s</tbody></table>' % ti) +
           section("链路健康", '<table><thead><tr><th>链路</th><th>说明</th><th>状态</th></tr></thead><tbody>%s</tbody></table>' % inf))

PAGES = [
    ("home", "🏠", "今日", "TODAY", "生意读数 · 该你做的 · AI 交付", p_home, "生意"),
    ("projects", "📈", "项目", "BUSINESS PORTFOLIO", "P0–P7 档案与六环漏斗——你的生意长什么样", p_projects, "生意"),
    ("ops", "📊", "运营看板", "OPERATIONS · GLOBAL", "吞吐 · 完成排行 · 发布关卡", p_ops, "生意"),
    ("board", "🗂", "任务看板", "TASK BOARD · KANBAN", "挂单不挂人：待认领 → 进行中 → 拍板 → 完成", p_board, "AI 引擎室"),
    ("lanes", "🤝", "协作泳道", "MULTI-LANE COLLABORATION", "九条线各自在手的工作与最近交付", p_lanes, "AI 引擎室"),
    ("agents", "🤖", "智能体", "AGENT ROSTER", "花名册：职责 · 文件边界 · 心跳 · 排程", p_agents, "AI 引擎室"),
    ("kb", "📚", "知识库", "KNOWLEDGE SOURCES", "真理地图：哪类问题去哪查", p_kb, "AI 引擎室"),
    ("infra", "🛠", "基础设施", "NODES & ROUTINES", "定时任务与链路健康", p_infra, "AI 引擎室"),
]

nav, lastgrp = "", None
for pid, ic, label, _, _, _, grp in PAGES:
    if grp != lastgrp:
        nav += '<div class="navh">%s</div>' % grp
        lastgrp = grp
    nav += '<div class="ni" data-p="%s"><span>%s</span>%s</div>' % (pid, ic, label)
pages_html = "".join('<div class="page" id="pg-%s"><div class="eyebrow">%s</div><h1>%s</h1><div class="sub">%s</div>%s</div>' % (pid, eb, label, sub, body) for pid, ic, label, eb, sub, body, _ in PAGES)

DOC = """<!doctype html><html lang="zh"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Fluxus 联邦控制台</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Serif:wght@500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
:root{--bg:#f7f6f3;--side:#efede6;--panel:#fdfdfb;--inset:#f2f0ea;--ink:#1c1e21;--mut:#7d7b72;--line:#e2dfd6;
--acc:#2f4a4d;--p0:#8f6c1e;--p1:#34638c;--p2:#5b7263;--p3:#918d80;--blk:#a63d35;--don:#33684d;--p0bg:#f6efdc;--blkbg:#f8ebe9}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#13151a;--side:#181b21;--panel:#1e222a;--inset:#181b21;
--ink:#e7e5e0;--mut:#8d8b83;--line:#2b2f37;--acc:#8fb3b6;--p0:#c9a24a;--p1:#6f9cc4;--p2:#8aa693;--p3:#7d7a71;--blk:#c96a61;--don:#6fa588;--p0bg:#292314;--blkbg:#2c1c1a}}
:root[data-theme="dark"]{--bg:#13151a;--side:#181b21;--panel:#1e222a;--inset:#181b21;--ink:#e7e5e0;--mut:#8d8b83;--line:#2b2f37;
--acc:#8fb3b6;--p0:#c9a24a;--p1:#6f9cc4;--p2:#8aa693;--p3:#7d7a71;--blk:#c96a61;--don:#6fa588;--p0bg:#292314;--blkbg:#2c1c1a}
*{box-sizing:border-box;margin:0}
body{background:var(--bg);color:var(--ink);font:14px/1.55 "IBM Plex Sans",-apple-system,"PingFang SC",sans-serif;display:flex;min-height:100vh}
aside{width:216px;flex:none;background:var(--side);border-right:1px solid var(--line);padding:18px 12px;position:sticky;top:0;height:100vh}
.logo{font:600 15px "IBM Plex Serif",serif;padding:4px 10px 2px}
.logo .mut{display:block;font:400 10.5px "IBM Plex Sans";letter-spacing:.06em}
.ni{display:flex;gap:9px;align-items:center;padding:8px 10px;border-radius:7px;cursor:pointer;color:var(--mut);font-size:13px;margin-top:2px;user-select:none}
.ni span{width:18px;text-align:center}
.ni.on{background:var(--panel);color:var(--ink);font-weight:600;border:1px solid var(--line)}
.ni:not(.on):hover{color:var(--ink)}
.ni:focus-visible{outline:2px solid var(--acc)}
.navh{font:500 9.5px "IBM Plex Mono",monospace;letter-spacing:.16em;text-transform:uppercase;color:var(--mut);padding:14px 10px 4px}
.funnel{display:flex;gap:6px;align-items:stretch;flex-wrap:wrap}
.fstage{flex:1;min-width:118px;background:var(--inset);border:1px solid var(--line);border-radius:8px;padding:9px 11px}
.fname{font-size:10.5px;letter-spacing:.1em;text-transform:uppercase;color:var(--mut)}
.fval{font:600 14px/1.3 "IBM Plex Serif",serif;margin:3px 0 1px;font-variant-numeric:tabular-nums}
.fsrc{font-size:10px;color:var(--mut)}
.farrow{align-self:center;color:var(--mut)}
.foot{position:absolute;bottom:14px;left:12px;right:12px;font-size:10.5px;color:var(--mut);border-top:1px solid var(--line);padding-top:8px}
main{flex:1;padding:26px 32px 70px;min-width:0}
.page{display:none;max-width:1080px}.page.on{display:block}
.eyebrow{font:500 10.5px "IBM Plex Mono",monospace;letter-spacing:.16em;color:var(--mut)}
h1{font:600 24px/1.2 "IBM Plex Serif",serif;margin:4px 0 2px}
.sub{color:var(--mut);font-size:12.5px;margin-bottom:18px}
.kpis{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:16px}
.kpi{background:var(--panel);border:1px solid var(--line);border-radius:9px;padding:12px 18px;min-width:110px}
.kpi b{font:600 26px/1.1 "IBM Plex Serif",serif;display:block;font-variant-numeric:tabular-nums}
.kpi span{font-size:10.5px;color:var(--mut);letter-spacing:.1em;text-transform:uppercase}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:14px 16px;margin-bottom:14px}
.ph{font:600 13px "IBM Plex Sans";margin-bottom:10px;letter-spacing:.02em}
.empty{color:var(--mut);font-size:12.5px}
.k{background:var(--panel);border:1px solid var(--line);border-radius:7px;padding:8px 10px 8px 13px;margin-bottom:8px;position:relative;font-size:12.5px;line-height:1.45}
.k::before{content:"";position:absolute;left:0;top:0;bottom:0;width:3px;border-radius:7px 0 0 7px;background:var(--pc)}
.k .m{display:flex;gap:8px;align-items:baseline;flex-wrap:wrap;margin-bottom:2px}
.pid{font:500 10px "IBM Plex Mono",monospace;color:var(--pc);border:1px solid var(--pc);border-radius:3px;padding:0 4px}
.kid,.dt{font:400 10px "IBM Plex Mono",monospace;color:var(--mut)}.dt{margin-left:auto}
.src{display:block;margin-top:3px;font-size:10.5px;color:var(--mut)}
.board{display:grid;grid-template-columns:repeat(4,1fr);gap:13px;align-items:start}
@media(max-width:1100px){.board{grid-template-columns:1fr 1fr}}
.col{background:var(--inset);border:1px solid var(--line);border-radius:10px;padding:11px}
.colh{display:flex;justify-content:space-between;font-size:12.5px;font-weight:600;margin-bottom:9px}
.colh .n{color:var(--mut);font-family:"IBM Plex Mono",monospace;font-weight:400}
.col .k{background:var(--panel)}
.lgroup{font-size:10px;color:var(--mut);letter-spacing:.12em;text-transform:uppercase;margin:9px 2px 5px}
.ctrl{display:flex;gap:8px;margin-bottom:12px;align-items:center;flex-wrap:wrap}
#q{border:1px solid var(--line);background:var(--panel);color:var(--ink);border-radius:7px;padding:6px 11px;font:12.5px "IBM Plex Sans";width:230px}
.chip{border:1px solid var(--line);background:var(--panel);color:var(--mut);border-radius:999px;padding:3px 12px;font-size:12px;cursor:pointer;user-select:none}
.chip.on{border-color:var(--acc);color:var(--acc);font-weight:600}
table{width:100%;border-collapse:collapse;font-size:12.5px}
th,td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--line);vertical-align:top}
th{font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:var(--mut)}
tr:last-child td{border-bottom:none}
td.num{font-family:"IBM Plex Mono",monospace;font-variant-numeric:tabular-nums}
.mut{color:var(--mut);font-size:11.5px}
.tag{display:inline-block;background:var(--inset);border:1px solid var(--line);border-radius:5px;padding:1px 7px;margin:1px 3px 1px 0;font-size:11px}
.tag.don{border-color:var(--don);color:var(--don)}
.agrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:13px}
.agent{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:13px 15px}
.ah{font-size:13.5px;margin-bottom:6px}
.ab{font-size:12.5px;margin-bottom:6px}
.af{font-size:11px;color:var(--mut);margin-top:3px}
.al{font:400 10.5px "IBM Plex Mono",monospace;color:var(--mut);margin-top:8px;border-top:1px dashed var(--line);padding-top:7px}
.chart{display:flex;gap:6px;align-items:flex-end;height:130px;padding-top:8px}
.bar{flex:1;display:flex;flex-direction:column;justify-content:flex-end;align-items:center;gap:4px;height:100%}
.bar i{display:block;width:100%;max-width:34px;background:var(--p1);border-radius:3px 3px 0 0;min-height:2px}
.bar s{text-decoration:none;font:400 9.5px "IBM Plex Mono",monospace;color:var(--mut)}
.gatebar{height:8px;background:var(--inset);border:1px solid var(--line);border-radius:4px;overflow:hidden;margin-bottom:6px}
.gatebar div{height:100%;background:var(--don)}
.k[data-pri="0"]{background:var(--p0bg)}
</style></head><body>
<aside><div class="logo">Fluxus 联邦<span class="mut">console · 只读 · __TS__</span></div>
<nav>__NAV__</nav>
<div class="foot">数据源 = origin/main + 定时任务清单。批注：选中卡片文字开评论（写卡号），@claude 后 OPS 能读到。说「刷新看板」即更新本页。</div></aside>
<main>__PAGES__</main>
<script>
const nis=[...document.querySelectorAll(".ni")],pgs=[...document.querySelectorAll(".page")];
function go(p){nis.forEach(n=>n.classList.toggle("on",n.dataset.p===p));pgs.forEach(g=>g.classList.toggle("on",g.id==="pg-"+p));location.hash=p;window.scrollTo(0,0)}
nis.forEach(n=>{n.tabIndex=0;n.onclick=()=>go(n.dataset.p);n.onkeydown=e=>{if(e.key==="Enter")go(n.dataset.p)}});
go(location.hash.replace("#","")||"home");
const q=document.getElementById("q");let pf=null;
function filt(){document.querySelectorAll("#pg-board .k").forEach(k=>{
 const okQ=!q.value||k.textContent.toLowerCase().includes(q.value.toLowerCase());
 const okP=pf===null||k.dataset.pri===String(pf);
 k.style.display=(okQ&&okP)?"":"none";});}
if(q){q.oninput=filt;document.querySelectorAll(".pf").forEach(c=>{c.onclick=()=>{const p=+c.dataset.p;pf=(pf===p)?null:p;document.querySelectorAll(".pf").forEach(x=>x.classList.toggle("on",+x.dataset.p===pf));filt();};});}
</script></body></html>"""

out = DOC.replace("__TS__", now.strftime("%m-%d %H:%M")).replace("__NAV__", nav).replace("__PAGES__", pages_html)
open(OUT, "w", encoding="utf-8").write(out)
print("console -> %s | cards=%d tasks=%d" % (OUT, len(cards), len(tasks)))
