"""Tests for MCP server functions — security and correctness."""

import re

import mcp.server as srv
from mcp.server import lookup_by_id, match_error


def _set_regex_cache(canons):
    """Manually populate the regex cache for test canons."""
    compiled = {}
    for canon in canons:
        canon_id = canon.get("id", "")
        regex_str = canon.get("error", {}).get("regex", "")
        try:
            compiled[canon_id] = re.compile(regex_str, re.IGNORECASE)
        except re.error:
            compiled[canon_id] = None
    srv._COMPILED_REGEXES = compiled


class TestLookupById:
    """Tests for error ID validation in lookup_by_id."""

    def test_valid_id_found(self):
        canons = [{"id": "python/error-a/py311-linux"}]
        result = lookup_by_id("python/error-a/py311-linux", canons)
        assert result is not None
        assert result["id"] == "python/error-a/py311-linux"

    def test_valid_id_not_found(self):
        canons = [{"id": "python/error-a/py311-linux"}]
        result = lookup_by_id("python/error-b/py311-linux", canons)
        assert result is None

    def test_rejects_empty_id(self):
        canons = [{"id": "python/error-a/py311-linux"}]
        assert lookup_by_id("", canons) is None

    def test_rejects_none_id(self):
        canons = [{"id": "python/error-a/py311-linux"}]
        assert lookup_by_id(None, canons) is None

    def test_rejects_path_traversal(self):
        canons = [{"id": "../../etc/passwd"}]
        assert lookup_by_id("../../etc/passwd", canons) is None

    def test_rejects_uppercase(self):
        canons = [{"id": "Python/Error/Env"}]
        assert lookup_by_id("Python/Error/Env", canons) is None

    def test_rejects_spaces(self):
        canons = [{"id": "python/error a/env1"}]
        assert lookup_by_id("python/error a/env1", canons) is None


class TestMatchError:
    """Tests for error message matching — security edge cases."""

    def _make_canon(self, canon_id="python/test/env1", regex="test error"):
        return {
            "id": canon_id,
            "error": {
                "signature": "Test Error",
                "regex": regex,
                "domain": "python",
            },
            "verdict": {
                "resolvable": "true",
                "fix_success_rate": 0.9,
                "summary": "Test fix",
            },
            "dead_ends": [
                {"action": "test", "why_fails": "test", "fail_rate": 0.8}
            ],
            "workarounds": [],
            "transition_graph": {"leads_to": []},
            "url": f"https://deadends.dev/{canon_id}",
            "environment": {},
            "metadata": {"generated_by": "test", "generation_date": "2025-01-01"},
        }

    def test_empty_message_returns_empty(self):
        assert match_error("", [self._make_canon()]) == []

    def test_whitespace_only_returns_empty(self):
        assert match_error("   ", [self._make_canon()]) == []

    def test_basic_match(self):
        canon = self._make_canon()
        _set_regex_cache([canon])
        results = match_error("test error occurred", [canon])
        assert len(results) == 1
        assert results[0]["id"] == "python/test/env1"

    def test_truncates_long_message(self):
        """Messages longer than 10K chars should be truncated, not rejected."""
        canon = self._make_canon(regex="x")
        _set_regex_cache([canon])
        long_msg = "x" * 20_000
        results = match_error(long_msg, [canon])
        # Should still match (the "x" is in the truncated prefix)
        assert len(results) >= 1

    def test_skips_invalid_regex_canon(self):
        """Canons with invalid regexes should be skipped, not crash."""
        canon = self._make_canon(regex="[invalid(")
        _set_regex_cache([canon])
        results = match_error("test", [canon])
        assert results == []
