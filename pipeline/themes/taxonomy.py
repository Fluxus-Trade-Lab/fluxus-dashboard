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


# --------------------------------------------------------------------------
# A. Themes TSF publishes that map cleanly onto Finviz industries.
#    Free and exact -- no ETF fetch, no hand list.
# --------------------------------------------------------------------------

_INDUSTRY_THEMES: list[Theme] = [
    Theme("Semiconductors Broad", "industry",
          industries=("Semiconductors", "Semiconductor Equipment & Materials")),
    Theme("Software", "industry",
          industries=("Software - Application", "Software - Infrastructure")),
    Theme("Biotech", "proxy", etf=("XBI",)),
    # Split 2026-08-09: "Banks" (344) and "Regional Banks" (324) overlapped
    # 94% -- one theme counted twice. Regionals and money-centre banks trade
    # on different things (NIM/CRE vs capital markets), so separate them.
    Theme("Banks - Money Center", "industry", industries=("Banks - Diversified",)),
    Theme("Regional Banks", "industry", industries=("Banks - Regional",)),
    Theme("Insurance", "industry",
          industries=("Insurance - Diversified", "Insurance - Property & Casualty",
                      "Insurance - Life", "Insurance - Specialty",
                      "Insurance - Reinsurance", "Insurance Brokers")),
    Theme("Homebuilders", "industry",
          industries=("Residential Construction", "Building Products & Equipment")),
    Theme("Oil & Gas", "industry",
          industries=("Oil & Gas E&P", "Oil & Gas Integrated", "Oil & Gas Midstream",
                      "Oil & Gas Refining & Marketing", "Oil & Gas Equipment & Services",
                      "Oil & Gas Drilling")),
    Theme("Gold Miners", "industry", source="tsf", industries=("Gold",)),
    Theme("Silver Miners", "industry", industries=("Silver",)),
    # Umbrella split 2026-08-09. The combined theme read +0.047 on 94%
    # coverage while Copper alone read +0.357 -- merging copper, steel and
    # coal averaged away the one grouping that was working.
    Theme("Steel", "industry", industries=("Steel", "Aluminum")),
    Theme("Coal", "industry", industries=("Coking Coal", "Thermal Coal")),
    # Industrial Metals removed 2026-08-10: 20 members correlated -0.0161
    # against size-matched random baskets -- its members were less synchronised
    # than a random draw. "Other Industrial Metals & Mining" is a Finviz
    # residual bucket, which is a filing category, not a trade. Still visible in
    # the industry layer; it just no longer claims to be a theme.
    Theme("Chemicals & Materials", "industry",
          industries=("Specialty Chemicals", "Chemicals", "Agricultural Inputs")),
    Theme("Agribusiness", "industry",
          industries=("Agricultural Inputs", "Farm Products", "Farm & Heavy Construction Machinery")),
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
    Theme("Healthcare", "proxy", etf=("XLV",)),
    Theme("Financials", "industry",
          industries=("Asset Management", "Capital Markets", "Financial Data & Stock Exchanges",
                      "Credit Services", "Financial Conglomerates")),
    Theme("Fintech", "industry",
          industries=("Credit Services", "Financial Data & Stock Exchanges")),
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
          industries=("Communication Equipment",)),
    # "Diversified Tech" read +0.016 on 93% coverage -- the label was doing
    # all the work. Split into the three components with enough tradeable
    # names to score; Consumer Electronics (4) folds into Computer Hardware.
    Theme("Electronic Components", "industry",
          industries=("Electronic Components",)),
    # Computer Hardware removed 2026-08-10: +0.0005 on 20 members -- effectively
    # zero. Consumer Electronics had been folded in here and now has no theme
    # home, which is the honest outcome: neither label describes a group the
    # market prices together.
    Theme("IT Services", "industry",
          industries=("Information Technology Services",)),
    # Was mapped to the whole Computer Hardware industry, which is servers and
    # peripherals -- hence -0.002 excess. Finviz has no memory industry, so
    # this is the hand-built list of actual memory and storage makers.
    Theme("Memory & Storage", "etf", etf=(),
          extra=("MU", "WDC", "STX", "SNDK", "NTAP"),
          note="MU sits in Semiconductors and WDC/STX/SNDK in Computer "
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
          extra=("VRT", "SMCI", "DLR", "EQIX", "CIEN", "ANET", "MOD",
                 "GEV", "PWR", "ETN", "VST", "TLN", "CEG", "NBIS", "APLD", "CRWV"),
          note="No ETF seed: AIQ is broad-AI and dragged in AAPL/AMZN, "
               "diluting the datacenter read into a megacap read."),
    # Generation side only. Equipment lives in Grid & Electrification -- they
    # shared "Electrical Equipment & Parts" and both ETFs, overlapping 64%.
    Theme("AI Power & Infrastructure", "etf", etf=("UTES",),
          industries=("Utilities - Regulated Electric",
                      "Utilities - Independent Power Producers")),
    Theme("Broad AI Theme", "etf", etf=("AIQ",),
          industries=("Semiconductors", "Software - Infrastructure")),
    Theme("Cybersecurity", "etf", etf=("CIBR",),
          extra=("CRWD", "PANW", "ZS", "S", "OKTA", "FTNT", "TENB",
                 "QLYS", "RPD", "VRNS", "SAIL"),
          note="CYBR dropped 2026-08-09: no longer resolves; PANW already listed."),
    Theme("Robotics & Automation", "etf", etf=("ROBO", "DRIV"),
          industries=("Specialty Industrial Machinery",)),
    Theme("Space", "etf", etf=(),
          extra=("RKLB", "LUNR", "ASTS", "RDW", "PL", "SPIR", "BKSY"),
          note="ARKX seed removed 2026-08-09 for the same reason as Drones. "
               "MNTS dropped -- does not resolve."),
    # No ETF seed. ARKX is a broad space/innovation fund and dragged in AMD,
    # AMZN, GOOG, DE, LHX and SPCX -- seven of thirteen "drone" names were not
    # drones, which is what the +0.017 excess was actually measuring.
    Theme("Drones", "etf", etf=(),
          extra=("KTOS", "AVAV", "ONDS", "UMAC", "RCAT", "EH"),
          note="Pure-play list; no ETF seed (ARKX dragged in AMD/AMZN/GOOG). "
               "DPRO, UAVS and AIRO were considered and dropped 2026-08-09: "
               "all three sit below the theme-tracking liquidity floor "
               "($54-268M cap), so their prints would shape a reading they "
               "could not support a position in."),
    Theme("Defense", "etf", etf=("ITA",), industries=("Aerospace & Defense",)),
    Theme("Solar", "etf", etf=("TAN",), industries=("Solar",)),
    Theme("Clean Energy", "etf", etf=("ICLN",),
          industries=("Solar", "Utilities - Renewable")),
    Theme("Uranium & Nuclear Energy", "etf", etf=("URA",), industries=("Uranium",)),
    Theme("Lithium & Battery Tech", "etf", etf=("LIT",),
          extra=("ALB", "LAC", "SLI", "ELVR", "ENS", "EOSE", "FLNC", "AMPX"),
          note="PLL -> ELVR 2026-08-09: PLL gone, ELVR verified in universe. "
               "ENS (EnerSys) is a genuine battery maker but weighted to "
               "industrial lead-acid, not lithium -- kept because the theme is "
               "named 'Battery Tech', but it is the loosest fit in the list."),
    Theme("Rare Earth Metals", "etf", etf=("REMX",),
          extra=("MP", "UUUU", "TMC", "IDR", "USAR", "CRML")),
    Theme("Copper Miners", "etf", etf=("COPX",), industries=("Copper",)),
    Theme("Crypto Equities", "etf", etf=(),
          extra=("COIN", "MARA", "RIOT", "CLSK", "HUT", "CIFR", "WULF", "IREN",
                 "HIVE", "CORZ", "GLXY", "BMNR", "SBET", "BTDR", "MSTR"),
          note="No ETF seed: BLOK is diversified fintech and pulled in AMD. "
               "BITF dropped 2026-08-09: does not resolve."),
    # Was 60% the same names as Crypto Equities. Bitcoin the *asset* and
    # bitcoin *stocks* are different reads -- spot leads, equities amplify.
    Theme("Bitcoin", "proxy", etf=("IBIT",)),
    Theme("China Tech", "proxy", etf=("KWEB",),
          note="The fund is the instrument; its HK holdings are not US-tradeable."),
    Theme("Speculative Tech", "etf", etf=("ARKK", "ARKF")),
    Theme("Tech Mega Caps", "etf", etf=("MGK",), exclude=("LLY",),
          note="MGK is a mega-cap GROWTH fund, not a tech fund, so its top "
               "holdings can include growth names that are not technology. "
               "LLY excluded 2026-08-10 on the AMGN precedent: a pharma "
               "priced off drug franchises does not belong in a theme named "
               "Tech, however it screens. Found when the primary-group rule "
               "assigned LLY here as its identity."),
    Theme("Semiconductors Large Caps", "etf", etf=("SMH",)),
    # TSF's Genomics list, transcribed from their Thematic Focus table
    # 2026-08-11 — all 61 names, verified present in our universe. ~21 sit
    # under the $1B floor and drop from scoring while staying on the record
    # here; the floor is the filter, not the transcription. ARKG seeds the
    # theme so holdings drift tracks the fund even if this list ages.
    # Publication is NOT automatic: etf-method themes need a co-movement
    # verdict of real/weak, same bar as every other curated theme.
    Theme("Genomics", "etf", etf=("ARKG",),
          extra=("TWST", "SOPH", "CAI", "CDNA", "TXG", "NEO", "NTRA", "ABEO",
                 "SCTX", "WGS", "SDGR", "ADPT", "DYN", "CSTL", "ARCT", "PSNL",
                 "PRAX", "TEM", "QURE", "ABSI", "TSHA", "ALMR", "RGNX", "ARWR",
                 "BNTC", "GH", "NTLA", "STOK", "LEGN", "IONS", "ILMN", "FLGT",
                 "CRSP", "RCKT", "GRAL", "SANA", "RXRX", "BEAM", "SLDB", "SRPT",
                 "GENB", "MRNA", "QGEN", "EDIT", "PRME", "LXEO", "VYGR", "CRBU",
                 "WVE", "DNA", "LAB", "BNTX", "QSI", "RARE", "KRYS", "MRVI",
                 "PACB", "VCYT", "ALNY", "BLLN", "MYGN")),
    # `proxy`, not `etf`: you cannot buy the list, you buy the fund that tracks
    # it, which is exactly the case this method exists for. It also settles the
    # sourcing question -- the IBD 50 is Investor's Business Daily subscription
    # content and not ours to republish, while FFTY's price is public. The two
    # routes that would have given constituents both fail on their own terms:
    # yfinance returns only the top 10 holdings, which would ship a ten-name
    # basket under a fifty-name label, and the issuer's holdings file is not at
    # any path worth guessing at. Tracking the fund needs no fetch at all, and
    # it re-weights itself whenever the list does.
    Theme("IBD 50", "proxy", etf=("FFTY",)),

    # --- Fluxus additions: TSF has no slot for these ---
    Theme("Quantum Computing", "etf", source="fluxus", etf=(),
          extra=("IONQ", "RGTI", "QBTS", "QUBT", "ARQQ", "QMCO", "IBM"),
          note="IBM added by hand 2026-08-10. It fails the standard's first "
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
    Theme("Grid & Electrification", "etf", source="fluxus", etf=("PAVE",),
          industries=("Electrical Equipment & Parts",)),
    Theme("Reshoring / Industrial Renaissance", "etf", source="fluxus", etf=("PAVE",),
          industries=("Engineering & Construction", "Metal Fabrication")),
    Theme("India", "proxy", source="fluxus", etf=("INDA",)),
    Theme("Japan", "proxy", source="fluxus", etf=("EWJ",)),
    Theme("Brazil", "proxy", source="fluxus", etf=("EWZ",)),
    Theme("Korea", "proxy", source="fluxus", etf=("EWY",)),
    Theme("Taiwan", "proxy", source="fluxus", etf=("EWT",)),
    Theme("Europe", "proxy", source="fluxus", etf=("IEUR",)),
    Theme("Emerging Markets", "proxy", source="fluxus", etf=("EEM",)),
    Theme("Gold", "proxy", etf=("GLD",)),
    Theme("Silver", "proxy", etf=("SLV",)),
    Theme("Bonds - Long Duration", "proxy", source="fluxus", etf=("TLT",)),
    Theme("Equal-Weighted S&P 500", "proxy", etf=("RSP",)),
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
        "by_source": {
            "tsf": sum(1 for t in THEMES if t.source == "tsf"),
            "fluxus": sum(1 for t in THEMES if t.source == "fluxus"),
        },
        "needs_manual": list(NEEDS_MANUAL),
    }
