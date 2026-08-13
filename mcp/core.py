"""Shared canon data layer for the MCP surfaces.

Both `mcp/server.py` (stdio JSON-RPC) and `api/mcp.py` (Vercel HTTP) answer the
same questions about the same data; only the transport differs. This module owns
that shared half: loading canons, indexing them by domain, compiling their
regexes, and matching an error message against them.

State lives on `CanonRepository` rather than in module globals. That is what
makes the caches ownable: a caller can hold its own repository, tests can build
one over a handful of fixture canons, and nothing has to reach into another
module to reset a cache between cases.
"""

import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

from generator.lookup import _extract_error_lines

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "canons"
OUTCOMES_DIR = PROJECT_ROOT / "data" / "outcomes"

# Long inputs are truncated rather than rejected: a caller pasting a huge stack
# trace should still get an answer, but an unbounded string multiplied by ~2400
# regexes is a denial-of-service waiting to happen.
MAX_ERROR_MESSAGE_LEN = 10_000
MAX_SEARCH_QUERY_LEN = 1_000

ID_PATTERN = re.compile(r"^[a-z0-9-]+/[a-z0-9-]+/[a-z0-9._-]+$")

FRESH_DAYS = 180
STALE_DAYS = 365


def is_valid_canon(canon) -> bool:
    """Check that a canon has the minimum structure the lookups rely on."""
    return (
        isinstance(canon, dict)
        and isinstance(canon.get("error"), dict)
        and isinstance(canon.get("verdict"), dict)
        and "domain" in canon["error"]
        and "signature" in canon["error"]
    )


def compute_freshness(canon: dict) -> str:
    """Classify a canon by how long ago its claim was last confirmed.

    Returns 'fresh' (<180 days), 'aging' (180-365), 'stale' (>365), or 'unknown'.
    """
    last_confirmed = canon.get("error", {}).get("last_confirmed")
    if not last_confirmed:
        return "unknown"
    try:
        confirmed = datetime.strptime(last_confirmed, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return "unknown"
    age = (date.today() - confirmed).days
    if age > STALE_DAYS:
        return "stale"
    if age > FRESH_DAYS:
        return "aging"
    return "fresh"


def summary_url(canon: dict) -> str:
    """URL of the canon's summary page.

    Canon `url` points at the per-environment page, which is a noindex redirect
    stub whenever the slug has a single environment. Callers want the summary
    page one level up - that is the page that is actually indexed and readable.
    """
    return canon["url"].rstrip("/").rsplit("/", 1)[0] + "/"


class CanonRepository:
    """Owns the canon corpus and the indexes derived from it.

    Everything is built lazily on first access and then reused. Pass `canons`
    to work over an in-memory corpus instead of reading from disk, which is how
    tests avoid loading ~2400 files to exercise two.
    """

    def __init__(
        self,
        data_dir: Path | None = None,
        outcomes_dir: Path | None = None,
        canons: list[dict] | None = None,
    ):
        self.data_dir = data_dir or DATA_DIR
        self.outcomes_dir = outcomes_dir or OUTCOMES_DIR
        self._canons = canons
        self._domain_index: dict[str, list[str]] | None = None
        self._compiled_regexes: dict[str, re.Pattern | None] | None = None
        self._outcome_stats: dict[str, dict] | None = None

    def reset(self) -> None:
        """Drop every cache, including any injected corpus."""
        self._canons = None
        self._domain_index = None
        self._compiled_regexes = None
        self._outcome_stats = None

    def invalidate_outcomes(self) -> None:
        """Drop only the outcome stats, so the next read picks up new results."""
        self._outcome_stats = None

    @property
    def canons(self) -> list[dict]:
        if self._canons is None:
            loaded = []
            for path in sorted(self.data_dir.rglob("*.json")):
                with open(path, encoding="utf-8") as fh:
                    data = json.load(fh)
                if is_valid_canon(data):
                    loaded.append(data)
            self._canons = loaded
        return self._canons

    @property
    def domain_index(self) -> dict[str, list[str]]:
        """domain -> [signature], in corpus order, deduplicated."""
        if self._domain_index is None:
            index: dict[str, list[str]] = {}
            for canon in self.canons:
                try:
                    domain = canon["error"]["domain"]
                    signature = canon["error"]["signature"]
                except (KeyError, TypeError):
                    continue
                bucket = index.setdefault(domain, [])
                if signature not in bucket:
                    bucket.append(signature)
            self._domain_index = index
        return self._domain_index

    @property
    def compiled_regexes(self) -> dict[str, re.Pattern | None]:
        """canon id -> compiled pattern, or None if the canon's regex is bad.

        Compiling once per process matters: matching walks every canon on every
        request. A canon whose regex does not compile maps to None rather than
        raising, so one malformed entry cannot take down the whole lookup.
        """
        if self._compiled_regexes is None:
            compiled: dict[str, re.Pattern | None] = {}
            for canon in self.canons:
                canon_id = canon.get("id", "")
                regex = canon.get("error", {}).get("regex", "")
                try:
                    compiled[canon_id] = re.compile(regex, re.IGNORECASE)
                except re.error as exc:
                    sys.stderr.write(f"WARNING: Invalid regex in {canon_id}: {exc}\n")
                    compiled[canon_id] = None
            self._compiled_regexes = compiled
        return self._compiled_regexes

    @property
    def outcome_stats(self) -> dict[str, dict]:
        """Aggregated workaround outcomes, empty when none have been collected."""
        if self._outcome_stats is None:
            stats: dict[str, dict] = {}
            aggregated = self.outcomes_dir / "aggregated.json"
            if aggregated.exists():
                try:
                    with open(aggregated, encoding="utf-8") as fh:
                        stats = json.load(fh).get("deltas", {})
                except (json.JSONDecodeError, KeyError, OSError):
                    stats = {}
            self._outcome_stats = stats
        return self._outcome_stats


def lookup_by_id(error_id: str, canons: list[dict]) -> dict | None:
    """Look up one canon by ID, rejecting IDs that are not well formed."""
    if not error_id or not ID_PATTERN.match(error_id):
        return None
    for canon in canons:
        if canon.get("id") == error_id:
            return canon
    return None


def list_domains(canons: list[dict]) -> dict:
    """Count canons per domain."""
    domains: dict[str, int] = {}
    for canon in canons:
        try:
            domain = canon["error"]["domain"]
        except (KeyError, TypeError):
            continue
        domains[domain] = domains.get(domain, 0) + 1
    return {"total": len(canons), "domains": domains}


def format_domain_listing(canons: list[dict], sort_by: str = "count") -> str:
    """Human-readable domain listing, biggest domains first unless asked otherwise."""
    counts = list_domains(canons)["domains"]
    if sort_by == "name":
        ordered = sorted(counts.items())
    else:
        ordered = sorted(counts.items(), key=lambda item: item[1], reverse=True)

    lines = [f"Total errors: {len(canons)}", ""]
    lines += [f"- {domain}: {count} errors" for domain, count in ordered]
    lines.append(
        "\nUse lookup_error to search by error message, or get_error_detail "
        "with an ID like 'python/modulenotfounderror/py311-linux'."
    )
    return "\n".join(lines)


def json_match_payload(matches: list[dict], limit: int) -> str:
    """Serialize matches for callers that asked for JSON instead of prose.

    `total` counts every match, not just the ones included, so a caller can tell
    a short list from a truncated one.
    """
    payload = [
        {
            "id": m["id"],
            "signature": m["signature"],
            "domain": m["domain"],
            "resolvable": m["resolvable"],
            "fix_success_rate": m["fix_success_rate"],
            "summary": m["summary"],
            "url": m["url"],
            "dead_ends": [
                {
                    "action": d["action"],
                    "why_fails": d["why_fails"],
                    "fail_rate": d["fail_rate"],
                }
                for d in m["dead_ends"]
            ],
            "workarounds": [
                {
                    "action": w["action"],
                    "success_rate": w["success_rate"],
                    "how": w.get("how", ""),
                }
                for w in m["workarounds"]
            ],
            "leads_to": m.get("leads_to", []),
        }
        for m in matches[:limit]
    ]
    return json.dumps({"matches": payload, "total": len(matches)}, ensure_ascii=False)


def match_error(
    error_message: str,
    canons: list[dict],
    repo: CanonRepository | None = None,
    preferred_domains: list[str] | None = None,
) -> list[dict]:
    """Match an error message against known patterns, best match first.

    Ranked by (match ratio, preferred domain, fix success rate): a pattern that
    accounts for more of the message beats one that matches a fragment, a
    caller's preferred domains break near-ties, and fix success rate settles the
    rest.

    `repo` supplies the compiled-regex cache. Without one, the patterns for
    `canons` are compiled on the spot - fine for a handful of canons, wasteful
    for the full corpus.
    """
    if not error_message or not error_message.strip():
        return []

    if len(error_message) > MAX_ERROR_MESSAGE_LEN:
        error_message = error_message[:MAX_ERROR_MESSAGE_LEN]

    if repo is None:
        repo = CanonRepository(canons=canons)
    compiled = repo.compiled_regexes
    preferred = preferred_domains or []

    # Stack traces bury the signature under frames; match the salient lines
    # first and fall back to the raw text so nothing is lost.
    extracted = _extract_error_lines(error_message)
    extracted_len = len(extracted)

    matches = []
    skipped = 0
    for canon in canons:
        try:
            pattern = compiled.get(canon.get("id", ""))
            if pattern is None:
                skipped += 1
                continue
            found = pattern.search(extracted)
            if not found and extracted != error_message:
                found = pattern.search(error_message)
            if not found:
                continue
            domain = canon["error"]["domain"]
            matches.append(
                {
                    "id": canon["id"],
                    "signature": canon["error"]["signature"],
                    "domain": domain,
                    "resolvable": canon["verdict"]["resolvable"],
                    "fix_success_rate": canon["verdict"]["fix_success_rate"],
                    "summary": canon["verdict"]["summary"],
                    "dead_ends": [
                        {
                            "action": d["action"],
                            "why_fails": d["why_fails"],
                            "fail_rate": d["fail_rate"],
                        }
                        for d in canon["dead_ends"]
                    ],
                    "workarounds": [
                        {
                            "action": w["action"],
                            "success_rate": w["success_rate"],
                            "how": w.get("how", ""),
                        }
                        for w in canon.get("workarounds", [])
                    ],
                    "leads_to": [
                        lt["error_id"]
                        for lt in canon.get("transition_graph", {}).get("leads_to", [])
                        if "error_id" in lt
                    ],
                    "freshness": compute_freshness(canon),
                    "url": summary_url(canon),
                    "_match_ratio": (
                        len(found.group()) / extracted_len if extracted_len else 0
                    ),
                    "_preferred": 1 if domain in preferred else 0,
                }
            )
        except (re.error, KeyError, TypeError, AttributeError) as exc:
            sys.stderr.write(
                f"WARNING: Skipping canon {canon.get('id', '<unknown>')}: {exc}\n"
            )
            skipped += 1
            continue

    matches.sort(
        key=lambda m: (m["_match_ratio"], m["_preferred"], m["fix_success_rate"]),
        reverse=True,
    )
    for match in matches:
        match.pop("_match_ratio", None)
        match.pop("_preferred", None)

    # Let callers tell users the answer is partial rather than silently short.
    if skipped and matches:
        matches[0]["_skipped_canons"] = skipped
    return matches


# Tool schemas are shared so the stdio server and the HTTP endpoint cannot
# advertise different capabilities. Both dispatchers must handle every argument
# declared here.
TOOLS = [{'name': 'lookup_error',
  'description': "Match an error message against deadends.dev's database of known "
                 'errors. Returns dead ends (what NOT to try), workarounds (what '
                 'works), and error chains (what comes next). Use this BEFORE '
                 'attempting to fix any error to avoid wasting time on approaches that '
                 'are known to fail. Covers 51 domains including python, node, docker, '
                 'git, cuda, typescript, rust, go, kubernetes, terraform, aws, react, '
                 'java, database, pytorch, tensorflow, and 34 more. Use '
                 'list_error_domains to see all.',
  'inputSchema': {'type': 'object',
                  'properties': {'error_message': {'type': 'string',
                                                   'description': 'The full error '
                                                                  'message to look up'},
                                 'format': {'type': 'string',
                                            'enum': ['markdown', 'json'],
                                            'description': 'Response format: '
                                                           "'markdown' (default, "
                                                           "human-readable) or 'json' "
                                                           '(structured, for '
                                                           'programmatic use by AI '
                                                           'agents)'}},
                  'required': ['error_message']},
  'annotations': {'title': 'Look up error',
                  'readOnlyHint': True,
                  'destructiveHint': False,
                  'idempotentHint': True,
                  'openWorldHint': False}},
 {'name': 'get_error_detail',
  'description': 'Get full details for a specific error by its ID (e.g., '
                 "'python/modulenotfounderror/py311-linux'). Includes all dead ends, "
                 'workarounds, error chain info, and source evidence.',
  'inputSchema': {'type': 'object',
                  'properties': {'error_id': {'type': 'string',
                                              'description': 'The error ID '
                                                             '(domain/slug/env)'}},
                  'required': ['error_id']},
  'annotations': {'title': 'Get error details',
                  'readOnlyHint': True,
                  'destructiveHint': False,
                  'idempotentHint': True,
                  'openWorldHint': False}},
 {'name': 'list_error_domains',
  'description': 'List all error domains and counts in the deadends.dev database. '
                 'Covers 51 domains including programming languages, frameworks, '
                 'infrastructure, ML/AI, culture, safety, medical, legal, and more.',
  'inputSchema': {'type': 'object',
                  'properties': {'sort_by': {'type': 'string',
                                             'description': "Sort domains by: 'count' "
                                                            '(default, most errors '
                                                            "first) or 'name' "
                                                            '(alphabetical)'}}},
  'annotations': {'title': 'List domains',
                  'readOnlyHint': True,
                  'destructiveHint': False,
                  'idempotentHint': True,
                  'openWorldHint': False}},
 {'name': 'search_errors',
  'description': 'Search errors by keyword across all domains. Unlike lookup_error '
                 '(which uses regex matching), this does fuzzy keyword search. Use '
                 "when you have a vague description like 'memory issues' or "
                 "'permission denied' rather than an exact error message.",
  'inputSchema': {'type': 'object',
                  'properties': {'query': {'type': 'string',
                                           'description': 'Search keywords (e.g., '
                                                          "'memory limit', 'timeout', "
                                                          "'permission denied')"},
                                 'domain': {'type': 'string',
                                            'description': 'Optional: filter to a '
                                                           'specific domain (e.g., '
                                                           "'python', 'docker')"},
                                 'limit': {'type': 'integer',
                                           'description': 'Max results to return '
                                                          '(default: 10)'}},
                  'required': ['query']},
  'annotations': {'title': 'Search errors',
                  'readOnlyHint': True,
                  'destructiveHint': False,
                  'idempotentHint': True,
                  'openWorldHint': False}},
 {'name': 'list_errors_by_domain',
  'description': 'List all errors in a specific domain with their fix rates. Use this '
                 'to understand coverage for a domain before relying on it.',
  'inputSchema': {'type': 'object',
                  'properties': {'domain': {'type': 'string',
                                            'description': 'The domain to list errors '
                                                           "for (e.g., 'python', "
                                                           "'kubernetes')"},
                                 'sort_by': {'type': 'string',
                                             'description': "Sort by: 'fix_rate' "
                                                            "(default), 'name', or "
                                                            "'confidence'"}},
                  'required': ['domain']},
  'annotations': {'title': 'List domain errors',
                  'readOnlyHint': True,
                  'destructiveHint': False,
                  'idempotentHint': True,
                  'openWorldHint': False}},
 {'name': 'batch_lookup',
  'description': 'Look up multiple error messages at once. Returns the best match for '
                 'each error. Use when debugging a chain of errors or analyzing a log '
                 'with multiple failures.',
  'inputSchema': {'type': 'object',
                  'properties': {'error_messages': {'type': 'array',
                                                    'items': {'type': 'string'},
                                                    'description': 'List of error '
                                                                   'messages to look '
                                                                   'up (max 10)',
                                                    'maxItems': 10}},
                  'required': ['error_messages']},
  'annotations': {'title': 'Batch lookup',
                  'readOnlyHint': True,
                  'destructiveHint': False,
                  'idempotentHint': True,
                  'openWorldHint': False}},
 {'name': 'get_domain_stats',
  'description': 'Get detailed statistics for a domain: error counts, average fix '
                 'rate, resolvability breakdown, top categories, and confidence '
                 'levels. Use this to assess how trustworthy deadends.dev data is for '
                 'a domain.',
  'inputSchema': {'type': 'object',
                  'properties': {'domain': {'type': 'string',
                                            'description': 'The domain to get stats '
                                                           'for'}},
                  'required': ['domain']},
  'annotations': {'title': 'Domain statistics',
                  'readOnlyHint': True,
                  'destructiveHint': False,
                  'idempotentHint': True,
                  'openWorldHint': False}},
 {'name': 'list_errors_by_country',
  'description': 'List all country-scoped dead ends for a given country (ISO alpha-2 '
                 "code, e.g. 'kr', 'jp', 'us', 'de'). Returns visa, banking, legal, "
                 'cultural, medical, food-safety, emergency, and safety dead ends '
                 'specific to that jurisdiction. Use this when an AI agent needs '
                 "jurisdiction-specific knowledge that global LLM training data won't "
                 'reliably cover.',
  'inputSchema': {'type': 'object',
                  'properties': {'country': {'type': 'string',
                                             'description': 'ISO 3166-1 alpha-2 '
                                                            'country code, lowercase '
                                                            "(e.g. 'kr' for Korea, "
                                                            "'jp' for Japan)"},
                                 'domain': {'type': 'string',
                                            'description': 'Optional: filter by domain '
                                                           "(e.g. 'visa', 'legal', "
                                                           "'culture')"}},
                  'required': ['country']},
  'annotations': {'title': 'List by country',
                  'readOnlyHint': True,
                  'destructiveHint': False,
                  'idempotentHint': True,
                  'openWorldHint': False}},
 {'name': 'get_country_summary',
  'description': 'Get a country-level summary: total entries, domain breakdown, '
                 'average fix rate, and most-recent updates for the country. Use this '
                 'to assess coverage for a country before relying on deadends.dev for '
                 'trip / business / legal planning advice.',
  'inputSchema': {'type': 'object',
                  'properties': {'country': {'type': 'string',
                                             'description': 'ISO 3166-1 alpha-2 '
                                                            'country code, lowercase'}},
                  'required': ['country']},
  'annotations': {'title': 'Country summary',
                  'readOnlyHint': True,
                  'destructiveHint': False,
                  'idempotentHint': True,
                  'openWorldHint': False}},
 {'name': 'get_error_chain',
  'description': 'Traverse the error transition graph for a specific error. Shows what '
                 'errors typically follow this one (leads_to), what errors usually '
                 'precede it (preceded_by), and what errors are frequently confused '
                 'with it. Use this to diagnose cascading failures and predict what '
                 'comes next.',
  'inputSchema': {'type': 'object',
                  'properties': {'error_id': {'type': 'string',
                                              'description': 'The error ID '
                                                             '(domain/slug/env) to get '
                                                             'the transition graph '
                                                             'for'}},
                  'required': ['error_id']},
  'annotations': {'title': 'Error chain',
                  'readOnlyHint': True,
                  'destructiveHint': False,
                  'idempotentHint': True,
                  'openWorldHint': False}},
 {'name': 'report_outcome',
  'description': 'Report whether a workaround from deadends.dev worked or failed. This '
                 'feedback improves fix_success_rate and confidence for future users. '
                 'Call this AFTER applying a workaround to help improve the database. '
                 'Accepts the error ID, the workaround action you tried, and whether '
                 'it succeeded.',
  'inputSchema': {'type': 'object',
                  'properties': {'error_id': {'type': 'string',
                                              'description': 'The error ID '
                                                             '(domain/slug/env)'},
                                 'workaround_action': {'type': 'string',
                                                       'description': 'The workaround '
                                                                      'action string '
                                                                      'you tried (from '
                                                                      'the workarounds '
                                                                      'list)'},
                                 'success': {'type': 'boolean',
                                             'description': 'Whether the workaround '
                                                            'resolved the error'},
                                 'environment': {'type': 'object',
                                                 'description': 'Optional: your '
                                                                'environment info '
                                                                '(runtime, os, '
                                                                'version, etc.)'},
                                 'notes': {'type': 'string',
                                           'description': 'Optional: additional '
                                                          'context or notes'}},
                  'required': ['error_id', 'workaround_action', 'success']},
  'annotations': {'title': 'Report outcome',
                  'readOnlyHint': False,
                  'destructiveHint': False,
                  'idempotentHint': False,
                  'openWorldHint': False}}]
