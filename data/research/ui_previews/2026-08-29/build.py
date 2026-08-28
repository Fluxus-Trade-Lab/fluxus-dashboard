"""Generate the three recipe-disclosure variants from the live watchlist.json.

Real strings, real panels, real ragged lengths -- a mock with tidy invented
copy would score every variant the same, which is the whole failure mode of
previewing with placeholder text.
"""
import html, json, re
from pathlib import Path

HERE = Path(__file__).resolve().parent
WL = json.load(open(HERE / "../../../output/watchlist.json"))
PANELS = [(z["key"], p) for z in WL["zones"] for p in z.get("panels", [])]

SEP = " -- "


def split(recipe):
    """rule, why. The separator exists in 7/19 panels; elsewhere the whole
    string is the rule and `why` is empty. Stated, not hidden."""
    if SEP in recipe:
        a, b = recipe.split(SEP, 1)
        return a.strip(), b.strip()
    return recipe.strip(), ""


def clauses(rule):
    """Split a rule on the connectives it actually uses. Parentheticals are
    kept with their clause; a clause we cannot split stays whole."""
    parts = re.split(r"\s+and\s+|;\s*|,\s+(?![^(]*\))", rule)
    return [p.strip() for p in parts if p.strip()]


HEAD = """<!doctype html><meta charset="utf-8"><title>{t}</title>
<link rel="stylesheet" href="_shared.css">
<h1>{t}</h1>
<p class="sub">{sub}</p>
<p class="legend">{legend}</p>
"""


def page(path, title, sub, legend, body):
    (HERE / path).write_text(
        HEAD.format(t=html.escape(title), sub=sub, legend=legend) + body, encoding="utf-8")


def head_html(zone, p, tog):
    return (f'<div class="phead"><span class="plabel">{html.escape(p["label"])}</span>'
            f'<span class="pcount">{p.get("count", 0)}</span>'
            f'<span class="ptog">{tog}</span></div>')


def names_html(p):
    tk = [t["ticker"] for t in p.get("tickers", [])[:6]]
    return f'<div class="names">{" ".join(tk) or "&mdash;"}</div>' if tk else ""


# ---------------------------------------------------------------- v0: as-is
body = []
for z, p in PANELS:
    body.append('<div class="panel">' + head_html(z, p, "recipe &minus;")
                + f'<div class="rbody">{html.escape(p.get("recipe",""))}</div>'
                + names_html(p) + "</div>")
page("v0_current.html", "v0 · 现网（配方 = 一整段，全部展开）",
     "现网 <code>WatchlistPage.jsx:658-661</code> 的渲染：点开 recipe，得到一段 41–655 字符不等的纯文本。"
     "这里把 19 个面板全部展开，好看清它有多参差。",
     "读者要在同一个位置，有时读到一行口径，有时读到一段研究笔记。",
     "".join(body))

# ---------------------------------------------------------------- v1 in-place layering
body = []
for z, p in PANELS:
    rule, why = split(p.get("recipe", ""))
    inner = f'<div class="rule">{html.escape(rule)}</div>'
    if why:
        inner += f'<div class="why">{html.escape(why)}</div>'
    body.append('<div class="panel">' + head_html(z, p, "recipe &minus;")
                + f'<div class="rbody">{inner}</div>' + names_html(p) + "</div>")
page("v1_layered.html", "v1 · 就地分层（规则在上，出处在下）",
     "同一个披露，内部分两层：<b>规则</b>（等宽，深一档）与 <b>为什么是这个杠</b>（正文体，浅一档，一条细线隔开）。"
     "点开次数不变，信息顺序变了。",
     "⚠️ 分割点是字符串里的 <code>--</code>，19 个面板里 <b>7 个</b>有；"
     "另外 12 个整段都当规则渲染，其中 <code>weekly_20_gainers</code>(191) / "
     "<code>liquid_leaders</code>(123) 的括号里其实也是出处，这一版分不出来。",
     "".join(body))

# ---------------------------------------------------------------- v2 rule always on
body = []
for z, p in PANELS:
    rule, why = split(p.get("recipe", ""))
    tog = "why &plus;" if why else ""
    body.append('<div class="panel">' + head_html(z, p, tog)
                + f'<div class="rbody"><div class="rule">{html.escape(rule)}</div></div>'
                + names_html(p) + "</div>")
page("v2_rule_always.html", "v2 · 规则常驻，出处收进二级",
     "规则**不再需要点开**——它和面板标题一起常驻；只有「为什么是这个杠」留在 <code>why +</code> 后面。"
     "12 个没有出处段的面板连按钮都不出现。",
     "⚠️ 代价：那 12 个整段规则里最长 215 字符（<code>ma_reclaim</code> 的前半段），常驻会把卡片撑高。"
     "本页把它照原样渲染出来，好让这个代价被看见而不是被描述。",
     "".join(body))

# ---------------------------------------------------------------- v3 clause list
body = []
for z, p in PANELS:
    rule, why = split(p.get("recipe", ""))
    cs = clauses(rule)
    inner = "".join(f'<span class="clause">{html.escape(c)}</span>' for c in cs)
    if why:
        inner += f'<div class="why">{html.escape(why)}</div>'
    body.append('<div class="panel">' + head_html(z, p, "recipe &minus;")
                + f'<div class="rbody">{inner}</div>' + names_html(p) + "</div>")
page("v3_clauses.html", "v3 · 条款逐行",
     "规则拆成一行一个条款（在 <code>and</code> / <code>;</code> / 括号外的逗号处切）。"
     "读者可以逐条对照一只票过没过。",
     "⚠️ 这一版最靠解析，而解析会在逗号处<b>把句子从中间切断</b>，再把碎片当成条款排出来。"
     "实测 <b>52 条款行里 8 行（15%）</b>不含任何比较符且长度 &gt;25 字符——它们不是条款是散文："
     "<code>pp_today</code> 的 <code>vol10_green today (green bar</code>（从括号中间断开）、"
     "<code>liquid_leader_pullback</code> 的 <code>the two clauses we cannot read</code>（单独一行毫无意义）。"
     "往下翻能看到这几格。<br>"
     "（更正：这里原先写的是「它把 OR 渲染成了 AND」——拿真输出核过之后发现不对，"
     "<code>any of A / B / C</code> 与 <code>A or B</code> 都完整留在一行。）",
     "".join(body))

print("panels", len(PANELS),
      "| with separator", sum(1 for _z, p in PANELS if SEP in p.get("recipe", "")),
      "| max rule len", max(len(split(p.get("recipe", ""))[0]) for _z, p in PANELS))


# ================= iteration on the winner (v2) ==========================
TAIL = re.compile(r"\s*\(([^()]{60,})\)\s*$")


def split2(recipe):
    """v2a: also move a TRAILING parenthetical of >= 60 chars into `why`.
    Threshold measured, not guessed: at 40 it eats real clauses
    (`ll_hl_trend_break` 70->25 chars, `stop_hit` 63->20 -- both times the
    parenthetical IS the rule in plain words). At 60 exactly one panel is
    touched, `weekly_20_gainers`, and what it moves is provenance."""
    rule, why = split(recipe)
    m = TAIL.search(rule)
    if m:
        rule, why = rule[:m.start()].strip(), (m.group(1) + (" -- " + why if why else ""))
    return rule, why


def v2page(path, title, sub, legend, splitter, overrides=None):
    body = []
    for _z, p in PANELS:
        rule, why = splitter(p.get("recipe", ""))
        if overrides and p["key"] in overrides:
            rule, why = overrides[p["key"]]
        tog = "why &plus;" if why else ""
        body.append('<div class="panel">' + head_html(_z, p, tog)
                    + f'<div class="rbody"><div class="rule">{html.escape(rule)}</div></div>'
                    + names_html(p) + "</div>")
    page(path, title, sub, legend, "".join(body))

    def rule_of(p):
        if overrides and p["key"] in overrides:
            return overrides[p["key"]][0]
        return splitter(p.get("recipe", ""))[0]
    ls = [max(1, -(-len(rule_of(p)) // 88)) for _z, p in PANELS]
    return {"resident_lines": sum(ls), "max_lines": max(ls),
            "cards_over_2_lines": sum(1 for x in ls if x > 2)}


n_a = v2page("v2a_tail_stripped.html", "v2a · v2 + 把结尾的长括号也挪进 why",
             "第 2 轮。规则里结尾那段 ≥60 字符的括号是出处不是条款，一起挪走。",
             "阈值 60 是量出来的：<b>40 会吃掉真条款</b>——<code>ll_hl_trend_break</code> 70→25 字符、"
             "<code>stop_hit</code> 63→20，被切掉的正是「close crossed the counter-trend line today」这种"
             "把口径讲成人话的部分。60 只动到 <code>weekly_20_gainers</code> 一个，切走的确实是出处。",
             split2)

# What a data-side rule/why field would buy. The two hand-splits below are
# NOT a proposed heuristic -- no client-side rule can find them, which is
# exactly the point of showing them.
HAND = {
    "ma_reclaim": ("cross_ema21_up or cross_sma50_up (yesterday's close under the MA, today's at/above it)",
                   "No volume clause. " + split(dict(PANELS)["ma_reclaim"]["recipe"] if False else
                                                next(p for _z, p in PANELS if p["key"] == "ma_reclaim")["recipe"])[1]),
    "morales_pp_10d": ("pp_count_10d >= 3",
                       next(p for _z, p in PANELS if p["key"] == "morales_pp_10d")["recipe"]),
}
n_b = v2page("v2b_dataside_field.html", "v2b · 如果数据端给 rule / why 两个字段",
             "第 3 轮。同样的版式，但 <code>ma_reclaim</code> 与 <code>morales_pp_10d</code> 的规则是<b>手工拆的</b>——"
             "它们的出处夹在句子中间，任何客户端启发式都找不到。",
             "⚠️ 这一版<b>不是可实现方案</b>，它是一个上限：把它和 v2a 并排看，差额就是"
             "「数据端补 <code>rule</code> / <code>why</code> 两个字段」能买到的东西。",
             split2, HAND)
print("v2a", n_a, "\nv2b (hand-split ceiling)", n_b)
