"""Tests for generator.quality_report — Data Quality Report."""

import copy
import json

from generator.quality_report import (
    analyze_categories,
    analyze_domain,
    analyze_graph_connectivity,
    generate_report,
)
from tests.conftest import VALID_CANON


def _make_canon(domain="python", confidence=0.8, fix_rate=0.85, evidence=5):
    canon = copy.deepcopy(VALID_CANON)
    canon["error"]["domain"] = domain
    canon["verdict"]["confidence"] = confidence
    canon["verdict"]["fix_success_rate"] = fix_rate
    canon["metadata"]["evidence_count"] = evidence
    return canon


class TestAnalyzeDomain:
    def test_single_domain(self):
        canons = [_make_canon("python", 0.9, 0.85)]
        result = analyze_domain(canons)
        assert "python" in result
        assert result["python"]["count"] == 1
        assert result["python"]["avg_confidence"] == 0.9

    def test_multiple_domains(self):
        canons = [
            _make_canon("python", 0.9, 0.85),
            _make_canon("docker", 0.7, 0.6),
        ]
        result = analyze_domain(canons)
        assert len(result) == 2
        assert result["docker"]["avg_fix_rate"] == 0.6


class TestAnalyzeGraphConnectivity:
    def test_connected_canons(self):
        canons = [
            {**_make_canon(), "id": "python/a/env1", "transition_graph": {
                "leads_to": [{"error_id": "python/b/env1"}],
                "preceded_by": [], "frequently_confused_with": [],
            }},
            {**_make_canon(), "id": "python/b/env1"},
        ]
        result = analyze_graph_connectivity(canons)
        assert result["connected_canons"] == 2
        assert result["orphan_canons"] == 0

    def test_orphan_canons(self):
        canons = [
            {**_make_canon(), "id": "python/a/env1"},
            {**_make_canon(), "id": "python/b/env1"},
        ]
        result = analyze_graph_connectivity(canons)
        assert result["orphan_canons"] == 2


class TestAnalyzeCategories:
    def test_categories(self):
        c1 = _make_canon()
        c1["error"]["category"] = "runtime_error"
        c2 = _make_canon()
        c2["error"]["category"] = "runtime_error"
        c3 = _make_canon()
        c3["error"]["category"] = "build_error"
        result = analyze_categories([c1, c2, c3])
        assert result["runtime_error"] == 2
        assert result["build_error"] == 1


class TestGenerateReport:
    def test_generates_json_output(self, tmp_path):
        canon_dir = tmp_path / "canons" / "python"
        canon_dir.mkdir(parents=True)
        canon = _make_canon()
        canon["id"] = "python/test-error/env1"
        with open(canon_dir / "test.json", "w") as f:
            json.dump(canon, f)

        output = tmp_path / "report.json"
        report = generate_report(data_dir=tmp_path / "canons", output_file=output)
        assert output.exists()
        assert report["summary"]["total_canons"] == 1
        assert "domains" in report
