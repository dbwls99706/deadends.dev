"""Build environment-independent signature index from ErrorCanon data.

Groups all environment variants of the same error together and exports
a deduplicated index to data/signatures/.

Usage:
    python -m generator.build_signatures
"""

import json
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "canons"
SIGNATURES_DIR = PROJECT_ROOT / "data" / "signatures"


def load_canons(data_dir: Path) -> list[dict]:
    """Load all ErrorCanon JSON files."""
    canons = []
    for f in sorted(data_dir.rglob("*.json")):
        with open(f, encoding="utf-8") as fh:
            canons.append(json.load(fh))
    return canons


def build_signature_index(canons: list[dict]) -> list[dict]:
    """Group canons by domain/slug and build signature entries."""
    groups: dict[str, list[dict]] = defaultdict(list)

    for canon in canons:
        canon_id = canon.get("id", "")
        parts = canon_id.split("/")
        if len(parts) < 3:
            continue
        key = f"{parts[0]}/{parts[1]}"
        groups[key].append(canon)

    entries = []
    for key, group in sorted(groups.items()):
        parts = key.split("/")
        domain = parts[0]
        slug = parts[1]

        signature = group[0].get("error", {}).get("signature", slug)
        regex = group[0].get("error", {}).get("regex", "")
        category = group[0].get("error", {}).get("category", "")

        environments = []
        fix_rates = []
        total_dead_ends = 0

        for canon in group:
            canon_id = canon.get("id", "")
            env_key = canon_id.split("/")[2] if len(canon_id.split("/")) >= 3 else ""
            env = canon.get("environment", {})
            runtime = env.get("runtime", {})

            environments.append({
                "env_key": env_key,
                "canon_id": canon_id,
                "runtime": runtime.get("name", ""),
                "version": runtime.get("version_range", ""),
                "os": env.get("os", ""),
            })

            rate = canon.get("verdict", {}).get("fix_success_rate", 0)
            fix_rates.append(rate)
            total_dead_ends += len(canon.get("dead_ends", []))

        entries.append({
            "domain": domain,
            "slug": slug,
            "signature": signature,
            "regex": regex,
            "category": category,
            "environment_count": len(environments),
            "environments": environments,
            "avg_fix_rate": round(sum(fix_rates) / len(fix_rates), 3) if fix_rates else 0,
            "total_dead_ends": total_dead_ends,
        })

    return entries


def compute_stats(entries: list[dict]) -> dict:
    """Compute signature index statistics."""
    domain_counts = defaultdict(int)
    total_envs = 0
    multi_env = 0

    for entry in entries:
        domain_counts[entry["domain"]] += 1
        total_envs += entry["environment_count"]
        if entry["environment_count"] > 1:
            multi_env += 1

    return {
        "unique_signatures": len(entries),
        "total_environment_variants": total_envs,
        "multi_environment_signatures": multi_env,
        "single_environment_signatures": len(entries) - multi_env,
        "domains": dict(sorted(domain_counts.items())),
    }


def build_signatures(
    data_dir: Path = DATA_DIR,
    output_dir: Path = SIGNATURES_DIR,
) -> dict:
    """Build signature index and write outputs.

    Returns the stats dict.
    """
    canons = load_canons(data_dir)
    entries = build_signature_index(canons)
    stats = compute_stats(entries)

    output_dir.mkdir(parents=True, exist_ok=True)

    index_file = output_dir / "index.jsonl"
    with open(index_file, "w", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    stats_file = output_dir / "stats.json"
    with open(stats_file, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
        f.write("\n")

    return stats


def main():
    """CLI entry point."""
    stats = build_signatures()
    print("Signature index built:")
    print(f"  Unique signatures:     {stats['unique_signatures']}")
    print(f"  Environment variants:  {stats['total_environment_variants']}")
    print(f"  Multi-env signatures:  {stats['multi_environment_signatures']}")
    print(f"  Single-env signatures: {stats['single_environment_signatures']}")
    print(f"  Domains: {len(stats['domains'])}")
    print("\nOutput: data/signatures/index.jsonl, data/signatures/stats.json")


if __name__ == "__main__":
    main()
