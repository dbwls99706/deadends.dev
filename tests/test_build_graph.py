"""Tests for generator.build_graph — Transition Graph Builder."""


from generator.build_graph import _count_components, compute_stats, extract_edges


def _make_canon(canon_id, leads_to=None, preceded_by=None, confused_with=None):
    """Create a minimal canon dict for graph testing."""
    return {
        "id": canon_id,
        "error": {"domain": canon_id.split("/")[0], "signature": f"Error {canon_id}"},
        "verdict": {"fix_success_rate": 0.8},
        "dead_ends": [],
        "transition_graph": {
            "leads_to": leads_to or [],
            "preceded_by": preceded_by or [],
            "frequently_confused_with": confused_with or [],
        },
    }


class TestExtractEdges:
    def test_empty_canons(self):
        assert extract_edges([]) == []

    def test_leads_to_creates_forward_and_reverse(self):
        canons = [
            _make_canon("python/err-a/env1", leads_to=[{"error_id": "python/err-b/env1"}]),
            _make_canon("python/err-b/env1"),
        ]
        edges = extract_edges(canons)
        types = {(e["source"], e["target"], e["type"]) for e in edges}
        assert ("python/err-a/env1", "python/err-b/env1", "leads_to") in types
        assert ("python/err-b/env1", "python/err-a/env1", "preceded_by") in types

    def test_preceded_by_creates_reverse_leads_to(self):
        canons = [
            _make_canon("python/err-a/env1"),
            _make_canon("python/err-b/env1", preceded_by=[{"error_id": "python/err-a/env1"}]),
        ]
        edges = extract_edges(canons)
        types = {(e["source"], e["target"], e["type"]) for e in edges}
        assert ("python/err-b/env1", "python/err-a/env1", "preceded_by") in types
        assert ("python/err-a/env1", "python/err-b/env1", "leads_to") in types

    def test_confused_with_creates_bidirectional(self):
        canons = [
            _make_canon(
                "python/err-a/env1",
                confused_with=[{"error_id": "python/err-b/env1", "distinction": "diff"}],
            ),
            _make_canon("python/err-b/env1"),
        ]
        edges = extract_edges(canons)
        confused = [e for e in edges if e["type"] == "confused_with"]
        assert len(confused) == 2
        sources = {e["source"] for e in confused}
        assert sources == {"python/err-a/env1", "python/err-b/env1"}

    def test_dangling_refs_excluded(self):
        canons = [
            _make_canon("python/err-a/env1", leads_to=[{"error_id": "python/nonexistent/env1"}]),
        ]
        edges = extract_edges(canons)
        assert len(edges) == 0

    def test_deduplication(self):
        canons = [
            _make_canon(
                "python/err-a/env1",
                leads_to=[{"error_id": "python/err-b/env1"}],
            ),
            _make_canon(
                "python/err-b/env1",
                preceded_by=[{"error_id": "python/err-a/env1"}],
            ),
        ]
        edges = extract_edges(canons)
        keys = [(e["source"], e["target"], e["type"]) for e in edges]
        assert len(keys) == len(set(keys))

    def test_probability_preserved(self):
        canons = [
            _make_canon(
                "python/err-a/env1",
                leads_to=[{"error_id": "python/err-b/env1", "probability": 0.7}],
            ),
            _make_canon("python/err-b/env1"),
        ]
        edges = extract_edges(canons)
        lt = [e for e in edges if e["type"] == "leads_to"][0]
        assert lt["probability"] == 0.7


class TestComputeStats:
    def test_stats_with_edges(self):
        canons = [
            _make_canon("python/err-a/env1", leads_to=[{"error_id": "python/err-b/env1"}]),
            _make_canon("python/err-b/env1"),
            _make_canon("python/err-c/env1"),
        ]
        edges = extract_edges(canons)
        stats = compute_stats(edges, canons)
        assert stats["total_canons"] == 3
        assert stats["nodes_in_graph"] == 2
        assert stats["orphan_canons"] == 1
        assert stats["total_edges"] > 0
        assert "leads_to" in stats["edges_by_type"]

    def test_empty_graph(self):
        canons = [_make_canon("python/err-a/env1")]
        stats = compute_stats([], canons)
        assert stats["orphan_canons"] == 1
        assert stats["nodes_in_graph"] == 0


class TestCountComponents:
    def test_single_component(self):
        nodes = {"a", "b", "c"}
        edges = [
            {"source": "a", "target": "b", "type": "leads_to"},
            {"source": "b", "target": "c", "type": "leads_to"},
        ]
        assert _count_components(nodes, edges) == 1

    def test_two_components(self):
        nodes = {"a", "b", "c", "d"}
        edges = [
            {"source": "a", "target": "b", "type": "leads_to"},
            {"source": "c", "target": "d", "type": "leads_to"},
        ]
        assert _count_components(nodes, edges) == 2

    def test_empty(self):
        assert _count_components(set(), []) == 0
