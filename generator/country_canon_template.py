"""Scaffold helper for authoring country-specific ErrorCanon JSON by hand.

Country-specific canons capture real-world dead ends that vary by jurisdiction:
visa/immigration rules, banking requirements, legal procedures, cultural
norms, emergency numbers, etc. Unlike code errors, they are authored manually
from reliable sources (government sites, embassies, reputable media).

Usage (interactive Python):

    from generator.country_canon_template import make_country_canon
    canon = make_country_canon(
        domain="banking",
        slug="foreigner-account-opening",
        country="jp",
        country_name="Japan",
        signature="AI advises opening a JP bank account without residency requirements",
        regex=r"(japan.*bank.*account|japanese.*account|open.*account.*japan)",
        category="administrative_barrier",
        summary=(
            "Major Japanese banks require a residence card (在留カード) with "
            "6+ months validity and a my-number card to open accounts."
        ),
        audience="foreigner-resident",
    )
    # Fill in canon["dead_ends"], canon["workarounds"], and canon["metadata"]["evidence_count"].
    # Then save to data/canons/{domain}/{slug}/{country}.json (or flat-file form).

The function produces a schema-valid skeleton. The author still must supply
at least one dead_end, at least one source per dead_end/workaround, and
adjust confidence / fix_success_rate so that business rules pass:

- resolvable="true"  → fix_success_rate >= 0.7 AND confidence >= 0.6
- resolvable="false" → fix_success_rate < 0.2  AND confidence >= 0.6
- evidence_count < 3 → confidence <= 0.3
"""

from __future__ import annotations

import re
from datetime import date

BASE_URL = "https://deadends.dev"

# ISO 3166-1 alpha-2 lowercase country codes used as the env segment in IDs.
# Extend this as new countries are added. Restrict to real codes to avoid typos.
SUPPORTED_COUNTRIES: dict[str, str] = {
    "kr": "South Korea",
    "jp": "Japan",
    "us": "United States",
    "de": "Germany",
    "uk": "United Kingdom",  # ISO is "gb" but "uk" is user-friendly
    "fr": "France",
    "cn": "China",
    "tw": "Taiwan",
    "sg": "Singapore",
    "ca": "Canada",
    "au": "Australia",
    "in": "India",
    "th": "Thailand",
    "vn": "Vietnam",
    "mx": "Mexico",
    "br": "Brazil",
    "it": "Italy",
    "es": "Spain",
    "nl": "Netherlands",
    "ch": "Switzerland",
    "sa": "Saudi Arabia",
    "ae": "United Arab Emirates",
    "tr": "Turkey",
    "il": "Israel",
    "ru": "Russia",
    "id": "Indonesia",
    "ma": "Morocco",
    "et": "Ethiopia",
    "eg": "Egypt",
    "pl": "Poland",
    "gr": "Greece",
    "pt": "Portugal",
    "ie": "Ireland",
    "at": "Austria",
    "be": "Belgium",
    "se": "Sweden",
    "no": "Norway",
    "dk": "Denmark",
    "fi": "Finland",
    "ph": "Philippines",
    "my": "Malaysia",
    "pk": "Pakistan",
    "bd": "Bangladesh",
    "za": "South Africa",
    "ng": "Nigeria",
    "ke": "Kenya",
    "ar": "Argentina",
    "cl": "Chile",
    "co": "Colombia",
    "pe": "Peru",
    "nz": "New Zealand",
    "hk": "Hong Kong",
}

# Who the guidance is aimed at — used for filtering and UI hints.
VALID_AUDIENCES = frozenset({
    "traveler",
    "foreigner-resident",
    "citizen",
    "business",
})

VALID_JURISDICTION_LEVELS = frozenset({"national", "regional", "city"})

# Domains that make sense for country-scoped canons. Code domains are excluded
# on purpose; this helper is for real-world knowledge.
COUNTRY_DOMAINS = frozenset({
    "visa",
    "banking",
    "emergency",
    "legal",
    "culture",
    "communication",
    "medical",
    "mental-health",
    "food-safety",
    "safety",
    "policy",
    "disaster",
})

_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*[a-z0-9]$")


def _validate_slug(slug: str) -> None:
    if not _SLUG_RE.match(slug):
        raise ValueError(
            f"Invalid slug {slug!r}: must be lowercase alphanumeric with hyphens, "
            "no leading/trailing hyphen."
        )


def make_country_canon(
    *,
    domain: str,
    slug: str,
    country: str,
    signature: str,
    regex: str,
    category: str,
    summary: str,
    country_name: str | None = None,
    audience: str = "foreigner-resident",
    jurisdiction_level: str = "national",
    resolvable: str = "true",
    fix_success_rate: float = 0.75,
    confidence: float = 0.7,
    first_seen: str | None = None,
) -> dict:
    """Return a schema-valid country-canon skeleton.

    The caller is responsible for populating dead_ends, workarounds, sources,
    transition_graph cross-references, and metadata.evidence_count before the
    canon is persisted. The validator will reject incomplete canons.
    """
    if domain not in COUNTRY_DOMAINS:
        raise ValueError(
            f"Domain {domain!r} is not a recognised country-canon domain. "
            f"Expected one of: {sorted(COUNTRY_DOMAINS)}"
        )

    country = country.lower()
    if country not in SUPPORTED_COUNTRIES:
        raise ValueError(
            f"Country code {country!r} not in SUPPORTED_COUNTRIES. "
            "Add it there if legitimate (ISO 3166-1 alpha-2)."
        )

    if audience not in VALID_AUDIENCES:
        raise ValueError(
            f"audience {audience!r} not in {sorted(VALID_AUDIENCES)}"
        )
    if jurisdiction_level not in VALID_JURISDICTION_LEVELS:
        raise ValueError(
            f"jurisdiction_level {jurisdiction_level!r} not in "
            f"{sorted(VALID_JURISDICTION_LEVELS)}"
        )
    if resolvable not in ("true", "partial", "false"):
        raise ValueError(f"resolvable must be 'true'|'partial'|'false', got {resolvable!r}")

    _validate_slug(slug)
    _validate_slug(domain)

    # Validate the regex compiles so downstream lookup doesn't blow up.
    try:
        re.compile(regex)
    except re.error as e:
        raise ValueError(f"regex does not compile: {e}") from e

    canon_id = f"{domain}/{slug}/{country}"
    today = date.today().isoformat()
    resolved_country_name = country_name or SUPPORTED_COUNTRIES[country]

    return {
        "schema_version": "1.0.0",
        "id": canon_id,
        "url": f"{BASE_URL}/{canon_id}",
        "error": {
            "signature": signature,
            "regex": regex,
            "domain": domain,
            "category": category,
            "first_seen": first_seen or today,
            "last_confirmed": today,
        },
        "environment": {
            "runtime": {"name": "ai-agent", "version_range": ">=1.0"},
            "os": "any",
            "additional": {
                "country": country,
                "country_name": resolved_country_name,
                "jurisdiction_level": jurisdiction_level,
                "audience": audience,
            },
        },
        "verdict": {
            "resolvable": resolvable,
            "fix_success_rate": fix_success_rate,
            "confidence": confidence,
            "last_updated": today,
            "summary": summary,
        },
        "dead_ends": [],  # Author must add at least one entry.
        "workarounds": [],
        "transition_graph": {
            "leads_to": [],
            "preceded_by": [],
            "frequently_confused_with": [],
        },
        "metadata": {
            "generated_by": "manual",
            "generation_date": today,
            "review_status": "human_reviewed",
            "evidence_count": 0,  # Bump this as you add sources.
            "last_verification": today,
        },
    }


def canon_country(canon: dict) -> str | None:
    """Return the ISO country code if the canon has country metadata, else None."""
    additional = canon.get("environment", {}).get("additional", {})
    country = additional.get("country")
    return country.lower() if isinstance(country, str) else None


def canon_country_name(canon: dict) -> str | None:
    """Return the display country name if present."""
    additional = canon.get("environment", {}).get("additional", {})
    name = additional.get("country_name")
    return name if isinstance(name, str) and name else None
