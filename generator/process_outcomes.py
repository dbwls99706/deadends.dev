"""Process collected outcome reports and aggregate into actionable data.

Reads data/outcomes/*.jsonl, aggregates success/failure counts per
error_id and workaround, computes implied fix rates, and compares
against current canon fix_success_rate values.

This closes the feedback loop: report_outcome (collect) → process_outcomes (analyze).

Usage:
    python -m generator.process_outcomes
"""

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
OUTCOMES_DIR = PROJECT_ROOT / "data" / "outcomes"
CANONS_DIR = PROJECT_ROOT / "data" / "canons"
OUTPUT_FILE = OUTCOMES_DIR / "aggregated.json"


def load_outcomes(outcomes_dir: Path = OUTCOMES_DIR) -> list[dict]:
    """Load all outcome JSONL files."""
    outcomes = []
    if not outcomes_dir.exists():
        return outcomes
    for f in sorted(outcomes_dir.glob("*.jsonl")):
        with open(f, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    try:
                        outcomes.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    return outcomes


def load_canon_fix_rates(canons_dir: Path = CANONS_DIR) -> dict[str, float]:
    """Load current fix_success_rate for all canons."""
    rates = {}
    for f in sorted(canons_dir.rglob("*.json")):
        with open(f, encoding="utf-8") as fh:
            canon = json.load(fh)
        canon_id = canon.get("id", "")
        rate = canon.get("verdict", {}).get("fix_success_rate", 0)
        rates[canon_id] = rate
    return rates


def aggregate_outcomes(outcomes: list[dict]) -> dict[str, dict]:
    """Aggregate outcomes by error_id and workaround action.

    Returns:
        {
            "python/err/env1": {
                "workarounds": {
                    "Try this": {"success": 5, "fail": 2, "implied_rate": 0.714}
                },
                "total_reports": 7,
                "overall_success_rate": 0.714
            }
        }
    """
    by_error: dict[str, dict[str, dict[str, int]]] = defaultdict(
        lambda: defaultdict(lambda: {"success": 0, "fail": 0})
    )

    for outcome in outcomes:
        eid = outcome.get("error_id", "")
        action = outcome.get("workaround_action", "")
        success = outcome.get("success", False)
        if not eid or not action:
            continue
        if success:
            by_error[eid][action]["success"] += 1
        else:
            by_error[eid][action]["fail"] += 1

    result = {}
    for eid, workarounds in by_error.items():
        wa_data = {}
        total_s = 0
        total_f = 0
        for action, counts in workarounds.items():
            s, f = counts["success"], counts["fail"]
            total_s += s
            total_f += f
            total = s + f
            wa_data[action] = {
                "success": s,
                "fail": f,
                "total": total,
                "implied_rate": round(s / total, 3) if total > 0 else 0,
            }
        total_all = total_s + total_f
        result[eid] = {
            "workarounds": wa_data,
            "total_reports": total_all,
            "overall_success_rate": round(
                total_s / total_all, 3
            ) if total_all > 0 else 0,
        }

    return result


def compute_deltas(
    aggregated: dict[str, dict],
    canon_rates: dict[str, float],
) -> dict[str, dict]:
    """Compare aggregated outcome rates against current canon fix rates.

    Returns entries where there's a meaningful delta.
    """
    deltas = {}
    for eid, data in aggregated.items():
        current = canon_rates.get(eid)
        implied = data["overall_success_rate"]
        total = data["total_reports"]
        entry = {
            "current_fix_rate": current,
            "implied_fix_rate": implied,
            "total_reports": total,
            "workarounds": data["workarounds"],
        }
        if current is not None:
            entry["delta"] = round(implied - current, 3)
        else:
            entry["delta"] = None
            entry["note"] = "canon not found in dataset"
        deltas[eid] = entry

    return deltas


def process_outcomes(
    outcomes_dir: Path = OUTCOMES_DIR,
    canons_dir: Path = CANONS_DIR,
    output_file: Path = OUTPUT_FILE,
) -> dict:
    """Full pipeline: load → aggregate → compare → write.

    Returns the full report dict.
    """
    outcomes = load_outcomes(outcomes_dir)
    canon_rates = load_canon_fix_rates(canons_dir)
    aggregated = aggregate_outcomes(outcomes)
    deltas = compute_deltas(aggregated, canon_rates)

    report = {
        "generated_at": datetime.now().isoformat(),
        "total_outcomes": len(outcomes),
        "unique_errors_reported": len(aggregated),
        "deltas": deltas,
    }

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
        f.write("\n")

    return report


def main():
    """CLI entry point."""
    report = process_outcomes()
    n = report["total_outcomes"]
    errs = report["unique_errors_reported"]

    print("Outcome Processing Report")
    print(f"  Total outcome reports: {n}")
    print(f"  Unique errors reported: {errs}")

    if not report["deltas"]:
        print("  No outcomes to process yet.")
        print("  Outcomes are collected via the report_outcome MCP tool.")
        return

    significant = [
        (eid, d) for eid, d in report["deltas"].items()
        if d.get("delta") is not None and abs(d["delta"]) >= 0.05
        and d["total_reports"] >= 3
    ]
    if significant:
        print("\n  Significant deltas (>= 5%, >= 3 reports):")
        for eid, d in sorted(significant, key=lambda x: abs(x[1]["delta"]), reverse=True):
            sign = "+" if d["delta"] > 0 else ""
            print(
                f"    {eid}: {d['current_fix_rate']:.0%} → "
                f"{d['implied_fix_rate']:.0%} ({sign}{d['delta']:.0%}, "
                f"n={d['total_reports']})"
            )
    else:
        print("  No significant deltas yet (need >= 3 reports per error).")

    print(f"\n  Output: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
