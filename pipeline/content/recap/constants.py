"""Fixed text for the recap.

THE RULES — Andy's seven, copied verbatim (skill daily-recap §结构 10「他的七条，固定文本照抄」;
spec §3 item 10). Source: his approved 2026-09-04 recap PDFs, extracted with pdftotext on
2026-09-13 (EN from Market_Recap_2026-09-04_EN.pdf, ZH from Market_Recap_2026-09-04_ZH.pdf —
the ZH set is his approved Chinese rewrite, not a translation of EN made here).
Never generated per session. Changing a rule = Andy's words only.

⚠️ Known tension, reported not resolved (2026-09-13): the 09-01/02/03 PDFs carry different
rules 1–6 each day; only rule 7 (200-day) repeats. Pinned to 09-04 per OPS instruction until
Andy rules whether 1–6 are fixed or per-session.

Voice (Andy 2026-09-13「正文里不出现Andy 说这样的字眼，也不用第一人称」): the body never names
him and never uses first person; his Discord judgments are restated as neutral sentences.
Enforced as delivery gates in gates.py, not as a style hope.
"""

RULES_SOURCE = "Market_Recap_2026-09-04_{EN,ZH}.pdf (Andy-approved), extracted 2026-09-13"

RULES_EN = (
    "Uptrend intact — weekly close above the 21 EMA — but bifurcated: big-cap AI leads, breadth lags",
    "Good news is bad news: strong data = higher hike odds = pressure; CPI/PPI decide next week",
    "7,800 is the S&P upside pivot; the declining-tops line is the near-term cap",
    "Trade leaders with buyable closes (DELL, CRCL, HOOD) — volume + a strong close",
    "Memory + the semi snapback is the constructive AI tell; NVDA holding its 8/21 is the key",
    "Software is two-tone — buy the reclaims, avoid the fails",
    "Never serious trouble until the S&P breaks the 200-day — mid/small caps are the weak link",
)

RULES_ZH = (
    "趋势还在——周线收在 21 EMA 上——但盘是劈的：大盘 AI 领涨，广度没跟",
    "好消息就是坏消息：数据强＝加息概率高＝压力；下周 CPI/PPI 说了算",
    "7,800 是标普往上的 pivot；下降趋势线是近处的顶",
    "只做收得强的龙头（DELL、CRCL、HOOD）——放量，收盘要硬",
    "Memory 加半导体回弹，是 AI 这条线还活着的证据；NVDA 守住 8/21 是钥匙",
    "软件两张脸——收回均线的可以买，破位的躲开",
    "标普不破 200 日线，都算不上真麻烦——短板在中小盘",
)

RULES = {"EN": RULES_EN, "ZH": RULES_ZH}
