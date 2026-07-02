"""Tests for the compiled-regex cache in generator/lookup.py."""

import copy

from tests.conftest import VALID_CANON


def _make_canon(canon_id, signature, regex):
    canon = copy.deepcopy(VALID_CANON)
    canon["id"] = canon_id
    canon["url"] = f"https://deadends.dev/{canon_id}"
    canon["error"]["signature"] = signature
    canon["error"]["regex"] = regex
    return canon


def _reset(lookup):
    lookup._CANONS_CACHE = None
    lookup._REGEX_CACHE = []
    lookup._REGEX_CACHE_SOURCE = None


class TestRegexCache:
    def test_lookup_uses_compiled_cache(self):
        from generator import lookup
        lookup._CANONS_CACHE = [
            _make_canon(
                "python/mem/env1", "MemoryError: out of memory",
                r"MemoryError: .+",
            ),
        ]
        try:
            results = lookup.lookup_all("MemoryError: out of memory")
            assert len(results) == 1
            # Cache is populated and aligned with the canon list
            assert lookup._REGEX_CACHE_SOURCE is lookup._CANONS_CACHE
            assert len(lookup._REGEX_CACHE) == 1
            # Second call reuses the same compiled list (identity)
            cache_before = lookup._REGEX_CACHE
            lookup.lookup_all("MemoryError: out of memory")
            assert lookup._REGEX_CACHE is cache_before
        finally:
            _reset(lookup)

    def test_cache_invalidates_when_canons_change(self):
        from generator import lookup
        lookup._CANONS_CACHE = [
            _make_canon("python/a/env1", "AError: x", r"AError: .+"),
        ]
        try:
            assert len(lookup.lookup_all("AError: x")) == 1

            # Swap the canon list (as other tests do) - cache must rebuild
            lookup._CANONS_CACHE = [
                _make_canon("python/b/env1", "BError: y", r"BError: .+"),
            ]
            results = lookup.lookup_all("BError: y")
            assert len(results) == 1
            assert results[0]["id"] == "python/b/env1"
            assert lookup.lookup_all("AError: x") == []
        finally:
            _reset(lookup)

    def test_invalid_regex_skipped(self):
        from generator import lookup
        lookup._CANONS_CACHE = [
            _make_canon("python/bad/env1", "unmatchable-xyz", r"[invalid("),
            _make_canon("python/good/env1", "GoodError: ok", r"GoodError: .+"),
        ]
        try:
            results = lookup.lookup_all("GoodError: ok")
            assert [r["id"] for r in results] == ["python/good/env1"]
            # Invalid regex cached as None, not recompiled per call
            assert lookup._REGEX_CACHE[0] is None
            assert lookup._REGEX_CACHE[1] is not None
        finally:
            _reset(lookup)
