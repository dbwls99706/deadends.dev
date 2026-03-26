"""Generate data quality report for ErrorCanon database.

Analyzes coverage, freshness, confidence, graph connectivity, and
identifies improvement priorities.

Usage:
    python -m generator.quality_report
"""

import json
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "canons"
OUTPUT_FILE = PROJECT_ROOT / "data" / "quality_report.json"


def load_canons(data_dir: Path) -> list[dict]:
    """Load all ErrorCanon JSON files."""
    canons = []
    for f in sorted(data_dir.rglob("*.json")):
        with open(f, encoding="utf-8") as fh:
            canons.append(json.load(fh))
    return canons


def _freshness(canon: dict) -> str:
    """Classify freshness: fresh/aging/stale/unknown."""
    lc = canon.get("error", {}).get("last_confirmed")
    if not lc:
        return "unknown"
    try:
        d = datetime.strptime(lc, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return "unknown"
    age = (date.today() - d).days
    if age > 365:
        return "stale"
    if age > 180:
        return "aging"
    return "fresh"


def analyze_domain(canons: list[dict]) -> dict:
    """Compute per-domain statistics."""
    domains = defaultdict(list)
    for c in canons:
        d = c.get("error", {}).get("domain", "unknown")
        domains[d].append(c)

    result = {}
    for domain, dcs in sorted(domains.items()):
        confidences = [
            c["verdict"]["confidence"] for c in dcs
            if "verdict" in c and "confidence" in c["verdict"]
        ]
        fix_rates = [
            c["verdict"]["fix_success_rate"] for c in dcs
            if "verdict" in c and "fix_success_rate" in c["verdict"]
        ]
        freshness = defaultdict(int)
        for c in dcs:
            freshness[_freshness(c)] += 1

        resolvable = defaultdict(int)
        for c in dcs:
            r = c.get("verdict", {}).get("resolvable", "unknown")
            resolvable[r] += 1

        evidence = [
            c.get("metadata", {}).get("evidence_count", 0) for c in dcs
        ]

        result[domain] = {
            "count": len(dcs),
            "avg_confidence": round(sum(confidences) / len(confidences), 3) if confidences else 0,
            "avg_fix_rate": round(sum(fix_rates) / len(fix_rates), 3) if fix_rates else 0,
            "freshness": dict(freshness),
            "resolvable": dict(resolvable),
            "avg_evidence_count": round(sum(evidence) / len(evidence), 1) if evidence else 0,
            "low_confidence_count": sum(1 for c in confidences if c < 0.5),
        }

    return result


def analyze_graph_connectivity(canons: list[dict]) -> dict:
    """Analyze transition graph connectivity."""
    all_ids = {c.get("id", "") for c in canons}
    connected = set()
    total_refs = 0

    for c in canons:
        tg = c.get("transition_graph", {})
        refs = []
        for lt in tg.get("leads_to", []):
            if lt.get("error_id"):
                refs.append(lt["error_id"])
        for pb in tg.get("preceded_by", []):
            if pb.get("error_id"):
                refs.append(pb["error_id"])
        for fc in tg.get("frequently_confused_with", []):
            if fc.get("error_id"):
                refs.append(fc["error_id"])

        if refs:
            connected.add(c.get("id", ""))
            total_refs += len(refs)
            for r in refs:
                if r in all_ids:
                    connected.add(r)

    return {
        "connected_canons": len(connected),
        "orphan_canons": len(all_ids) - len(connected),
        "total_cross_references": total_refs,
        "connectivity_rate": round(len(connected) / len(all_ids), 3) if all_ids else 0,
    }


def analyze_categories(canons: list[dict]) -> dict:
    """Analyze category distribution."""
    categories = defaultdict(int)
    for c in canons:
        cat = c.get("error", {}).get("category", "unknown")
        categories[cat] += 1
    return dict(sorted(categories.items(), key=lambda x: x[1], reverse=True))


def generate_report(
    data_dir: Path = DATA_DIR,
    output_file: Path = OUTPUT_FILE,
) -> dict:
    """Generate full quality report.

    Returns the report dict and writes it to output_file.
    """
    canons = load_canons(data_dir)

    domain_stats = analyze_domain(canons)
    graph_stats = analyze_graph_connectivity(canons)
    category_stats = analyze_categories(canons)

    all_confidences = [
        c["verdict"]["confidence"] for c in canons
        if "verdict" in c and "confidence" in c["verdict"]
    ]
    all_fix_rates = [
        c["verdict"]["fix_success_rate"] for c in canons
        if "verdict" in c and "fix_success_rate" in c["verdict"]
    ]

    report = {
        "generated_at": datetime.now().isoformat(),
        "summary": {
            "total_canons": len(canons),
            "total_domains": len(domain_stats),
            "avg_confidence": round(
                sum(all_confidences) / len(all_confidences), 3
            ) if all_confidences else 0,
            "avg_fix_rate": round(
                sum(all_fix_rates) / len(all_fix_rates), 3
            ) if all_fix_rates else 0,
        },
        "graph": graph_stats,
        "categories": category_stats,
        "domains": domain_stats,
    }

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
        f.write("\n")

    return report


def print_report(report: dict):
    """Print a terminal-friendly summary."""
    s = report["summary"]
    g = report["graph"]

    print("=" * 60)
    print("  deadends.dev Data Quality Report")
    print("=" * 60)
    print(f"\n  Total canons:     {s['total_canons']}")
    print(f"  Total domains:    {s['total_domains']}")
    print(f"  Avg confidence:   {s['avg_confidence']}")
    print(f"  Avg fix rate:     {s['avg_fix_rate']}")
    print("\n  Graph connectivity:")
    print(f"    Connected:      {g['connected_canons']} ({g['connectivity_rate']:.1%})")
    print(f"    Orphans:        {g['orphan_canons']}")
    print(f"    Cross-refs:     {g['total_cross_references']}")

    print("\n  Domain breakdown (top 15 by count):")
    print(f"  {'Domain':<20} {'Count':>6} {'Confidence':>11} {'Fix Rate':>10}")
    print(f"  {'-'*20} {'-'*6} {'-'*11} {'-'*10}")
    domains = sorted(
        report["domains"].items(),
        key=lambda x: x[1]["count"],
        reverse=True,
    )
    for domain, stats in domains[:15]:
        print(
            f"  {domain:<20} {stats['count']:>6} "
            f"{stats['avg_confidence']:>10.3f} "
            f"{stats['avg_fix_rate']:>9.3f}"
        )

    print("\n  Top categories:")
    for cat, count in list(report["categories"].items())[:10]:
        print(f"    {cat}: {count}")

    print(f"\n  Output: {OUTPUT_FILE}")


def main():
    """CLI entry point."""
    report = generate_report()
    print_report(report)


if __name__ == "__main__":
    main()
