"""Tests for enhanced TF-IDF search in generator/lookup.py."""

import copy

from tests.conftest import VALID_CANON


def _make_search_canon(canon_id, signature, summary, domain="python"):
    canon = copy.deepcopy(VALID_CANON)
    canon["id"] = canon_id
    canon["url"] = f"https://deadends.dev/{canon_id}"
    canon["error"]["signature"] = signature
    canon["error"]["domain"] = domain
    canon["verdict"]["summary"] = summary
    canon["environment"]["runtime"] = {"name": "python", "version_range": ">=3.10"}
    canon["environment"]["os"] = "linux"
    return canon


class TestTfIdfSearch:
    def test_search_returns_results(self):
        from generator import lookup
        lookup._CANONS_CACHE = [
            _make_search_canon(
                "python/memory-error/env1",
                "MemoryError: out of memory",
                "Process runs out of memory on large datasets.",
            ),
            _make_search_canon(
                "python/import-error/env1",
                "ImportError: no module named foo",
                "Module not found in virtual environment.",
            ),
        ]
        lookup._IDF_CACHE = None
        lookup._DOC_WORDS_CACHE = None

        results = lookup.search("memory")
        assert len(results) >= 1
        assert results[0]["signature"] == "MemoryError: out of memory"

        lookup._CANONS_CACHE = None
        lookup._IDF_CACHE = None
        lookup._DOC_WORDS_CACHE = None

    def test_domain_filter(self):
        from generator import lookup
        lookup._CANONS_CACHE = [
            _make_search_canon(
                "python/err/env1", "PermissionError: denied",
                "Permission was denied by OS", "python"
            ),
            _make_search_canon(
                "docker/err/env1", "PermissionError: container denied",
                "Container permission denied", "docker"
            ),
        ]
        lookup._IDF_CACHE = None
        lookup._DOC_WORDS_CACHE = None

        results = lookup.search("permission denied", domain="docker")
        assert len(results) == 1
        assert results[0]["domain"] == "docker"

        lookup._CANONS_CACHE = None
        lookup._IDF_CACHE = None
        lookup._DOC_WORDS_CACHE = None

    def test_env_filter_boosts_matching(self):
        from generator import lookup
        c1 = _make_search_canon(
            "python/err/env1", "TimeoutError: connection",
            "Connection timeout in socket",
        )
        c1["environment"]["runtime"] = {"name": "python", "version_range": ">=3.10"}
        c1["environment"]["os"] = "linux"

        c2 = _make_search_canon(
            "node/err/env1", "TimeoutError: request",
            "Request timeout in HTTP client",
        )
        c2["environment"]["runtime"] = {"name": "node", "version_range": ">=18"}
        c2["environment"]["os"] = "macos"
        c2["error"]["domain"] = "node"

        # Add a third canon so IDF values are more meaningful
        c3 = _make_search_canon(
            "docker/err/env1", "OOMKilled: container",
            "Container killed by kernel OOM",
        )
        c3["error"]["domain"] = "docker"

        lookup._CANONS_CACHE = [c1, c2, c3]
        lookup._IDF_CACHE = None
        lookup._DOC_WORDS_CACHE = None

        results = lookup.search("timeout", runtime="python", os_name="linux")
        assert len(results) >= 2
        # Python canon should rank first due to env boost
        assert results[0]["id"] == "python/err/env1"
        # Node canon should also appear (has "timeout" in text)
        node_ids = [r["id"] for r in results]
        assert "node/err/env1" in node_ids

        lookup._CANONS_CACHE = None
        lookup._IDF_CACHE = None
        lookup._DOC_WORDS_CACHE = None

    def test_empty_query(self):
        from generator import lookup
        lookup._CANONS_CACHE = [
            _make_search_canon("python/err/env1", "Error", "Summary"),
        ]
        lookup._IDF_CACHE = None
        lookup._DOC_WORDS_CACHE = None

        results = lookup.search("")
        assert results == []

        lookup._CANONS_CACHE = None
        lookup._IDF_CACHE = None
        lookup._DOC_WORDS_CACHE = None

    def test_tfidf_ranks_rare_words_higher(self):
        from generator import lookup
        lookup._CANONS_CACHE = [
            _make_search_canon(
                "python/segfault/env1",
                "Segmentation fault (core dumped)",
                "Segfault in native extension.",
            ),
            _make_search_canon(
                "python/err-common/env1",
                "runtime processing issue",
                "Common runtime processing problem.",
            ),
            _make_search_canon(
                "python/err-another/env1",
                "another processing task",
                "Processing tasks fail intermittently.",
            ),
        ]
        lookup._IDF_CACHE = None
        lookup._DOC_WORDS_CACHE = None

        results = lookup.search("segfault")
        assert len(results) >= 1
        assert results[0]["id"] == "python/segfault/env1"

        lookup._CANONS_CACHE = None
        lookup._IDF_CACHE = None
        lookup._DOC_WORDS_CACHE = None
