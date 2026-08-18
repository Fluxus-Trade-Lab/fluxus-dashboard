"""Theme taxonomy: the curated layer that sits above Finviz industries.

Two layers ship side by side:

* **Industry layer** -- all ~145 Finviz industries, mechanical and zero
  maintenance.  Built directly from ``universe.json``; no definitions here.
* **Theme layer** -- this file.  Themes cut *across* industries ("AI -
  Datacenters" spans semiconductors, utilities, industrials and REITs), or
  express factors and lists that are not industries at all ("High Octane",
  "Mega Caps", "Recent IPOs").

Every theme resolves by exactly one of four methods:

``industry``  map to one or more Finviz industry names -- free, exact
``etf``       industry backbone plus proxy-ETF holdings, intersected with our universe
``rule``      a predicate over universe columns -- free, zero maintenance
``proxy``     track the ETF's *own* price action, no constituents at all

``proxy`` exists because for a geography or a commodity the ETF **is** the
tradeable instrument.  KWEB's holdings are HK lines and INDA's are NSE lines,
so intersecting them with a US stock universe yields nothing -- but the fund
itself is exactly what you would buy.  Reaching for US-listed ADRs instead
would be measuring a different thing than the one being traded.

The starting set is The Setup Factory's published 53 themes (their
Thematic Focus View is public to subscribers) plus the cross-cutting and
factor themes their taxonomy has no slot for.  Attribution is tracked in
``source`` so we can tell borrowed structure from our own.

Governing rule for membership disputes
--------------------------------------
**When the story and the tape disagree, the tape decides.**

Worked example: several bitcoin miners (IREN, CORZ, WULF, HUT) have pivoted
much of their capacity to AI/HPC hosting, so on business grounds they belong
in AI - Datacenters.  Measured over the last year they still correlate 0.664
with pure crypto names and only 0.484 with datacenter names.  The market has
not repriced them, so they stay in Crypto Equities.  We are grouping names by
how they trade, not by what their filings say they do.

The crossover itself is worth watching: the day those two correlations swap is
the day the market accepts the pivot, and that is a tradeable observation
rather than a taxonomy chore.

Two guards on this rule, so it does not eat itself:

1. **The narrative still defines the candidate set.**  Price decides which of
   the plausible members belong, not which names are worth considering --
   otherwise this stops being a taxonomy and becomes an unsupervised cluster
   with labels stapled on afterwards.
2. **Selection and validation must not share a window.**  Assigning members by
   correlation and then validating the theme on correlation over the same
   period proves nothing.  ``validate_taxonomy`` therefore has to run on a
   period the membership decision did not use.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Mapping, Optional

# --------------------------------------------------------------------------
# Rule helpers -- predicates over a universe row.
# --------------------------------------------------------------------------


def _num(row: Mapping[str, Any], key: str) -> float | None:
    value = row.get(key)
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    return f if f == f else None  # drop NaN


def _high_octane(row: Mapping[str, Any]) -> bool:
    """Fast movers with real momentum and enough size to be tradeable."""
    adr = _num(row, "adr_pct")
    rs = _num(row, "rs_ibd")
    cap = _num(row, "market_cap")
    return (
        adr is not None and adr >= 5.0
        and rs is not None and rs >= 90.0
        and cap is not None and cap >= 3e8
    )


def _small_caps(row: Mapping[str, Any]) -> bool:
    cap = _num(row, "market_cap")
    return cap is not None and 1e9 <= cap < 1e10


def _mega_caps(row: Mapping[str, Any]) -> bool:
    cap = _num(row, "market_cap")
    return cap is not None and cap >= 2e11


def _growth_factor(row: Mapping[str, Any]) -> bool:
    """Momentum-as-growth proxy.

    ``eps_growth_next_y`` is null for all 3,000 universe rows, so the
    fundamental definition is unavailable.  Standing in for it: names with
    strong medium-term relative strength that are still trending.
    """
    rs = _num(row, "rs_ibd")
    p6 = _num(row, "perf_6m")
    sma200 = _num(row, "sma200_dist")
    return (
        rs is not None and rs >= 80.0
        and p6 is not None and p6 >= 0.20
        and sma200 is not None and sma200 > 0
    )


def _high_beta(row: Mapping[str, Any]) -> bool:
    adr = _num(row, "adr_pct")
    return adr is not None and adr >= 4.0


def _value_factor(row: Mapping[str, Any]) -> bool:
    """Proxy: beaten-down names still above their long-term average."""
    dist = _num(row, "high_52w")
    sma200 = _num(row, "sma200_dist")
    return (
        dist is not None and dist <= -0.25
        and sma200 is not None and sma200 > 0
    )


def _leaders_52w(row: Mapping[str, Any]) -> bool:
    dist = _num(row, "high_52w")
    rs = _num(row, "rs_ibd")
    return (
        dist is not None and dist >= -0.05
        and rs is not None and rs >= 85.0
    )


def _recent_ipo(row: Mapping[str, Any]) -> bool:
    """No IPO date in the feed; 1y perf being null while 3m exists is the tell."""
    return row.get("perf_1y") in (None, "") and row.get("perf_3m") not in (None, "")


# --------------------------------------------------------------------------
# Theme definition
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Theme:
    name: str
    method: str                                   # industry | etf | rule
    source: str = "tsf"                           # tsf | fluxus
    industries: tuple[str, ...] = ()
    etf: tuple[str, ...] = ()
    rule: Optional[Callable[[Mapping[str, Any]], bool]] = None
    extra: tuple[str, ...] = ()                   # manual adds (tickers)
    exclude: tuple[str, ...] = ()                 # manual removes (tickers)
    note: str = ""
    # What kind of thing this is, for the page to group by (2026-08-18 audit,
    # data/reference/theme_audit_2026-08-18.md). Derived unless set:
    #   theme  -- a business theme with a common driver (uranium price, DC capex)
    #   sector -- a Finviz-industry union whose common driver is macro (rates,
    #             oil): useful for rotation, but not what "theme" means on the page
    #   factor -- a rule over attributes (size, growth, beta); no common-driver test
    #   proxy  -- the fund IS the instrument
    kind: str = ""
    # Per-theme liquidity floor (market cap, dollar volume) for hand-written
    # `extra` names, overriding the global $1B / $2M tradeable gate. Only for
    # a theme whose real constituents live below the gate (Rare Earth: 7 of
    # TSF's 10 are $0.5-1B). Members admitted this way are still real rows;
    # the reading just admits it rests on thinner names.
    floor: tuple[float, float] | None = None
    # Publish even without a co-movement verdict. Only by the operator's
    # explicit call; the theme still ships its real `validation` field.
    publish_override: bool = False


# --------------------------------------------------------------------------
# A. Themes TSF publishes that map cleanly onto Finviz industries.
#    Free and exact -- no ETF fetch, no hand list.
# --------------------------------------------------------------------------

_INDUSTRY_THEMES: list[Theme] = [
    Theme("Semiconductors Broad", "industry",
          industries=("Semiconductors", "Semiconductor Equipment & Materials"),
          extra=(
                 "SNDK", "SHMD", "KOPN", "IPWR", "STX", "AEIS", "TRT", "TDY", "NVEC", "MRAM",
                 "ADEA", "LFUS", "LAES", "MBLY", "GSIT", "ALMU", "PENG", "PDFS", "ASYS", "CPSH",
                 "SNPS", "MKSI", "ATOM", "WDC", "AOSL", "CEVA", "CDNS", "QUIK", "SVCO", "VPG",
                 "BZAI",),
          note="TSF names added 2026-08-18 (Andy: 他们有我们没的加进去): SNDK SHMD KOPN IPWR STX AEIS TRT TDY NVEC MRAM ADEA LFUS LAES MBLY GSIT ALMU PENG PDFS ASYS CPSH SNPS MKSI ATOM WDC AOSL CEVA CDNS QUIK SVCO VPG BZAI."),
    Theme("Software", "industry",
          industries=("Software - Application", "Software - Infrastructure")),
    # Split 2026-08-09: "Banks" (344) and "Regional Banks" (324) overlapped
    # 94% -- one theme counted twice. Regionals and money-centre banks trade
    # on different things (NIM/CRE vs capital markets), so separate them.
    Theme("Regional Banks", "industry", industries=("Banks - Regional",)),
    Theme("Insurance", "industry",
          industries=("Insurance - Diversified", "Insurance - Property & Casualty",
                      "Insurance - Life", "Insurance - Specialty",
                      "Insurance - Reinsurance", "Insurance Brokers")),
    Theme("Homebuilders", "etf", etf=(),
          extra=(
                 "SKY", "SN", "WTS", "SWIM", "ARHS", "GFF", "HVT", "W", "LEGH", "JHX", "TILE",
                 "TREX", "OC", "JCI", "MHK", "DFH", "NX", "LGIH", "HNI", "CVCO", "WFG", "CCS",
                 "BZH", "ALLE", "AWI", "MLKN", "IBP", "TT", "ROCK", "WMS", "SSD", "MHO", "LOW",
                 "NVR", "PATK", "LZB", "RH", "DHI", "MBC", "WSM", "FND", "BCC", "CSL", "LII",
                 "SPXC", "AOS", "WHR", "APOG", "HOV", "MTH", "PHM", "HD", "CARR", "MAS", "GRBK",
                 "KBH", "ZWS", "LPX", "SGI", "POOL", "FELE", "ETD", "BLDR", "TOL", "SITE", "UFPI",
                 "LEG", "JBI", "ALH", "FBIN", "LEN", "QXO", "FOR",),
          note="candidate back-search 2026-08-18, Andy 采纳建议 (data/reference/theme_candidates_2026-08-18.md): LEN QXO FOR. TSF Thematic Focus list, 2026-08-18 (Andy: 按 TSF 改); data/reference/tsf_themes_2026-08-18/full.json. TSF's list is builders + building products + home "
               "furnishings (SN WTS MHK HNI POOL LEG WHR LOW HD). It also keeps "
               "TT JCI CARR LII (commercial HVAC) -- data-side reservation on "
               "record: those fail the common-driver test; kept because Andy said "
               "follow TSF. LEN-B BLD BBBY not in universe."),
    Theme("Oil & Gas", "industry",
          industries=("Oil & Gas E&P", "Oil & Gas Integrated", "Oil & Gas Midstream",
                      "Oil & Gas Refining & Marketing", "Oil & Gas Equipment & Services",
                      "Oil & Gas Drilling")),
    Theme("Gold Miners", "industry", source="tsf", industries=("Gold",),
          extra=(
                 "MAKO", "MTA", "DC", "HL", "PPTA", "ITRG", "CMCL", "AG", "GROY", "SKE", "CTGO",
                 "GLDG", "GAU", "CNL", "NFGC", "BVN", "TFPM", "USAU", "MUX", "IDR",),
          note="TSF names added 2026-08-18 (Andy: 他们有我们没的加进去; second pass): MAKO MTA DC HL PPTA ITRG CMCL AG GROY SKE CTGO GLDG GAU CNL NFGC BVN TFPM USAU MUX IDR."),
    Theme("Silver Miners", "industry", industries=("Silver",), extra=(
                 "HL", "SCZM", "ITRG", "FSM", "SSRM", "ASM", "HYMC", "GORO", "SSMR", "USAS", "CDE",
                 "SA", "WPM", "TMQ", "BVN", "CTGO", "VZLA", "PAAS", "OR", "TFPM", "MUX",),
          note="TSF names added 2026-08-18 (Andy: 他们有我们没的加进去): SCZM ITRG FSM SSRM ASM HYMC GORO SSMR USAS CDE SA WPM TMQ BVN CTGO VZLA PAAS OR TFPM MUX. HL added 2026-08-18: Hecla sits in Other Precious Metals on Finviz; TSF lists it under Silver."),
    # Umbrella split 2026-08-09. The combined theme read +0.047 on 94%
    # coverage while Copper alone read +0.357 -- merging copper, steel and
    # coal averaged away the one grouping that was working.
    Theme("Steel", "etf", etf=(),
          extra=(
                 "FRD", "GSM", "HCC", "ATI", "TX", "METC", "AMR", "SXC", "MT", "MTUS", "NUE",
                 "CLF", "IIIN", "RS", "PKX", "ASTL", "WS", "RYZ", "MSB", "CMC", "STLD", "CRS",
                 "EAF", "SID", "GGB", "TS", "NWPX",),
          note="candidate back-search 2026-08-18, Andy 采纳建议 (data/reference/theme_candidates_2026-08-18.md): NWPX. TSF Thematic Focus list, 2026-08-18 (Andy: 按 TSF 改); data/reference/tsf_themes_2026-08-18/full.json. Aluminum (AA CENX CSTM KALU) out -- a different price; "
               "it stays visible in the industry layer. TSF adds specialty "
               "metals/met coal (ATI CRS HCC AMR METC SXC)."),
    Theme("Coal", "industry", industries=("Coking Coal", "Thermal Coal")),
    # Industrial Metals removed 2026-08-10: 20 members correlated -0.0161
    # against size-matched random baskets -- its members were less synchronised
    # than a random draw. "Other Industrial Metals & Mining" is a Finviz
    # residual bucket, which is a filing category, not a trade. Still visible in
    # the industry layer; it just no longer claims to be a theme.
    Theme("Chemicals & Materials", "industry",
          industries=("Specialty Chemicals", "Chemicals", "Agricultural Inputs")),
    Theme("Agribusiness", "etf", etf=(),
          extra=(
                 "DAR", "USFD", "IPI", "ICL", "ADM", "MZTI", "NTR", "TTC", "NEOG", "SYY", "BG",
                 "PPC", "CENTA", "PAHC", "PFGC", "INGR", "LAND", "SEB", "CTVA", "CF", "DE", "ANDE",
                 "FMC", "UAN", "ZTS", "VITL", "UNFI", "LNN", "TSN", "MOS", "AGCO", "CNH", "HRL",
                 "CALM", "ELAN", "SFD", "SMG", "DNA", "BYND",),
          note="TSF Thematic Focus list, 2026-08-18 (Andy: 按 TSF 改); data/reference/tsf_themes_2026-08-18/full.json. Was Agricultural Inputs + Farm Products + Farm & HEAVY "
               "Construction Machinery -- CAT (405B) PCAR OSK TEX FSS BLBD came "
               "along. TSF: food chain + inputs + farm equipment. FDP not in universe."),
    Theme("Consumer Retail", "industry",
          industries=("Specialty Retail", "Internet Retail", "Apparel Retail",
                      "Discount Stores", "Home Improvement Retail")),
    # Packaged Foods removed 2026-08-10: +0.0092 against random on 29 members,
    # short of the +0.02 a weak verdict needs. The earlier split that folded
    # Confectioners in did not rescue it -- 29 packaged-food names move no more
    # together than 29 names drawn at random.
    Theme("Beverages", "industry", industries=("Beverages - Non-Alcoholic",)),
    Theme("Household & Personal Products", "industry",
          industries=("Household & Personal Products",)),
    Theme("Tobacco", "industry", industries=("Tobacco",)),
    Theme("Travel & Leisure", "industry",
          industries=("Travel Services", "Resorts & Casinos", "Lodging",
                      "Restaurants", "Airlines")),
    Theme("Transportation & Logistics", "industry",
          industries=("Integrated Freight & Logistics", "Trucking", "Railroads",
                      "Marine Shipping", "Airports & Air Services")),
    Theme("Utilities", "industry",
          industries=("Utilities - Regulated Electric", "Utilities - Diversified",
                      "Utilities - Regulated Gas", "Utilities - Renewable",
                      "Utilities - Regulated Water", "Utilities - Independent Power Producers")),
    Theme("Real Estate", "industry",
          industries=("REIT - Specialty", "REIT - Industrial", "REIT - Residential",
                      "REIT - Retail", "REIT - Office", "REIT - Healthcare Facilities",
                      "REIT - Hotel & Motel", "REIT - Diversified", "REIT - Mortgage",
                      "Real Estate Services")),
    # Constituents do not co-move (excess +0.011 on 168 names) and neither
    # theme is traded name-by-name here -- the exposure is taken through the
    # funds, so the funds are what we measure.
    Theme("Financials", "industry",
          industries=("Asset Management", "Capital Markets", "Financial Data & Stock Exchanges",
                      "Credit Services", "Financial Conglomerates")),
    Theme("Fintech", "etf", etf=(),
          extra=(
                 "JCAP", "CHYM", "PRAA", "RELY", "GWRE", "SHOP", "CRCL", "PAY", "FLYW", "ECPG",
                 "KSPI", "SE", "CPAY", "NCNO", "WEX", "BULL", "BLSH", "RKT", "GPN", "QTWO", "ENVA",
                 "BFH", "PGY", "WU", "MITK", "PURR", "HOOD", "NRDS", "INTU", "SYF", "FCFS", "OMF",
                 "PAYO", "WSE", "PYPL", "COIN", "BILL", "FUTU", "NU", "COF", "GDOT", "SSNC",
                 "GLXY", "CACC", "ALLY", "MA", "V", "HQY", "EVTC", "XYZ", "BKKT", "FISV", "EEFT",
                 "VERX", "NAVI", "SOFI", "UPST", "VIRT", "WRLD", "KLAR", "AFRM", "AXP", "EZPW",
                 "JKHY", "MELI", "PRG", "FIS", "NNI", "DLO", "ACIW", "PAGS", "VYX", "FINV", "MQ",
                 "QFIN", "DAVE", "RPAY", "STNE", "FOUR", "SECZ", "ETOR", "BLND", "SEZL", "BETR",
                 "GRAB",),
          note="candidate back-search 2026-08-18, Andy 采纳建议 (data/reference/theme_candidates_2026-08-18.md): GRAB. TSF Thematic Focus list, 2026-08-18 (Andy: 按 TSF 改); data/reference/tsf_themes_2026-08-18/full.json. Was Credit Services + Financial Data (37): exchanges and "
               "rating agencies, not fintech. TSF's list is payments/lending/"
               "brokerage software. LC not in universe."),
    Theme("Industrials", "industry",
          industries=("Specialty Industrial Machinery", "Engineering & Construction",
                      "Building Products & Equipment", "Industrial Distribution",
                      "Conglomerates", "Metal Fabrication")),
    # Split 2026-08-09: carriers and equipment vendors read -0.009 combined
    # on 99% coverage. A telco's revenue is a subscriber base; an optical
    # component maker's is a capex cycle. Nothing made them one theme but the
    # word "telecom".
    # Telecom Services removed 2026-08-10: +0.0042 on 37 members. Splitting the
    # carriers out from the equipment vendors was the right call and still left
    # a group that does not trade as one.
    Theme("Optics & Networking Equipment", "industry",
          industries=("Communication Equipment",),
          extra=(
                 "CRDO", "SMTC", "LPTH", "OPTX", "SKM", "AXTI", "AEVA", "POET", "SILC", "IDCC",
                 "LILAK", "SMCI", "FN", "MTSI", "MXL", "COHR", "BAND", "MRVL", "OCC", "GLW",
                 "KODK", "JBL", "OUST", "KEYS", "ANET", "GLIBK", "APH", "VZ", "IDT", "TIGO",
                 "TTMI", "TSEM", "LWLG", "AVNW", "PLAB", "ALMU", "TEL", "T", "CMCSA", "HSAI",
                 "TDS", "ADTN", "ATEX", "NTCT", "CALX", "QUBT", "MKSI", "UNIT", "LUMN", "TMUS",
                 "SHEN", "AD", "IPGP", "AVGO", "BKTI", "LBTYK", "NTGR", "ITG", "CLFD", "ATEN",
                 "CCOI", "AMPG", "LASR", "GOGO",),
          note="TSF 'Telecom, Optics & Connectivity' names added 2026-08-18 (Andy: 他的多,加进来): optics/interconnect (CRDO MRVL COHR FN AVGO ANET…) and the carriers (VZ T TMUS CMCSA…) on top of the Communication Equipment industry."),
    # "Diversified Tech" read +0.016 on 93% coverage -- the label was doing
    # all the work. Split into the three components with enough tradeable
    # names to score; Consumer Electronics (4) folds into Computer Hardware.
    # Computer Hardware removed 2026-08-10: +0.0005 on 20 members -- effectively
    # zero. Consumer Electronics had been folded in here and now has no theme
    # home, which is the honest outcome: neither label describes a group the
    # market prices together.
    # Was mapped to the whole Computer Hardware industry, which is servers and
    # peripherals -- hence -0.002 excess. Finviz has no memory industry, so
    # this is the hand-built list of actual memory and storage makers.
    Theme("Memory & Storage", "etf", etf=(),
          extra=(
                 "MU", "WDC", "STX", "SNDK", "NTAP", "P", "ONTO", "MRAM", "FORM", "SKHY", "PENG",
                 "LRCX", "RMBS", "SIMO",),
          note="TSF names added 2026-08-18 (Andy: 他们有我们没的加进去): P ONTO MRAM FORM SKHY PENG LRCX RMBS SIMO. MU sits in Semiconductors and WDC/STX/SNDK in Computer "
               "Hardware, which is exactly why no industry mapping works."),
    # NOTE: no "Aerospace & Defense" theme here -- it would resolve to exactly
    # the same 50 rows as the "Defense" theme below and show up twice in every
    # ranking. The industry layer already carries it separately.
    Theme("Energy", "industry",
          industries=("Oil & Gas E&P", "Oil & Gas Midstream", "Uranium",
                      "Solar", "Thermal Coal")),
]

# --------------------------------------------------------------------------
# B. Cross-cutting themes -- no industry expresses these.  Seeded from a
#    proxy ETF's holdings, intersected with our universe.
# --------------------------------------------------------------------------

# ETF top-holdings are thin (~10 names) and often foreign-listed, so most of
# these carry an *industry backbone* as well.  Members = ETF seed ∪ industries.
_ETF_THEMES: list[Theme] = [
    # --- TSF's list ---
    # COMM dropped 2026-08-09: does not resolve in a 5,615-row universe.
    Theme("AI - Datacenters", "etf", etf=(),
          extra=(
                 "NBIS", "SHAZ", "EROC", "CSQR", "WYFI", "DLR", "CRWV", "IREN", "VNET", "BRUN",
                 "IRM", "BXDC", "GDS", "EQIX", "APLD", "FRMI", "IOND", "DGXX", "GLXY", "AMT",
                 "WULF", "KEEL", "CORZ", "HUT", "CIFR", "PENG",),
          note="candidate back-search 2026-08-18, Andy 采纳建议 (data/reference/theme_candidates_2026-08-18.md): PENG. TSF Thematic Focus list, 2026-08-18 (Andy: 按 TSF 改); data/reference/tsf_themes_2026-08-18/full.json. TSF's cut: the buildings and hosts (colo/hyperscale "
               "hosts, DC REITs, miners turned AI hosts); the power and equipment "
               "side (GEV VRT ETN PWR CEG VST TLN) moved to AI Power & Infrastructure. "
               "Overlap with our old list was 5/25."),
    # Generation side only. Equipment lives in Grid & Electrification -- they
    # shared "Electrical Equipment & Parts" and both ETFs, overlapping 64%.
    Theme("AI Power & Infrastructure", "etf", etf=(),
          extra=(
                 "PLPC", "NPWR", "OKE", "WOLF", "PSIX", "IPWR", "NVTS", "AEIS", "BDC", "VGNT",
                 "NVT", "IESC", "JCI", "EMR", "ETN", "VICR", "NNE", "BELFB", "NUAI", "GEV", "PWR",
                 "ET", "WCC", "ITRI", "SEI", "MTZ", "INIO", "VRT", "FLEX", "MOD", "GNRC", "EME",
                 "EOSE", "FCEL", "WMB", "AME", "AZZ", "SMR", "XEL", "D", "AEE", "FPS", "CWEN",
                 "BE", "BW", "ON", "TT", "KMI", "POWI", "CEG", "FTAI", "EVRG", "MYRG", "PCG",
                 "ETR", "OGE", "DTE", "DUK", "SO", "BWXT", "LII", "ENS", "OKLO", "FIX", "CAT",
                 "HUBB", "MPWR", "DY", "AMSC", "VMI", "TLN", "HLIO", "PPL", "EXC", "NEE", "POWL",
                 "AGX", "CARR", "CMI", "STRL", "LNT", "PEG", "AEP", "IDA", "SRE", "AAON", "NI",
                 "PRIM", "VST", "ROK", "NRG", "FLNC", "INV", "FRMI", "EROC",),
          note="candidate back-search 2026-08-18, Andy 采纳建议 (data/reference/theme_candidates_2026-08-18.md): FRMI EROC. TSF Thematic Focus list, 2026-08-18 (Andy: 按 TSF 改); data/reference/tsf_themes_2026-08-18/full.json. Was UTES seed + regulated/IPP utilities (44, incl. HE, "
               "CIG, ENIC -- nothing to do with AI); TSF's cut is electrical "
               "equipment + grid contractors + IPPs + nuclear. Overlap was 23/93."),
    Theme("Cybersecurity", "etf", etf=(),
          extra=(
                 "RBRK", "ARQQ", "ZS", "CACI", "QLYS", "FSLY", "RPD", "ESTC", "LDOS", "NTSK", "S",
                 "CVLT", "FROG", "PANW", "NET", "SAIL", "CRWD", "VRNS", "SAIC", "OKTA", "DT",
                 "BAH", "RDWR", "AKAM", "CHKP", "BB", "TENB", "OSPN", "GEN", "FFIV", "NTCT",
                 "FTNT", "TLS", "ATEN", "DDOG",),
          note="TSF Thematic Focus list, 2026-08-18 (Andy: 按 TSF 改); data/reference/tsf_themes_2026-08-18/full.json. CIBR seed dropped: it brought AVGO (1.9T, dilution) and "
               "CSCO. TSF adds RBRK RPD CVLT CHKP RDWR OSPN NTCT ATEN BB and the "
               "gov-IT names (CACI LDOS SAIC BAH) and observability (DDOG DT ESTC)."),
    Theme("Robotics & Automation", "etf", etf=(),
          extra=(
                 "ZBRA", "ALNT", "PATH", "DDD", "TER", "PRLB", "CCXI", "EMR", "VELO", "AEVA",
                 "PDYN", "PRCT", "RR", "OUST", "OII", "MANH", "ZBH", "TDY", "ARBE", "LIDR", "MBLY",
                 "NOVT", "LECO", "PH", "HSAI", "AMBA", "MCHP", "BSX", "TSLA", "IOT", "UBER",
                 "AMBQ", "GMED", "ISRG", "AUR", "NDSN", "IPGP", "PONY", "DE", "CGNX", "XPEV",
                 "KITT", "CTS", "OMCL", "ROK", "INVZ", "SSYS", "CAT", "SYNA", "PTC", "WRD", "NNDM",
                 "KDK", "TRMB", "AGCO", "CRNC", "GXO", "HON", "SYM", "KSCP", "APTV", "SERV",
                 "MBOT", "JBTM", "VPG",),
          note="TSF Thematic Focus list, 2026-08-18 (Andy: 按 TSF 改); data/reference/tsf_themes_2026-08-18/full.json. Was ROBO/DRIV seed + Specialty Industrial Machinery (60, "
               "incl. NVDA GOOGL MSFT ILMN and general industrials); overlap with "
               "TSF was 9/65. Whole list replaced."),
    Theme("Space", "etf", etf=(),
          extra=(
                 "VOYG", "LUNR", "SATL", "VELO", "RDW", "SIDU", "TSAT", "BKSY", "SPCX", "IRDM",
                 "VSAT", "GSAT", "AADX", "FLY", "MNTS", "ECHO", "RKLB", "PL", "ASTS", "SPIR",
                 "SPCE", "MDA", "FJET", "HAWK", "GILT", "YSS",),
          note="TSF Thematic Focus list, 2026-08-18 (Andy: 按 TSF 改); data/reference/tsf_themes_2026-08-18/full.json. Adds SPCX (was only in Defense), VOYG MDA IRDM VSAT GSAT "
               "AADX FLY SPCE HAWK GILT YSS. SPCX will trip the dilution rule; it "
               "is the theme's price-setter, accepted."),
    # No ETF seed. ARKX is a broad space/innovation fund and dragged in AMD,
    # AMZN, GOOG, DE, LHX and SPCX -- seven of thirteen "drone" names were not
    # drones, which is what the +0.017 excess was actually measuring.
    Theme("Drones", "etf", etf=(),
          extra=(
                 "KTOS", "AVAV", "ONDS", "UMAC", "RCAT", "EH", "BETA", "ZENA", "AIRO", "ACHR",
                 "SWMR", "AVEX", "EMBJ", "UAVS", "PDYN", "MRCY", "ESLT", "AMPX", "DPRO", "JOBY",
                 "SRFM", "EVTL",),
          note="TSF names added 2026-08-18 (Andy: 他们有我们没的加进去): BETA ZENA AIRO ACHR SWMR AVEX EMBJ UAVS PDYN MRCY ESLT AMPX DPRO JOBY SRFM EVTL. Pure-play list; no ETF seed (ARKX dragged in AMD/AMZN/GOOG). "
               "DPRO, UAVS and AIRO were considered and dropped 2026-08-09: "
               "all three sit below the theme-tracking liquidity floor "
               "($54-268M cap), so their prints would shape a reading they "
               "could not support a position in."),
    Theme("Defense", "etf", etf=("ITA",), industries=("Aerospace & Defense",),
          extra=(
                 "CACI", "ISSC", "PLTR", "BKSY", "ATI", "ELMT", "LDOS", "ASTC", "BBAI", "SPIR",
                 "PKE", "SAIC", "ONDS", "CPSH", "PSN", "BAH", "IRDM", "TATT", "POWW", "CRS", "RBC",
                 "RGR", "SWBI", "MRLN", "AMTM", "TDY", "ESE",),
          note="second-round list 2026-08-18, Andy 采纳数据端倾向: TDY ESE. TSF names added 2026-08-18 (Andy: 他们有我们没的加进去; second pass): CACI ISSC PLTR BKSY ATI ELMT LDOS ASTC BBAI SPIR PKE SAIC ONDS CPSH PSN BAH IRDM TATT POWW CRS RBC RGR SWBI MRLN AMTM."),
    Theme("Solar", "etf", etf=("TAN",), industries=("Solar",),
          extra=(
                 "MWH", "RNW", "DQ", "ENLT", "ASTI", "JKS", "SPWR", "TYGO", "ARRY", "TE",),
          note="candidate back-search 2026-08-18, Andy 采纳建议 (data/reference/theme_candidates_2026-08-18.md): TE. TSF names added 2026-08-18 (Andy: 他们有我们没的加进去; second pass): MWH RNW DQ ENLT ASTI JKS SPWR TYGO ARRY."),
    Theme("Clean Energy", "etf", etf=("ICLN",),
          industries=("Solar", "Utilities - Renewable"),
          extra=(
                 "PLPC", "ELVR", "NRGV", "ASPN", "NVT", "ADUR", "NVTS", "AMRC", "LZM", "ATLX",
                 "SQM", "HASI", "GEV", "PWR", "ETN", "WCC", "ATKR", "ITRI", "ALB", "SLI", "GEVO",
                 "GNRC", "HUBB", "ESE", "ENS", "LAR", "LAC", "EOSE", "FCEL", "REX", "MYRG", "NEE",
                 "TE", "GPRE", "SGML", "JKS", "BW", "AMSC", "POWL", "AGX", "BLDP", "EVGO", "CLNE",
                 "ARRY", "AES",),
          note="candidate back-search 2026-08-18, Andy 采纳建议 (data/reference/theme_candidates_2026-08-18.md): AES. TSF names added 2026-08-18 (Andy: 他们有我们没的加进去; second pass): PLPC ELVR NRGV ASPN NVT ADUR NVTS AMRC LZM ATLX SQM HASI GEV PWR ETN WCC ATKR ITRI ALB SLI GEVO GNRC HUBB ESE ENS LAR LAC EOSE FCEL REX MYRG NEE TE GPRE SGML JKS BW AMSC POWL AGX BLDP EVGO CLNE ARRY."),
    Theme("Uranium & Nuclear Energy", "etf", etf=(),
          extra=(
                 "GHM", "NUCL", "UROY", "UUUU", "ISOU", "EMR", "AMRC", "XE", "NKLR", "IMSR", "UEC",
                 "NNE", "FLR", "GEV", "FLS", "HII", "MTZ", "NXE", "J", "LEU", "DNN", "CCJ", "EU",
                 "PWR", "TLN", "CEG", "URG", "OKLO", "SMR", "SOLS", "MIR", "BWXT", "ASPI", "LTBR",
                 "VST", "CW", "NRG", "AMTM", "ACM", "STDN",),
          note="candidate back-search 2026-08-18, Andy 采纳建议 (data/reference/theme_candidates_2026-08-18.md): STDN. TSF Thematic Focus list, 2026-08-18 (Andy: 按 TSF 改); data/reference/tsf_themes_2026-08-18/full.json. TSF's 50 minus the 11 regulated utilities (PCG XEL ETR D "
               "PNW DTE DUK SO NEE PEG AEP -- they belong to Utilities and would "
               "dilute a nuclear read); IPPs with nuclear fleets (CEG VST TLN NRG) "
               "kept. Was URA seed + Uranium industry (8)."),
    Theme("Lithium & Battery Tech", "etf", etf=("LIT",),
          extra=(
                 "ALB", "SQM", "LAC", "SLI", "ELVR", "ENS", "EOSE", "FLNC", "AMPX", "CBAT", "WWR",
                 "HBM", "LOT", "NRGV", "XPON", "TECK", "FCX", "STI", "FLUX", "ELBM", "QS", "BHP",
                 "ABAT", "NMG", "DFLI", "VFS", "XPEV", "RIVN", "NIO", "LCID", "ATLX", "SLDP",
                 "SGML", "STEM", "LAR", "MVST", "IONR", "SES", "PSNY", "LI", "ELVA", "ENVX",),
          note="TSF names added 2026-08-18 (Andy: 他们有我们没的加进去): CBAT WWR HBM LOT NRGV XPON TECK FCX STI FLUX ELBM QS BHP ABAT NMG DFLI VFS XPEV RIVN NIO LCID ATLX SLDP SGML STEM LAR MVST IONR SES PSNY LI ELVA ENVX. SQM added 2026-08-18 (was mis-filed under Rare Earth via REMX). PLL -> ELVR 2026-08-09: PLL gone, ELVR verified in universe. "
               "ENS (EnerSys) is a genuine battery maker but weighted to "
               "industrial lead-acid, not lithium -- kept because the theme is "
               "named 'Battery Tech', but it is the loosest fit in the list."),
    Theme("Rare Earth Metals", "etf", etf=(), floor=(2e8, 1e6), publish_override=True,
          extra=(
                 "ALOY", "MP", "AREC", "METC", "UUUU", "IDR", "USAR", "NB", "CRML", "UAMY", "PPTA",),
          note="second-round list 2026-08-18, Andy 采纳数据端倾向: PPTA. TSF Thematic Focus list, 2026-08-18 (Andy: 按 TSF 改); data/reference/tsf_themes_2026-08-18/full.json. REMX seed dropped: it brought ALB SQM (lithium) and TMC "
               "(deep-sea nodules)."),
    Theme("Copper Miners", "etf", etf=("COPX",), industries=("Copper",),
          extra=(
                 "TMQ", "WRN", "BHP", "RIO", "VALE",),
          note="TSF names added 2026-08-18 (Andy: 他们有我们没的加进去): TMQ WRN BHP RIO VALE."),
    Theme("Crypto Equities", "etf", etf=(),
          extra=(
                 "COIN", "MARA", "RIOT", "CLSK", "HUT", "CIFR", "WULF", "IREN", "HIVE", "CORZ",
                 "GLXY", "BMNR", "SBET", "BTDR", "MSTR", "FIGR", "CRCL", "BTBT", "PURR", "BLSH",
                 "ABTC", "HOOD", "XYZ", "BKKT", "DGXX", "KEEL", "ETOR", "GPUS", "XXI",),
          note="candidate back-search 2026-08-18, Andy 采纳建议 (data/reference/theme_candidates_2026-08-18.md): XXI. TSF names added 2026-08-18 (Andy: 他们有我们没的加进去): FIGR CRCL BTBT PURR BLSH ABTC HOOD XYZ BKKT DGXX KEEL ETOR GPUS. No ETF seed: BLOK is diversified fintech and pulled in AMD. "
               "BITF dropped 2026-08-09: does not resolve."),
    # Was 60% the same names as Crypto Equities. Bitcoin the *asset* and
    # bitcoin *stocks* are different reads -- spot leads, equities amplify.
    Theme("Tech Mega Caps", "etf", etf=("MGK",), exclude=("LLY",),
          note="MGK is a mega-cap GROWTH fund, not a tech fund, so its top "
               "holdings can include growth names that are not technology. "
               "LLY excluded 2026-08-10 on the AMGN precedent: a pharma "
               "priced off drug franchises does not belong in a theme named "
               "Tech, however it screens. Found when the primary-group rule "
               "assigned LLY here as its identity."),
    Theme("Semiconductors Large Caps", "etf", etf=("SMH",)),
    # TSF's Medical Devices list, transcribed from their Thematic Focus
    # table 2026-08-11 — all 81 names verified present in our universe, 21
    # under the $1B floor (on record, not scored). IHI seeds the theme so
    # holdings drift keeps tracking the fund as the hand list ages. Same
    # co-movement gate as every curated theme; no exemption for borrowing.
    Theme("Medical Devices", "etf", etf=("IHI",),
          extra=("VREX", "BFLY", "SMTI", "UFPT", "SGHT", "ITGR", "MMSI",
                 "KIDS", "ANGO", "TNDM", "PLSE", "KMTS", "GKOS", "TMDX",
                 "AXGN", "SENS", "PRCT", "DXCM", "BAX", "INSP", "BDX",
                 "ATRC", "MMED", "GEHC", "CNMD", "ICUI", "DRTS", "EW",
                 "ABT", "TMCI", "BVS", "NYXH", "BSX", "ISRG", "GMED",
                 "AVR", "ATEC", "STAA", "STE", "COO", "HAE", "RMD",
                 "SOLV", "NVST", "BLCO", "SI", "MOBI", "IRTC", "SIBN",
                 "ALC", "PHG", "IDXX", "CBLL", "ZBH", "MDT", "TCMD",
                 "ALGN", "SYK", "BBNX", "PEN", "NVCR", "TFX", "AORT",
                 "CLPT", "INMD", "NPCE", "SNN", "IRMD", "LIVN", "LNTH",
                 "OMCL", "XRAY", "IART", "PODD", "OFIX", "ENOV", "MDLN",
                 "CERS", "LMAT", "QDEL", "ESTA")),
    # TSF's Genomics list, transcribed from their Thematic Focus table
    # 2026-08-11 — all 61 names, verified present in our universe. ~21 sit
    # under the $1B floor and drop from scoring while staying on the record
    # here; the floor is the filter, not the transcription. ARKG seeds the
    # theme so holdings drift tracks the fund even if this list ages.
    # Publication is NOT automatic: etf-method themes need a co-movement
    # verdict of real/weak, same bar as every other curated theme.
    Theme("Genomics", "etf", etf=("ARKG",),
          extra=(
                 "TWST", "SOPH", "CAI", "CDNA", "TXG", "NEO", "NTRA", "ABEO", "SCTX", "WGS",
                 "SDGR", "ADPT", "DYN", "CSTL", "ARCT", "PSNL", "PRAX", "TEM", "QURE", "ABSI",
                 "TSHA", "ALMR", "RGNX", "ARWR", "BNTC", "GH", "NTLA", "STOK", "LEGN", "IONS",
                 "ILMN", "FLGT", "CRSP", "RCKT", "GRAL", "SANA", "RXRX", "BEAM", "SLDB", "SRPT",
                 "GENB", "MRNA", "QGEN", "EDIT", "PRME", "LXEO", "VYGR", "CRBU", "WVE", "DNA",
                 "LAB", "BNTX", "QSI", "RARE", "KRYS", "MRVI", "PACB", "VCYT", "ALNY", "BLLN",
                 "MYGN", "AZTA",),
          note="second-round list 2026-08-18, Andy 采纳数据端倾向: AZTA."),
    # `proxy`, not `etf`: you cannot buy the list, you buy the fund that tracks
    # it, which is exactly the case this method exists for. It also settles the
    # sourcing question -- the IBD 50 is Investor's Business Daily subscription
    # content and not ours to republish, while FFTY's price is public. The two
    # routes that would have given constituents both fail on their own terms:
    # yfinance returns only the top 10 holdings, which would ship a ten-name
    # basket under a fifty-name label, and the issuer's holdings file is not at
    # any path worth guessing at. Tracking the fund needs no fetch at all, and
    # it re-weights itself whenever the list does.

    # --- Fluxus additions: TSF has no slot for these ---
    Theme("Quantum Computing", "etf", publish_override=True, source="fluxus", etf=(),
          extra=(
                 "IONQ", "RGTI", "QBTS", "QUBT", "ARQQ", "QMCO", "IBM", "QNT", "INFQ", "HQ",
                 "IQMX", "ALMU", "BTQ", "XNDU",),
          note="TSF names added 2026-08-18 (Andy: 他们有我们没的加进去; second pass): QNT INFQ HQ IQMX ALMU BTQ XNDU. IBM added by hand 2026-08-10. It fails the standard's first "
               "two tests the way AMGN did for GLP-1: quantum is a rounding "
               "error against ~$62B of revenue, and the share price is set by "
               "software, consulting and mainframe. Kept because the operator "
               "asked for it; watch the co-movement verdict, which is the "
               "check that does not care who asked."),
    # Both GLP-1 themes removed 2026-08-10. Not for failing validation -- for
    # being unable to face it. The $1B floor left Clinical Stage with 2 members
    # and Commercial with 2, and two members make one pair, which cannot be
    # compared against random baskets at all. They read `measurable=False`.
    #
    # The membership work behind them is worth keeping in mind if they are ever
    # rebuilt: AMGN and CORT were both rejected on the standard (a diversified
    # $222B biotech is priced off its other franchises; Corcept is Cushing's,
    # and only matched because "cortisol" sat in a keyword list), and the
    # combined five-name version correlated BELOW random at -0.068 on full
    # coverage. A correct business list is not automatically a group that
    # trades together, and that finding survives the themes being deleted.
    Theme("Physical AI & Humanoid Robotics", "etf", source="tsf", etf=(),
          extra=(
                 "INDI", "ALNT", "CCXI", "AMBA", "AEVA", "ARBE", "LIDR", "MBLY", "RR", "AMCI",
                 "OUST", "AUR", "HSAI", "TKR", "NOVT", "PONY", "XPEV", "INVZ", "TSLA", "WRD",
                 "KDK", "SYM", "KSCP", "SERV", "VPG", "MVIS", "LSCC",),
          note="second-round list 2026-08-18, Andy 采纳数据端倾向: LSCC. TSF Thematic Focus list, added 2026-08-18 (Andy: 要的); data/reference/tsf_themes_2026-08-18/full.json."),
    Theme("Cloud Software", "etf", source="tsf", etf=(),
          extra=(
                 "TEAM", "AMPL", "WIX", "PAYC", "FSLY", "PATH", "MDB", "ESTC", "VEEV", "RNG",
                 "INTA", "PLTR", "SHOP", "BLZE", "TWLO", "FROG", "GTLB", "FIVN", "SNOW", "BAND",
                 "WDAY", "SPT", "ZM", "DT", "CCC", "PCOR", "BILL", "SPSC", "BLKB", "BRZE", "NET",
                 "ALKT", "NTNX", "PAR", "TTAN", "GTM", "PD", "IOT", "MANH", "FRSH", "TYL", "TOST",
                 "NAVN", "QTWO", "YEXT", "BOX", "DBX", "KARO", "MNDY", "GWRE", "DOCU", "DCBO",
                 "DOCN", "NCNO", "INTU", "LAW", "PCTY", "ASAN", "NOW", "CXM", "CRM", "APPF",
                 "PEGA", "AGYS", "ADBE", "FIG", "AI", "LSPD", "AVPT", "DSGX", "NICE", "KVYO",
                 "GLOO", "DDOG", "HUBS", "BL", "EVCM", "WEAV", "NABL", "ZETA",),
          note="candidate back-search 2026-08-18, Andy 采纳建议 (data/reference/theme_candidates_2026-08-18.md): ZETA. TSF Thematic Focus list, added 2026-08-18 (Andy: 要的); data/reference/tsf_themes_2026-08-18/full.json."),
    Theme("Consumer Staples", "etf", source="tsf", etf=(),
          extra=(
                 "TBBB", "SENEA", "FRPT", "YSWY", "GO", "JJSF", "USFD", "OFRM", "CLX", "CAG",
                 "DEO", "TGT", "PRMB", "CELH", "TPB", "ENR", "GIS", "MKC", "ADM", "MICC", "REYN",
                 "EPC", "SJM", "LW", "JBSS", "BG", "ACI", "MZTI", "MGPI", "COCO", "WMT", "INGR",
                 "HSY", "KOF", "CASY", "WEST", "DLTR", "KO", "JBS", "PPC", "TR", "FLO", "AVO",
                 "MDLZ", "CL", "OLLI", "KMB", "BF-A", "BF-B", "PEP", "KVUE", "ANDE", "CENTA",
                 "CHD", "AGRO", "CCEP", "MNST", "HELE", "SMPL", "NOMD", "IMKTA", "DG", "MAMA",
                 "PSMT", "SFM", "NGVC", "BRBR", "COKE", "UNFI", "CPB", "COST", "EL", "STZ", "SPB",
                 "PG", "FIZZ", "PM", "TSN", "KDP", "SAM", "BJ", "TAP", "BGS", "KR", "SYY", "UL",
                 "HRL", "HLF", "KHC", "MO", "BTI", "FMX", "CALM", "BUD", "PFGC", "NUS", "DOLE",
                 "WMK", "POST", "VITL", "SFD", "UVV",),
          note="TSF Thematic Focus list, added 2026-08-18 (Andy: 要的); data/reference/tsf_themes_2026-08-18/full.json. Not in universe: FDP CVGW."),
]

# --------------------------------------------------------------------------
# C. Factor and list themes -- pure rules over universe columns.
#    Zero maintenance, and the category Finviz industries cannot express.
# --------------------------------------------------------------------------

_RULE_THEMES: list[Theme] = [
    Theme("Growth Factor", "rule", rule=_growth_factor),
    Theme("Value Factor", "rule", rule=_value_factor),
    Theme("High Beta Factor", "rule", rule=_high_beta),
    # Microcaps removed 2026-08-10: the $1B tradeable floor deletes by
    # definition the thing this theme exists to track, so it reported 0 members.
    # It needs its own floor to come back, not this one.
    Theme("Small Caps", "rule", rule=_small_caps),
    Theme("Mega Caps", "rule", rule=_mega_caps),
    Theme("IPOs", "rule", rule=_recent_ipo),
    Theme("High Octane", "rule", source="fluxus", rule=_high_octane,
          note="Fast + strong + tradeable. TSF uses the label; the rule is ours."),
    Theme("52-Week High Leaders", "rule", source="fluxus", rule=_leaders_52w),
]

THEMES: list[Theme] = _INDUSTRY_THEMES + _ETF_THEMES + _RULE_THEMES

# Sector buckets: industry unions of 50-185 names whose members move on
# macro, not on a product narrative. Named explicitly (not by size) so a
# small sector and a large theme are still told apart.
SECTOR_NAMES: frozenset = frozenset({
    "Software", "Regional Banks", "Oil & Gas", "Financials", "Industrials",
    "Real Estate", "Energy", "Insurance", "Utilities",
    "Travel & Leisure", "Consumer Retail", "Chemicals & Materials",
    "Transportation & Logistics",
    "Agribusiness", "Beverages",
    "Household & Personal Products", "Tobacco", "Consumer Staples",
    # Homebuilders, Semiconductors Broad, Gold/Silver/Copper/Steel/Coal stay
    # `theme`: single-industry groups with one price/rate driver, traded as
    # themes on the page even though they resolve by industry.
})


def kind_of(t: Theme) -> str:
    if t.kind:
        return t.kind
    if t.method == "rule":
        return "factor"
    if t.method == "proxy":
        return "proxy"
    return "sector" if t.name in SECTOR_NAMES else "theme"


def by_kind() -> Dict[str, List[Theme]]:
    out: Dict[str, List[Theme]] = {}
    for t in THEMES:
        out.setdefault(kind_of(t), []).append(t)
    return out

# Themes still needing a hand-built member list before they mean anything.
NEEDS_MANUAL: tuple[str, ...] = (
    "AI - Datacenters",
    "Quantum Computing",
    "Memory & Storage",
)
# Dropped from this list 2026-08-10: "GLP-1 / Obesity" (both halves removed --
# the $1B floor left two members each, too few to validate at all) and
# "IBD 50", which now tracks FFTY as a proxy and needs no hand list.


def by_name() -> Dict[str, Theme]:
    return {t.name: t for t in THEMES}


def by_method() -> Dict[str, List[Theme]]:
    out: Dict[str, List[Theme]] = {}
    for t in THEMES:
        out.setdefault(t.method, []).append(t)
    return out


def summary() -> Dict[str, Any]:
    methods = by_method()
    return {
        "total": len(THEMES),
        "by_method": {k: len(v) for k, v in methods.items()},
        "by_kind": {k: len(v) for k, v in by_kind().items()},
        "by_source": {
            "tsf": sum(1 for t in THEMES if t.source == "tsf"),
            "fluxus": sum(1 for t in THEMES if t.source == "fluxus"),
        },
        "needs_manual": list(NEEDS_MANUAL),
    }
