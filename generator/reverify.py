"""Pick which aging canons a content cycle should re-verify.

Every content PR refreshes a few of the oldest canons alongside its new pages.
When each session picks "the N canons with the oldest ``last_confirmed``", they
all pick the *same* files, and whichever PR merges first leaves the rest
conflicting on the very date fields they came to update.

This module hands out disjoint slices instead. Every canon belongs to a bucket
determined solely by hashing its ID; a cycle's ``seed`` hashes to one bucket and
it takes the oldest canons in there.

Bucketing by ID rather than by position in the aging list is the whole trick.
Two cycles never see the same list - each branches from a different ``main``,
and any merge that ages canons in or refreshes them would shift every later
boundary. Position-based blocks would then overlap *in part* between two cycles,
which is precisely the shape that conflicts on merge. A canon's ID does not move.

Two seeds therefore either own the same bucket (identical picks - visible at
once, and harmless) or share nothing at all. The CLI additionally excludes what
other pushed branches already touch (see :func:`claimed_canon_ids`), on by
default: a guarantee nobody has to remember beats one that needs the right flag.

CLI::

    python -m generator.reverify --seed nz
    python -m generator.reverify --seed visa-br --count 3
    python -m generator.reverify --seed nz --exclude docker/foo/bar,rust/baz/qux
    python -m generator.reverify --seed nz --no-auto-exclude
"""

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import NamedTuple

from generator.validate import AGING_THRESHOLD_DAYS, _canon_age_days

REPO_ROOT = Path(__file__).parent.parent
DATA_DIR = REPO_ROOT / "data" / "canons"

# Number of buckets the aging canons are spread over. MUST stay constant: it is
# what makes a canon's bucket independent of corpus state, so two cycles reading
# different `main`s still agree on who owns what. Changing it re-shuffles every
# canon and is only safe when no content PR is open.
#
# 128 buckets over a ~1000-canon aging cohort leaves ~8 per bucket, comfortably
# more than a cycle claims. What matters for collisions is how many cycles run
# *concurrently*, not how many seeds exist: 3 at once collide ~2.3% of the time,
# 4 at once ~4.6%. (Across all ~30 country seeds some pair inevitably shares a
# bucket - that is fine, since those cycles do not run together.) And a
# collision is not a conflict: both cycles get the identical set, visible
# immediately rather than at merge time.
DEFAULT_BUCKETS = 128
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


def _git(*args: str, repo_root: Path | None = None) -> str | None:
    """Run a read-only git command. Returns None if git or the ref is unavailable."""
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=repo_root or REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return proc.stdout if proc.returncode == 0 else None


def _canon_id_from_path(path: str) -> str | None:
    """Derive a canon ID from its path, for blobs that cannot be read.

    Handles both layouts: ``{domain}/{slug}/{env}.json`` and the flat
    ``{domain}/{slug}_{env}.json``.
    """
    parts = Path(path).with_suffix("").parts
    if len(parts) >= 5 and parts[:2] == ("data", "canons"):
        return "/".join(parts[2:5])
    if len(parts) == 4 and parts[:2] == ("data", "canons"):
        slug_env = parts[3]
        if "_" in slug_env:
            slug, _, env = slug_env.rpartition("_")
            return f"{parts[2]}/{slug}/{env}"
    return None


class ClaimScan(NamedTuple):
    """Result of scanning pushed branches for canons they already touch.

    ``ok`` distinguishes "scanned, found nothing" from "could not scan". They
    are the same empty set but very different facts: the first means the
    bucket is genuinely free, the second means nothing was checked. Collapsing
    would let a shallow clone or a typo'd base ref look exactly like a clean
    bill of health.
    """

    ids: frozenset[str]
    branches: int
    ok: bool
    reason: str | None = None


def claimed_canon_ids(
    base_ref: str = "origin/main",
    repo_root: Path | None = None,
    skip_branch: str | None = None,
) -> ClaimScan:
    """Canon IDs touched by pushed branches other than ``base_ref``.

    Deliberately conservative: it does not try to tell a merged branch from a
    live one. The repo squash-merges, which severs ancestry, so ``git
    merge-base --is-ancestor`` reports long-merged branches as unmerged and
    there is no reliable local signal to replace it. Over-excluding is cheap -
    the caller takes the next canon in its bucket - while under-excluding
    reintroduces exactly the merge conflicts this module exists to prevent.

    Only sees branches that have been **pushed**. Two cycles that start close
    together can both pick before either pushes, so re-run the scan before
    committing rather than trusting a single check at the start.

    Never raises: an unusable repo comes back as ``ok=False`` with a reason, so
    the caller can degrade to hash-only selection *and say so*.
    """
    if not _git("rev-parse", "--git-dir", repo_root=repo_root):
        return ClaimScan(frozenset(), 0, False, "not a git repository, or git unavailable")
    base_commit = _git("rev-parse", "--verify", "--quiet", f"{base_ref}^{{commit}}",
                       repo_root=repo_root)
    if base_commit is None:
        return ClaimScan(frozenset(), 0, False, f"base ref {base_ref!r} not found")

    # Full refnames, not %(refname:short): the short form renders
    # refs/remotes/origin/HEAD as bare "origin", which no HEAD test can catch.
    refs_out = _git("for-each-ref", "--format=%(refname)", "refs/remotes/",
                    repo_root=repo_root)
    if refs_out is None:
        return ClaimScan(frozenset(), 0, False, "could not list remote refs")

    claimed: set[str] = set()
    scanned = 0
    unreadable: list[str] = []
    for refname in refs_out.split():
        if refname.endswith("/HEAD"):
            continue
        ref = refname.removeprefix("refs/remotes/")
        if ref == base_ref:
            continue
        # ref is "<remote>/<branch>"; compare the branch part.
        if skip_branch and ref.partition("/")[2] == skip_branch:
            continue
        scanned += 1
        paths = _git("diff", "--name-only", f"{base_ref}...{ref}", "--", "data/canons",
                     repo_root=repo_root)
        if paths is None:
            # Unrelated histories, a shallow clone with no merge base, a
            # corrupt ref. Whatever the cause, this branch went unchecked and
            # the scan must not go on to report itself clean.
            unreadable.append(ref)
            continue
        if not paths:
            continue
        for path in paths.splitlines():
            path = path.strip()
            if not path.endswith(".json"):
                continue
            blob = _git("show", f"{ref}:{path}", repo_root=repo_root)
            canon_id = None
            if blob:
                try:
                    canon_id = json.loads(blob).get("id")
                except json.JSONDecodeError:
                    canon_id = None
            claimed.add(canon_id or _canon_id_from_path(path) or path)

    if unreadable:
        # Keep the IDs that were readable - they are still real claims - but
        # report the scan as incomplete so the caller does not read it as clean.
        listed = ", ".join(sorted(unreadable)[:3])
        more = f" (+{len(unreadable) - 3} more)" if len(unreadable) > 3 else ""
        return ClaimScan(frozenset(claimed), scanned, False,
                         f"could not diff {len(unreadable)} branch(es): {listed}{more}")
    return ClaimScan(frozenset(claimed), scanned, True)


def current_branch(repo_root: Path | None = None) -> str | None:
    """Name of the checked-out branch, or None when detached or git is absent."""
    out = _git("rev-parse", "--abbrev-ref", "HEAD", repo_root=repo_root)
    name = (out or "").strip()
    return name if name and name != "HEAD" else None


def seed_bucket(seed: str, buckets: int = DEFAULT_BUCKETS) -> int:
    """Map a cycle's seed to the bucket it owns, stably across processes.

    ``hash()`` is salted per process, so it cannot be used here - two sessions
    would disagree about which bucket a seed owns.
    """
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    return int(digest, 16) % buckets


def canon_bucket(canon_id: str, buckets: int = DEFAULT_BUCKETS) -> int:
    """Which bucket a canon belongs to. A pure function of its ID.

    Bucket membership deliberately does not depend on the corpus. Cutting the
    aging list into positional blocks would have been simpler, but two cycles
    never see the same list - each branches from a different `main` - and any
    merge that ages in or refreshes canons shifts every later boundary. Two
    cycles would then get blocks that overlap in part, which is exactly the
    shape that conflicts on merge. Hashing the ID keeps a canon in the same
    bucket no matter what else changed.
    """
    digest = hashlib.sha256(canon_id.encode("utf-8")).hexdigest()
    return int(digest, 16) % buckets


def select_targets(
    seed: str,
    count: int = DEFAULT_COUNT,
    exclude: set[str] | None = None,
    buckets: int = DEFAULT_BUCKETS,
    data_dir: Path | None = None,
    reference_date: date | None = None,
) -> list[dict]:
    """Pick up to ``count`` aging canons for the cycle identified by ``seed``.

    ``seed`` should identify this cycle - the target country code, or
    ``domain-cc`` when a country gets more than one cycle. The seed hashes to
    one bucket, and the cycle takes the oldest unclaimed canons in it.

    Two seeds that hash to different buckets can never share a canon, whatever
    state either corpus is in, because bucket membership depends only on the
    canon ID. Two seeds that hash to the *same* bucket get the same picks, not
    a partial overlap - so a collision is visible and harmless rather than a
    silent conflict.

    ``exclude`` holds canon IDs already claimed elsewhere; they are skipped
    within the bucket, so the cycle stays in its own lane instead of wandering
    into someone else's. Returns ``[]`` when nothing is aging, or when the
    bucket holds nothing unclaimed - in which case vary the seed
    (``nz`` -> ``nz-2``) rather than widening the search.
    """
    if count < 1:
        raise ValueError("count must be at least 1")
    if buckets < 1:
        raise ValueError("buckets must be at least 1")

    entries = load_aging_canons(data_dir=data_dir, reference_date=reference_date)
    if not entries:
        return []

    excluded = exclude or set()
    target = seed_bucket(seed, buckets)
    # `entries` is already oldest-first, so this takes the most overdue members.
    return [
        e for e in entries
        if canon_bucket(e["id"], buckets) == target and e["id"] not in excluded
    ][:count]


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
    parser.add_argument("--buckets", type=int, default=DEFAULT_BUCKETS,
                        help=f"Bucket count (default: {DEFAULT_BUCKETS}). Changing this "
                             f"re-shuffles every canon - leave it alone unless no PR is open.")
    parser.add_argument("--exclude", default="",
                        help="Comma-separated canon IDs to treat as already claimed.")
    parser.add_argument("--base-ref", default="origin/main",
                        help="Ref the other branches are compared against (default: origin/main).")
    parser.add_argument("--no-auto-exclude", action="store_true",
                        help="Do not read claimed IDs from other pushed branches.")
    args = parser.parse_args()

    if args.count < 1:
        parser.error("--count must be at least 1")
    if args.buckets < 1:
        parser.error("--buckets must be at least 1")

    exclude = {s.strip() for s in args.exclude.split(",") if s.strip()}
    scan: ClaimScan | None = None
    if not args.no_auto_exclude:
        scan = claimed_canon_ids(base_ref=args.base_ref, skip_branch=current_branch())
        exclude |= set(scan.ids)

    # Report the scan before the result: an unavailable scan changes how much
    # the result below can be trusted, and must not be buried under it.
    if scan is None:
        print("Claim scan: OFF (--no-auto-exclude). Selection is hash-only.")
    elif not scan.ok:
        print(f"Claim scan: INCOMPLETE - {scan.reason}.")
        if scan.ids:
            print(f"  Applied the {len(scan.ids)} claim(s) it did read, but the rest went "
                  f"unchecked.")
        else:
            print("  Nothing was checked; selection is hash-only.")
        print("  Another branch may already own these canons. Run `git fetch origin --prune`, "
              "or pass claims with --exclude.")
    elif scan.ids:
        print(f"Claim scan: excluded {len(scan.ids)} canon(s) claimed by "
              f"{scan.branches} other pushed branch(es).")
    else:
        print(f"Claim scan: clean - none of the {scan.branches} other pushed branch(es) "
              f"touch data/canons.")

    targets = select_targets(args.seed, count=args.count, buckets=args.buckets, exclude=exclude)

    if not targets:
        aging = load_aging_canons()
        if not aging:
            print("\nNothing is past the aging threshold - no re-verification needed.")
            return 1
        # Distinguish "bucket is empty" from "bucket is fully claimed" by
        # asking the corpus, not by whether `exclude` happens to be non-empty -
        # with the claim scan on by default it almost always is.
        owned = [e for e in aging if canon_bucket(e["id"], args.buckets) == seed_bucket(
            args.seed, args.buckets)]
        if not owned:
            print(f"\nBucket for seed {args.seed!r} is empty ({len(aging)} aging canons over "
                  f"{args.buckets} buckets). Vary the seed, e.g. {args.seed}-2.")
        else:
            print(f"\nAll {len(owned)} canon(s) in the bucket for seed {args.seed!r} are "
                  f"already claimed. Vary the seed, e.g. {args.seed}-2.")
        return 1

    print(f"\nRe-verification bucket for seed {args.seed!r} ({len(targets)} canons):\n")
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
    try:
        sys.exit(main())
    except BrokenPipeError:
        # Output was piped into something that closed early (`| head`).
        sys.stderr.close()
        sys.exit(0)
