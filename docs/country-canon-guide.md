# Country-Canon Authoring Guide

deadends.dev started as a code-error database, but its real long-term value is
**structured knowledge of real-world dead ends that vary by country** — visa
rules, banking requirements, legal procedures, cultural norms, emergency
numbers. These change across jurisdictions, they are not well-represented in
LLM training data, and generic "best-effort" AI answers routinely go wrong.

Country-canons capture that friction. This guide is for contributors writing
them by hand from reliable sources.

## ID & file layout

Every canon has an ID of the form `{domain}/{slug}/{env}`.

For country-scoped canons:

- **domain** — one of `visa`, `banking`, `emergency`, `legal`, `culture`,
  `communication`, `medical`, `mental-health`, `food-safety`, `safety`,
  `policy`, `disaster`.
- **slug** — topic-oriented, lowercase, hyphens (e.g. `foreigner-account-opening`,
  `esta-90-day-no-extension`, `hanko-seal-required`). Avoid country names
  inside the slug — the country lives in the env segment.
- **env** — ISO 3166-1 alpha-2 country code, lowercase (`kr`, `jp`, `us`,
  `de`, `uk`, `fr`, `cn`, `tw`, `sg`, `ca`, `au`, `in`, `th`, `vn`, `mx`,
  `br`, `it`, `es`, `nl`, `ch`). Add sub-region as `kr-seoul` only if
  necessary.

Place the JSON file as either:

- `data/canons/{domain}/{slug}/{env}.json` (directory style, preferred when
  multiple countries will exist for the same slug)
- `data/canons/{domain}/{slug}_{env}.json` (flat-file, fine for one-offs)

## Required `environment` block for country canons

```json
"environment": {
  "runtime": { "name": "ai-agent", "version_range": ">=1.0" },
  "os": "any",
  "additional": {
    "country": "kr",
    "country_name": "South Korea",
    "jurisdiction_level": "national",
    "audience": "foreigner-resident"
  }
}
```

- `country` — ISO code (matches env).
- `country_name` — human display name.
- `jurisdiction_level` — one of `national | regional | city`.
- `audience` — one of `traveler | foreigner-resident | citizen | business`.

The `build_env_summary` helper renders country + audience on the page; the
country landing pages at `/country/{cc}/` use these fields to group entries.

## Source requirements

Each `dead_ends[]` and `workarounds[]` entry should carry a `sources` array.
Quality order:

1. **Primary government & regulator** — official agency sites in the country
   (Ministry of Justice, immigration authority, financial supervisor, health
   authority, police). These are the source of truth.
2. **Embassies & consular bulletins** — particularly for visa and emergency
   content.
3. **Treaty / directive text** — EUR-Lex, WIPO, Schengen Regulations, etc.
4. **Reputable media & NGOs** — only for color / qualitative claims, not for
   the legal rule itself.
5. **Reddit, personal blogs, forums** — never as sole source; may be cited
   inside `condition` or `common_misconception` to document a widespread
   wrong belief but never as authority for the canonical claim.

Avoid non-https URLs, localhost, private IPs, and cloud metadata endpoints —
the site builder rejects those.

## Confidence & success-rate calibration

The validator enforces these business rules:

| `verdict.resolvable` | Required `fix_success_rate` | Required `confidence` |
|----------------------|------------------------------|------------------------|
| `true`               | ≥ 0.7                        | ≥ 0.6                  |
| `partial`            | (any)                        | (any)                  |
| `false`              | < 0.2                        | ≥ 0.6                  |

Plus: `evidence_count < 3` forces `confidence ≤ 0.3`.

Rough guidance for manual authors:

- **Confidence 0.85+**: black-letter law or a single regulator's official
  procedure you have verified on their site this quarter.
- **Confidence 0.70–0.85**: well-documented practice across ≥3 primary
  sources, with some variation by branch / region / year.
- **Confidence 0.40–0.60**: cultural / etiquette claims that hold broadly
  but admit individual exceptions; always lean lower.
- **Confidence ≤ 0.30**: fewer than 3 sources, new regulation not yet
  stabilized, or disputed claim.

For `fix_success_rate`, estimate **what fraction of users following this
workaround avoid the dead end**. If even the best workaround still fails
30%+ of the time, set `resolvable: "partial"` rather than padding the rate.

## Slug and regex patterns

- The regex is used by `/api/v1/match.json` and the MCP `lookup_error` tool
  to match user-supplied error text. Include both English and local-language
  terms when plausible — e.g. `(korea.*overstay|한국.*불법체류|south korea.*visa.*expire)`.
- Avoid nested quantifiers like `(a+)+` or quantified alternation `(a|b)+` —
  the validator warns on obvious ReDoS patterns but cannot catch all cases.
- Keep the regex short; every canon's regex is scanned against every query.

## Scaffolding a canon in Python

```python
from generator.country_canon_template import make_country_canon
import json, pathlib

canon = make_country_canon(
    domain="banking",
    slug="foreigner-account-opening",
    country="jp",
    signature="AI tells a foreign visitor to walk into a bank in Japan and open an account like at home",
    regex=r"(japan.*bank.*account|japanese.*bank.*open|在留カード.*口座)",
    category="administrative_barrier",
    summary="Most major Japanese banks require a residence card with 6+ months remaining...",
    audience="foreigner-resident",
    fix_success_rate=0.78,
    confidence=0.82,
)

# Fill in canon["dead_ends"] and canon["workarounds"] from your research.
# Update canon["metadata"]["evidence_count"] to match sources.
pathlib.Path("data/canons/banking/foreigner-account-opening").mkdir(parents=True, exist_ok=True)
pathlib.Path("data/canons/banking/foreigner-account-opening/jp.json").write_text(
    json.dumps(canon, indent=2, ensure_ascii=False), encoding="utf-8"
)
```

Then run:

```bash
python -m generator.validate --data-only
```

## Dead ends: what to look for

Good country-canon dead ends have three properties:

1. **Plausible to generalize** — the generic advice is what a naive assistant
   would say ("call 911", "tip 15%", "open a bank account with just a
   passport"). This is the trap.
2. **Wrong locally, with real cost** — not a stylistic nit. Missing the
   actual rule loses money, time, legal standing, or safety.
3. **Fixable with specific alternative steps** — you can write workarounds
   that are concrete, verifiable, and materially different from the dead
   end.

If all three aren't present, the canon is probably better written as a
non-country entry in the existing `legal` / `culture` / `medical` domain
without a country suffix.
