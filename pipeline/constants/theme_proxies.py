"""每个主题一只代理 ETF —— 主题层读一条干净的价格序列，不再由成分股拼篮子。

为什么改：等权成分股篮子和市值加权的基准比，会让整张板长期偏向 Lagging，
而且篮子成分一换、读数就跳。代理 ETF 的曲线连续、可复算、和任何人看到的
同一只基金一致。成分股名单继续用于 screener 与名单层，不进主题读数。

主键是 **ticker，不是基金显示名** —— 同一只基金在不同地方的显示名并不一致。

⚠️ 代理会换（实测：2026 年 6–7 月用 XLF/XLE/XLP/XLV 的位置，9 月换成了
等权的 RSPF/RSPG/RSPS/RSPH）。所以这张表带日期，改动要留痕，历史复算必须
用当时那一版，不能拿今天的表回算过去。
"""
from __future__ import annotations

# 表的版本日期：改这张表时一起改，历史复算按日期取表。
PROXY_MAP_DATE = "2026-09-24"

# 主题名（与 taxonomy 的 Theme 名一致） -> 代理 ETF
THEME_PROXIES: dict[str, str] = {
    "Cloud Software": "WCLD",
    "Silver Miners": "SIL",
    "Gold Miners": "GDX",
    "Cybersecurity": "HACK",
    "Genomics": "ARKG",
    "Growth Factor": "IWO",
    "Copper Miners": "COPX",
    "Software": "XSW",
    "Coal": "COAL",
    "Oil & Gas": "XOP",
    "Tech Mega Caps": "MAGS",
    "Energy": "RSPG",
    "Value Factor": "RPV",
    "Financials": "RSPF",
    "Fintech": "FINX",
    "Medical Devices": "XHE",
    "Insurance": "KIE",
    "High Beta Factor": "SPHB",
    "Steel": "SLX",
    "Physical AI & Humanoid Robotics": "KOID",
    "Drones": "DRNZ",
    "Small Caps": "IWM",
    "Robotics & Automation": "ROBO",
    "IPOs": "IPO",
    "Regional Banks": "KRE",
    "Consumer Retail": "XRT",
    "Agribusiness": "MOO",
    "Consumer Staples": "RSPS",
    "Semiconductors Large Caps": "SMH",
    "Crypto Equities": "BITQ",
    "Chemicals & Materials": "RSPM",
    "Optics & Networking Equipment": "LYTE",
    "Real Estate": "VNQ",
    "Transportation & Logistics": "XTN",
    "Space": "UFO",
    "Defense": "XAR",
    "Utilities": "RSPU",
    "Industrials": "RSPN",
    "Homebuilders": "XHB",
    "Travel & Leisure": "PEJ",
    "Uranium & Nuclear Energy": "URA",
    "Memory & Storage": "DRAM",
    "Semiconductors Broad": "XSD",
    "AI - Datacenters": "DTCR",
    "Quantum Computing": "WQTM",
    "AI Power & Infrastructure": "VOLT",
    "Lithium & Battery Tech": "BATT",
    "Clean Energy": "PBW",
    "Rare Earth Metals": "REXC",
    "Solar": "TAN",
}

# 没有可用代理、因此不进主题板的主题（Andy 2026-09-23 裁决：
# 「主题没有的我们也直接取消不要了」）。名单本身不受影响，
# 这些股票在 screener 与个股层照常出现。
RETIRED_FROM_BOARD: dict[str, str] = {
    "Mega Caps": "没有等价 ETF（MAGS 只含少数科技股，不是超大市值全体）",
    "Tobacco": "没有美国 ETF",
    "Household & Personal Products": "只有欧洲上市 ETF",
    "Beverages": "只有食品+饮料混合 ETF，口径不纯",
}

# 本来就是筛选规则而不是主题：成分每天变，没法有固定代理。
# 留在 screener，不上主题板（Andy 2026-09-23：「撤下」）。
SCREEN_ONLY: dict[str, str] = {
    "52-Week High Leaders": "规则：距 52 周高点 5% 以内 且 RS ≥ 85",
    "High Octane": "规则：日均波幅 ≥5% 且 RS ≥90 且 市值 ≥3 亿",
}


def board_themes() -> list[str]:
    """上主题板的主题名，按字母序。"""
    return sorted(THEME_PROXIES)
