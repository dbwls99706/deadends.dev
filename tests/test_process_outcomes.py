"""Tests for generator.process_outcomes."""

import json

from generator.process_outcomes import (
    aggregate_outcomes,
    compute_deltas,
    load_outcomes,
    process_outcomes,
)


def test_load_outcomes_empty(tmp_path):
    """Empty directory returns empty list."""
    assert load_outcomes(tmp_path) == []


def test_load_outcomes_missing_dir(tmp_path):
    """Non-existent directory returns empty list."""
    assert load_outcomes(tmp_path / "nope") == []


def test_load_outcomes_reads_jsonl(tmp_path):
    """Reads JSONL lines correctly."""
    f = tmp_path / "2025-01-01.jsonl"
    f.write_text(
        json.dumps({"error_id": "a", "workaround_action": "x", "success": True}) + "\n"
        + json.dumps({"error_id": "b", "workaround_action": "y", "success": False}) + "\n"
    )
    outcomes = load_outcomes(tmp_path)
    assert len(outcomes) == 2
    assert outcomes[0]["error_id"] == "a"


def test_load_outcomes_skips_invalid_json(tmp_path):
    """Skips invalid JSON lines gracefully."""
    f = tmp_path / "bad.jsonl"
    f.write_text("not json\n" + json.dumps({"error_id": "a"}) + "\n")
    outcomes = load_outcomes(tmp_path)
    assert len(outcomes) == 1


def test_aggregate_outcomes_basic():
    """Aggregates success/fail counts per error and workaround."""
    outcomes = [
        {"error_id": "e1", "workaround_action": "fix1", "success": True},
        {"error_id": "e1", "workaround_action": "fix1", "success": True},
        {"error_id": "e1", "workaround_action": "fix1", "success": False},
        {"error_id": "e1", "workaround_action": "fix2", "success": False},
    ]
    result = aggregate_outcomes(outcomes)
    assert "e1" in result
    assert result["e1"]["total_reports"] == 4
    wa = result["e1"]["workarounds"]
    assert wa["fix1"]["success"] == 2
    assert wa["fix1"]["fail"] == 1
    assert wa["fix1"]["implied_rate"] == 0.667


def test_aggregate_outcomes_skips_incomplete():
    """Skips outcomes missing error_id or workaround_action."""
    outcomes = [
        {"error_id": "", "workaround_action": "x", "success": True},
        {"error_id": "e1", "workaround_action": "", "success": True},
        {"error_id": "e1", "workaround_action": "x", "success": True},
    ]
    result = aggregate_outcomes(outcomes)
    assert len(result) == 1
    assert result["e1"]["total_reports"] == 1


def test_compute_deltas_with_canon():
    """Computes delta when canon exists."""
    aggregated = {
        "e1": {
            "workarounds": {"fix1": {"success": 8, "fail": 2, "total": 10, "implied_rate": 0.8}},
            "total_reports": 10,
            "overall_success_rate": 0.8,
        }
    }
    canon_rates = {"e1": 0.7}
    deltas = compute_deltas(aggregated, canon_rates)
    assert deltas["e1"]["delta"] == 0.1
    assert deltas["e1"]["current_fix_rate"] == 0.7


def test_compute_deltas_missing_canon():
    """Handles missing canon gracefully."""
    aggregated = {
        "missing": {
            "workarounds": {},
            "total_reports": 1,
            "overall_success_rate": 1.0,
        }
    }
    deltas = compute_deltas(aggregated, {})
    assert deltas["missing"]["delta"] is None
    assert "note" in deltas["missing"]


def test_process_outcomes_full(tmp_path):
    """Full pipeline writes aggregated.json."""
    outcomes_dir = tmp_path / "outcomes"
    outcomes_dir.mkdir()
    canons_dir = tmp_path / "canons"
    canons_dir.mkdir()
    output = tmp_path / "aggregated.json"

    # Write an outcome
    (outcomes_dir / "test.jsonl").write_text(
        json.dumps({"error_id": "e1", "workaround_action": "fix", "success": True}) + "\n"
    )

    report = process_outcomes(outcomes_dir, canons_dir, output)
    assert report["total_outcomes"] == 1
    assert report["unique_errors_reported"] == 1
    assert output.exists()

    data = json.loads(output.read_text())
    assert "deltas" in data
