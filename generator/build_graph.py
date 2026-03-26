"""Build materialized transition graph from ErrorCanon data.

Extracts all edges from canon transition_graph fields, infers reverse edges,
and exports a unified graph to data/graph/.

Usage:
    python -m generator.build_graph
"""

import json
import sys
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "canons"
GRAPH_DIR = PROJECT_ROOT / "data" / "graph"


def load_canons(data_dir: Path) -> list[dict]:
    """Load all ErrorCanon JSON files."""
    canons = []
    for f in sorted(data_dir.rglob("*.json")):
        with open(f, encoding="utf-8") as fh:
            canons.append(json.load(fh))
    return canons


def extract_edges(canons: list[dict]) -> list[dict]:
    """Extract all graph edges from canon transition_graph fields.

    Also infers reverse edges: if A leads_to B, then B preceded_by A.
    Deduplicates by (source, target, type).
    """
    all_ids = {c.get("id", "") for c in canons}
    seen = set()
    edges = []

    for canon in canons:
        canon_id = canon.get("id", "")
        graph = canon.get("transition_graph", {})

        for lt in graph.get("leads_to", []):
            target = lt.get("error_id", "")
            if not target:
                continue
            key = (canon_id, target, "leads_to")
            if key not in seen:
                seen.add(key)
                edges.append({
                    "source": canon_id,
                    "target": target,
                    "type": "leads_to",
                    "probability": lt.get("probability"),
                    "condition": lt.get("condition"),
                })
            rev_key = (target, canon_id, "preceded_by")
            if rev_key not in seen:
                seen.add(rev_key)
                edges.append({
                    "source": target,
                    "target": canon_id,
                    "type": "preceded_by",
                    "probability": lt.get("probability"),
                    "condition": lt.get("condition"),
                })

        for pb in graph.get("preceded_by", []):
            target = pb.get("error_id", "")
            if not target:
                continue
            key = (canon_id, target, "preceded_by")
            if key not in seen:
                seen.add(key)
                edges.append({
                    "source": canon_id,
                    "target": target,
                    "type": "preceded_by",
                    "probability": pb.get("probability"),
                    "condition": pb.get("condition"),
                })
            rev_key = (target, canon_id, "leads_to")
            if rev_key not in seen:
                seen.add(rev_key)
                edges.append({
                    "source": target,
                    "target": canon_id,
                    "type": "leads_to",
                    "probability": pb.get("probability"),
                    "condition": pb.get("condition"),
                })

        for fc in graph.get("frequently_confused_with", []):
            target = fc.get("error_id", "")
            if not target:
                continue
            key = (canon_id, target, "confused_with")
            if key not in seen:
                seen.add(key)
                edges.append({
                    "source": canon_id,
                    "target": target,
                    "type": "confused_with",
                    "distinction": fc.get("distinction"),
                })
            rev_key = (target, canon_id, "confused_with")
            if rev_key not in seen:
                seen.add(rev_key)
                edges.append({
                    "source": target,
                    "target": canon_id,
                    "type": "confused_with",
                    "distinction": fc.get("distinction"),
                })

    valid_edges = [e for e in edges if e["source"] in all_ids and e["target"] in all_ids]
    dangling = len(edges) - len(valid_edges)
    if dangling:
        sys.stderr.write(f"WARNING: {dangling} edges reference non-existent canon IDs\n")

    return valid_edges


def compute_stats(edges: list[dict], canons: list[dict]) -> dict:
    """Compute graph statistics."""
    all_ids = {c.get("id", "") for c in canons}
    nodes_in_graph = set()
    for e in edges:
        nodes_in_graph.add(e["source"])
        nodes_in_graph.add(e["target"])

    edge_counts = defaultdict(int)
    for e in edges:
        edge_counts[e["type"]] += 1

    degree = defaultdict(int)
    for e in edges:
        degree[e["source"]] += 1
        degree[e["target"]] += 1

    components = _count_components(nodes_in_graph, edges)

    hub_nodes = sorted(degree.items(), key=lambda x: x[1], reverse=True)[:10]

    return {
        "total_canons": len(canons),
        "nodes_in_graph": len(nodes_in_graph),
        "orphan_canons": len(all_ids - nodes_in_graph),
        "total_edges": len(edges),
        "edges_by_type": dict(edge_counts),
        "connected_components": components,
        "hub_nodes": [{"id": nid, "degree": deg} for nid, deg in hub_nodes],
    }


def _count_components(nodes: set, edges: list[dict]) -> int:
    """Count connected components using union-find."""
    parent = {n: n for n in nodes}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for e in edges:
        if e["source"] in parent and e["target"] in parent:
            union(e["source"], e["target"])

    return len({find(n) for n in nodes})


def build_graph(data_dir: Path = DATA_DIR, output_dir: Path = GRAPH_DIR) -> dict:
    """Build the transition graph and write outputs.

    Returns the stats dict.
    """
    canons = load_canons(data_dir)
    edges = extract_edges(canons)
    stats = compute_stats(edges, canons)

    output_dir.mkdir(parents=True, exist_ok=True)

    edges_file = output_dir / "edges.jsonl"
    with open(edges_file, "w", encoding="utf-8") as f:
        for edge in edges:
            clean = {k: v for k, v in edge.items() if v is not None}
            f.write(json.dumps(clean, ensure_ascii=False) + "\n")

    stats_file = output_dir / "stats.json"
    with open(stats_file, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
        f.write("\n")

    return stats


def main():
    """CLI entry point."""
    stats = build_graph()
    print("Transition graph built:")
    print(f"  Nodes: {stats['nodes_in_graph']} / {stats['total_canons']} canons")
    print(f"  Orphans: {stats['orphan_canons']} canons with no graph edges")
    print(f"  Edges: {stats['total_edges']}")
    for etype, count in stats["edges_by_type"].items():
        print(f"    {etype}: {count}")
    print(f"  Connected components: {stats['connected_components']}")
    print("  Top hubs:")
    for hub in stats["hub_nodes"][:5]:
        print(f"    {hub['id']} (degree {hub['degree']})")
    print("\nOutput: data/graph/edges.jsonl, data/graph/stats.json")


if __name__ == "__main__":
    main()
