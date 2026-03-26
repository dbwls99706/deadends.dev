"""Tests for generator.analytics."""

import json

from generator.analytics import (
    aggregate,
    generate_summary,
    load_events,
    record_event,
)


def test_record_event_creates_file(tmp_path):
    """record_event creates a daily JSONL file."""
    record_event("lookup_error", domain="python", matched=True, match_count=3,
                 analytics_dir=tmp_path)
    files = list(tmp_path.glob("*.jsonl"))
    assert len(files) == 1
    line = files[0].read_text().strip()
    event = json.loads(line)
    assert event["tool"] == "lookup_error"
    assert event["domain"] == "python"
    assert event["matched"] is True
    assert event["match_count"] == 3


def test_record_event_appends(tmp_path):
    """Multiple events append to the same daily file."""
    record_event("lookup_error", analytics_dir=tmp_path)
    record_event("search_errors", analytics_dir=tmp_path)
    files = list(tmp_path.glob("*.jsonl"))
    assert len(files) == 1
    lines = files[0].read_text().strip().split("\n")
    assert len(lines) == 2


def test_record_event_no_domain(tmp_path):
    """Event without domain omits the field."""
    record_event("list_error_domains", analytics_dir=tmp_path)
    files = list(tmp_path.glob("*.jsonl"))
    event = json.loads(files[0].read_text().strip())
    assert "domain" not in event


def test_load_events_empty(tmp_path):
    """Empty directory returns empty list."""
    assert load_events(tmp_path) == []


def test_load_events_missing(tmp_path):
    """Non-existent directory returns empty list."""
    assert load_events(tmp_path / "nope") == []


def test_load_events_reads_jsonl(tmp_path):
    """Reads events from JSONL files."""
    f = tmp_path / "2025-01-01.jsonl"
    f.write_text(
        json.dumps({"tool": "a", "matched": True, "match_count": 1, "ts": "2025-01-01T00:00:00"})
        + "\n"
    )
    events = load_events(tmp_path)
    assert len(events) == 1


def test_aggregate_basic():
    """Aggregate computes tool counts and match rate."""
    events = [
        {"tool": "lookup_error", "matched": True, "match_count": 2,
         "domain": "python", "ts": "2025-01-01T10:00:00"},
        {"tool": "lookup_error", "matched": False, "match_count": 0,
         "domain": "docker", "ts": "2025-01-01T11:00:00"},
        {"tool": "list_error_domains", "matched": False, "match_count": 0,
         "ts": "2025-01-01T12:00:00"},
    ]
    result = aggregate(events)
    assert result["total_events"] == 3
    assert result["tool_usage"]["lookup_error"] == 2
    assert result["total_lookups"] == 2
    assert result["matched_lookups"] == 1
    assert result["lookup_match_rate"] == 0.5
    assert "python" in result["domain_queries"]


def test_aggregate_empty():
    """Aggregate handles empty events."""
    result = aggregate([])
    assert result["total_events"] == 0
    assert result["lookup_match_rate"] == 0


def test_generate_summary_writes_file(tmp_path):
    """generate_summary writes summary.json."""
    output = tmp_path / "summary.json"
    summary = generate_summary(analytics_dir=tmp_path, output_file=output)
    assert output.exists()
    assert summary["total_events"] == 0
    data = json.loads(output.read_text())
    assert "generated_at" in data
