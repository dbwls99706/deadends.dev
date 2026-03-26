"""Tests for generator.build_signatures — Signature Index Builder."""

import copy
import json

from generator.build_signatures import build_signature_index, compute_stats
from tests.conftest import VALID_CANON


def _make_canon(canon_id, signature="TestError"):
    canon = copy.deepcopy(VALID_CANON)
    canon["id"] = canon_id
    canon["url"] = f"https://deadends.dev/{canon_id}"
    canon["error"]["signature"] = signature
    return canon


class TestBuildSignatureIndex:
    def test_groups_by_slug(self):
        canons = [
            _make_canon("python/test-error/env1", "TestError: failed"),
            _make_canon("python/test-error/env2", "TestError: failed"),
            _make_canon("python/other-error/env1", "OtherError"),
        ]
        entries = build_signature_index(canons)
        assert len(entries) == 2

        test_entry = [e for e in entries if e["slug"] == "test-error"][0]
        assert test_entry["environment_count"] == 2
        assert test_entry["domain"] == "python"

    def test_avg_fix_rate(self):
        c1 = _make_canon("python/err/env1")
        c1["verdict"]["fix_success_rate"] = 0.8
        c2 = _make_canon("python/err/env2")
        c2["verdict"]["fix_success_rate"] = 0.6
        entries = build_signature_index([c1, c2])
        assert entries[0]["avg_fix_rate"] == 0.7

    def test_total_dead_ends(self):
        c1 = _make_canon("python/err/env1")
        c1["dead_ends"] = [{"action": "a", "why_fails": "b", "fail_rate": 0.9}]
        c2 = _make_canon("python/err/env2")
        c2["dead_ends"] = [
            {"action": "a", "why_fails": "b", "fail_rate": 0.9},
            {"action": "c", "why_fails": "d", "fail_rate": 0.8},
        ]
        entries = build_signature_index([c1, c2])
        assert entries[0]["total_dead_ends"] == 3

    def test_empty_canons(self):
        assert build_signature_index([]) == []


class TestComputeStats:
    def test_stats(self):
        entries = [
            {"domain": "python", "environment_count": 3},
            {"domain": "python", "environment_count": 1},
            {"domain": "docker", "environment_count": 2},
        ]
        stats = compute_stats(entries)
        assert stats["unique_signatures"] == 3
        assert stats["total_environment_variants"] == 6
        assert stats["multi_environment_signatures"] == 2
        assert stats["domains"]["python"] == 2
        assert stats["domains"]["docker"] == 1


class TestBuildSignatures:
    def test_full_build(self, tmp_path):
        canon_dir = tmp_path / "canons" / "python"
        canon_dir.mkdir(parents=True)
        canon = _make_canon("python/test-error/env1")
        with open(canon_dir / "test.json", "w") as f:
            json.dump(canon, f)

        from generator.build_signatures import build_signatures
        output_dir = tmp_path / "signatures"
        stats = build_signatures(data_dir=tmp_path / "canons", output_dir=output_dir)
        assert (output_dir / "index.jsonl").exists()
        assert (output_dir / "stats.json").exists()
        assert stats["unique_signatures"] == 1
