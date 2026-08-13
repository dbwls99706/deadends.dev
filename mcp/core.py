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
