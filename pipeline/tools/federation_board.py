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
    ("Studio Q", "课程线", "课程整理与设计、视频生成工作流、试读本（08-31 拆分后瘦身，不碰对外 marketing）", "~/Documents/SwingMasterclass · vault 20_Course/", ["studio", "masterclass", "course", "课程", "试读", "讲义"]),
    ("Writer Mia", "写作线", "X / Substack / newsletter 一切对外成稿、声音库维护——笔在这条线", "Fluxus_Substack · Fluxus_Brand/voice|templates|copybook|record|site", ["mia", "content(#", "draft", "substack", "mrna", "成稿", "letter", "voice(", "写作线"]),
    ("Visual Vera", "视觉线", "品牌视觉 MR. FLUXUS、海报系统、图像语料、数据艺术可视化", "Fluxus_Brand/visual · Fluxus_Marketing_Visual_Design · visuals/", ["vera", "visual", "poster", "海报", "mr_fluxus", "mr. fluxus", "视觉线", "配图"]),
    ("Marketing Steve", "编辑部/运营", "对外调研、选题与 brief、五道闸审稿（不改原稿）、发布运营与记账、夜间六站产线工头", "Fluxus_Brand/research|ops|brain · BRAIN.md · data/content · Fluxus_Receipts", ["steve", "material(", "fix(posts", "brief", "post:", "调研", "research(", "brain", "campaign", "gate("]),
    ("Nighty Zac", "夜间自学", "04:32 JST 唯一动手窗口：测试/研究/收藏夹/UI 预览稿", "data/research（night_reports/collection/ui_previews）", ["night(", "prereg(", "collect(", "preview(", "tests(", "adr", "vcp", "amplitude", "stockbee", "zac"]),
    ("Plumber Joe", "可靠性巡检", "07:20 JST 数据晨检；全联邦天然的 Gate", "incidents · DATA_RELIABILITY §六 · audit 工具", ["joe", "audit", "contracts(§", "巡检", "plumb"]),
    ("Growth Gary", "增长官", "会员台账/转化率/收入对账/canceling 哨位", "data/growth/", ["growth", "product:", "tool(post", "gary", "增长"]),
    ("OPS Fable", "联邦运维", "宪法/花名册/跨线协调/裁决投递/看板", "TEAM.md · PROJECTS.md · KNOWLEDGE.md · repo_health", ["ops", "rules(", "verdict(", "task(", "rescue(", "projects(", "governance", "board(", "team"]),
]

# ---------- lane 归属（v6：路径优先；08-31 内容侧拆四线后重抄） ----------
# 路径规则**逐条抄自 TEAM.md 花名册的「文件边界」列与「资料区与单一写入方」节**，不是照错误拟合出来的。
# 顺序 = 从具体到笼统，第一条命中即算该文件的票；owner=None 的是公箱（各线都能写），不投票。
# ⚠️ 08-31 之前本表把 `Fluxus_Substack/` 与 `Fluxus_Brand/*` 大半判给 Studio Q，
#    而 TEAM.md 当天已把内容侧拆成 Steve(选题/审稿) → Mia(执笔) → Vera(视觉)，Studio Q 收窄为课程线。
#    后果实测：08-31 当天 9 个 `content(#001)` commit 全部误记到 Studio Q 名下。
PATH_RULES = [
    ("data/research/repo_health/", "OPS Fable"),
    ("data/research/night_reports/INBOX.md", None),
    ("data/reference/DATA_CONTRACTS.md", None),
    ("data/reference/DATA_RELIABILITY.md", None),
    ("Fluxus_Brand/ops/material_inbox.md", None),
    ("Fluxus_Brand/voice/verdicts.jsonl", None),
    ("data/reference/incidents/", "Plumber Joe"),
    ("pipeline/tools/audit_", "Nighty Zac"),
    ("data/research/", "Nighty Zac"),
    ("data/growth/", "Growth Gary"),
    ("frontend/", "UI Claire"),
    ("data/history/regime_ledger.csv", "RND Linda"),
    ("pipeline/screeners/", "DATA ALEX"), ("pipeline/tickers/", "DATA ALEX"),
    ("pipeline/adapters/", "DATA ALEX"), ("data/output/", "DATA ALEX"),
    ("data/history/", "DATA ALEX"),
    # --- 写作线 Writer Mia（08-31 新设）---
    ("Fluxus_Substack/", "Writer Mia"),
    ("Fluxus_Brand/voice/", "Writer Mia"), ("Fluxus_Brand/templates/", "Writer Mia"),
    ("Fluxus_Brand/copybook/", "Writer Mia"), ("Fluxus_Brand/record/", "Writer Mia"),
    ("Fluxus_Brand/site/", "Writer Mia"),
    # --- 视觉线 Visual Vera（08-31 新设）---
    ("Fluxus_Brand/visual/", "Visual Vera"),
    ("Fluxus_Marketing_Visual_Design/", "Visual Vera"),
    ("visuals/", "Visual Vera"), ("Fluxus_DataArt/", "Visual Vera"),
    # --- 编辑部/运营 Marketing Steve ---
    ("Fluxus_Brand/research/", "Marketing Steve"), ("Fluxus_Brand/ops/", "Marketing Steve"),
    ("Fluxus_Brand/brain/", "Marketing Steve"), ("Fluxus_Brand/BRAIN.md", "Marketing Steve"),
    ("Fluxus_Brand/", "Marketing Steve"),   # Fluxus_Brand 兜底（未列二级目录）
    ("data/content/", "Marketing Steve"), ("Fluxus_Receipts/", "Marketing Steve"),
    # --- 课程线 Studio Q（仓外为主，留规则以防 vault 入库）---
    ("FluxusTrading_Obsidian/20_Course/", "Studio Q"), ("SwingMasterclass/", "Studio Q"),
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
    ("Studio Q", "Studio Q"), ("StudioQ", "Studio Q"), ("课程线", "Studio Q"),
    ("Writer Mia", "Writer Mia"), ("Mia", "Writer Mia"), ("写作线", "Writer Mia"),
    ("Visual Vera", "Visual Vera"), ("Vera", "Visual Vera"), ("视觉线", "Visual Vera"),
    ("Marketing Steve", "Marketing Steve"), ("Steve", "Marketing Steve"), ("编辑部", "Marketing Steve"),
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


# ---------- 两种语义，两个函数（Andy 08-31 裁决）----------
# 裁决原文：看板上「线」的意思是**「谁欠这件事、谁该动手」**（收件人语义），
# **不是**「谁做了这件事」（作者语义）。
#
# 此前只有一个 `lane_for(text, paths)` 两边共用：`done`/`doing` 列问的是「谁提交的」，
# 而 `claim`/`blocked` 列问的是「谁该动手」——**同一个函数回答了两个不同的问题**。
# 两名独立盲判 agent 的 7 处分歧全落在这里；Zac 08-28 原话：「没定义之前这部分准确率量不出来，
# 不是量不出，是题目没答案。」现在有答案了，所以拆开——**不加注释了事，让调用点必须显式选一个**。
#
# 两者的实质分歧就是那个箭头：
#   commit `contracts(§7): → 前端 P/L 1D 把跳空算成盈亏` 是 **Joe 写的**（作者），
#   要动手修的是 **UI Claire**（收件人）。旧的 `lane_for` 把这条 commit 记在 Claire 名下，
#   于是「7 天完成排行」给 Claire 记了一笔她没干的活，而 Joe 少了一笔。


def lane_authored_by(text, paths=None):
    """**谁做了这件事**（作者语义）。只用于确实要问作者的地方：done / doing 列的「谁提交的」。

    路径 > 关键词。**故意不看「→ 收件人」箭头**——箭头指的是谁该动手，
    把它算进作者会把「Joe 转投递给前端」的 commit 记到前端头上。"""
    return lane_of_paths(paths) or lane_of(text)


def lane_owed_to(text, paths=None):
    """**谁欠这件事、谁该动手**（收件人语义 —— 这是看板的默认语义，Andy 08-31 裁决）。

    箭头 > 路径 > 关键词：`→ X` 是明写的收件人，比任何推断都硬。
    路径次之（文件边界＝谁的地盘谁动手），关键词垫底。"""
    return lane_of_arrow(text) or lane_of_paths(paths) or lane_of(text)

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
    # 吞吐统计（7 天完成排行 / 泳道「今日」/ 智能体心跳）问的是**谁做的**。
    ln = lane_authored_by(s, commit_paths.get(h))
    days_ago = (now - datetime.datetime.strptime("2026-" + ad, "%Y-%m-%d %H:%M")).days
    if days_ago < 7:
        lane_7d[ln] += 1
        lane_last.setdefault(ln, (ad, s, h))
    if ad.split(" ")[0] == TODAY:
        lane_today[ln] += 1

import hashlib
cards = []
_seen_ids = set()
def add(col, pri, title, src, lane, date=""):
    # ⚠️ `lane` 没有默认值是**故意的**（Andy 08-31 裁决）：调用点必须自己说清这张卡的线
    # 是「谁欠的」（lane_owed_to，面向行动的列）还是「谁做的」（lane_authored_by，done/doing）。
    # 留一个默认兜底 = 把两种语义又混回一个函数里，正是这次要拆掉的东西。
    # 内容寻址卡号：同一事项跨刷新稳定（评论/对话引用不漂移）
    base = hashlib.sha1((col + "|" + title.strip()[:80]).encode("utf-8")).hexdigest()
    kid = "K" + base[:4].upper()
    n = 0
    while kid in _seen_ids:
        n += 1
        kid = "K" + base[:3].upper() + str(n)
    _seen_ids.add(kid)
    cards.append(dict(id=kid, col=col, pri=pri,
                      lane=lane, t=title.strip()[:170], src=src, d=date))

# --- PARSERS BEGIN（纯函数区：不碰 git / 文件系统，pipeline/tests/test_federation_board.py 靠标记切片测它们）---
def bell_section(md):
    """取晨报「门铃待按」节的正文。

    **标题锚定**：只认标题行里的「门铃待按」。旧写法 `门铃待按[^\\n]*\\n(...)` 会命中正文里
    顺带提到这四个字的段落（08-26 报告的回执表格就被这样误抓过）。
    编号形式 `## 七、门铃待按` / `## 四、门铃待按` / `## ⑤ 门铃待按` 全部覆盖。"""
    m = re.search(r"^#+ *[^\n]*门铃待按[^\n]*\n(.*?)(\n#{1,3} |\Z)", md, re.S | re.M)
    return m.group(1) if m else None


def parse_bell(body):
    """节正文 -> [(收件人, 事项)]。表格与 bullet **两种格式都收**。

    08-27～08-30 四晚的晨报门铃节都是 bullet 列表，而解析器只认表格，
    于是 claim 列连续四晚 0 张来自晨报——**假零**。"""
    out = []
    # 格式 ①：markdown 表格 | 收件人 | 事项 |
    for who, what in re.findall(r"^\| *\*?\*?([^|*]+?)\*?\*? *\| *([^|]+?) *\|", body, re.M):
        if "收件人" in who or "---" in who:
            continue
        out.append((who.strip(), what.strip()))
    # 格式 ②：bullet `- **收件人** · 事项`；允许 `- ⚠️ **X** · …` 前缀，事项可跨续行
    for blk in re.split(r"\n(?=- )", body):
        m = re.match(r"- +[^*\n]{0,8}\*\*(.+?)\*\* *[·:：] *(.+)", blk.strip(), re.S)
        if not m:
            continue
        out.append((m.group(1).strip(),
                    re.sub(r"\s+", " ", re.sub(r"[*`]", "", m.group(2))).strip()))
    return out


def parse_gate(md):
    """NOW.md -> (本周关卡读数, 说明)。读数取不到时**面板不消失**，改印说明。

    旧写法 `周关卡[^\\n]*?(\\d)\\s*/\\s*5` 不跨行，而读数从来不在标题那一行，
    于是 gate_n 恒为 None、整个 🎮 面板**静默消失**——「没有读数」被显示成「没有关卡」。"""
    sec = re.search(r"^#+ *[^\n]*本周关卡[^\n]*\n(.*?)(\n#{1,3} |\Z)", md, re.S | re.M)
    if sec:
        m = re.search(r"(\d+)\s*/\s*5", sec.group(1))
        if m:
            return int(m.group(1)), ""
    m2 = re.search(r"关卡\s*(\d+)\s*/\s*5", md)
    if m2:
        return None, "本周进度 NOW.md 尚未写（周一刚翻周）· 上周结算 %s/5" % m2.group(1)
    if sec:
        return None, "⚠️ 本周关卡节里找不到 N/5 读数——NOW.md 格式变了，修解析器"
    return None, "⚠️ NOW.md 里找不到「本周关卡」节——格式变了，修解析器"


def sessions_behind(data_day, last_sess, is_td):
    """数据落到 `data_day`（session 标签）时，到 `last_sess` 之间隔了几个**交易日**。

    旧写法「14 天窗口内有过任意一条 chore: market data 就 🟢」= cron 连挂 13 天照样满绿。"""
    d = datetime.date.fromisoformat(data_day)
    n, cur = 0, last_sess
    while cur > d and n < 40:
        if is_td(cur):
            n += 1
        cur -= datetime.timedelta(days=1)
    return n


def cron_state(behind):
    """落后 0–1 个 session 算正常（cron 收盘后才跑）；2 个 warn；3 个及以上 red。"""
    return "ok" if behind <= 1 else ("warn" if behind == 2 else "red")


def sig(t):
    """去掉标点/空白，只留字母数字与汉字——用于跨文件比对同一件事。"""
    return re.sub(r"[^0-9A-Za-z一-鿿]", "", t)


# 核销标记：待办项在权威源里出现带这些标记的后续行 = 已办结，不该再上「等你拍板」。
SETTLED_MARKS = ("已拍板", "已执行", "已否决", "已作废", "已撤销", "已销账", "已完成",
                 "✅", "作废", "裁决：", "裁决:", "status: deferred", "status: 作废", "status: 已完成")


def settled_sigs(texts):
    """从权威源正文里抽出「已办结」的行指纹。划掉的标题（`~~…~~`）本身就是核销标记。"""
    idx = []
    for md in texts:
        for ln in md.splitlines():
            if any(k in ln for k in SETTLED_MARKS) or re.search(r"~~[^~]{6,}~~", ln):
                s = sig(ln)
                if len(s) >= 12:
                    idx.append(s)
    return idx


def is_settled(title, idx):
    """标题与任一核销行有 >=12 字的公共片段 = 同一件事已办结。"""
    k = sig(title)
    if len(k) < 12:
        return False
    return any(any(k[i:i + 12] in p for i in range(len(k) - 11)) for p in idx)
# --- PARSERS END ---


reports = sorted(re.findall(r"night_reports/(2026-\d\d-\d\d)\.md", git("ls-tree", "-r", "--name-only", "origin/main", "data/research/night_reports/")))
if reports:
    _d = reports[-1][5:]
    _body = bell_section(show("data/research/night_reports/%s.md" % reports[-1]))
    if _body is not None:
        _items = parse_bell(_body)
        for _who, _what in _items:
            # 门铃的 `_who` 就是收件人本人——这一列问的永远是「谁该去按这个铃」。
            add("claim", 1, _what, "晨报门铃 %s" % _d, lane_owed_to(_who), _d)
        # 显式失败告警：节里有内容却一条都没解析出来 = 格式又变了。
        # 本文件下面自己写过「假零比空着更糟」——那条规矩这里也算数。
        _lines = [l for l in _body.splitlines() if l.strip()]
        if _lines and not _items:
            add("claim", 1,
                "晨报门铃节 %d 行未能解析（格式变了）—— 修 pipeline/tools/federation_board.py 的门铃解析器" % len(_lines),
                "晨报门铃 %s · 解析失败" % _d, "OPS Fable", _d)

for b in git("branch", "-r", "--no-merged", "origin/main").splitlines():
    b = b.strip()
    if not b or "HEAD" in b or "archive/" in b:
        continue
    n = git("rev-list", "--count", "origin/main.." + b).strip()
    if n and n != "0":
        last = git("log", "-1", "--format=%ad|%s", "--date=format:%m-%d", b).strip().split("|", 1)
        bpaths = git("diff", "--name-only", "origin/main..." + b).split()
        add("claim", 2, "%s（+%s）%s" % (b.replace("origin/", ""), n, ("· " + last[1][:60]) if len(last) > 1 else ""),
            # 待合分支挂在**该去合它的那条线**名下（谁的文件边界谁合），不是「谁提交的」。
            "待合分支", lane_owed_to(b + (last[1] if len(last) > 1 else ""), bpaths), last[0] if last else "")

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
        # 契约行两列都是面向行动的：等谁拍板 / 谁该认领——一律收件人语义。
        add("blocked", 0, head, "契约行", lane_owed_to(line), date)
    elif "→" in txt[:60]:
        add("claim", 3, head, "契约行", lane_owed_to(txt), date)

# ---------- 核销（08-31 修）----------
# 「等你拍板」曾端出 KB388「回收两个 Discord 付费角色」，源标「INBOX 待办」；
# 而权威源 `data/growth/weekly/2026-08-25-paypal-reconcile.md` 的 T1 早已被 Andy 08-28 拍板
# （「否定。还不做这件事。」），标题也已划掉。**信箱里的指针不会自己跟着权威源变**，
# 所以待办项进板前必须回权威源核一次销——这是通用检查，不是给这一条写的补丁。
def settle_blocked():
    """把已在权威源核销的「等 Andy 拍板」卡摘掉；摘了多少打在 stdout 上，别静默。"""
    srcs = [show("data/reference/DATA_CONTRACTS.md"), nowmd,
            show("data/research/night_reports/INBOX.md")]
    srcs += [show("data/growth/weekly/" + w) for w in weeklies]
    idx = settled_sigs(srcs)
    dropped, out = 0, []
    for c in cards:
        if c["col"] == "blocked" and is_settled(c["t"], idx):
            dropped += 1
            continue
        out.append(c)
    cards[:] = out
    return dropped


def dedupe_blocked():
    """同一件等 Andy 的事常在两处登记（INBOX 的指针 + 增长台账的正本）。
    判同：去掉标点后有 >=12 字的公共片段。保留先入的那张。"""
    def sig(t):
        return re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]", "", t)

    kept, out = [], []
    for c in cards:
        if c["col"] != "blocked":
            out.append(c)
            continue
        k = sig(c["t"])
        dup = any(any(k[i:i + 12] in p for i in range(len(k) - 11)) for p in kept)
        if dup:
            continue
        kept.append(k)
        out.append(c)
    cards[:] = out


# NOW.md：**权威版优先**（`git show origin/main:`）。旧写法硬编码主树绝对路径先读工作区副本，
# 于是看板端出的是「某个分支上未提交的 NOW.md」——只有在读文件抛异常时才回落 main，
# 而主树上 NOW.md 总是存在，所以那条回落分支实际从没走过。
# 仅当权威版里根本没有「📋 等你动手」这一节时才回落工作区，且回落要在面板上说出来。
nowmd = show("NOW.md")
nowmd_src = "origin/main"
if "📋 等你动手" not in nowmd:
    try:
        _wt = open(os.path.join(REPO, "NOW.md"), encoding="utf-8").read()
        if "📋 等你动手" in _wt:
            nowmd, nowmd_src = _wt, "worktree"
    except Exception:
        pass
for line in nowmd.splitlines():
    if "待你" in line and "- [ ]" in line:
        add("blocked", 0, re.sub(r"[*\[\]~]", "", line.replace("- [ ]", "")).strip()[:150], "NOW.md", "OPS Fable", "")

# 「等你拍板」的另外两个耐久处。
# 08-28 实测：只扫契约行 + NOW.md 时首页印「现在没有等你的事」，而 INBOX 的
# 「📌 给 Andy 的待办」里 T1（Andy 原话「这个是要处理的，提醒我」）与 T3 都还挂着 `status: 待办`，
# 晨报「建议 Andy 决定的事」一节也从来没被读过。**假零比空着更糟**——它让 Andy 以为清了。
def andy_todos(md, heading_re, source):
    """取某个标题节下未打勾的顶层条目。"""
    m = re.search(heading_re + r"[^\n]*\n(.*?)(\n## |\Z)", md, re.S | re.M)
    if not m:
        return
    for ln in m.group(1).splitlines():
        if not ln.startswith("- ") or "✅" in ln or "~~" in ln:
            continue
        txt = re.sub(r"[*`\[\]]", "", ln[2:]).strip()
        if len(txt) < 8:
            continue
        add("blocked", 0, txt[:150], source, "OPS Fable", "")

andy_todos(show("data/research/night_reports/INBOX.md"), r"^## [^\n]*给 Andy 的待办", "INBOX 待办")

# 增长台账的「⏳ 待办」节：每条自带 `status: 待办`，且有明写的核销协议
# （「直到 Andy 明确说做完了才改 ✅」），所以可以当数据源。
# ⚠️ **晨报的「建议 Andy 决定的事」一节不接**——晨报是 append-only 快照，没有核销协议，
# 接进来必然把已拍板的事(如 08-27 的 ADR 闸)当成还在等，假阳性比假零更快让人不再信这一列。
weeklies = sorted(re.findall(r"weekly/(\S+\.md)", git("ls-tree", "-r", "--name-only", "origin/main", "data/growth/weekly/")))
if weeklies:
    led = show("data/growth/weekly/" + weeklies[-1])
    sec = re.search(r"^## [^\n]*⏳ 待办[^\n]*\n(.*?)(\n## |\Z)", led, re.S | re.M)
    if sec:
        for blk in re.split(r"\n### ", sec.group(1))[1:]:
            title = blk.splitlines()[0]
            if "~~" in title or "✅" in title:
                continue
            if re.search(r"status: *待办", blk[:400]):
                add("blocked", 0, re.sub(r"[*`]", "", title).strip()[:150],
                    "增长台账 " + weeklies[-1][:10], "Growth Gary", "")

for h, ad, s in log14:
    hrs = (now - datetime.datetime.strptime("2026-" + ad, "%Y-%m-%d %H:%M")).total_seconds() / 3600
    if hrs < 24:
        # done / doing 是**已经发生的 commit**——这两列的线名是「谁提交的」，唯二的作者语义。
        add("done", 9, s[:150], h, lane_authored_by(s, commit_paths.get(h)), ad)
    if ad.split(" ")[0] == TODAY:
        add("doing", 9, s[:130], h, lane_authored_by(s, commit_paths.get(h)), ad.split(" ")[1])

andy_todo = []
_sec = re.search(r"## 📋 等你动手[^\n]*\n(.*?)(\n## |\Z)", nowmd, re.S)
if _sec:
    for _l in _sec.group(1).splitlines():
        _m = re.match(r"- \[ \] (.+)", _l.strip())
        if _m:
            andy_todo.append(re.sub(r"[*`]", "", _m.group(1)).strip()[:150])

gate_n, gate_note = parse_gate(nowmd)
if gate_n is None and gate_note.startswith("⚠️"):
    add("claim", 1, "NOW.md 关卡读数解析失败：%s" % gate_note.lstrip("⚠️ "),
        "NOW.md · 解析失败", "OPS Fable", "")

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
# 数据 cron 的绿灯：旧写法是「14 天窗口内有过任意一条 `chore: market data` 就 🟢」——
# cron 连挂 13 天照样满绿。改成按**最近完成交易日**判：落后 0–1 个 session 才算 ok。
# 判据用 commit **标题里的 session 标签**（`chore: market data 2026-08-30`），不用 commit 时间戳
# ——后者是 JST 本机时间，跟 ET session 差半天，比较会系统性差一天。
try:
    sys.path.insert(0, REPO)
    from pipeline.marketcal import is_trading_day as _is_td, last_completed_session as _lcs
    _last_sess = _lcs()
except Exception:      # marketcal 依赖 pandas；取不到就退成「周一到周五」的粗算，并在说明里讲清楚
    def _is_td(d):
        return d.weekday() < 5
    _t = datetime.date.today()
    while not _is_td(_t):
        _t -= datetime.timedelta(days=1)
    _last_sess = _t

_datalog = git("log", "origin/main", "--since=90 days ago", "--format=%s", "--grep=chore: market data")
_dates = sorted(re.findall(r"chore: market data (\d{4}-\d\d-\d\d)", _datalog))
if _dates:
    _behind = sessions_behind(_dates[-1], _last_sess, _is_td)
    _cron_state = cron_state(_behind)
    _cron_note = "最近落数据 %s · 最近完成 session %s · 落后 %d 个交易日" % (_dates[-1], _last_sess, _behind)
else:
    _cron_state, _cron_note = "red", "90 天内没有一条 `chore: market data` —— cron 死了"
infra = [
    ("数据 cron（GitHub Actions 21:30 UTC）", _cron_note, _cron_state),
    ("Vercel 自动部署", "跟随 main push（本页不直连，状态未测量）", "na"),
    ("GAS / Google Sheets 回拉", "挂 run_all（本页不直连，状态未测量）", "na"),
    ("本机（唯一节点 MacBook）", "定时任务 App 开着才跑", "ok"),
]

_settled_n = settle_blocked()
dedupe_blocked()

counts = {c: sum(1 for k in cards if k["col"] == c) for c in ["claim", "doing", "blocked", "done"]}

# ---------- 生意数据 ----------
def last_nonempty(csv_text, col):
    """返回 (读数, 该读数所在行的 date)。**读数必须带日期**——首页两个生意 KPI 此前
    直接印 metrics.csv 最后一个非空值、不说它是哪天量的，于是一个 6 天前的数字长得和实时读数一模一样。
    （`pitfall_a_measurement_expires`：我量的数也会过期。）"""
    lines = [l for l in csv_text.splitlines() if l.strip()]
    if not lines:
        return None, None
    hdr = lines[0].split(",")
    if col not in hdr:
        return None, None
    i = hdr.index(col)
    for l in reversed(lines[1:]):
        parts = l.split(",")
        if i < len(parts) and parts[i].strip():
            return parts[i].strip(), parts[0].strip()
    return None, None


def stale_days(d):
    """读数距今几天；解析不了返回 None。"""
    try:
        return (datetime.date.today() - datetime.date.fromisoformat(d)).days
    except Exception:
        return None


met = show("data/growth/metrics.csv")
_members, _members_d = last_nonempty(met, "whop_members")
_mrr, _mrr_d = last_nonempty(met, "mrr_usd")
BIZ = dict(
    members=_members or "—",
    mrr=_mrr or "—",
    discord=last_nonempty(met, "discord_members")[0] or "—",
    followers=last_nonempty(met, "x_followers")[0] or "未测量",
    subs=last_nonempty(met, "substack_subs")[0] or "未测量",
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
PROJ_KEYS = {
    "P0": ["portfolio", "receipts", "交易"],
    "P1": ["post", "tool(post", "content", "material(", "日推", "thread"],
    "P2": ["substack", "mrna", "letter", "publish"],
    "P3": ["masterclass", "课程", "course"],
    "P4": ["growth", "whop", "discord", "member", "product:"],
    "P5": ["feat(", "fix(watchlist", "fix(schema", "frontend", "chore: market", "data(", "screener", "groups_history"],
    "P6": ["night(", "prereg(", "collect(", "tests(", "amplitude", "adr", "vcp", "stockbee", "regime", "gex"],
    "P7": ["visual", "brand", "mr_fluxus", "track record", "官网", "squarespace"],
}
PROJS = []
_secs = re.split(r"^### ", projmd, flags=re.M)
for sec in _secs:
    m = re.match(r"(P\d) · ([^（(\n]+)[（(]([^）)\n]*)[）)]?([^\n]*)\n", sec)
    if not m:
        continue
    pid, pname, prole, pstar = m.group(1), m.group(2).strip(), m.group(3).strip(), m.group(4)
    body = sec[m.end():]

    def grab(*pats):
        for p in pats:
            r = re.search(p, body)
            if r:
                return re.sub(r"[*`]", "", r.group(1)).strip()
        return ""
    st = grab(r"- 状态[：:]\s*(.+)", r"- 状态（[^）]*）[：:]\s*(.+)", r"- \*\*?状态[^：:]*[：:]\*?\*?\s*(.+)")
    act = grab(r"- 本周动作[：:]\s*(.+)", r"- \*\*当前真任务[^：:]*[：:]\*?\*?\s*(.+)", r"- 体系义务[：:]\s*(.+)")
    trio = grab(r"- 三件套[^：:]*[：:]\s*(.+)", r"- \*\*三件套[^：:]*[：:]\*?\*?\s*(.+)")
    owner = grab(r"负责线[：:]\s*([^。\n]+)")
    # 最近 7 天该项目的 commit（关键词映射，近似）
    recent = []
    for h, ad, s in log14:
        days = (now - datetime.datetime.strptime("2026-" + ad, "%Y-%m-%d %H:%M")).days
        if days >= 7:
            continue
        low = s.lower()
        if any(k in low for k in PROJ_KEYS.get(pid, [])):
            recent.append((ad, s))
    light = "🟢" if ("🟢" in st or "自转" in st) else ("🔴" if ("空" in st[:14] or "没落地" in st) else ("⏸" if ("冻结" in st or "未定" in st) else "🟡"))
    PROJS.append(dict(pid=pid, name=pname, role=prole, star="⭐" in pstar, light=light,
                      st=st[:230] or "（PROJECTS.md 该节缺状态行——该修档案）",
                      act=act[:180], trio=trio[:200], owner=owner[:60],
                      recent=recent[:3], n7=len(recent)))

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
def kpi(v, label, color="", asof=None):
    """asof = 该读数的日期（YYYY-MM-DD）。有日期就印出来；超过 7 天加陈旧徽章。"""
    tail = ""
    if asof:
        n = stale_days(asof)
        tail = '<i class="asof%s">读数 %s%s</i>' % (
            " old" if (n is not None and n > 7) else "", E(asof[5:]),
            (" · %d 天前" % n) if n is not None else "")
    return '<div class="kpi"><b style="%s">%s</b><span>%s</span>%s</div>' % (
        ("color:" + color) if color else "", v, label, tail)

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
    '<div class="kpis">' + kpi(BIZ["members"], "会员", asof=_members_d) + kpi("$" + str(BIZ["mrr"]), "MRR", asof=_mrr_d) +
    kpi("%d/5" % posts_week, "本周发布") + kpi(format(views7, ",") if views7 else "—", "7d views") +
    kpi(len(andy_todo), "等你动手", "var(--p0)") + kpi(counts["blocked"], "等你拍板", "var(--blk)") + "</div>" +
    section("本周主线", '<div>%s</div><div class="mut" style="margin-top:6px">今天的一件事：%s</div>' % (E(now_main or "（NOW.md 未写）"), E(today_one or "（未写）"))) +
    section("📋 等你动手（生意动作 · 做完在 NOW.md 划掉）",
            ('<div class="mut" style="margin-bottom:8px">⚠️ 本节读自**未提交的工作区副本**（origin/main 上的 NOW.md 没有这一节）</div>' if nowmd_src == "worktree" else "") +
            ("".join('<div class="k" style="--pc:var(--p0)"><div class="m"><span class="pid">DO</span></div>%s</div>' % E(t) for t in andy_todo) or '<div class="empty">队列为空</div>')) +
    section("⚠ 等你拍板", "".join(cardh(c) for c in blocked_cards) or '<div class="empty">现在没有等你的事</div>') +
    section("AI 今日已落地（详见任务看板）", "".join(cardh(c) for c in today_stream) or '<div class="empty">今天还没有 commit</div>'))

# --- 页1.5 项目 ---
fun = "".join('<div class="fstage"><div class="fname">%s</div><div class="fval">%s</div><div class="fsrc">%s</div></div><div class="farrow">→</div>' % (n, E(v), E(s)) for n, v, s in FUNNEL)
fun = fun.rsplit('<div class="farrow">', 1)[0]
pcards = ""
for P in PROJS:
    rec = "".join('<div class="prow"><span class="pt">%s</span>%s</div>' % (r[0], E(r[1][:96])) for r in P["recent"]) \
          or '<div class="prow mut">近 7 天无落地（%s）</div>' % ("冻结中，符合预期" if P["light"] == "⏸" else "留意")
    pcards += ('<div class="proj"><div class="pjh">%s <b>%s · %s</b>%s<span class="pjrole">%s</span>'
               '<span class="pjn">7d 落地 %d</span></div>'
               '<div class="pjgrid">'
               '<div><div class="pjl">现在在哪</div><div class="pjv">%s</div></div>'
               '<div><div class="pjl">最近做了什么</div><div class="pjv">%s</div></div>'
               '<div><div class="pjl">下一步</div><div class="pjv">%s</div></div>'
               '<div><div class="pjl">三件套 · 截止规则</div><div class="pjv">%s</div></div>'
               '</div>%s</div>'
               % (P["light"], P["pid"], E(P["name"]), " ⭐" if P["star"] else "", E(P["role"]),
                  P["n7"],
                  E(P["st"]),
                  rec,
                  E(P["act"]) or '<span class="mut">（档案未写本周动作）</span>',
                  E(P["trio"]) or '<span class="mut">（三件套未立——按立项规矩该补）</span>',
                  ('<div class="pjo">负责线：%s</div>' % E(P["owner"])) if P["owner"] else ""))
p_projects = (section("生意漏斗（内容 → 售后）", '<div class="funnel">%s</div>' % fun) +
              '<div class="mut" style="margin:2px 0 10px">四格答案全部实时映射自 PROJECTS.md + git——档案缺哪格，卡上就露哪格；该修的是档案，不是看板。</div>' +
              pcards)

# --- 页2 看板 ---
# 列头必须自己说清线名是哪种语义（Andy 08-31 裁决）：前三列「谁欠」，done 列「谁做的」。
# 两种语义不加区分地混在一张页面上，正是此前 7 处盲判分歧的来源。
COLS = [("claim", "待认领 · 挂单板<span class=\"sem\">线 = 谁该动手</span>"),
        ("doing", "进行中 · 今日<span class=\"sem\">线 = 谁提交的</span>"),
        ("blocked", "等 Andy 拍板<span class=\"sem\">线 = 谁该动手</span>"),
        ("done", "已完成 · 24h<span class=\"sem\">线 = 谁提交的</span>")]
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
    kb_cols += '<div class="col"><div class="colh"><span class="cl">%s</span><span class="n">%d</span></div>%s</div>' % (label, len(items), inner or '<div class="empty">（空）</div>')
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
p_lanes = (section("%d 线泳道" % len(ROSTER),
                   '<div class="mut" style="margin-bottom:8px">「在手挂单」= 这条线<b>欠</b>的事（收件人语义）；'
                   '「今日提交 / 近期完成」= 这条线<b>做</b>的事（作者语义）。同一条 commit 可能欠在一边、做在另一边——'
                   '例：<code>contracts(§7): → 前端 …</code> 由 Joe 提交、由 UI Claire 动手。</div>'
                   '<table><thead><tr><th>线</th><th>在手挂单 · 谁欠</th><th>今日提交 · 谁做</th><th>近期完成 · 谁做</th></tr></thead><tbody>%s</tbody></table>' % rows))

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
         section("7 天完成排行（按提交者，不是按收件人）", '<table><thead><tr><th>#</th><th>线 · 谁做的</th><th>commit</th></tr></thead><tbody>%s</tbody></table>' % rank_h) +
         section("🎮 发布关卡",
                 ('<div class="gatebar"><div style="width:%d%%"></div></div><div class="mut">本周 %d / 5</div>'
                  % (min(gate_n, 5) * 20, gate_n)) if gate_n is not None
                 else '<div class="gatebar"><div style="width:0%%"></div></div><div class="mut">本周 — / 5 · %s</div>' % E(gate_note)))

# --- 页6 知识库 ---
kbh = ""
for layer, sub, items in KB:
    rows_k = "".join('<tr><td>%s</td><td class="num">%s</td></tr>' % (E(str(n)), v) for n, v in items)
    kbh += '<div class="panel"><div class="ph">%s <span class="mut" style="font-weight:400">· %s</span></div><table><tbody>%s</tbody></table></div>' % (layer, sub, rows_k)
p_kb = '<div class="mut" style="margin-bottom:12px">地图版真理索引 · 全文在仓库根 <b>KNOWLEDGE.md</b> · 全文检索不存在（靠 grep + 本图）</div>' + kbh

# --- 页7 基础设施 ---
ti = "".join('<tr><td><b>%s</b><div class="mut">%s</div></td><td>%s</td></tr>' % (t["name"], E(t["desc"][:90]), E(t["sched"] or "—")) for t in tasks if not t["personal"])
inf = "".join('<tr><td>%s</td><td>%s</td><td>%s</td></tr>' % (n, E(d), {"ok": "🟢", "warn": "🟠", "red": "🔴", "na": "◻︎ 未测量"}[s]) for n, d, s in infra)
p_infra = (section("定时任务（工作线）", '<table><thead><tr><th>任务</th><th>排程</th></tr></thead><tbody>%s</tbody></table>' % ti) +
           section("链路健康", '<table><thead><tr><th>链路</th><th>说明</th><th>状态</th></tr></thead><tbody>%s</tbody></table>' % inf))

PAGES = [
    ("home", "🏠", "今日", "TODAY", "生意读数 · 该你做的 · AI 交付", p_home, "生意"),
    ("projects", "📈", "项目", "BUSINESS PORTFOLIO", "P0–P7 档案与六环漏斗——你的生意长什么样", p_projects, "生意"),
    ("ops", "📊", "运营看板", "OPERATIONS · GLOBAL", "吞吐 · 完成排行 · 发布关卡", p_ops, "生意"),
    ("board", "🗂", "任务看板", "TASK BOARD · KANBAN", "挂单不挂人：待认领 → 进行中 → 拍板 → 完成（前三列的线 = 谁该动手，已完成列的线 = 谁提交的）", p_board, "AI 引擎室"),
    ("lanes", "🤝", "协作泳道", "MULTI-LANE COLLABORATION", "%d 条线各自<b>欠</b>的工作与各自<b>做</b>的交付" % len(ROSTER), p_lanes, "AI 引擎室"),
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
.proj{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:14px 16px;margin-bottom:13px}
.pjh{display:flex;align-items:baseline;gap:8px;margin-bottom:10px;font-size:14px;flex-wrap:wrap}
.pjrole{color:var(--mut);font-size:11.5px}
.pjn{margin-left:auto;font:400 10.5px "IBM Plex Mono",monospace;color:var(--mut)}
.pjgrid{display:grid;grid-template-columns:1fr 1fr;gap:10px 18px}
@media(max-width:900px){.pjgrid{grid-template-columns:1fr}}
.pjl{font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:var(--mut);margin-bottom:3px}
.pjv{font-size:12.5px;line-height:1.5}
.prow{font-size:12px;margin-bottom:3px}
.pt{font:400 10px "IBM Plex Mono",monospace;color:var(--mut);margin-right:7px}
.pjo{margin-top:9px;border-top:1px dashed var(--line);padding-top:7px;font-size:11px;color:var(--mut)}
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
.asof{display:block;margin-top:4px;font:400 10px "IBM Plex Mono",monospace;font-style:normal;color:var(--mut)}
.asof.old{color:var(--p0);border:1px solid var(--p0);border-radius:3px;padding:0 4px;display:inline-block}
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
.colh{display:flex;justify-content:space-between;align-items:baseline;gap:6px;font-size:12.5px;font-weight:600;margin-bottom:9px}
.colh .n{color:var(--mut);font-family:"IBM Plex Mono",monospace;font-weight:400}
.colh .cl{display:block}
.sem{display:block;font:400 10px "IBM Plex Mono",monospace;color:var(--mut);letter-spacing:.04em;margin-top:2px}
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
<div class="foot">数据源 = origin/main + 定时任务清单。批注：选中卡片文字开评论并**写上卡号**（左上角 K 码，同一事项永久同号，跨刷新不变）。@claude 后 OPS 能读到并执行。说「刷新看板」即更新本页。</div></aside>
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
print("console -> %s | cards=%d tasks=%d | NOW.md=%s 已核销拍板项=%d cron=%s" % (
    OUT, len(cards), len(tasks), nowmd_src, _settled_n, _cron_state))
