"""Tests for report_outcome MCP tool in mcp/server.py."""

import copy
import json
from unittest.mock import patch

# Import the handler and recording function
from mcp.server import _record_outcome, handle_request
from tests.conftest import VALID_CANON


def _make_canons():
    canon = copy.deepcopy(VALID_CANON)
    return [canon]


class TestRecordOutcome:
    def test_writes_jsonl(self, tmp_path):
        with patch("mcp.server.OUTCOMES_DIR", tmp_path):
            outcome = {
                "timestamp": "2025-06-01T00:00:00",
                "error_id": "python/test-error/env1",
                "workaround_action": "Try this instead",
                "success": True,
            }
            _record_outcome(outcome)

        files = list(tmp_path.glob("*.jsonl"))
        assert len(files) == 1
        with open(files[0]) as f:
            line = f.readline()
        data = json.loads(line)
        assert data["error_id"] == "python/test-error/env1"
        assert data["success"] is True

    def test_appends_multiple(self, tmp_path):
        with patch("mcp.server.OUTCOMES_DIR", tmp_path):
            for i in range(3):
                _record_outcome({"index": i})
        files = list(tmp_path.glob("*.jsonl"))
        with open(files[0]) as f:
            lines = f.readlines()
        assert len(lines) == 3


class TestReportOutcomeHandler:
    def test_success_report(self, tmp_path):
        canons = _make_canons()
        with patch("mcp.server.OUTCOMES_DIR", tmp_path):
            result = handle_request("tools/call", {
                "name": "report_outcome",
                "arguments": {
                    "error_id": "python/test-error/env1",
                    "workaround_action": "Try this instead",
                    "success": True,
                },
            }, canons)
        text = result["content"][0]["text"]
        assert "Outcome recorded" in text
        assert "SUCCESS" in text

    def test_failure_report(self, tmp_path):
        canons = _make_canons()
        with patch("mcp.server.OUTCOMES_DIR", tmp_path):
            result = handle_request("tools/call", {
                "name": "report_outcome",
                "arguments": {
                    "error_id": "python/test-error/env1",
                    "workaround_action": "Try this instead",
                    "success": False,
                },
            }, canons)
        text = result["content"][0]["text"]
        assert "FAILED" in text

    def test_missing_fields(self):
        result = handle_request("tools/call", {
            "name": "report_outcome",
            "arguments": {"error_id": "python/test-error/env1"},
        }, [])
        text = result["content"][0]["text"]
        assert "Missing required fields" in text

    def test_invalid_id_format(self):
        result = handle_request("tools/call", {
            "name": "report_outcome",
            "arguments": {
                "error_id": "../../etc/passwd",
                "workaround_action": "test",
                "success": True,
            },
        }, [])
        text = result["content"][0]["text"]
        assert "Invalid" in text

    def test_nonexistent_canon_still_records(self, tmp_path):
        with patch("mcp.server.OUTCOMES_DIR", tmp_path):
            result = handle_request("tools/call", {
                "name": "report_outcome",
                "arguments": {
                    "error_id": "python/nonexistent/env1",
                    "workaround_action": "test",
                    "success": True,
                },
            }, _make_canons())
        text = result["content"][0]["text"]
        assert "not found" in text
        assert "still recorded" in text
