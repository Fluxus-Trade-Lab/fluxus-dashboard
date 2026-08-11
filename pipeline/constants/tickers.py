"""
Cherry-picked from traderwillhu/market_dashboard — scripts/build_data.py lines 40-55.
144 ETFs organized into 6 groups for the macro/equities dashboard.
"""

STOCK_GROUPS = {
    "Indices": ["QQQE", "MGK", "QQQ", "IBIT", "RSP", "MDY", "IWM", "TLT", "SPY", "ETHA", "DIA"],
    "S&P Style ETFs": ["IJS", "IJR", "IJT", "IJJ", "IJH", "IJK", "IVE", "IVV", "IVW"],
    "Sel Sectors": ["XLK", "XLI", "XLC", "XLF", "XLU", "XLY", "XLRE", "XLP", "XLB", "XLE", "XLV"],
    "EW Sectors": ["RSPT", "RSPC", "RSPN", "RSPF", "RSP", "RSPD", "RSPU", "RSPR", "RSPH", "RSPM", "RSPS", "RSPG"],
    "Industries": [
        "TAN", "KCE", "IBUY", "QQQE", "JETS", "IBB", "SMH", "CIBR", "UTES", "ROBO", "IGV", "WCLD", "ITA", "PAVE", "BLOK", "AIQ", "IYZ", "PEJ", "FDN", "KBE",
        "UNG", "BOAT", "KWEB", "KRE", "IBIT", "XRT", "IHI", "DRIV", "MSOS", "SOCL", "XLU", "ARKF", "SLX", "ARKK", "XTN", "XME", "KIE", "GLD", "GXC", "SCHH",
        "GDX", "IPAY", "IWM", "XOP", "VNQ", "EATZ", "FXI", "DBA", "ICLN", "SILJ", "REZ", "LIT", "SLV", "XHB", "XHE", "PBJ", "USO", "DBC", "FCG", "XBI",
        "ARKG", "CPER", "XES", "OIH", "PPH", "FNGS", "URA", "WGMI", "REMX",
        # FFTY tracks the IBD 50. Held here so the theme layer can read its
        # price -- the list itself is IBD subscription content and is not ours
        # to republish, but the fund that tracks it is a tradeable instrument
        # with public daily pricing.
        "FFTY"
    ],
    "Countries": [
        "EZA", "ARGT", "EWA", "THD", "EIDO", "EWC", "GREK", "EWP", "EWG", "EWL", "EUFN", "EWY", "IEUR", "EFA", "ACWI",
        "IEV", "EWQ", "EWI", "EWJ", "EWW", "ECH", "EWD", "ASHR", "EWS", "KSA", "INDA", "EEM", "EWZ", "TUR", "EWH", "EWT", "MCHI"
    ]
}

# Flatten all tickers for batch operations
ALL_TICKERS = list({t for group in STOCK_GROUPS.values() for t in group})
