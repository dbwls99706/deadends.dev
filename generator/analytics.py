"""Usage analytics for deadends.dev MCP tools.

Aggregates anonymized usage logs from data/analytics/*.jsonl into
actionable metrics: most queried domains, match rates, tool usage.

Usage:
    python -m generator.analytics
"""

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
ANALYTICS_DIR = PROJECT_ROOT / "data" / "analytics"
OUTPUT_FILE = ANALYTICS_DIR / "summary.json"


def record_event(
    tool: str,
    domain: str | None = None,
    matched: bool = False,
    match_count: int = 0,
    analytics_dir: Path = ANALYTICS_DIR,
) -> None:
    """Record a single analytics event to daily JSONL file.

    Only records: timestamp, tool name, domain (if applicable),
    match success, and match count. No error messages or PII.
    """
    analytics_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    filepath = analytics_dir / f"{today}.jsonl"

    event = {
        "ts": datetime.now().isoformat(),
        "tool": tool,
        "matched": matched,
        "match_count": match_count,
    }
    if domain:
        event["domain"] = domain

    with open(filepath, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def load_events(analytics_dir: Path = ANALYTICS_DIR) -> list[dict]:
    """Load all analytics events."""
    events = []
    if not analytics_dir.exists():
        return events
    for f in sorted(analytics_dir.glob("*.jsonl")):
        with open(f, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    return events


def aggregate(events: list[dict]) -> dict:
    """Aggregate events into summary metrics."""
    tool_counts: dict[str, int] = defaultdict(int)
    domain_counts: dict[str, int] = defaultdict(int)
    total_lookups = 0
    matched_lookups = 0
    daily_counts: dict[str, int] = defaultdict(int)

    for event in events:
        tool = event.get("tool", "unknown")
        tool_counts[tool] += 1

        domain = event.get("domain")
        if domain:
            domain_counts[domain] += 1

        if tool in ("lookup_error", "search_errors", "batch_lookup"):
            total_lookups += 1
            if event.get("matched"):
                matched_lookups += 1

        ts = event.get("ts", "")
        if len(ts) >= 10:
            daily_counts[ts[:10]] += 1

    match_rate = round(matched_lookups / total_lookups, 3) if total_lookups else 0

    return {
        "generated_at": datetime.now().isoformat(),
        "total_events": len(events),
        "tool_usage": dict(sorted(tool_counts.items(), key=lambda x: x[1], reverse=True)),
        "domain_queries": dict(
            sorted(domain_counts.items(), key=lambda x: x[1], reverse=True)[:20]
        ),
        "lookup_match_rate": match_rate,
        "total_lookups": total_lookups,
        "matched_lookups": matched_lookups,
        "daily_activity": dict(sorted(daily_counts.items())),
    }


def generate_summary(
    analytics_dir: Path = ANALYTICS_DIR,
    output_file: Path = OUTPUT_FILE,
) -> dict:
    """Generate analytics summary and write to file."""
    events = load_events(analytics_dir)
    summary = aggregate(events)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
        f.write("\n")

    return summary


def main():
    """CLI entry point."""
    summary = generate_summary()
    n = summary["total_events"]

    print("Usage Analytics Summary")
    print(f"  Total events: {n}")

    if n == 0:
        print("  No events recorded yet.")
        print("  Events are recorded when MCP tools are called.")
        return

    print(f"  Lookup match rate: {summary['lookup_match_rate']:.1%}")
    print(f"    ({summary['matched_lookups']}/{summary['total_lookups']} lookups matched)")

    print("\n  Tool usage:")
    for tool, count in summary["tool_usage"].items():
        print(f"    {tool}: {count}")

    if summary["domain_queries"]:
        print("\n  Top queried domains:")
        for domain, count in list(summary["domain_queries"].items())[:10]:
            print(f"    {domain}: {count}")

    print(f"\n  Output: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
