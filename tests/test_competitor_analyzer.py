"""Unit tests for the CompetitorAnalyzer module, covering competitor benchmarking and hidden prompt discovery.

These tests ensure:
- The configuration passed to CompetitorAnalyzer is stored and used for TrendScanner initialization.
- `benchmark_competitors` returns correct competitor entries derived from trending data.
- Default values (0.0 for interest and projected RPM) are used when trending data is missing those fields.
- The `count` limit parameter is respected, capping the number of competitors returned.
- Edge cases like an empty seed list result in empty output, and exceptions from TrendScanner propagate properly.
- `discover_hidden_prompts` returns prompt templates as dicts with the correct structure, description, and tags.
- The `limit` parameter in `discover_hidden_prompts` restricts the number of results appropriately.
- Edge cases like empty input lists yield no prompt templates.
- External dependencies (TrendScanner, PromptDiscoverer) are monkeypatched to avoid real API calls or heavy processing.
"""
import os
import sys
import pytest

# Ensure the project root is in sys.path so that nova package is importable
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(base_dir)

import nova.competitor_analyzer as competitor_analyzer
from nova.competitor_analyzer import CompetitorAnalyzer


def test_competitor_analyzer_stores_config():
    """It should store the provided config dictionary internally."""
    cfg = {"test_key": "test_value"}
    analyzer = CompetitorAnalyzer(cfg)
    # The config passed in should be accessible via the `cfg` attribute (identity or equality).
    assert analyzer.cfg == cfg
    assert analyzer.cfg is cfg


class TestBenchmarkCompetitors:
    """Tests for the async method CompetitorAnalyzer.benchmark_competitors."""

    @pytest.mark.asyncio
    async def test_basic_output_and_competitor_numbering(self, monkeypatch):
        """benchmark_competitors should return a list of competitor dicts with correct fields."""
        # Dummy TrendScanner that returns two trending entries
        class DummyScanner:
            def __init__(self, cfg):
                # Capture the config to verify it was passed correctly
                DummyScanner.captured_cfg = cfg

            async def scan(self, seeds):
                # Return dummy trending data for testing
                return [
                    {"keyword": "Alpha", "interest": 5.0, "projected_rpm": 10.0},
                    {"keyword": "Beta", "interest": 3.5, "projected_rpm": 7.0},
                ]

        # Monkeypatch TrendScanner to use DummyScanner
        monkeypatch.setattr(competitor_analyzer, "TrendScanner", DummyScanner)
        cfg = {"rpm_multiplier": 1.0, "top_n": 10}
        analyzer = CompetitorAnalyzer(cfg)
        results = await analyzer.benchmark_competitors(["seed1", "seed2"], count=10)

        # Verify TrendScanner was initialized with the same config
        assert DummyScanner.captured_cfg == cfg
        # The result should contain two competitor entries (since DummyScanner returned 2 trends)
        assert isinstance(results, list)
        assert len(results) == 2

        # Each result should be a dict with the expected keys
        for idx, comp in enumerate(results, start=1):
            assert set(comp.keys()) == {"competitor", "keyword", "interest", "projected_rpm"}
            # Competitor names should be "Competitor 1", "Competitor 2", etc.
            assert comp["competitor"] == f"Competitor {idx}"
        # Check that the values were carried over correctly
        assert results[0]["keyword"] == "Alpha" and results[0]["interest"] == 5.0 and results[0]["projected_rpm"] == 10.0
        assert results[1]["keyword"] == "Beta" and results[1]["interest"] == 3.5 and results[1]["projected_rpm"] == 7.0

    @pytest.mark.asyncio
    async def test_respects_count_limit(self, monkeypatch):
        """It should return at most `count` competitors even if more trends are available."""
        # Dummy TrendScanner returning three trending entries
        class DummyScanner:
            def __init__(self, cfg):
                pass

            async def scan(self, seeds):
                return [
                    {"keyword": "K1", "interest": 10, "projected_rpm": 100},
                    {"keyword": "K2", "interest": 20, "projected_rpm": 80},
                    {"keyword": "K3", "interest": 5, "projected_rpm": 60},
                ]

        monkeypatch.setattr(competitor_analyzer, "TrendScanner", DummyScanner)
        analyzer = CompetitorAnalyzer({})
        # Request only 2 competitors while 3 trends are available
        results = await analyzer.benchmark_competitors(["seed"], count=2)
        # Should return exactly 2 results (the first two trends)
        assert len(results) == 2
        assert results[0]["competitor"] == "Competitor 1" and results[1]["competitor"] == "Competitor 2"
        # Verify that we got the first two trend entries and the third was dropped
        assert results[0]["keyword"] == "K1" and results[1]["keyword"] == "K2"
        # The dropped third trend ("K3") should not appear in results
        keywords = [res["keyword"] for res in results]
        assert "K3" not in keywords

    @pytest.mark.asyncio
    async def test_defaults_for_missing_interest_and_rpm(self, monkeypatch):
        """If trend data is missing 'interest' or 'projected_rpm', defaults (0.0) should be used."""
        # Dummy TrendScanner returning entries with some missing fields
        class DummyScanner:
            def __init__(self, cfg):
                pass

            async def scan(self, seeds):
                return [
                    {"keyword": "Test1", "projected_rpm": 55},   # missing 'interest'
                    {"keyword": "Test2", "interest": 9},         # missing 'projected_rpm'
                    {"interest": 2, "projected_rpm": 4},         # missing 'keyword'
                ]

        monkeypatch.setattr(competitor_analyzer, "TrendScanner", DummyScanner)
        analyzer = CompetitorAnalyzer({})
        results = await analyzer.benchmark_competitors(["seed"], count=3)
        # We expect three competitors in the result
        assert len(results) == 3

        # Competitor 1: no 'interest' in trend -> interest should default to 0.0
        comp1 = results[0]
        assert comp1["competitor"] == "Competitor 1"
        assert comp1["keyword"] == "Test1"
        assert comp1["interest"] == 0.0  # default used
        assert comp1["projected_rpm"] == 55  # provided value

        # Competitor 2: no 'projected_rpm' in trend -> projected_rpm should default to 0.0
        comp2 = results[1]
        assert comp2["competitor"] == "Competitor 2"
        assert comp2["keyword"] == "Test2"
        assert comp2["interest"] == 9   # provided value
        assert comp2["projected_rpm"] == 0.0  # default used

        # Competitor 3: no 'keyword' in trend -> keyword should be None
        comp3 = results[2]
        assert comp3["competitor"] == "Competitor 3"
        assert comp3["keyword"] is None  # missing keyword yields None
        assert comp3["interest"] == 2
        assert comp3["projected_rpm"] == 4

    @pytest.mark.asyncio
    async def test_empty_seed_list_returns_empty(self, monkeypatch):
        """An empty list of seed keywords should result in an empty list of competitors."""
        class DummyScanner:
            def __init__(self, cfg):
                pass

            async def scan(self, seeds):
                # Even if called (likely with empty seeds), return no trends
                return []

        monkeypatch.setattr(competitor_analyzer, "TrendScanner", DummyScanner)
        analyzer = CompetitorAnalyzer({})
        results = await analyzer.benchmark_competitors([], count=5)
        # Should return an empty list when no seeds are provided
        assert results == []  # empty output expected
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_exception_propagation(self, monkeypatch):
        """Any exception raised during TrendScanner.scan should propagate out of benchmark_competitors."""
        class DummyScanner:
            def __init__(self, cfg):
                pass

            async def scan(self, seeds):
                # Simulate an error (e.g., network or policy error) during scanning
                raise RuntimeError("Scan failure")

        monkeypatch.setattr(competitor_analyzer, "TrendScanner", DummyScanner)
        analyzer = CompetitorAnalyzer({})
        # The RuntimeError from DummyScanner.scan should bubble up to the caller
        with pytest.raises(RuntimeError, match="Scan failure"):
            await analyzer.benchmark_competitors(["term"], count=5)


class TestDiscoverHiddenPrompts:
    """Tests for the sync method CompetitorAnalyzer.discover_hidden_prompts."""

    def test_returns_prompt_dicts_with_correct_structure(self):
        """discover_hidden_prompts should generate dictionaries with expected keys and values."""
        analyzer = CompetitorAnalyzer({})  # No external config needed for prompt discovery
        roles = ["RoleX"]
        domains = ["DomainY"]
        outcomes = ["OutcomeZ"]
        niches = ["NicheW"]
        # Use default limit (10). With single elements in each list, actual combinations are 36, so result will be capped at 10.
        results = analyzer.discover_hidden_prompts(roles, domains, outcomes, niches)
        # Should return a list of dicts (each representing a PromptTemplate)
        assert isinstance(results, list)
        assert len(results) == 10  # default limit is 10

        for item in results:
            # Each item should be a dict with keys 'structure', 'description', 'tags'
            assert set(item.keys()) == {"structure", "description", "tags"}
            # The tags should exactly match the input seeds
            assert item["tags"] == ["RoleX", "DomainY", "OutcomeZ", "NicheW"]
            # The description is expected to follow the known format incorporating the seeds
            expected_desc = "Prompt for a RoleX in DomainY to deliver a OutcomeZ for NicheW."
            assert item["description"] == expected_desc
            # The structure should be a non-empty string containing the seed values (RoleX, DomainY, OutcomeZ, NicheW)
            struct = item["structure"]
            assert isinstance(struct, str) and struct != ""
            assert "RoleX" in struct and "DomainY" in struct and "OutcomeZ" in struct and "NicheW" in struct

    def test_respects_limit_parameter(self):
        """It should return at most the specified number of prompt templates (limit)."""
        analyzer = CompetitorAnalyzer({})
        # Using single-element lists again, total possible combos = 36. We'll request a smaller limit.
        roles = ["A"]
        domains = ["B"]
        outcomes = ["C"]
        niches = ["D"]
        results = analyzer.discover_hidden_prompts(roles, domains, outcomes, niches, limit=5)
        # Should return exactly 5 prompts (since limit=5)
        assert len(results) == 5
        # All results should still contain the correct tags and description for the given seeds
        for item in results:
            assert item["tags"] == ["A", "B", "C", "D"]
            assert item["description"] == "Prompt for a A in B to deliver a C for D."

    def test_empty_input_lists_produce_no_results(self):
        """If any of the input lists (roles, domains, outcomes, niches) is empty, the result should be an empty list."""
        analyzer = CompetitorAnalyzer({})
        # Test each scenario where one of the lists is empty
        assert analyzer.discover_hidden_prompts([], ["B"], ["C"], ["D"], limit=10) == []
        assert analyzer.discover_hidden_prompts(["A"], [], ["C"], ["D"], limit=10) == []
        assert analyzer.discover_hidden_prompts(["A"], ["B"], [], ["D"], limit=10) == []
        assert analyzer.discover_hidden_prompts(["A"], ["B"], ["C"], [], limit=10) == []

    def test_monkeypatched_discoverer_integration(self, monkeypatch):
        """Monkeypatch PromptDiscoverer to return predefined templates and verify output mapping."""
        # Create a couple of dummy PromptTemplate instances to simulate discovered prompts
        DummyTemplate1 = competitor_analyzer.PromptTemplate(structure="DummyStruct1", description="DummyDesc1", tags=["X", "Y"])
        DummyTemplate2 = competitor_analyzer.PromptTemplate(structure="DummyStruct2", description="DummyDesc2", tags=["Z"])
        # Dummy PromptDiscoverer that ignores input and returns the dummy templates above
        class DummyDiscoverer:
            def __init__(self):
                pass

            def discover_prompts(self, roles, domains, outcomes, niches, limit=10):
                # We can optionally verify that the parameters are passed correctly (not strictly necessary here)
                DummyDiscoverer.last_call = {"roles": roles, "domains": domains, "outcomes": outcomes, "niches": niches, "limit": limit}
                return [DummyTemplate1, DummyTemplate2]

        monkeypatch.setattr(competitor_analyzer, "PromptDiscoverer", DummyDiscoverer)
        analyzer = CompetitorAnalyzer({})
        # Call discover_hidden_prompts with arbitrary input (the DummyDiscoverer will return the dummy templates regardless)
        results = analyzer.discover_hidden_prompts(["role"], ["domain"], ["outcome"], ["niche"], limit=5)
        # The results should be a list of two dictionaries corresponding to DummyTemplate1 and DummyTemplate2
        assert isinstance(results, list) and len(results) == 2
        assert results[0]["structure"] == "DummyStruct1"
        assert results[0]["description"] == "DummyDesc1"
        assert results[0]["tags"] == ["X", "Y"]
        assert results[1]["structure"] == "DummyStruct2"
        assert results[1]["description"] == "DummyDesc2"
        assert results[1]["tags"] == ["Z"] 