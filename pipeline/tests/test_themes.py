"""Tests for the theme taxonomy and group builder."""

from __future__ import annotations

import pytest

from pipeline.themes import build_groups, taxonomy


class TestTaxonomy:
    def test_every_theme_declares_a_usable_method(self):
        for theme in taxonomy.THEMES:
            assert theme.method in ("industry", "etf", "rule", "proxy"), theme.name

    def test_rule_themes_carry_a_predicate(self):
        for theme in taxonomy.THEMES:
            if theme.method == "rule":
                assert callable(theme.rule), theme.name

    def test_proxy_themes_name_exactly_one_fund(self):
        """A proxy theme *is* its ETF, so a missing or ambiguous fund makes the
        theme meaningless rather than merely thin."""
        for theme in taxonomy.THEMES:
            if theme.method == "proxy":
                assert len(theme.etf) == 1, theme.name
                assert not theme.extra and not theme.industries, theme.name

    def test_non_rule_themes_can_resolve_members(self):
        """An industry/etf theme with no industries, no ETF and no manual list
        can never produce members -- it would silently vanish from output."""
        for theme in taxonomy.THEMES:
            if theme.method in ("industry", "etf"):
                has_source = theme.industries or theme.etf or theme.extra
                assert has_source or theme.name in taxonomy.NEEDS_MANUAL, theme.name

    def test_names_are_unique(self):
        names = [t.name for t in taxonomy.THEMES]
        assert len(names) == len(set(names))

    def test_summary_counts_match(self):
        s = taxonomy.summary()
        assert s["total"] == len(taxonomy.THEMES)
        assert sum(s["by_method"].values()) == len(taxonomy.THEMES)


class TestForeignListingFilter:
    @pytest.mark.parametrize("symbol", ["0700.HK", "CCO.TO", "PLS.AX",
                                        "600111.SS", "HDFCBANK.NS", "6752.T"])
    def test_rejects_foreign_lines(self, symbol):
        assert build_groups.is_foreign_listing(symbol) is True

    @pytest.mark.parametrize("symbol", ["NVDA", "MP", "COIN", "BRK-B"])
    def test_keeps_us_lines(self, symbol):
        assert build_groups.is_foreign_listing(symbol) is False


class TestResolveThemeMembers:
    UNIVERSE = [
        {"ticker": "NVDA", "industry": "Semiconductors", "market_cap": 3e12,
         "adr_pct": 3.0, "rs_rating": 95},
        {"ticker": "AMD", "industry": "Semiconductors", "market_cap": 3e11,
         "adr_pct": 4.0, "rs_rating": 88},
        {"ticker": "CCJ", "industry": "Uranium", "market_cap": 3e10,
         "adr_pct": 6.0, "rs_rating": 92},
        {"ticker": "TINY", "industry": "Uranium", "market_cap": 5e8,
         "adr_pct": 9.0, "rs_rating": 96},
    ]

    def test_industry_backbone(self):
        theme = taxonomy.Theme("T", "industry", industries=("Semiconductors",))
        members = build_groups.resolve_theme_members(theme, self.UNIVERSE, {})
        assert {m["ticker"] for m in members} == {"NVDA", "AMD"}

    def test_etf_seed_intersects_universe_and_skips_foreign(self):
        theme = taxonomy.Theme("T", "etf", etf=("URA",))
        holdings = {"URA": ["CCJ", "CCO.TO", "NXE.TO", "NOTINUNIVERSE"]}
        members = build_groups.resolve_theme_members(theme, self.UNIVERSE, holdings)
        assert {m["ticker"] for m in members} == {"CCJ"}

    def test_industry_and_etf_seed_are_unioned(self):
        theme = taxonomy.Theme("T", "etf", etf=("URA",), industries=("Semiconductors",))
        members = build_groups.resolve_theme_members(theme, self.UNIVERSE, {"URA": ["CCJ"]})
        assert {m["ticker"] for m in members} == {"NVDA", "AMD", "CCJ"}

    def test_extra_adds_and_exclude_removes(self):
        theme = taxonomy.Theme("T", "etf", industries=("Semiconductors",),
                               extra=("CCJ",), exclude=("AMD",))
        members = build_groups.resolve_theme_members(theme, self.UNIVERSE, {})
        assert {m["ticker"] for m in members} == {"NVDA", "CCJ"}

    def test_no_duplicate_members_when_sources_overlap(self):
        theme = taxonomy.Theme("T", "etf", etf=("X",), industries=("Semiconductors",))
        members = build_groups.resolve_theme_members(theme, self.UNIVERSE, {"X": ["NVDA"]})
        assert len(members) == len({m["ticker"] for m in members})

    def test_rule_theme_selects_by_predicate(self):
        theme = taxonomy.Theme("T", "rule", rule=lambda r: r["market_cap"] < 1e9)
        members = build_groups.resolve_theme_members(theme, self.UNIVERSE, {})
        assert {m["ticker"] for m in members} == {"TINY"}


class TestRuleThemesAgainstRealShape:
    """The rule themes must not silently select nothing when a column the
    predicate depends on is entirely null in the feed."""

    ROWS = [
        {"ticker": "A", "market_cap": 5e8, "adr_pct": 6.0, "rs_rating": 95,
         "perf_6m": 0.4, "sma200_dist": 0.1, "high_52w": -0.02,
         "eps_growth_next_y": None, "perf_1y": 0.5, "perf_3m": 0.2},
        {"ticker": "B", "market_cap": 5e9, "adr_pct": 1.0, "rs_rating": 40,
         "perf_6m": -0.3, "sma200_dist": -0.2, "high_52w": -0.40,
         "eps_growth_next_y": None, "perf_1y": -0.2, "perf_3m": -0.1},
    ]

    # Microcaps dropped from this list 2026-08-10 with the theme itself: the
    # $1B tradeable floor deletes by definition the thing it selected for.
    @pytest.mark.parametrize("name", ["Growth Factor", "High Octane",
                                      "52-Week High Leaders"])
    def test_rule_matches_at_least_one_row(self, name):
        theme = taxonomy.by_name()[name]
        matched = [r for r in self.ROWS if theme.rule(r)]
        assert matched, f"{name} selected nothing"

    def test_growth_factor_does_not_depend_on_null_eps_column(self):
        """Regression: eps_growth_next_y is null for all 3,000 rows, so the
        fundamental definition selected zero names."""
        theme = taxonomy.by_name()["Growth Factor"]
        assert theme.rule(self.ROWS[0]) is True


class TestStateCounts:
    def test_counts_every_state_key(self):
        groups = [{"state": "Leading"}, {"state": "Leading"}, {"state": "Lagging"}]
        counts = build_groups.state_counts(groups)
        assert counts == {"Leading": 2, "Weakening": 0, "Improving": 0, "Lagging": 1}


class TestAuditTaxonomy:
    UNIVERSE = [
        {"ticker": "NVDA", "industry": "Semiconductors"},
        {"ticker": "CCJ", "industry": "Uranium"},
    ]

    def test_clean_when_everything_resolves(self):
        audit = build_groups.audit_taxonomy(self.UNIVERSE, {"URA": ["CCJ"]},
                                            {"KWEB": {"ticker": "KWEB"}})
        # The real taxonomy is checked separately; here we only assert shape.
        assert set(audit) == {
            "unknown_extra_tickers", "unknown_industries",
            "proxy_etf_not_in_etf_data", "etf_without_cached_holdings", "clean",
        }

    def test_flags_a_ticker_that_does_not_exist(self, monkeypatch):
        bogus = taxonomy.Theme("T", "etf", extra=("NOTAREALTICKER",))
        monkeypatch.setattr(taxonomy, "THEMES", [bogus])
        audit = build_groups.audit_taxonomy(self.UNIVERSE, {}, {})
        assert audit["clean"] is False
        assert audit["unknown_extra_tickers"] == [
            {"theme": "T", "ticker": "NOTAREALTICKER"}
        ]

    def test_flags_a_misspelled_industry(self, monkeypatch):
        bogus = taxonomy.Theme("T", "industry", industries=("Semiconductor",))
        monkeypatch.setattr(taxonomy, "THEMES", [bogus])
        audit = build_groups.audit_taxonomy(self.UNIVERSE, {}, {})
        assert audit["unknown_industries"] == [
            {"theme": "T", "industry": "Semiconductor"}
        ]

    def test_flags_a_proxy_fund_missing_from_etf_data(self, monkeypatch):
        bogus = taxonomy.Theme("T", "proxy", etf=("NOPE",))
        monkeypatch.setattr(taxonomy, "THEMES", [bogus])
        audit = build_groups.audit_taxonomy(self.UNIVERSE, {}, {})
        assert audit["proxy_etf_not_in_etf_data"] == [{"theme": "T", "etf": "NOPE"}]


class TestJsonSerialisable:
    """groups.json is consumed by a browser, and Python writes bare NaN.

    A single NaN in one perf_1y field made the whole document unparseable in
    the frontend while still serving a 200 with valid-looking bytes on disk.
    """

    def test_safe_round_maps_nan_to_none(self):
        from pipeline.themes import rs_engine
        assert rs_engine.safe_round(float("nan")) is None
        assert rs_engine.safe_round(float("inf")) is None
        assert rs_engine.safe_round(None) is None
        assert rs_engine.safe_round(0.123456789) == 0.123457

    def test_built_payload_contains_no_nan(self, tmp_path):
        import json
        import math

        payload = build_groups.run()
        text = json.dumps(payload, default=str)
        assert "NaN" not in text
        assert "Infinity" not in text
        # Round-trips through a strict parser, the way a browser would.
        json.loads(text, parse_constant=_reject)


def _reject(name):  # pragma: no cover - only fires on a regression
    raise AssertionError(f"non-finite constant {name!r} in groups.json")


class TestPrimaryGroup:
    """One home per stock. Rule themes are screens (properties), not
    identities — a stock can hold five properties at once but comes from
    exactly one place."""

    THEMES = [
        {"group": "Broad AI Theme", "method": "etf", "members": 155,
         "tickers": ["AEVA", "NVDA"]},
        {"group": "Semiconductors Large Caps", "method": "etf", "members": 10,
         "tickers": ["NVDA"]},
        {"group": "High Octane", "method": "rule", "members": 300,
         "tickers": ["AEVA", "NVDA", "ORPH"]},
        {"group": "Bitcoin", "method": "proxy", "members": 1,
         "tickers": ["IBIT"]},
    ]
    UNIVERSE = [
        {"ticker": "AEVA", "industry": "Software - Application"},
        {"ticker": "NVDA", "industry": "Semiconductors"},
        {"ticker": "ORPH", "industry": "Biotechnology"},
    ]

    def _run(self):
        stocks = {t["ticker"]: {} for t in self.UNIVERSE}
        build_groups.assign_primary_group(stocks, self.THEMES, self.UNIVERSE)
        return stocks

    def test_smallest_curated_theme_wins(self):
        s = self._run()
        assert s["NVDA"] == {"primary_group": "Semiconductors Large Caps",
                             "primary_kind": "theme"}

    def test_rule_themes_are_never_a_home(self):
        """ORPH is only in High Octane — a screen it happens to pass this
        week. Its home is its industry."""
        s = self._run()
        assert s["ORPH"] == {"primary_group": "Biotechnology",
                             "primary_kind": "industry"}

    def test_curated_theme_beats_industry(self):
        s = self._run()
        assert s["AEVA"]["primary_group"] == "Broad AI Theme"

    def test_every_stock_gets_exactly_one_home(self):
        s = self._run()
        assert all(v.get("primary_group") for v in s.values())

    def test_deterministic_under_theme_order(self):
        stocks = {t["ticker"]: {} for t in self.UNIVERSE}
        build_groups.assign_primary_group(
            stocks, list(reversed(self.THEMES)), self.UNIVERSE)
        assert stocks == self._run()

    def test_unscored_industry_is_marked_not_left_dangling(self):
        """48 stocks pointed at industries the scoring step had dropped
        (<5 tradeable members). The pointer stays truthful instead of being
        reassigned: kind flips to industry_unscored and the UI draws no
        ribbon — unmeasured is not zero, and it is not someone else's group
        either."""
        stocks = {"LUX1": {"primary_group": "Luxury Goods",
                           "primary_kind": "industry"},
                  "NVDA": {"primary_group": "Semiconductors",
                           "primary_kind": "industry"}}
        industries = [{"group": "Semiconductors"}]
        moved = build_groups.resolve_dangling_primaries(stocks, industries)
        assert moved == 1
        assert stocks["LUX1"]["primary_kind"] == "industry_unscored"
        assert stocks["LUX1"]["primary_group"] == "Luxury Goods"
        assert stocks["NVDA"]["primary_kind"] == "industry"
