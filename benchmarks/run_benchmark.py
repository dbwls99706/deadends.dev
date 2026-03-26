"""Benchmark deadends.dev lookup effectiveness.

Measures how well the lookup SDK retrieves correct workarounds
and identifies known dead ends for 20 representative error scenarios.

Metrics:
- Precision@1: Is the top result for the correct domain?
- Precision@3: Is a correct result in the top 3?
- Dead End Hit Rate: Does the result warn about known dead ends?
- MRR: Mean Reciprocal Rank of the first correct result.

Usage:
    python benchmarks/run_benchmark.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from generator.lookup import lookup_all  # noqa: E402

SCENARIOS_FILE = Path(__file__).parent / "error_scenarios.json"


def load_scenarios() -> list[dict]:
    """Load benchmark scenarios."""
    with open(SCENARIOS_FILE, encoding="utf-8") as f:
        return json.load(f)


def evaluate_match(
    scenario: dict,
    match: dict,
) -> dict:
    """Evaluate a single match against scenario expectations."""
    domain_match = match.get("domain") == scenario["expected_domain"]

    workaround_hit = False
    for wa in match.get("workarounds", []):
        action = wa.get("action", "").lower() + " " + wa.get("how", "").lower()
        for kw in scenario["correct_workaround_keywords"]:
            if kw.lower() in action:
                workaround_hit = True
                break

    dead_end_hit = False
    for de in match.get("dead_ends", []):
        text = de.get("action", "").lower() + " " + de.get("why_fails", "").lower()
        for kw in scenario["known_dead_end_keywords"]:
            if kw.lower() in text:
                dead_end_hit = True
                break

    return {
        "domain_match": domain_match,
        "workaround_hit": workaround_hit,
        "dead_end_hit": dead_end_hit,
    }


def run_benchmark() -> dict:
    """Run the full benchmark suite."""
    scenarios = load_scenarios()

    results = []
    domain_correct_at_1 = 0
    domain_correct_at_3 = 0
    workaround_hits = 0
    dead_end_hits = 0
    reciprocal_ranks = []
    no_match = 0

    for scenario in scenarios:
        matches = lookup_all(scenario["error_message"])

        if not matches:
            no_match += 1
            reciprocal_ranks.append(0)
            results.append({
                "id": scenario["id"],
                "status": "NO_MATCH",
                "matches": 0,
            })
            continue

        top = evaluate_match(scenario, matches[0])
        if top["domain_match"]:
            domain_correct_at_1 += 1

        found_in_top3 = False
        first_correct_rank = 0
        for i, m in enumerate(matches[:3]):
            ev = evaluate_match(scenario, m)
            if ev["domain_match"] and not found_in_top3:
                found_in_top3 = True
                domain_correct_at_3 += 1
                first_correct_rank = i + 1

        if first_correct_rank > 0:
            reciprocal_ranks.append(1.0 / first_correct_rank)
        else:
            for i, m in enumerate(matches):
                if m.get("domain") == scenario["expected_domain"]:
                    reciprocal_ranks.append(1.0 / (i + 1))
                    break
            else:
                reciprocal_ranks.append(0)

        if top["workaround_hit"]:
            workaround_hits += 1
        if top["dead_end_hit"]:
            dead_end_hits += 1

        results.append({
            "id": scenario["id"],
            "status": "MATCH",
            "matches": len(matches),
            "top_domain": matches[0].get("domain"),
            "expected_domain": scenario["expected_domain"],
            "domain_correct": top["domain_match"],
            "workaround_hit": top["workaround_hit"],
            "dead_end_hit": top["dead_end_hit"],
        })

    n = len(scenarios)
    mrr = sum(reciprocal_ranks) / n if n else 0

    report = {
        "total_scenarios": n,
        "no_match": no_match,
        "precision_at_1": round(domain_correct_at_1 / n, 3) if n else 0,
        "precision_at_3": round(domain_correct_at_3 / n, 3) if n else 0,
        "workaround_hit_rate": round(workaround_hits / n, 3) if n else 0,
        "dead_end_hit_rate": round(dead_end_hits / n, 3) if n else 0,
        "mrr": round(mrr, 3),
        "details": results,
    }

    return report


def main():
    """CLI entry point."""
    report = run_benchmark()
    n = report["total_scenarios"]

    print("=" * 60)
    print("  deadends.dev Lookup Benchmark")
    print("=" * 60)
    print(f"\n  Scenarios:          {n}")
    print(f"  No match:           {report['no_match']}")
    print(f"  Precision@1:        {report['precision_at_1']:.1%}")
    print(f"  Precision@3:        {report['precision_at_3']:.1%}")
    print(f"  Workaround hit:     {report['workaround_hit_rate']:.1%}")
    print(f"  Dead end hit:       {report['dead_end_hit_rate']:.1%}")
    print(f"  MRR:                {report['mrr']:.3f}")

    print("\n  Per-scenario:")
    for r in report["details"]:
        if r["status"] == "NO_MATCH":
            print(f"    {r['id']}: NO MATCH")
        else:
            d = "OK" if r["domain_correct"] else f"WRONG ({r['top_domain']})"
            w = "Y" if r["workaround_hit"] else "N"
            de = "Y" if r["dead_end_hit"] else "N"
            print(f"    {r['id']}: domain={d} wa={w} de={de}")

    output = Path(__file__).parent / "results.json"
    with open(output, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
        f.write("\n")
    print(f"\n  Results saved to: {output}")


if __name__ == "__main__":
    main()
