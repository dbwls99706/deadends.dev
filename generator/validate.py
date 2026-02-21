"""Validation script for ErrorCanon JSON files and generated HTML pages."""

import argparse
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

from jsonschema import ValidationError, validate

from generator.schema import ERRORCANON_SCHEMA

BASE_URL = "https://deadends.dev"

# Staleness thresholds (days since last_confirmed)
STALE_THRESHOLD_DAYS = 365
AGING_THRESHOLD_DAYS = 180


def _parse_date(date_str: str) -> date | None:
    """Parse a YYYY-MM-DD string into a date object."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def _canon_age_days(data: dict, reference_date: date | None = None) -> int | None:
    """Calculate days since last_confirmed. Returns None if date is missing/invalid."""
    ref = reference_date or date.today()
    last_confirmed = data.get("error", {}).get("last_confirmed")
    d = _parse_date(last_confirmed)
    if d is None:
        return None
    return (ref - d).days


def validate_canon_json(data: dict) -> tuple[list[str], list[str]]:
    """Validate an ErrorCanon JSON object against the schema and business rules.

    Returns (errors, warnings) — errors fail the build, warnings do not.
    """
    errors = []
    warnings = []

    # Schema validation
    try:
        validate(instance=data, schema=ERRORCANON_SCHEMA)
    except ValidationError as e:
        errors.append(f"Schema validation error: {e.message}")
        return errors, warnings  # No point checking business rules if schema fails

    # Business rule: dead_ends must have at least 1 item
    if len(data.get("dead_ends", [])) < 1:
        errors.append("dead_ends must contain at least 1 item")

    # Business rule: id must match URL pattern
    expected_url = f"{BASE_URL}/{data['id']}"
    if data["url"] != expected_url:
        errors.append(f"URL mismatch: expected {expected_url}, got {data['url']}")

    # Business rule: verdict.resolvable consistency
    verdict = data["verdict"]
    rate = verdict["fix_success_rate"]
    conf = verdict["confidence"]
    resolvable = verdict["resolvable"]

    if resolvable == "true" and (rate < 0.7 or conf < 0.6):
        errors.append(
            f"verdict 'true' requires fix_success_rate >= 0.7 and confidence >= 0.6, "
            f"got rate={rate}, confidence={conf}"
        )
    if resolvable == "false" and (rate >= 0.2 or conf < 0.6):
        errors.append(
            f"verdict 'false' requires fix_success_rate < 0.2 and confidence >= 0.6, "
            f"got rate={rate}, confidence={conf}"
        )

    # Business rule: low evidence warning
    evidence_count = data["metadata"].get("evidence_count", 0)
    if evidence_count < 3 and conf > 0.3:
        errors.append(
            f"evidence_count={evidence_count} < 3 but confidence={conf} > 0.3. "
            "Low evidence should have confidence <= 0.3."
        )

    # Business rule: all numeric rates in 0.0-1.0 range
    for i, de in enumerate(data.get("dead_ends", [])):
        if not 0.0 <= de["fail_rate"] <= 1.0:
            errors.append(f"dead_ends[{i}].fail_rate out of range: {de['fail_rate']}")

    for i, wa in enumerate(data.get("workarounds", [])):
        if not 0.0 <= wa["success_rate"] <= 1.0:
            errors.append(f"workarounds[{i}].success_rate out of range: {wa['success_rate']}")

    # Business rule: regex should be valid
    try:
        re.compile(data["error"]["regex"])
    except re.error as e:
        errors.append(f"Invalid error regex: {e}")

    # Warning: dead_ends with empty sources
    for i, de in enumerate(data.get("dead_ends", [])):
        if not de.get("sources"):
            warnings.append(
                f"dead_ends[{i}] '{de['action']}' has no sources — "
                "consider adding evidence URLs"
            )

    # Warning: evidence_count vs actual sources mismatch
    total_sources = sum(
        len(de.get("sources", [])) for de in data.get("dead_ends", [])
    ) + sum(len(wa.get("sources", [])) for wa in data.get("workarounds", []))

    if total_sources == 0 and data["metadata"]["evidence_count"] > 10:
        warnings.append(
            f"evidence_count={data['metadata']['evidence_count']} but no source URLs provided"
        )

    # Warning: staleness check based on last_confirmed age
    age = _canon_age_days(data)
    if age is not None:
        if age > STALE_THRESHOLD_DAYS:
            warnings.append(
                f"Stale canon: last_confirmed {data['error']['last_confirmed']} "
                f"({age} days ago, threshold: {STALE_THRESHOLD_DAYS} days). "
                "Consider re-verifying this error."
            )
        elif age > AGING_THRESHOLD_DAYS:
            warnings.append(
                f"Aging canon: last_confirmed {data['error']['last_confirmed']} "
                f"({age} days ago). Consider re-verification before "
                f"{STALE_THRESHOLD_DAYS} days."
            )

    return errors, warnings


def staleness_summary(
    canons: list[dict], reference_date: date | None = None
) -> str:
    """Generate a summary report of canon freshness across the dataset.

    Returns a formatted string with staleness statistics.
    """
    ref = reference_date or date.today()
    fresh = 0
    aging = 0
    stale = 0
    unknown = 0
    stale_ids: list[tuple[str, int]] = []

    for canon in canons:
        age = _canon_age_days(canon, ref)
        if age is None:
            unknown += 1
        elif age > STALE_THRESHOLD_DAYS:
            stale += 1
            stale_ids.append((canon["id"], age))
        elif age > AGING_THRESHOLD_DAYS:
            aging += 1
        else:
            fresh += 1

    total = len(canons)
    lines = [
        f"\n  FRESHNESS REPORT ({ref.isoformat()})",
        f"  Total: {total} | Fresh: {fresh} | "
        f"Aging: {aging} | Stale: {stale} | Unknown: {unknown}",
    ]

    if stale_ids:
        stale_ids.sort(key=lambda x: x[1], reverse=True)
        lines.append(f"\n  Top stale canons (>{STALE_THRESHOLD_DAYS} days):")
        for canon_id, age in stale_ids[:10]:
            lines.append(f"    {canon_id} — {age} days")
        if len(stale_ids) > 10:
            lines.append(f"    ... and {len(stale_ids) - 10} more")

    return "\n".join(lines)


def validate_unique_ids(canons: list[dict]) -> list[str]:
    """Validate that all canon IDs are unique across the dataset.

    Duplicate IDs can occur when both flat-file (slug_env.json) and
    directory-style (slug/env.json) formats coexist for the same canon.

    Returns errors so duplicates fail the build.
    """
    errors = []
    seen: dict[str, list[str]] = {}
    for canon in canons:
        cid = canon["id"]
        url = canon.get("url", "")
        key = f"{cid}|{url}"
        seen.setdefault(cid, []).append(url)

    for cid, urls in seen.items():
        if len(urls) > 1:
            errors.append(
                f"Duplicate canon ID '{cid}' found {len(urls)} times. "
                "Remove the duplicate file (flat-file vs directory-style conflict)."
            )
    return errors


def validate_cross_references(canons: list[dict]) -> list[str]:
    """Validate that all referenced error_ids exist in the dataset.

    Returns errors so broken references fail the build.
    """
    errors = []
    known_ids = {c["id"] for c in canons}

    for canon in canons:
        graph = canon.get("transition_graph", {})

        for lt in graph.get("leads_to", []):
            if lt["error_id"] not in known_ids:
                errors.append(
                    f"{canon['id']}: transition_graph.leads_to references "
                    f"non-existent error '{lt['error_id']}'"
                )

        for pb in graph.get("preceded_by", []):
            if pb["error_id"] not in known_ids:
                errors.append(
                    f"{canon['id']}: transition_graph.preceded_by references "
                    f"non-existent error '{pb['error_id']}'"
                )

        for fc in graph.get("frequently_confused_with", []):
            if fc["error_id"] not in known_ids:
                errors.append(
                    f"{canon['id']}: transition_graph.frequently_confused_with "
                    f"references non-existent error '{fc['error_id']}'"
                )

    return errors


def validate_html(html_path: Path) -> list[str]:
    """Validate a generated HTML page."""
    errors = []
    content = html_path.read_text(encoding="utf-8")

    # Must contain JSON-LD
    if 'application/ld+json' not in content:
        errors.append(f"{html_path}: Missing JSON-LD structured data")

    # Must contain canonical link
    if 'rel="canonical"' not in content:
        errors.append(f"{html_path}: Missing canonical link")

    # Must contain ai-summary
    if 'id="ai-summary"' not in content:
        errors.append(f"{html_path}: Missing ai-summary section")

    # Must contain dead-ends section
    if 'id="dead-ends"' not in content:
        errors.append(f"{html_path}: Missing dead-ends section")

    # Extract and validate embedded JSON-LD
    json_ld_match = re.search(
        r'<script type="application/ld\+json">\s*(.*?)\s*</script>',
        content,
        re.DOTALL,
    )
    if json_ld_match:
        try:
            json.loads(json_ld_match.group(1))
        except json.JSONDecodeError as e:
            errors.append(f"{html_path}: Invalid JSON-LD: {e}")
    else:
        errors.append(f"{html_path}: Could not extract JSON-LD")

    return errors


def validate_html_json_consistency(
    html_path: Path, canons_by_id: dict[str, dict]
) -> list[str]:
    """Verify that HTML page content matches the source JSON data."""
    errors = []
    content = html_path.read_text(encoding="utf-8")

    json_ld_match = re.search(
        r'<script type="application/ld\+json">\s*(.*?)\s*</script>',
        content,
        re.DOTALL,
    )
    if not json_ld_match:
        return [f"{html_path}: Could not extract JSON-LD for consistency check"]

    try:
        ld_data = json.loads(json_ld_match.group(1))
    except json.JSONDecodeError:
        return [f"{html_path}: Invalid JSON-LD for consistency check"]

    canon_id = ld_data.get("id")
    if canon_id and canon_id in canons_by_id:
        source = canons_by_id[canon_id]
        ld_verdict = ld_data.get("verdict", {})
        src_verdict = source["verdict"]

        if ld_verdict.get("resolvable") != src_verdict["resolvable"]:
            errors.append(
                f"{html_path}: JSON-LD verdict.resolvable mismatch with source data"
            )
        if ld_verdict.get("fix_success_rate") != src_verdict["fix_success_rate"]:
            errors.append(
                f"{html_path}: JSON-LD fix_success_rate mismatch with source data"
            )

    return errors


def validate_all(
    data_dir: Path | None = None,
    site_dir: Path | None = None,
    skip_data_validation: bool = False,
) -> bool:
    """Validate canon JSON files and/or generated HTML.

    Args:
        data_dir: Path to canon JSON data. If provided, loads canons for validation
            and/or consistency checks.
        site_dir: Path to generated site. If provided, validates HTML pages.
        skip_data_validation: If True, loads canon data (for consistency checks)
            but skips JSON schema/business rule validation.

    Returns True if all validations pass (warnings don't cause failure).
    """
    all_errors = []
    all_warnings = []
    all_canons = []

    # Load and optionally validate canon JSON files
    if data_dir:
        canon_files = list(data_dir.rglob("*.json"))
        if not canon_files:
            print("WARNING: No canon JSON files found")
        else:
            for canon_file in canon_files:
                try:
                    with open(canon_file, encoding="utf-8") as f:
                        data = json.load(f)
                    all_canons.append(data)

                    if not skip_data_validation:
                        errors, warnings = validate_canon_json(data)
                        for error in errors:
                            all_errors.append(f"{canon_file}: {error}")
                            print(f"  FAIL: {canon_file}: {error}")
                        for warning in warnings:
                            all_warnings.append(f"{canon_file}: {warning}")
                            print(f"  WARN: {canon_file}: {warning}")
                        if not errors:
                            print(f"  OK: {canon_file}")
                except json.JSONDecodeError as e:
                    all_errors.append(f"{canon_file}: Invalid JSON: {e}")
                    print(f"  FAIL: {canon_file}: Invalid JSON: {e}")

            if not skip_data_validation:
                # Duplicate ID validation (errors — fail the build)
                dup_errors = validate_unique_ids(all_canons)
                for error in dup_errors:
                    all_errors.append(error)
                    print(f"  FAIL: {error}")

                # Cross-reference validation (errors — fail the build)
                xref_errors = validate_cross_references(all_canons)
                for error in xref_errors:
                    all_errors.append(error)
                    print(f"  FAIL: {error}")

    # Validate HTML files if site_dir provided
    if site_dir and site_dir.exists():
        html_files = list(site_dir.rglob("index.html"))
        # Only validate env-specific error pages (depth >= 4: domain/slug/env/index.html)
        # Excludes: top-level index, domain listings (depth 2), error summaries (depth 3)
        error_pages = [
            f
            for f in html_files
            if f.parent != site_dir and len(f.relative_to(site_dir).parts) > 3
        ]
        for html_file in error_pages:
            errors = validate_html(html_file)
            for error in errors:
                all_errors.append(error)
                print(f"  FAIL: {error}")
            if not errors:
                print(f"  OK: {html_file}")

        # HTML-JSON consistency check
        if all_canons:
            canons_by_id = {c["id"]: c for c in all_canons}
            for html_file in error_pages:
                errors = validate_html_json_consistency(html_file, canons_by_id)
                for error in errors:
                    all_errors.append(error)
                    print(f"  FAIL: {error}")

    # Staleness summary (always show when canons are loaded)
    if all_canons:
        print(staleness_summary(all_canons))

    if all_warnings:
        print(f"\n{len(all_warnings)} warning(s)")

    if all_errors:
        print(f"\nValidation FAILED: {len(all_errors)} error(s)")
        return False
    else:
        print("\nValidation PASSED")
        return True


def main():
    parser = argparse.ArgumentParser(description="Validate ErrorCanon data and site")
    parser.add_argument(
        "--data-only", action="store_true", help="Validate canon JSON only"
    )
    parser.add_argument(
        "--site-only", action="store_true", help="Validate generated HTML only"
    )
    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data" / "canons"
    site_dir = project_root / "site"

    print("Validating ErrorCanon data and site...\n")

    if args.site_only:
        # HTML validation + JSON-HTML consistency (loads canon data for comparison)
        success = validate_all(data_dir=data_dir, site_dir=site_dir, skip_data_validation=True)
    elif args.data_only:
        success = validate_all(data_dir=data_dir, site_dir=None)
    else:
        site_path = site_dir if site_dir.exists() else None
        success = validate_all(data_dir, site_path)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
