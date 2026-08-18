"""Pick which aging canons a content cycle should re-verify.

Every content PR refreshes a few of the oldest canons alongside its new pages.
When each session picks "the N canons with the oldest ``last_confirmed``", they
all pick the *same* files, and whichever PR merges first leaves the rest
conflicting on the very date fields they came to update.

This module hands out disjoint slices instead. The aging canons are sorted
oldest-first, cut into fixed blocks, and each caller gets the block its ``seed``
hashes to - so two sessions working on different countries claim different
files without coordinating.

CLI::

    python -m generator.reverify --seed nz
    python -m generator.reverify --seed visa-br --count 3
    python -m generator.reverify --seed nz --exclude docker/foo/bar,rust/baz/qux
"""

import argparse
import hashlib
import json
import sys
from datetime import date
from pathlib import Path

from generator.validate import AGING_THRESHOLD_DAYS, _canon_age_days

DATA_DIR = Path(__file__).parent.parent / "data" / "canons"

# How deep into the oldest-first ordering blocks are cut from. Everything in
# this window is past AGING_THRESHOLD_DAYS anyway, so a caller landing at the
# far end still re-verifies something genuinely due. A wider pool means more
# blocks and a smaller chance that two seeds collide, traded against reaching
# less urgent canons; 600 keeps the window inside the oldest two thirds of a
# ~1000-canon aging cohort while leaving ~200 blocks to spread across.
#
# Hashing only makes a collision unlikely, never impossible. `exclude` is what
# makes disjointness a guarantee - pass the IDs open PRs already touch.
DEFAULT_POOL = 600
DEFAULT_COUNT = 3


def load_aging_canons(
    data_dir: Path | None = None,
    reference_date: date | None = None,
    threshold_days: int = AGING_THRESHOLD_DAYS,
) -> list[dict]:
    """Return aging canons, oldest ``last_confirmed`` first.

    Each entry is ``{"id", "path", "age_days", "last_confirmed"}``. Canons with
    a missing or unparseable ``last_confirmed`` are skipped - they are reported
    separately by the validator and are not re-verification targets. Ties break
    on ``id`` so the ordering is stable across machines and runs.
    """
    root = data_dir or DATA_DIR
    entries = []
    for f in sorted(root.rglob("*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        age = _canon_age_days(data, reference_date)
        if age is None or age <= threshold_days:
            continue
        canon_id = data.get("id")
        if not canon_id:
            continue
        entries.append({
            "id": canon_id,
            "path": f,
            "age_days": age,
            "last_confirmed": data["error"]["last_confirmed"],
        })
    entries.sort(key=lambda e: (-e["age_days"], e["id"]))
    return entries


def _block_index(seed: str, block_count: int) -> int:
    """Map a seed to a block, stably across processes.

    ``hash()`` is salted per process, so it cannot be used here - two sessions
    would disagree about which block a seed owns.
    """
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    return int(digest, 16) % block_count


def select_targets(
    seed: str,
    count: int = DEFAULT_COUNT,
    pool: int = DEFAULT_POOL,
    exclude: set[str] | None = None,
    data_dir: Path | None = None,
    reference_date: date | None = None,
) -> list[dict]:
    """Pick ``count`` aging canons for the cycle identified by ``seed``.

    ``seed`` should identify this cycle - the target country code, or
    ``domain-cc`` when a country gets more than one cycle. The same seed always
    returns the same canons; different seeds almost always return disjoint sets.

    ``exclude`` holds canon IDs already claimed elsewhere (an open PR, an
    earlier batch). Blocks containing any of them are skipped, so a caller that
    passes the IDs touched by open PRs never lands on a file someone else is
    editing. Returns ``[]`` when nothing is aging, or when every block is
    excluded.
    """
    if count < 1:
        raise ValueError("count must be at least 1")

    entries = load_aging_canons(data_dir=data_dir, reference_date=reference_date)
    if not entries:
        return []

    window = entries[:pool]
    blocks = [window[i:i + count] for i in range(0, len(window) - count + 1, count)]
    if not blocks:
        # Fewer aging canons than a full block: hand back what there is.
        return window[:count]

    excluded = exclude or set()
    start = _block_index(seed, len(blocks))
    for offset in range(len(blocks)):
        block = blocks[(start + offset) % len(blocks)]
        if not any(entry["id"] in excluded for entry in block):
            return block
    return []


def main() -> int:
    """CLI: print the canons this cycle should re-verify."""
    parser = argparse.ArgumentParser(
        description="Pick which aging canons this content cycle should re-verify.",
    )
    parser.add_argument(
        "--seed",
        required=True,
        help="Identifier for this cycle, e.g. the target country code ('nz') or 'domain-cc'.",
    )
    parser.add_argument("--count", type=int, default=DEFAULT_COUNT,
                        help=f"How many canons to claim (default: {DEFAULT_COUNT}).")
    parser.add_argument("--pool", type=int, default=DEFAULT_POOL,
                        help=f"How deep into the oldest-first ordering to cut blocks from "
                             f"(default: {DEFAULT_POOL}).")
    parser.add_argument("--exclude", default="",
                        help="Comma-separated canon IDs already claimed by an open PR.")
    args = parser.parse_args()

    exclude = {s.strip() for s in args.exclude.split(",") if s.strip()}
    targets = select_targets(args.seed, count=args.count, pool=args.pool, exclude=exclude)

    if not targets:
        print("No aging canon block available for this seed.")
        if exclude:
            print("Every block overlapped an excluded ID - widen --pool or re-check open PRs.")
        return 1

    print(f"Re-verification block for seed {args.seed!r} ({len(targets)} canons):\n")
    for entry in targets:
        try:
            rel = entry["path"].relative_to(Path.cwd())
        except ValueError:
            rel = entry["path"]
        print(f"  {entry['id']}")
        print(f"    file:           {rel}")
        print(f"    last_confirmed: {entry['last_confirmed']} ({entry['age_days']} days ago)")
    print("\nRe-fetch every source URL on these before touching any date field.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
