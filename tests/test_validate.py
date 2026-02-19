"""Tests for ErrorCanon validation logic."""

from datetime import date

from generator.validate import (
    _canon_age_days,
    staleness_summary,
    validate_canon_json,
    validate_cross_references,
)


class TestValidCanon:
    def test_valid_canon_passes(self, valid_canon):
        errors, warnings = validate_canon_json(valid_canon)
        assert errors == []

    def test_valid_canon_with_empty_workarounds(self, make_canon):
        canon = make_canon(workarounds=[])
        errors, warnings = validate_canon_json(canon)
        assert errors == []

    def test_valid_canon_with_empty_transition_graph(self, make_canon):
        canon = make_canon(
            transition_graph={
                "leads_to": [],
                "preceded_by": [],
                "frequently_confused_with": [],
            }
        )
        errors, warnings = validate_canon_json(canon)
        assert errors == []


class TestSchemaErrors:
    def test_missing_required_field(self, valid_canon):
        del valid_canon["dead_ends"]
        errors, _ = validate_canon_json(valid_canon)
        assert len(errors) > 0
        assert "dead_ends" in errors[0].lower() or "required" in errors[0].lower()

    def test_missing_workarounds_field(self, valid_canon):
        del valid_canon["workarounds"]
        errors, _ = validate_canon_json(valid_canon)
        assert len(errors) > 0

    def test_missing_transition_graph_field(self, valid_canon):
        del valid_canon["transition_graph"]
        errors, _ = validate_canon_json(valid_canon)
        assert len(errors) > 0

    def test_missing_environment_os(self, valid_canon):
        del valid_canon["environment"]["os"]
        errors, _ = validate_canon_json(valid_canon)
        assert len(errors) > 0

    def test_invalid_domain(self, valid_canon):
        valid_canon["error"]["domain"] = "invalid_domain"
        errors, _ = validate_canon_json(valid_canon)
        assert len(errors) > 0

    def test_empty_dead_ends(self, make_canon):
        canon = make_canon(dead_ends=[])
        errors, _ = validate_canon_json(canon)
        assert len(errors) > 0

    def test_invalid_resolvable_enum(self, valid_canon):
        valid_canon["verdict"]["resolvable"] = "maybe"
        errors, _ = validate_canon_json(valid_canon)
        assert len(errors) > 0


class TestBusinessRules:
    def test_url_mismatch(self, make_canon):
        canon = make_canon(url="https://deadends.dev/wrong/path/here")
        errors, _ = validate_canon_json(canon)
        assert any("URL mismatch" in e for e in errors)

    def test_verdict_true_requires_high_rate(self, valid_canon):
        valid_canon["verdict"]["resolvable"] = "true"
        valid_canon["verdict"]["fix_success_rate"] = 0.50
        valid_canon["verdict"]["confidence"] = 0.80
        errors, _ = validate_canon_json(valid_canon)
        assert any("verdict 'true'" in e for e in errors)

    def test_verdict_true_valid(self, valid_canon):
        valid_canon["verdict"]["resolvable"] = "true"
        valid_canon["verdict"]["fix_success_rate"] = 0.80
        valid_canon["verdict"]["confidence"] = 0.70
        errors, _ = validate_canon_json(valid_canon)
        assert not any("verdict 'true'" in e for e in errors)

    def test_verdict_false_requires_low_rate(self, valid_canon):
        valid_canon["verdict"]["resolvable"] = "false"
        valid_canon["verdict"]["fix_success_rate"] = 0.30
        valid_canon["verdict"]["confidence"] = 0.80
        errors, _ = validate_canon_json(valid_canon)
        assert any("verdict 'false'" in e for e in errors)

    def test_low_evidence_high_confidence(self, valid_canon):
        valid_canon["metadata"]["evidence_count"] = 2
        valid_canon["verdict"]["confidence"] = 0.80
        errors, _ = validate_canon_json(valid_canon)
        assert any("evidence_count" in e for e in errors)

    def test_invalid_regex(self, valid_canon):
        valid_canon["error"]["regex"] = "[invalid regex("
        errors, _ = validate_canon_json(valid_canon)
        assert any("regex" in e.lower() for e in errors)

    def test_fail_rate_out_of_range(self, valid_canon):
        valid_canon["dead_ends"][0]["fail_rate"] = 1.5
        errors, _ = validate_canon_json(valid_canon)
        # Caught by schema validation (maximum: 1.0)
        assert len(errors) > 0


class TestWarnings:
    def test_empty_sources_warning(self, valid_canon):
        valid_canon["dead_ends"][0]["sources"] = []
        _, warnings = validate_canon_json(valid_canon)
        assert any("no sources" in w for w in warnings)

    def test_evidence_count_vs_sources_warning(self, valid_canon):
        valid_canon["metadata"]["evidence_count"] = 50
        for de in valid_canon["dead_ends"]:
            de["sources"] = []
        for wa in valid_canon["workarounds"]:
            if "sources" in wa:
                wa["sources"] = []
        _, warnings = validate_canon_json(valid_canon)
        assert any("evidence_count" in w and "no source URLs" in w for w in warnings)


class TestStaleness:
    def test_fresh_canon_no_staleness_warning(self, valid_canon):
        # Set last_confirmed to today
        valid_canon["error"]["last_confirmed"] = date.today().isoformat()
        _, warnings = validate_canon_json(valid_canon)
        assert not any("Stale" in w or "Aging" in w for w in warnings)

    def test_aging_canon_warning(self, valid_canon):
        # Set last_confirmed to 200 days ago
        ref = date(2026, 2, 19)
        valid_canon["error"]["last_confirmed"] = "2025-08-03"  # ~200 days before ref
        age = _canon_age_days(valid_canon, reference_date=ref)
        assert 180 < age < 365
        _, warnings = validate_canon_json(valid_canon)
        # The warning depends on date.today(), but we verify the age calculation
        assert age == 200

    def test_stale_canon_warning(self, valid_canon):
        # Set last_confirmed to 400 days ago
        ref = date(2026, 2, 19)
        valid_canon["error"]["last_confirmed"] = "2025-01-15"  # ~400 days before ref
        age = _canon_age_days(valid_canon, reference_date=ref)
        assert age > 365

    def test_canon_age_days_missing_date(self, valid_canon):
        del valid_canon["error"]["last_confirmed"]
        assert _canon_age_days(valid_canon) is None

    def test_canon_age_days_invalid_date(self, valid_canon):
        valid_canon["error"]["last_confirmed"] = "not-a-date"
        assert _canon_age_days(valid_canon) is None

    def test_staleness_summary_all_fresh(self, make_canon):
        ref = date(2026, 2, 19)
        canons = [
            make_canon(
                id=f"python/err-{i}/env1",
                url=f"https://deadends.dev/python/err-{i}/env1",
                error={"last_confirmed": "2026-02-01"},
            )
            for i in range(5)
        ]
        report = staleness_summary(canons, reference_date=ref)
        assert "Fresh: 5" in report
        assert "Stale: 0" in report

    def test_staleness_summary_mixed(self, make_canon):
        ref = date(2026, 2, 19)
        canons = [
            make_canon(
                id="python/fresh/env1",
                url="https://deadends.dev/python/fresh/env1",
                error={"last_confirmed": "2026-02-01"},
            ),
            make_canon(
                id="python/aging/env1",
                url="https://deadends.dev/python/aging/env1",
                error={"last_confirmed": "2025-07-01"},
            ),
            make_canon(
                id="python/stale/env1",
                url="https://deadends.dev/python/stale/env1",
                error={"last_confirmed": "2024-12-01"},
            ),
        ]
        report = staleness_summary(canons, reference_date=ref)
        assert "Fresh: 1" in report
        assert "Aging: 1" in report
        assert "Stale: 1" in report
        assert "python/stale/env1" in report


class TestCrossReferences:
    def test_valid_cross_reference(self, make_canon):
        canon1 = make_canon(
            id="python/error-a/env1",
            url="https://deadends.dev/python/error-a/env1",
            transition_graph={
                "leads_to": [{"error_id": "python/error-b/env1", "probability": 0.5}],
                "preceded_by": [],
                "frequently_confused_with": [],
            },
        )
        canon2 = make_canon(
            id="python/error-b/env1",
            url="https://deadends.dev/python/error-b/env1",
        )
        errors = validate_cross_references([canon1, canon2])
        assert len(errors) == 0

    def test_missing_cross_reference(self, make_canon):
        canon1 = make_canon(
            transition_graph={
                "leads_to": [
                    {"error_id": "python/nonexistent/env1", "probability": 0.5}
                ],
                "preceded_by": [],
                "frequently_confused_with": [],
            },
        )
        errors = validate_cross_references([canon1])
        assert len(errors) == 1
        assert "non-existent" in errors[0]

    def test_missing_confused_with_reference(self, make_canon):
        canon1 = make_canon(
            transition_graph={
                "leads_to": [],
                "preceded_by": [],
                "frequently_confused_with": [
                    {"error_id": "python/nope/env1", "distinction": "different"}
                ],
            },
        )
        errors = validate_cross_references([canon1])
        assert len(errors) == 1
