"""deadends.dev error lookup SDK.

Programmatic error lookup for AI coding agents and developer tools.
Works offline with bundled data or online via the deadends.dev API.

Usage:
    from generator.lookup import lookup, lookup_all

    # Single best match
    result = lookup("ModuleNotFoundError: No module named 'torch'")
    print(result["dead_ends"])      # What NOT to try
    print(result["workarounds"])    # What works

    # All matches
    results = lookup_all("CUDA error: out of memory")

CLI Usage:
    python -m generator.lookup "ModuleNotFoundError: No module named 'torch'"
"""

import json
import math
import re
import sys
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data" / "canons"

_CANONS_CACHE: list[dict] | None = None


def _load_canons() -> list[dict]:
    """Load all canon data (cached after first call)."""
    global _CANONS_CACHE
    if _CANONS_CACHE is not None:
        return _CANONS_CACHE

    canons = []
    for f in sorted(DATA_DIR.rglob("*.json")):
        with open(f, encoding="utf-8") as fh:
            canons.append(json.load(fh))
    _CANONS_CACHE = canons
    return canons


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


_STOPWORDS = frozenset({
    "", "the", "a", "an", "is", "of", "in", "to", "for", "and", "or",
    "no", "not", "on", "at", "by", "it", "be", "as", "do", "if",
    "error", "failed", "exception", "cannot", "can", "could",
    "was", "were", "been", "being", "has", "have", "had",
    "with", "from", "this", "that", "when", "which", "while",
})


# Patterns that indicate the key error line in a stack trace
_ERROR_LINE_PATTERNS = [
    re.compile(r"(?:Error|Exception|Fault|Failure|FATAL|CRITICAL|panic)[:]\s", re.I),
    re.compile(r"^(?:E\s|error\[E\d+\])", re.I),
    re.compile(r"^(?:CUDA|NCCL|RuntimeError|TypeError|ValueError|KeyError)", re.I),
    re.compile(r"^(?:ModuleNotFoundError|ImportError|SyntaxError|FileNotFoundError)", re.I),
    re.compile(r"^(?:Traceback|Caused by:)", re.I),
    re.compile(r"^(?:fatal:|error:)\s", re.I),
    re.compile(r"^\w+Error:", re.I),
    re.compile(r"^\w+Exception:", re.I),
]


def _extract_error_lines(text: str) -> str:
    """Extract the key error line(s) from a potentially long stack trace.

    AI agents often paste full stack traces (50-200 lines). This extracts
    the most relevant lines for matching, improving lookup accuracy.

    Returns the original text if it's short (< 5 lines) or if no key
    error line pattern is found.
    """
    lines = text.strip().splitlines()
    if len(lines) <= 5:
        return text.strip()

    # Collect lines that match error patterns
    key_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        for pat in _ERROR_LINE_PATTERNS:
            if pat.search(stripped):
                key_lines.append(stripped)
                break

    if key_lines:
        # Return the last error line (usually the most specific)
        # plus any earlier ones for context
        return "\n".join(key_lines[-3:])

    # Fallback: last non-empty line (often the actual error)
    for line in reversed(lines):
        stripped = line.strip()
        if stripped and not stripped.startswith("at ") and not stripped.startswith("File "):
            return stripped

    return text.strip()


def lookup_all(error_message: str) -> list[dict]:
    """Match an error message against all known patterns.

    Returns a list of matching canons sorted by relevance, each containing:
    - id, signature, domain, resolvable, fix_success_rate, summary
    - dead_ends: list of {action, why_fails, fail_rate}
    - workarounds: list of {action, success_rate, how}

    For long stack traces (> 5 lines), automatically extracts the key error
    lines before matching. The full text is still searched as a fallback.
    """
    if not error_message or not error_message.strip():
        return []

    # Extract key error lines from long stack traces
    extracted = _extract_error_lines(error_message)

    canons = _load_canons()
    matches = []

    for canon in canons:
        try:
            pattern = re.compile(canon["error"]["regex"], re.IGNORECASE)
        except re.error as e:
            print(f"[lookup] skipping canon with invalid regex: {e}", file=sys.stderr)
            continue

        try:
            score = 0

            # Regex match — try extracted first, then full text as fallback
            if pattern.search(extracted):
                score += 100
            elif extracted != error_message and pattern.search(error_message):
                score += 100

            # Signature substring match (check both extracted and full)
            sig = canon["error"]["signature"].lower()
            ext_lower = extracted.lower()
            msg_lower = error_message.lower()
            if sig in ext_lower or ext_lower in sig:
                score += 50
            elif sig in msg_lower or msg_lower in sig:
                score += 50

            # Word overlap (excluding stopwords) — use extracted
            sig_words = set(re.split(r"\W+", sig))
            msg_words = set(re.split(r"\W+", ext_lower))
            overlap = (sig_words & msg_words) - _STOPWORDS
            score += len(overlap) * 5

            if score > 0:
                matches.append({
                    "score": score,
                    "id": canon["id"],
                    "signature": canon["error"]["signature"],
                    "domain": canon["error"]["domain"],
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
                    "freshness": _compute_freshness(canon),
                    "url": canon["url"].rstrip("/").rsplit("/", 1)[0] + "/",
                })
        except (KeyError, TypeError) as e:
            print(f"[lookup] skipping malformed canon {canon.get('id', '?')}: {e}", file=sys.stderr)
            continue

    # Sort by: score DESC, then fix_success_rate DESC
    matches.sort(
        key=lambda m: (m["score"], m["fix_success_rate"]),
        reverse=True,
    )
    return matches


def lookup(error_message: str) -> dict | None:
    """Return the single best matching canon for an error message.

    Returns None if no match found.
    """
    matches = lookup_all(error_message)
    return matches[0] if matches else None


def batch_lookup(error_messages: list[str]) -> list[dict | None]:
    """Look up multiple error messages at once.

    Returns a list of best matches (or None) for each input message.
    Convenience wrapper for looking up multiple error messages at once.
    Canon data is loaded once and cached at the module level regardless.

    Usage:
        from generator.lookup import batch_lookup

        results = batch_lookup([
            "ModuleNotFoundError: No module named 'torch'",
            "CUDA error: out of memory",
            "CrashLoopBackOff",
        ])
        for msg, result in zip(error_messages, results):
            if result:
                print(f"{msg} -> {result['signature']}")
    """
    _load_canons()  # ensure loaded once
    return [lookup(msg) for msg in error_messages]


_IDF_CACHE: dict[str, float] | None = None
_DOC_WORDS_CACHE: dict[str, set[str]] | None = None


def _build_idf_index() -> tuple[dict[str, float], dict[str, set[str]]]:
    """Build IDF index across all canons (cached)."""
    global _IDF_CACHE, _DOC_WORDS_CACHE
    if _IDF_CACHE is not None and _DOC_WORDS_CACHE is not None:
        return _IDF_CACHE, _DOC_WORDS_CACHE

    canons = _load_canons()
    doc_freq: dict[str, int] = defaultdict(int)
    doc_words: dict[str, set[str]] = {}
    n = len(canons)

    for canon in canons:
        canon_id = canon.get("id", "")
        words = set()
        sig = canon.get("error", {}).get("signature", "").lower()
        summary = canon.get("verdict", {}).get("summary", "").lower()
        words.update(re.split(r"\W+", sig))
        words.update(re.split(r"\W+", summary))
        for de in canon.get("dead_ends", []):
            words.update(re.split(r"\W+", de.get("action", "").lower()))
            words.update(re.split(r"\W+", de.get("why_fails", "").lower()))
        for wa in canon.get("workarounds", []):
            words.update(re.split(r"\W+", wa.get("action", "").lower()))
        words -= _STOPWORDS
        doc_words[canon_id] = words
        for w in words:
            doc_freq[w] += 1

    idf = {}
    for word, df in doc_freq.items():
        idf[word] = math.log((n + 1) / (df + 1)) + 1.0 if df > 0 else 0

    _IDF_CACHE = idf
    _DOC_WORDS_CACHE = doc_words
    return idf, doc_words


def _env_match_score(canon: dict, runtime: str | None, os_name: str | None) -> float:
    """Score how well a canon's environment matches the given filters."""
    if not runtime and not os_name:
        return 0.0
    score = 0.0
    env = canon.get("environment", {})
    if runtime:
        rt = env.get("runtime", {})
        rt_name = rt.get("name", "").lower()
        if runtime.lower() in rt_name or rt_name in runtime.lower():
            score += 5.0
    if os_name:
        canon_os = env.get("os", "").lower()
        if os_name.lower() in canon_os or canon_os in os_name.lower():
            score += 3.0
    return score


def search(
    query: str,
    domain: str | None = None,
    limit: int = 10,
    runtime: str | None = None,
    os_name: str | None = None,
) -> list[dict]:
    """Search errors by keyword with TF-IDF scoring.

    Uses TF-IDF weighting for more accurate relevance ranking.
    Optionally filters by domain and boosts results matching the
    given runtime/OS environment.

    Args:
        query: Search keywords (e.g., 'memory limit', 'timeout')
        domain: Optional domain filter (e.g., 'python', 'docker')
        limit: Max results (default 10)
        runtime: Optional runtime filter (e.g., 'python', 'node')
        os_name: Optional OS filter (e.g., 'linux', 'macos')

    Usage:
        from generator.lookup import search

        results = search("memory limit", domain="docker", limit=5)
        results = search("segfault", runtime="python", os_name="linux")
    """
    canons = _load_canons()
    idf, doc_words = _build_idf_index()
    q_words = set(query.lower().split()) - _STOPWORDS
    scored = []

    for canon in canons:
        if domain and canon["error"]["domain"] != domain:
            continue

        canon_id = canon.get("id", "")
        canon_words = doc_words.get(canon_id, set())
        sig = canon.get("error", {}).get("signature", "").lower()

        score = 0.0
        for w in q_words:
            if w not in canon_words:
                continue
            w_idf = idf.get(w, 0)
            if w in sig:
                score += w_idf * 3.0
            else:
                score += w_idf * 1.0

        score += _env_match_score(canon, runtime, os_name)

        if score > 0:
            scored.append({
                "score": round(score, 2),
                "id": canon["id"],
                "signature": canon["error"]["signature"],
                "domain": canon["error"]["domain"],
                "resolvable": canon["verdict"]["resolvable"],
                "fix_success_rate": canon["verdict"]["fix_success_rate"],
                "summary": canon["verdict"]["summary"],
            })

    scored.sort(key=lambda m: m["score"], reverse=True)
    return scored[:limit]


def main():
    """CLI interface for error lookup."""
    if len(sys.argv) < 2:
        print("Usage: python -m generator.lookup 'ERROR MESSAGE'")
        print("       python -m generator.lookup --list")
        sys.exit(1)

    if sys.argv[1] == "--list":
        canons = _load_canons()
        domains: dict[str, list[str]] = {}
        for c in canons:
            d = c["error"]["domain"]
            domains.setdefault(d, []).append(c["error"]["signature"])
        for domain in sorted(domains):
            print(f"\n{domain} ({len(domains[domain])} errors):")
            for sig in sorted(set(domains[domain])):
                print(f"  {sig}")
        sys.exit(0)

    error_msg = " ".join(sys.argv[1:])
    matches = lookup_all(error_msg)

    if not matches:
        print(f"No matches for: {error_msg}")
        sys.exit(1)

    for m in matches[:3]:
        print(f"\n{'='*60}")
        print(f"  {m['signature']}")
        print(f"  Resolvable: {m['resolvable']} | "
              f"Fix rate: {int(m['fix_success_rate']*100)}%")
        print(f"  {m['summary']}")
        print(f"{'='*60}")

        print("\n  DEAD ENDS (do NOT try):")
        for d in m["dead_ends"]:
            print(f"    X {d['action']} — fails {int(d['fail_rate']*100)}%")
            print(f"      {d['why_fails']}")

        print("\n  WORKAROUNDS (try these):")
        for w in m["workarounds"]:
            print(f"    > {w['action']} — works {int(w['success_rate']*100)}%")
            if w["how"]:
                print(f"      {w['how']}")

        print(f"\n  Details: {m['url']}")


if __name__ == "__main__":
    main()
