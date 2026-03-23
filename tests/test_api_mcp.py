"""Tests for the Vercel serverless MCP endpoint (api/mcp.py)."""

import api.mcp as api_mod
from api.mcp import handle_mcp, match_error


def _make_canon(canon_id="python/test/env1", regex="test error"):
    return {
        "id": canon_id,
        "error": {
            "signature": "Test Error",
            "regex": regex,
            "domain": "python",
            "category": "import",
        },
        "verdict": {
            "resolvable": "true",
            "fix_success_rate": 0.9,
            "confidence": 0.8,
            "summary": "Test fix",
            "last_updated": "2025-01-01",
        },
        "dead_ends": [
            {"action": "test", "why_fails": "test", "fail_rate": 0.8}
        ],
        "workarounds": [
            {"action": "do this", "success_rate": 0.9, "how": "run it"}
        ],
        "transition_graph": {
            "leads_to": [],
            "preceded_by": [],
            "frequently_confused_with": [],
        },
        "url": f"https://deadends.dev/{canon_id}",
        "environment": {"runtime": {"name": "python", "version_range": ">=3.10"}, "os": "linux"},
        "metadata": {
            "generated_by": "test",
            "generation_date": "2025-01-01",
            "review_status": "auto_generated",
            "evidence_count": 5,
        },
        "schema_version": "1.0.0",
    }


class TestApiMatchError:
    """Tests for Vercel endpoint match_error — security parity with mcp/server.py."""

    def test_empty_message_returns_empty(self):
        assert match_error("", [_make_canon()]) == []

    def test_whitespace_returns_empty(self):
        assert match_error("   ", [_make_canon()]) == []

    def test_basic_match(self):
        canon = _make_canon()
        api_mod._COMPILED_REGEXES = None
        api_mod._CANONS = [canon]
        results = match_error("test error occurred", [canon])
        assert len(results) == 1
        assert results[0]["id"] == "python/test/env1"
        api_mod._CANONS = None
        api_mod._COMPILED_REGEXES = None

    def test_truncates_long_message(self):
        canon = _make_canon(regex="x")
        api_mod._COMPILED_REGEXES = None
        api_mod._CANONS = [canon]
        results = match_error("x" * 20_000, [canon])
        assert len(results) >= 1
        api_mod._CANONS = None
        api_mod._COMPILED_REGEXES = None

    def test_skips_invalid_regex(self):
        canon = _make_canon(regex="[invalid(")
        api_mod._COMPILED_REGEXES = None
        api_mod._CANONS = [canon]
        results = match_error("test", [canon])
        assert results == []
        api_mod._CANONS = None
        api_mod._COMPILED_REGEXES = None


class TestApiHandleMcp:
    """Tests for Vercel MCP handler routing."""

    def test_initialize(self):
        result = handle_mcp("initialize", {}, [])
        assert result["serverInfo"]["name"] == "deadends-dev"
        assert "protocolVersion" in result

    def test_ping(self):
        result = handle_mcp("ping", {}, [])
        assert result == {}

    def test_tools_list(self):
        result = handle_mcp("tools/list", {}, [])
        assert "tools" in result
        tool_names = [t["name"] for t in result["tools"]]
        assert "lookup_error" in tool_names
        assert "search_errors" in tool_names

    def test_unknown_method(self):
        result = handle_mcp("nonexistent/method", {}, [])
        assert "error" in result
        assert result["error"]["code"] == -32601

    def test_get_error_detail_rejects_invalid_id(self):
        result = handle_mcp(
            "tools/call",
            {"name": "get_error_detail", "arguments": {"error_id": "../../etc/passwd"}},
            [_make_canon()],
        )
        assert "Invalid" in result["content"][0]["text"]

    def test_get_error_chain_rejects_invalid_id(self):
        result = handle_mcp(
            "tools/call",
            {"name": "get_error_chain", "arguments": {"error_id": "<script>"}},
            [_make_canon()],
        )
        assert "Invalid" in result["content"][0]["text"]

    def test_search_errors_truncates_query(self):
        """Very long search queries should not crash."""
        result = handle_mcp(
            "tools/call",
            {"name": "search_errors", "arguments": {"query": "a" * 5000}},
            [_make_canon()],
        )
        assert "content" in result

    def test_notifications_initialized_returns_none(self):
        result = handle_mcp("notifications/initialized", {}, [])
        assert result is None
