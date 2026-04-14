"""Tests for country-scoped ErrorCanon authoring and rendering helpers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import validate as jsonschema_validate

from generator.build_site import (
    _canon_country_info,
    build_env_summary,
    country_stats,
)
from generator.country_canon_template import (
    SUPPORTED_COUNTRIES,
    canon_country,
    canon_country_name,
    make_country_canon,
)
from generator.schema import ERRORCANON_SCHEMA
from generator.validate import validate_canon_json

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "canons"


# --- make_country_canon skeleton -------------------------------------------------


def test_make_country_canon_produces_schema_valid_skeleton():
    canon = make_country_canon(
        domain="banking",
        slug="test-slug",
        country="kr",
        signature="sig",
        regex=r"foo|bar",
        category="administrative_barrier",
        summary="A summary that is long enough to be informative.",
    )
    # Caller must add at least one dead_end before the validator will pass,
    # but the skeleton itself must still satisfy the JSON schema.
    canon["dead_ends"].append({
        "action": "Don't do this",
        "why_fails": "Because it fails",
        "fail_rate": 0.8,
        "sources": ["https://example.gov/doc"],
    })
    jsonschema_validate(instance=canon, schema=ERRORCANON_SCHEMA)

    canon["metadata"]["evidence_count"] = 3
    errors, _warnings = validate_canon_json(canon)
    assert errors == []


def test_make_country_canon_rejects_unknown_domain():
    with pytest.raises(ValueError, match="not a recognised country-canon domain"):
        make_country_canon(
            domain="python",  # code domain — not allowed for country canons
            slug="x",
            country="kr",
            signature="s",
            regex=".",
            category="c",
            summary="s",
        )


def test_make_country_canon_rejects_unknown_country():
    with pytest.raises(ValueError, match="not in SUPPORTED_COUNTRIES"):
        make_country_canon(
            domain="visa",
            slug="x",
            country="zz",
            signature="s",
            regex=".",
            category="c",
            summary="s",
        )


def test_make_country_canon_rejects_bad_slug():
    with pytest.raises(ValueError, match="Invalid slug"):
        make_country_canon(
            domain="visa",
            slug="Bad_Slug",  # uppercase + underscore
            country="kr",
            signature="s",
            regex=".",
            category="c",
            summary="s",
        )


def test_make_country_canon_rejects_invalid_regex():
    with pytest.raises(ValueError, match="regex does not compile"):
        make_country_canon(
            domain="visa",
            slug="valid-slug",
            country="kr",
            signature="s",
            regex="(unclosed",
            category="c",
            summary="s",
        )


def test_canon_country_helpers_return_metadata_when_present():
    canon = make_country_canon(
        domain="visa",
        slug="valid-slug",
        country="jp",
        signature="s",
        regex=".",
        category="c",
        summary="s",
    )
    assert canon_country(canon) == "jp"
    assert canon_country_name(canon) == SUPPORTED_COUNTRIES["jp"]


def test_canon_country_returns_none_for_non_country_canon():
    assert canon_country({"environment": {}}) is None
    assert canon_country_name({"environment": {"additional": {}}}) is None


# --- Seed canons on disk ---------------------------------------------------------


def _all_country_canons() -> list[tuple[Path, dict]]:
    """Load every JSON canon in data/canons and return the country-tagged ones."""
    results = []
    for path in DATA_DIR.rglob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        additional = data.get("environment", {}).get("additional", {})
        if "country" in additional:
            results.append((path, data))
    return results


def test_seed_country_canons_exist():
    canons = _all_country_canons()
    assert len(canons) >= 10, (
        f"Expected at least 10 country-tagged seed canons, found {len(canons)}"
    )


def test_all_seed_country_canons_validate():
    canons = _all_country_canons()
    failures = []
    for path, canon in canons:
        errors, _warnings = validate_canon_json(canon)
        if errors:
            failures.append((str(path.relative_to(DATA_DIR)), errors))
    assert failures == [], f"Country canon validation failures: {failures}"


def test_all_seed_country_canons_use_supported_country_code():
    for path, canon in _all_country_canons():
        code = canon["environment"]["additional"]["country"]
        assert code in SUPPORTED_COUNTRIES, (
            f"{path}: country code '{code}' not in SUPPORTED_COUNTRIES — add it to "
            f"generator/country_canon_template.py if legitimate"
        )


def test_seed_country_canons_env_segment_matches_country():
    """The third path segment in the canon ID should equal the country code."""
    for path, canon in _all_country_canons():
        env_segment = canon["id"].rsplit("/", 1)[1]
        country = canon["environment"]["additional"]["country"]
        # Allow sub-region like "kr-seoul" but the prefix must match.
        assert env_segment == country or env_segment.startswith(country + "-"), (
            f"{path}: env segment '{env_segment}' does not match country '{country}'"
        )


# --- build_site helpers ----------------------------------------------------------


def test_build_env_summary_includes_country_info(make_canon):
    canon = make_canon(
        environment={
            "runtime": {"name": "ai-agent", "version_range": ">=1.0"},
            "os": "any",
            "additional": {
                "country": "kr",
                "country_name": "South Korea",
                "jurisdiction_level": "national",
                "audience": "foreigner-resident",
            },
        }
    )
    summary = build_env_summary(canon)
    assert "South Korea" in summary
    assert "foreigner-resident" in summary


def test_canon_country_info_extracts_tuple():
    canon = {
        "environment": {
            "additional": {"country": "JP", "country_name": "Japan"},
        }
    }
    info = _canon_country_info(canon)
    assert info == ("jp", "Japan")  # lowercased


def test_canon_country_info_returns_none_without_country():
    canon = {"environment": {"additional": {"architecture": "x86_64"}}}
    assert _canon_country_info(canon) is None


def test_country_stats_aggregates_by_code():
    canons = [
        {"environment": {"additional": {"country": "kr", "country_name": "South Korea"}}},
        {"environment": {"additional": {"country": "kr", "country_name": "South Korea"}}},
        {"environment": {"additional": {"country": "jp", "country_name": "Japan"}}},
        {"environment": {}},  # not a country canon; should be ignored
    ]
    stats = country_stats(canons)
    # sorted by count desc
    assert stats[0]["slug"] == "kr"
    assert stats[0]["count"] == 2
    assert stats[1]["slug"] == "jp"
    assert stats[1]["count"] == 1
    assert len(stats) == 2
