"""
Cherry-picked from traderwillhu/market_dashboard — scripts/build_data.py lines 111-139.
Sector/industry color mapping for frontend visualization.
"""

SECTOR_COLORS = {
    "Information Technology": "#3f51b5",
    "Industrials": "#333",
    "Emerging Markets": "#00bcd4",
    "Consumer Discretionary": "#4caf50",
    "Health Care": "#e91e63",
    "Financials": "#ff5722",
    "Energy": "#795548",
    "Communication Services": "#9c27b0",
    "Real Estate": "#673ab7",
    "Commodities": "#8b6914",
    "Materials": "#ff9800",
    "Utilities": "#009688",
    "Consumer Staples": "#8bc34a",
    "Broad Market": "#9e9e9e",
}

Industries_COLORS = {
    "SMH": "#3f51b5", "ARKK": "#3f51b5", "XTN": "#333", "KWEB": "#00bcd4",
    "XRT": "#4caf50", "KRE": "#ff5722", "ARKF": "#3f51b5", "ARKG": "#e91e63",
    "BOAT": "#333", "DRIV": "#4caf50", "KBE": "#ff5722", "XES": "#795548",
    "XBI": "#e91e63", "OIH": "#795548", "SOCL": "#9c27b0", "ROBO": "#333",
    "AIQ": "#3f51b5", "XHB": "#4caf50", "FNGS": "#9e9e9e", "BLOK": "#3f51b5",
    "LIT": "#ff9800", "WCLD": "#3f51b5", "XOP": "#795548", "FDN": "#4caf50",
    "TAN": "#795548", "IBB": "#e91e63", "PAVE": "#333", "PEJ": "#4caf50",
    "KCE": "#ff5722", "XHE": "#e91e63", "IBUY": "#4caf50", "MSOS": "#4caf50",
    "FCG": "#795548", "JETS": "#4caf50", "IPAY": "#ff5722", "SLX": "#ff9800",
    "IGV": "#3f51b5", "CIBR": "#3f51b5", "PPH": "#e91e63",
    "IHI": "#e91e63", "UTES": "#009688", "ICLN": "#795548", "XME": "#ff9800",
    "IYZ": "#9c27b0", "URA": "#795548", "ITA": "#333", "VNQ": "#673ab7",
    "SCHH": "#673ab7", "KIE": "#ff5722", "REZ": "#673ab7", "CPER": "#8b6914",
    "PBJ": "#8bc34a", "SLV": "#8b6914", "GLD": "#8b6914", "SILJ": "#ff9800",
    "GDX": "#ff9800", "FXI": "#00bcd4", "GXC": "#00bcd4", "USO": "#8b6914",
    "DBA": "#8b6914", "UNG": "#8b6914", "DBC": "#8b6914", "WGMI": "#3f51b5",
    "REMX": "#ff9800",
}


def _build_ticker_to_sector() -> dict[str, str]:
    """Reverse-map industry ticker -> sector name via shared colors."""
    color_to_sector = {c: s for s, c in SECTOR_COLORS.items()}
    return {t: color_to_sector.get(c, "Broad Market") for t, c in Industries_COLORS.items()}


TICKER_TO_SECTOR = _build_ticker_to_sector()
