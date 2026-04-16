"""deadends.dev MCP Server — Error knowledge for AI coding agents.

Exposes structured failure knowledge through the Model Context Protocol.
AI coding agents can query error signatures to get dead ends, workarounds,
and error chains without web search.

Usage:
    python -m mcp.server              # stdio mode (for Claude Desktop, Cursor)

Claude Desktop config (~/.claude/claude_desktop_config.json):
{
  "mcpServers": {
    "deadend": {
      "command": "python",
      "args": ["-m", "mcp.server"],
      "cwd": "/path/to/deadends.dev"
    }
  }
}

Cursor config (MCP settings):
{
  "mcpServers": {
    "deadend": {
      "command": "python",
      "args": ["-m", "mcp.server"],
      "cwd": "/path/to/deadends.dev"
    }
  }
}
"""

import json
import os
import re
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any

from generator.analytics import record_event as _record_event
from generator.lookup import _extract_error_lines

# Import shared domain utilities
sys.path.insert(0, str(Path(__file__).parent.parent))
from generator.domains import suggest_domains as _suggest_domains

DATA_DIR = Path(__file__).parent.parent / "data" / "canons"
OUTCOMES_DIR = Path(__file__).parent.parent / "data" / "outcomes"

# Smithery configuration via environment variables
_PREFERRED_DOMAINS: list[str] = [
    d.strip() for d in os.getenv("DEADENDS_PREFERRED_DOMAINS", "").split(",")
    if d.strip()
]
_MAX_RESULTS: int = min(
    max(int(os.getenv("DEADENDS_MAX_RESULTS", "10")), 1), 20
)
_VERBOSE: bool = os.getenv("DEADENDS_VERBOSE", "true").lower() != "false"

# Module-level caches — loaded once on first request
_OUTCOME_STATS: dict[str, dict] | None = None
_CANONS: list[dict] | None = None
_DOMAIN_INDEX: dict[str, list[str]] | None = None
_COMPILED_REGEXES: dict[str, re.Pattern | None] | None = None

# Maximum length for error messages to prevent ReDoS
_MAX_ERROR_MESSAGE_LEN = 10_000


def _get_outcome_stats() -> dict[str, dict]:
    """Load aggregated outcome stats if available (cached)."""
    global _OUTCOME_STATS
    if _OUTCOME_STATS is not None:
        return _OUTCOME_STATS

    agg_file = OUTCOMES_DIR / "aggregated.json"
    if agg_file.exists():
        try:
            with open(agg_file, encoding="utf-8") as f:
                data = json.load(f)
            _OUTCOME_STATS = data.get("deltas", {})
        except (json.JSONDecodeError, KeyError):
            _OUTCOME_STATS = {}
    else:
        _OUTCOME_STATS = {}
    return _OUTCOME_STATS


def _get_canons() -> list[dict]:
    """Load all ErrorCanon JSON files (cached after first call)."""
    global _CANONS
    if _CANONS is not None:
        return _CANONS

    canons = []
    for f in sorted(DATA_DIR.rglob("*.json")):
        with open(f, encoding="utf-8") as fh:
            canons.append(json.load(fh))
    _CANONS = canons
    return canons


def _get_domain_index() -> dict[str, list[str]]:
    """Build domain -> [signature] index (cached)."""
    global _DOMAIN_INDEX
    if _DOMAIN_INDEX is not None:
        return _DOMAIN_INDEX

    canons = _get_canons()
    index: dict[str, list[str]] = {}
    for c in canons:
        try:
            d = c["error"]["domain"]
            sig = c["error"]["signature"]
        except (KeyError, TypeError):
            continue
        index.setdefault(d, [])
        if sig not in index[d]:
            index[d].append(sig)
    _DOMAIN_INDEX = index
    return index


def _compute_freshness(canon: dict) -> str:
    """Compute freshness status based on last_confirmed date.

    Returns 'fresh' (<180 days), 'aging' (180-365), 'stale' (>365), or 'unknown'.
    """
    last_confirmed = canon.get("error", {}).get("last_confirmed")
    if not last_confirmed:
        return "unknown"
    try:
        d = datetime.strptime(last_confirmed, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return "unknown"
    age = (date.today() - d).days
    if age > 365:
        return "stale"
    elif age > 180:
        return "aging"
    return "fresh"


def _get_compiled_regexes() -> dict[str, re.Pattern | None]:
    """Pre-compile and cache all canon regexes (prevents per-request overhead)."""
    global _COMPILED_REGEXES
    if _COMPILED_REGEXES is not None:
        return _COMPILED_REGEXES

    canons = _get_canons()
    compiled: dict[str, re.Pattern | None] = {}
    for canon in canons:
        canon_id = canon.get("id", "")
        regex_str = canon.get("error", {}).get("regex", "")
        try:
            compiled[canon_id] = re.compile(regex_str, re.IGNORECASE)
        except re.error as exc:
            sys.stderr.write(
                f"WARNING: Invalid regex in {canon_id}: {exc}\n"
            )
            compiled[canon_id] = None
    _COMPILED_REGEXES = compiled
    return compiled


def match_error(error_message: str, canons: list[dict]) -> list[dict]:
    """Match an error message against all known patterns.

    Returns matches sorted by (match_ratio, preferred_domain, fix_success_rate)
    so longer regex matches rank higher, preferred domains get a boost, and
    fix_success_rate breaks ties.
    """
    if not error_message or not error_message.strip():
        return []

    # Truncate excessively long messages to prevent ReDoS
    if len(error_message) > _MAX_ERROR_MESSAGE_LEN:
        error_message = error_message[:_MAX_ERROR_MESSAGE_LEN]

    # Extract key error lines from long stack traces
    extracted = _extract_error_lines(error_message)

    compiled = _get_compiled_regexes()
    matches = []
    skipped = 0
    msg_len = len(extracted)
    for canon in canons:
        try:
            canon_id = canon.get("id", "")
            pattern = compiled.get(canon_id)
            if pattern is None:
                skipped += 1
                continue
            # Try extracted text first, then full text as fallback
            m = pattern.search(extracted)
            if not m and extracted != error_message:
                m = pattern.search(error_message)
            if m:
                match_ratio = len(m.group()) / msg_len if msg_len else 0
                domain = canon["error"]["domain"]
                preferred = 1 if domain in _PREFERRED_DOMAINS else 0
                matches.append({
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
                        for lt in canon.get("transition_graph", {}).get(
                            "leads_to", []
                        )
                        if "error_id" in lt
                    ],
                    "freshness": _compute_freshness(canon),
                    "url": canon["url"].rstrip("/").rsplit("/", 1)[0] + "/",
                    "_match_ratio": match_ratio,
                    "_preferred": preferred,
                })
        except (re.error, KeyError, TypeError) as exc:
            canon_id = canon.get("id", "<unknown>")
            sys.stderr.write(
                f"WARNING: Skipping canon {canon_id}: {exc}\n"
            )
            skipped += 1
            continue

    matches.sort(
        key=lambda m: (m["_match_ratio"], m["_preferred"], m["fix_success_rate"]),
        reverse=True,
    )
    # Strip internal scoring fields
    for m in matches:
        m.pop("_match_ratio", None)
        m.pop("_preferred", None)

    # Surface skipped canon count so callers can inform users
    if skipped and matches:
        matches[0]["_skipped_canons"] = skipped
    return matches


_ID_PATTERN = re.compile(r"^[a-z0-9-]+/[a-z0-9-]+/[a-z0-9._-]+$")


def lookup_by_id(error_id: str, canons: list[dict]) -> dict | None:
    """Look up a specific error by its ID.

    Validates that error_id matches the expected format before searching.
    """
    if not error_id or not _ID_PATTERN.match(error_id):
        return None
    for canon in canons:
        if canon["id"] == error_id:
            return canon
    return None


def list_domains(canons: list[dict]) -> dict:
    """List all domains with error counts."""
    domains: dict[str, int] = {}
    for canon in canons:
        try:
            d = canon["error"]["domain"]
        except (KeyError, TypeError):
            continue
        domains[d] = domains.get(d, 0) + 1
    return {"total": len(canons), "domains": domains}



# _suggest_domains is imported from generator.domains


# === MCP Protocol Implementation (JSON-RPC over stdio) ===

TOOLS = [
    {
        "name": "lookup_error",
        "description": (
            "Match an error message against deadends.dev's database of known "
            "errors. Returns dead ends (what NOT to try), workarounds (what "
            "works), and error chains (what comes next). Use this BEFORE "
            "attempting to fix any error to avoid wasting time on approaches "
            "that are known to fail. Covers 51 domains including python, "
            "node, docker, git, cuda, typescript, rust, go, kubernetes, "
            "terraform, aws, react, java, database, pytorch, tensorflow, "
            "and 34 more. Use list_error_domains to see all."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "error_message": {
                    "type": "string",
                    "description": "The full error message to look up",
                },
                "format": {
                    "type": "string",
                    "enum": ["markdown", "json"],
                    "description": (
                        "Response format: 'markdown' (default, "
                        "human-readable) or 'json' (structured, for "
                        "programmatic use by AI agents)"
                    ),
                },
            },
            "required": ["error_message"],
        },
        "annotations": {
            "title": "Look up error",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    },
    {
        "name": "get_error_detail",
        "description": (
            "Get full details for a specific error by its ID "
            "(e.g., 'python/modulenotfounderror/py311-linux'). "
            "Includes all dead ends, workarounds, error chain info, "
            "and source evidence."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "error_id": {
                    "type": "string",
                    "description": "The error ID (domain/slug/env)",
                }
            },
            "required": ["error_id"],
        },
        "annotations": {
            "title": "Get error details",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    },
    {
        "name": "list_error_domains",
        "description": (
            "List all error domains and counts in the deadends.dev database. "
            "Covers 51 domains including programming languages, frameworks, "
            "infrastructure, ML/AI, culture, safety, medical, legal, and more."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
        "annotations": {
            "title": "List domains",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    },
    {
        "name": "search_errors",
        "description": (
            "Search errors by keyword across all domains. Unlike lookup_error "
            "(which uses regex matching), this does fuzzy keyword search. "
            "Use when you have a vague description like 'memory issues' or "
            "'permission denied' rather than an exact error message."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "Search keywords (e.g., 'memory limit', 'timeout', "
                        "'permission denied')"
                    ),
                },
                "domain": {
                    "type": "string",
                    "description": (
                        "Optional: filter to a specific domain "
                        "(e.g., 'python', 'docker')"
                    ),
                },
                "limit": {
                    "type": "integer",
                    "description": "Max results to return (default: 10)",
                },
            },
            "required": ["query"],
        },
        "annotations": {
            "title": "Search errors",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    },
    {
        "name": "list_errors_by_domain",
        "description": (
            "List all errors in a specific domain with their fix rates. "
            "Use this to understand coverage for a domain before relying on it."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string",
                    "description": (
                        "The domain to list errors for "
                        "(e.g., 'python', 'kubernetes')"
                    ),
                },
                "sort_by": {
                    "type": "string",
                    "description": (
                        "Sort by: 'fix_rate' (default), 'name', or 'confidence'"
                    ),
                },
            },
            "required": ["domain"],
        },
        "annotations": {
            "title": "List domain errors",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    },
    {
        "name": "batch_lookup",
        "description": (
            "Look up multiple error messages at once. Returns the best match "
            "for each error. Use when debugging a chain of errors or analyzing "
            "a log with multiple failures."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "error_messages": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of error messages to look up (max 10)",
                    "maxItems": 10,
                }
            },
            "required": ["error_messages"],
        },
        "annotations": {
            "title": "Batch lookup",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    },
    {
        "name": "get_domain_stats",
        "description": (
            "Get detailed statistics for a domain: error counts, average fix "
            "rate, resolvability breakdown, top categories, and confidence "
            "levels. Use this to assess how trustworthy deadends.dev data is "
            "for a domain."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string",
                    "description": "The domain to get stats for",
                }
            },
            "required": ["domain"],
        },
        "annotations": {
            "title": "Domain statistics",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    },
    {
        "name": "list_errors_by_country",
        "description": (
            "List all country-scoped dead ends for a given country (ISO "
            "alpha-2 code, e.g. 'kr', 'jp', 'us', 'de'). Returns visa, "
            "banking, legal, cultural, medical, food-safety, emergency, "
            "and safety dead ends specific to that jurisdiction. Use this "
            "when an AI agent needs jurisdiction-specific knowledge that "
            "global LLM training data won't reliably cover."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "country": {
                    "type": "string",
                    "description": (
                        "ISO 3166-1 alpha-2 country code, lowercase "
                        "(e.g. 'kr' for Korea, 'jp' for Japan)"
                    ),
                },
                "domain": {
                    "type": "string",
                    "description": (
                        "Optional: filter by domain "
                        "(e.g. 'visa', 'legal', 'culture')"
                    ),
                },
            },
            "required": ["country"],
        },
        "annotations": {
            "title": "List by country",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    },
    {
        "name": "get_country_summary",
        "description": (
            "Get a country-level summary: total entries, domain breakdown, "
            "average fix rate, and most-recent updates for the country. "
            "Use this to assess coverage for a country before relying on "
            "deadends.dev for trip / business / legal planning advice."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "country": {
                    "type": "string",
                    "description": (
                        "ISO 3166-1 alpha-2 country code, lowercase"
                    ),
                }
            },
            "required": ["country"],
        },
        "annotations": {
            "title": "Country summary",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    },
    {
        "name": "get_error_chain",
        "description": (
            "Traverse the error transition graph for a specific error. "
            "Shows what errors typically follow this one (leads_to), "
            "what errors usually precede it (preceded_by), and what "
            "errors are frequently confused with it. Use this to "
            "diagnose cascading failures and predict what comes next."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "error_id": {
                    "type": "string",
                    "description": (
                        "The error ID (domain/slug/env) to get the "
                        "transition graph for"
                    ),
                }
            },
            "required": ["error_id"],
        },
        "annotations": {
            "title": "Error chain",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    },
    {
        "name": "report_outcome",
        "description": (
            "Report whether a workaround from deadends.dev worked or failed. "
            "This feedback improves fix_success_rate and confidence for future "
            "users. Call this AFTER applying a workaround to help improve the "
            "database. Accepts the error ID, the workaround action you tried, "
            "and whether it succeeded."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "error_id": {
                    "type": "string",
                    "description": "The error ID (domain/slug/env)",
                },
                "workaround_action": {
                    "type": "string",
                    "description": (
                        "The workaround action string you tried "
                        "(from the workarounds list)"
                    ),
                },
                "success": {
                    "type": "boolean",
                    "description": "Whether the workaround resolved the error",
                },
                "environment": {
                    "type": "object",
                    "description": (
                        "Optional: your environment info "
                        "(runtime, os, version, etc.)"
                    ),
                },
                "notes": {
                    "type": "string",
                    "description": "Optional: additional context or notes",
                },
            },
            "required": ["error_id", "workaround_action", "success"],
        },
        "annotations": {
            "title": "Report outcome",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": False,
        },
    },
]


def _record_outcome(outcome: dict[str, Any]) -> None:
    """Append an outcome record to the daily JSONL file."""
    OUTCOMES_DIR.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    filepath = OUTCOMES_DIR / f"{today}.jsonl"
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(json.dumps(outcome, ensure_ascii=False) + "\n")


def handle_request(method: str, params: dict, canons: list[dict]) -> dict:
    """Handle a JSON-RPC request."""
    if method == "initialize":
        return {
            "protocolVersion": "2025-03-26",
            "capabilities": {
                "tools": {},
            },
            "serverInfo": {
                "name": "deadends-dev",
                "version": "1.6.0",
            },
            "instructions": (
                "Use lookup_error BEFORE attempting to fix any error to "
                "avoid wasting time on known dead ends. Use search_errors "
                "for vague descriptions, get_error_detail for full info by "
                "ID, and get_error_chain to predict cascading failures."
            ),
        }
    elif method == "ping":
        return {}
    elif method == "resources/list":
        return {"resources": []}
    elif method == "prompts/list":
        return {"prompts": []}
    elif method == "tools/list":
        return {"tools": TOOLS}
    elif method == "tools/call":
        tool_name = params.get("name", "")
        args = params.get("arguments", {})

        if tool_name == "lookup_error":
            error_msg = args.get("error_message", "").strip()
            output_format = args.get("format", "markdown")
            if not error_msg:
                return {
                    "content": [{
                        "type": "text",
                        "text": (
                            "Empty error message. Please provide the "
                            "full error message to look up."
                        ),
                    }],
                }
            matches = match_error(error_msg, canons)
            top_domain = matches[0]["domain"] if matches else None
            try:
                _record_event(
                    "lookup_error", domain=top_domain,
                    matched=bool(matches), match_count=len(matches),
                )
            except Exception:
                pass  # analytics must never break tool calls
            if not matches:
                suggested = _suggest_domains(error_msg)
                text = (
                    "No matching errors found in deadends.dev database.\n\n"
                    f"Searched {len(canons)} error patterns across "
                    f"{len(_get_domain_index())} domains.\n"
                )
                if suggested != "unknown":
                    text += (
                        f"Likely domains based on keywords: {suggested}\n"
                        "The error may not be in our database yet.\n"
                    )
                text += (
                    "\nTip: Try the full error message including the "
                    "error type (e.g., 'ModuleNotFoundError: ...')."
                )
            else:
                parts = []
                skipped_count = matches[0].pop("_skipped_canons", 0)
                if skipped_count:
                    parts.append(
                        f"⚠ {skipped_count} canon(s) skipped due to data "
                        f"errors (results may be incomplete).\n"
                    )
                for m in matches[:_MAX_RESULTS]:
                    parts.append(f"## {m['signature']}")
                    parts.append(f"Resolvable: {m['resolvable']} | "
                                 f"Fix rate: {m['fix_success_rate']}")
                    parts.append(f"Summary: {m['summary']}")
                    parts.append("")
                    parts.append("### Dead Ends (DO NOT TRY):")
                    for d in m["dead_ends"]:
                        parts.append(f"- {d['action']} "
                                     f"(fails {int(d['fail_rate']*100)}%): "
                                     f"{d['why_fails']}")
                    if _VERBOSE:
                        parts.append("")
                        parts.append("### Workarounds (TRY THESE):")
                        for w in m["workarounds"]:
                            how = f" — `{w['how']}`" if w["how"] else ""
                            parts.append(f"- {w['action']} "
                                         f"(works {int(w['success_rate']*100)}%)"
                                         f"{how}")
                        if m.get("leads_to"):
                            parts.append("")
                            parts.append("### Next Errors (after fixing this):")
                            for lt in m["leads_to"]:
                                parts.append(f"- {lt}")
                    else:
                        parts.append("")
                        parts.append("### Workarounds (TRY THESE):")
                        for w in m["workarounds"]:
                            parts.append(f"- {w['action']} "
                                         f"(works {int(w['success_rate']*100)}%)")
                    outcome_stats = _get_outcome_stats()
                    ostats = outcome_stats.get(m["id"])
                    if ostats and ostats.get("total_reports", 0) >= 2:
                        n = ostats["total_reports"]
                        cr = int(ostats["implied_fix_rate"] * 100)
                        parts.append("")
                        parts.append(
                            f"### Community Reports ({n} reports): "
                            f"{cr}% success rate"
                        )
                    parts.append(f"\nFull details: {m['url']}")
                    parts.append("")
                text = "\n".join(parts)

            # JSON format: return structured data for programmatic use
            if output_format == "json" and matches:
                json_matches = []
                for m in matches[:_MAX_RESULTS]:
                    json_matches.append({
                        "id": m["id"],
                        "signature": m["signature"],
                        "domain": m["domain"],
                        "resolvable": m["resolvable"],
                        "fix_success_rate": m["fix_success_rate"],
                        "summary": m["summary"],
                        "url": m["url"],
                        "dead_ends": [
                            {"action": d["action"],
                             "why_fails": d["why_fails"],
                             "fail_rate": d["fail_rate"]}
                            for d in m["dead_ends"]
                        ],
                        "workarounds": [
                            {"action": w["action"],
                             "success_rate": w["success_rate"],
                             "how": w.get("how", "")}
                            for w in m["workarounds"]
                        ],
                        "leads_to": m.get("leads_to", []),
                    })
                return {
                    "content": [{
                        "type": "text",
                        "text": json.dumps({
                            "matches": json_matches,
                            "total": len(matches),
                        }, ensure_ascii=False),
                    }],
                }

            return {
                "content": [{"type": "text", "text": text}],
            }

        elif tool_name == "get_error_detail":
            error_id = args.get("error_id", "")
            canon = lookup_by_id(error_id, canons)
            if not canon:
                # Try partial match
                partial = [
                    c for c in canons
                    if "id" in c
                    and (error_id in c["id"] or c["id"] in error_id)
                ]
                if partial:
                    suggestions = [c["id"] for c in partial[:5]]
                    text = (
                        f"Error ID not found: {error_id}\n\n"
                        f"Did you mean one of these?\n"
                        + "\n".join(f"- {s}" for s in suggestions)
                    )
                else:
                    text = (
                        f"Error ID not found: {error_id}\n\n"
                        f"Use list_error_domains to see available domains, "
                        f"or lookup_error to search by error message."
                    )
            else:
                # Inject page_url (canonical summary URL) alongside the raw
                # env-specific url field so consumers have the indexed page link
                enriched = dict(canon)
                enriched["page_url"] = (
                    canon["url"].rstrip("/").rsplit("/", 1)[0] + "/"
                )
                text = json.dumps(enriched, indent=2, ensure_ascii=False)
            return {
                "content": [{"type": "text", "text": text}],
            }

        elif tool_name == "list_error_domains":
            info = list_domains(canons)
            text = f"Total errors: {info['total']}\n\n"
            for domain, count in sorted(info["domains"].items()):
                text += f"- {domain}: {count} errors\n"
            text += (
                "\nUse lookup_error to search by error message, "
                "or get_error_detail with an ID like "
                "'python/modulenotfounderror/py311-linux'."
            )
            return {
                "content": [{"type": "text", "text": text}],
            }

        elif tool_name == "search_errors":
            query = args.get("query", "")[:1000].strip().lower()
            if not query:
                return {
                    "content": [{
                        "type": "text",
                        "text": "Empty search query. Provide keywords.",
                    }],
                }
            domain_filter = args.get("domain", "")
            raw_limit = args.get("limit", _MAX_RESULTS)
            limit = min(int(raw_limit) if isinstance(raw_limit, (int, float)) else _MAX_RESULTS, 20)
            scored = []
            for c in canons:
                try:
                    c_domain = c["error"]["domain"]
                    c_sig = c["error"]["signature"]
                    c_summary = c["verdict"]["summary"]
                except (KeyError, TypeError):
                    continue
                if domain_filter and c_domain != domain_filter:
                    continue
                # Score by keyword presence in signature, summary, dead ends
                score = 0
                sig = c_sig.lower()
                summary = c_summary.lower()
                _stopwords = {
                    "", "the", "a", "an", "is", "of", "in", "to",
                    "for", "and", "or", "no", "not", "on", "at",
                    "error", "failed", "exception", "cannot",
                }
                q_words = set(query.split()) - _stopwords
                for w in q_words:
                    if w in sig:
                        score += 10
                    if w in summary:
                        score += 5
                    for de in c["dead_ends"]:
                        if w in de["action"].lower():
                            score += 3
                        if w in de["why_fails"].lower():
                            score += 2
                    for wa in c.get("workarounds", []):
                        if w in wa["action"].lower():
                            score += 3
                if score > 0:
                    if c_domain in _PREFERRED_DOMAINS:
                        score += 5
                    scored.append((score, c))
            scored.sort(key=lambda x: x[0], reverse=True)
            try:
                _record_event(
                    "search_errors", domain=domain_filter or None,
                    matched=bool(scored), match_count=len(scored),
                )
            except Exception:
                pass
            if not scored:
                text = f"No errors matching '{query}'"
                if domain_filter:
                    text += f" in domain '{domain_filter}'"
                text += (
                    ".\n\nTry broader keywords or use "
                    "lookup_error with the exact error message."
                )
            else:
                parts = [f"Found {min(len(scored), limit)} results for '{query}':\n"]
                for score, c in scored[:limit]:
                    parts.append(
                        f"- **{c['error']['signature']}** [{c['error']['domain']}] "
                        f"(fix rate: {int(c['verdict']['fix_success_rate']*100)}%) "
                        f"— ID: {c['id']}"
                    )
                parts.append(
                    "\nUse get_error_detail with the ID for full dead ends and workarounds."
                )
                text = "\n".join(parts)
            return {"content": [{"type": "text", "text": text}]}

        elif tool_name == "list_errors_by_country":
            country = args.get("country", "").strip().lower()
            domain_filter = args.get("domain", "").strip()
            if not country:
                return {
                    "content": [{
                        "type": "text",
                        "text": "Provide a country code (ISO alpha-2, e.g. 'kr')",
                    }]
                }
            country_canons = []
            for c in canons:
                additional = c.get("environment", {}).get("additional", {})
                if additional.get("country", "").lower() != country:
                    continue
                if domain_filter and c.get("error", {}).get("domain") != domain_filter:
                    continue
                country_canons.append(c)
            if not country_canons:
                available = sorted({
                    c.get("environment", {}).get("additional", {})
                        .get("country", "")
                    for c in canons
                    if c.get("environment", {}).get("additional", {})
                        .get("country")
                })
                text = (
                    f"No entries for country '{country}'"
                    f"{' in domain ' + domain_filter if domain_filter else ''}.\n"
                    f"Available country codes: {', '.join(available)}"
                )
            else:
                country_canons.sort(
                    key=lambda c: (
                        c["error"]["domain"], -c["verdict"]["fix_success_rate"]
                    )
                )
                country_name = (
                    country_canons[0]["environment"]["additional"]
                    .get("country_name", country.upper())
                )
                parts = [
                    f"## {country_name} — {len(country_canons)} entr"
                    f"{'ies' if len(country_canons) != 1 else 'y'}"
                    f"{' (filtered to domain ' + domain_filter + ')' if domain_filter else ''}\n",
                ]
                current_domain = None
                for c in country_canons:
                    d = c["error"]["domain"]
                    if d != current_domain:
                        parts.append(f"\n### {d}")
                        current_domain = d
                    res = c["verdict"]["resolvable"]
                    rate = int(c["verdict"]["fix_success_rate"] * 100)
                    parts.append(
                        f"- [{res}] {c['error']['signature']} "
                        f"(fix: {rate}%) — {c['id']}"
                    )
                parts.append(
                    f"\nFull aggregate: GET https://deadends.dev/api/v1/country/{country}.json"
                )
                text = "\n".join(parts)
            return {"content": [{"type": "text", "text": text}]}

        elif tool_name == "get_country_summary":
            country = args.get("country", "").strip().lower()
            country_canons = [
                c for c in canons
                if c.get("environment", {}).get("additional", {})
                    .get("country", "").lower() == country
            ]
            if not country_canons:
                available = sorted({
                    c.get("environment", {}).get("additional", {})
                        .get("country", "")
                    for c in canons
                    if c.get("environment", {}).get("additional", {})
                        .get("country")
                })
                text = (
                    f"No entries for country '{country}'.\n"
                    f"Available: {', '.join(available)}"
                )
            else:
                additional = country_canons[0]["environment"]["additional"]
                country_name = additional.get("country_name", country.upper())
                domains = {}
                rates = []
                resolvable_counts = {"true": 0, "partial": 0, "false": 0}
                latest = ""
                for c in country_canons:
                    d = c["error"]["domain"]
                    domains[d] = domains.get(d, 0) + 1
                    rates.append(c["verdict"]["fix_success_rate"])
                    r = c["verdict"]["resolvable"]
                    resolvable_counts[r] = resolvable_counts.get(r, 0) + 1
                    last = c.get("error", {}).get("last_confirmed", "")
                    if last and last > latest:
                        latest = last
                avg_fix = sum(rates) / len(rates) if rates else 0
                domain_list = sorted(
                    domains.items(), key=lambda x: -x[1]
                )
                parts = [
                    f"## {country_name} ({country})",
                    f"Total entries: {len(country_canons)}",
                    f"Average fix rate: {int(avg_fix * 100)}%",
                    f"Resolvable: {resolvable_counts['true']} fixable, "
                    f"{resolvable_counts['partial']} partial, "
                    f"{resolvable_counts['false']} not fixable",
                    f"Most recent update: {latest or 'unknown'}",
                    "",
                    "### Domain breakdown",
                    *[f"- {d}: {n}" for d, n in domain_list],
                    "",
                    f"Country page: https://deadends.dev/country/{country}/",
                    f"JSON aggregate: https://deadends.dev/api/v1/country/{country}.json",
                ]
                text = "\n".join(parts)
            return {"content": [{"type": "text", "text": text}]}

        elif tool_name == "list_errors_by_domain":
            domain = args.get("domain", "")
            sort_by = args.get("sort_by", "fix_rate")
            domain_canons = [
                c for c in canons
                if c.get("error", {}).get("domain") == domain
            ]
            if not domain_canons:
                available = sorted({
                    c.get("error", {}).get("domain", "?")
                    for c in canons
                    if c.get("error", {}).get("domain")
                })
                text = (
                    f"Unknown domain: '{domain}'\n\n"
                    f"Available domains: {', '.join(available)}"
                )
            else:
                if sort_by == "name":
                    domain_canons.sort(key=lambda c: c["error"]["signature"])
                elif sort_by == "confidence":
                    domain_canons.sort(
                        key=lambda c: c["verdict"]["confidence"], reverse=True
                    )
                else:
                    domain_canons.sort(
                        key=lambda c: c["verdict"]["fix_success_rate"], reverse=True
                    )
                parts = [f"## {domain} — {len(domain_canons)} errors\n"]
                for c in domain_canons:
                    res = c["verdict"]["resolvable"]
                    rate = int(c["verdict"]["fix_success_rate"] * 100)
                    parts.append(
                        f"- [{res}] {c['error']['signature']} "
                        f"(fix: {rate}%) — {c['id']}"
                    )
                text = "\n".join(parts)
            return {"content": [{"type": "text", "text": text}]}

        elif tool_name == "batch_lookup":
            messages = args.get("error_messages", [])[:10]
            parts = [f"Batch lookup: {len(messages)} errors\n"]
            for i, msg in enumerate(messages):
                matches = match_error(msg, canons)
                parts.append(f"### Error {i+1}: {msg[:80]}")
                if matches:
                    m = matches[0]
                    parts.append(
                        f"Match: **{m['signature']}** "
                        f"[{m['resolvable']}] fix rate: "
                        f"{int(m['fix_success_rate']*100)}%"
                    )
                    if m["dead_ends"]:
                        parts.append(
                            f"Top dead end: {m['dead_ends'][0]['action']}"
                        )
                    if m["workarounds"]:
                        parts.append(
                            f"Top workaround: {m['workarounds'][0]['action']}"
                        )
                    parts.append(f"ID: {m['id']}")
                else:
                    parts.append("No match found.")
                parts.append("")
            text = "\n".join(parts)
            return {"content": [{"type": "text", "text": text}]}

        elif tool_name == "get_domain_stats":
            domain = args.get("domain", "")
            dc = [
                c for c in canons
                if c.get("error", {}).get("domain") == domain
            ]
            if not dc:
                available = sorted({
                    c.get("error", {}).get("domain", "?")
                    for c in canons
                    if c.get("error", {}).get("domain")
                })
                text = (
                    f"Unknown domain: '{domain}'\n"
                    f"Available: {', '.join(available)}"
                )
            else:
                rates = [
                    c["verdict"]["fix_success_rate"]
                    for c in dc
                    if "verdict" in c and "fix_success_rate" in c["verdict"]
                ]
                avg_rate = sum(rates) / len(rates) if rates else 0
                res_counts = {"true": 0, "partial": 0, "false": 0}
                categories: dict[str, int] = {}
                conf_levels = {"high": 0, "medium": 0, "low": 0}
                for c in dc:
                    try:
                        r = c["verdict"]["resolvable"]
                        res_counts[r] = res_counts.get(r, 0) + 1
                        cat = c["error"]["category"]
                        categories[cat] = categories.get(cat, 0) + 1
                        conf = c["verdict"]["confidence"]
                    except (KeyError, TypeError):
                        continue
                    if isinstance(conf, (int, float)):
                        conf_label = (
                            "high" if conf >= 0.8
                            else "medium" if conf >= 0.5
                            else "low"
                        )
                    else:
                        conf_label = str(conf)
                    conf_levels[conf_label] = (
                        conf_levels.get(conf_label, 0) + 1
                    )
                top_cats = sorted(
                    categories.items(), key=lambda x: x[1], reverse=True
                )[:5]
                parts = [
                    f"## {domain} — Domain Statistics\n",
                    f"Total errors: {len(dc)}",
                    f"Average fix rate: {int(avg_rate*100)}%\n",
                    "Resolvability:",
                    f"  - Resolvable: {res_counts['true']}",
                    f"  - Partial: {res_counts['partial']}",
                    f"  - Not resolvable: {res_counts['false']}\n",
                    "Confidence:",
                    f"  - High: {conf_levels.get('high', 0)}",
                    f"  - Medium: {conf_levels.get('medium', 0)}",
                    f"  - Low: {conf_levels.get('low', 0)}\n",
                    "Top categories:",
                ]
                for cat, count in top_cats:
                    parts.append(f"  - {cat}: {count}")
                text = "\n".join(parts)
            return {"content": [{"type": "text", "text": text}]}

        elif tool_name == "get_error_chain":
            error_id = args.get("error_id", "")
            canon = lookup_by_id(error_id, canons)
            if not canon:
                partial = [
                    c for c in canons
                    if "id" in c
                    and (error_id in c["id"] or c["id"] in error_id)
                ]
                if partial:
                    suggestions = [c["id"] for c in partial[:5]]
                    text = (
                        f"Error ID not found: {error_id}\n\n"
                        f"Did you mean one of these?\n"
                        + "\n".join(f"- {s}" for s in suggestions)
                    )
                else:
                    text = f"Error ID not found: {error_id}"
            else:
                graph = canon.get("transition_graph", {})
                sig = canon.get("error", {}).get("signature", error_id)
                parts = [
                    f"## Error Chain: {sig}",
                    f"ID: {error_id}\n",
                ]
                leads_to = graph.get("leads_to", [])
                if leads_to:
                    parts.append("### This error often leads to:")
                    for lt in leads_to:
                        lt_id = lt.get("error_id")
                        if not lt_id:
                            continue
                        lt_canon = lookup_by_id(lt_id, canons)
                        if lt_canon:
                            sig = lt_canon.get("error", {}).get(
                                "signature", lt_id
                            )
                            rate = int(
                                lt_canon.get("verdict", {}).get(
                                    "fix_success_rate", 0
                                ) * 100
                            )
                            parts.append(
                                f"- **{sig}** (p={lt.get('probability', '?')}, "
                                f"fix rate: {rate}%) — {lt_id}"
                            )
                        else:
                            parts.append(
                                f"- {lt_id} "
                                f"(p={lt.get('probability', '?')})"
                            )
                        if lt.get("condition"):
                            parts.append(
                                f"  Condition: {lt['condition']}"
                            )
                    parts.append("")

                preceded = graph.get("preceded_by", [])
                if preceded:
                    parts.append("### Usually preceded by:")
                    for pb in preceded:
                        pb_id = pb.get("error_id")
                        if not pb_id:
                            continue
                        pb_canon = lookup_by_id(pb_id, canons)
                        if pb_canon:
                            sig = pb_canon.get("error", {}).get(
                                "signature", pb_id
                            )
                            parts.append(
                                f"- **{sig}** (p={pb.get('probability', '?')}) "
                                f"— {pb_id}"
                            )
                        else:
                            parts.append(
                                f"- {pb_id} "
                                f"(p={pb.get('probability', '?')})"
                            )
                    parts.append("")

                confused = graph.get("frequently_confused_with", [])
                if confused:
                    parts.append("### Frequently confused with:")
                    for fc in confused:
                        fc_id = fc.get("error_id")
                        if not fc_id:
                            continue
                        fc_canon = lookup_by_id(fc_id, canons)
                        if fc_canon:
                            sig = fc_canon.get("error", {}).get(
                                "signature", fc_id
                            )
                            parts.append(
                                f"- **{sig}** — {fc_id}"
                            )
                        else:
                            parts.append(f"- {fc_id}")
                        if fc.get("distinction"):
                            parts.append(
                                f"  Distinction: {fc['distinction']}"
                            )
                    parts.append("")

                if not leads_to and not preceded and not confused:
                    parts.append(
                        "No transition graph data for this error. "
                        "It may be a standalone error."
                    )

                text = "\n".join(parts)
            return {"content": [{"type": "text", "text": text}]}

        elif tool_name == "report_outcome":
            error_id = args.get("error_id", "").strip()
            action = args.get("workaround_action", "").strip()
            success = args.get("success")

            if not error_id or not action or success is None:
                return {
                    "content": [{
                        "type": "text",
                        "text": (
                            "Missing required fields. Provide error_id, "
                            "workaround_action, and success (boolean)."
                        ),
                    }],
                }

            if not _ID_PATTERN.match(error_id):
                return {
                    "content": [{
                        "type": "text",
                        "text": f"Invalid error_id format: {error_id}",
                    }],
                }

            canon = lookup_by_id(error_id, canons)
            canon_exists = canon is not None

            outcome = {
                "timestamp": datetime.now().isoformat(),
                "error_id": error_id,
                "workaround_action": action,
                "success": bool(success),
                "canon_exists": canon_exists,
            }
            env = args.get("environment")
            if env and isinstance(env, dict):
                outcome["environment"] = env
            notes = args.get("notes", "").strip()
            if notes:
                outcome["notes"] = notes[:1000]

            _record_outcome(outcome)

            text = (
                f"Outcome recorded. Thank you for the feedback!\n\n"
                f"Error: {error_id}\n"
                f"Workaround: {action}\n"
                f"Result: {'SUCCESS' if success else 'FAILED'}\n"
            )
            if not canon_exists:
                text += (
                    f"\nNote: error_id '{error_id}' was not found in the "
                    f"current database. The outcome was still recorded."
                )
            return {"content": [{"type": "text", "text": text}]}

        return {
            "content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}],
            "isError": True,
        }

    elif method == "notifications/initialized":
        return None  # No response needed for notifications

    return {"error": {"code": -32601, "message": f"Unknown method: {method}"}}


def main():
    """Run MCP server in stdio mode."""
    canons = _get_canons()
    sys.stderr.write(
        f"deadends.dev MCP server loaded: {len(canons)} errors "
        f"across {len(_get_domain_index())} domains\n"
    )

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            continue

        result = handle_request(
            request.get("method", ""),
            request.get("params", {}),
            canons,
        )

        if result is None:
            continue  # Notification, no response

        response = {
            "jsonrpc": "2.0",
            "id": request.get("id"),
        }

        if "error" in result:
            response["error"] = result["error"]
        else:
            response["result"] = result

        sys.stdout.write(json.dumps(response) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
