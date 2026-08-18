"""Tests for disjoint re-verification target selection."""

import json
import subprocess
from datetime import date

import pytest

from generator.reverify import (
    _canon_id_from_path,
    canon_bucket,
    claimed_canon_ids,
    current_branch,
    load_aging_canons,
    seed_bucket,
    select_targets,
)

REFERENCE = date(2026, 8, 18)


def _write_canon(root, canon_id, last_confirmed):
    """Write a minimal canon just rich enough for age calculation."""
    domain, slug, env = canon_id.split("/")
    path = root / domain / slug
    path.mkdir(parents=True, exist_ok=True)
    (path / f"{env}.json").write_text(
        json.dumps({"id": canon_id, "error": {"last_confirmed": last_confirmed}}),
        encoding="utf-8",
    )


# Countries the project already ships canons for - a realistic spread of seeds.
SEEDS = [
    "nz", "za", "my", "ph", "ke", "et", "jp", "kr", "us", "de",
    "uk", "fr", "cn", "hk", "tw", "th", "in", "vn", "id", "sg",
    "sa", "ae", "tr", "il", "ru", "br", "mx", "au", "ca", "pl",
]


# Mirrors production: ~1000 aging canons over DEFAULT_BUCKETS is ~8 per bucket,
# so bucket occupancy and hash spread behave as they do against the real corpus.
CORPUS_SIZE = 1024


def _build_corpus(root, size=CORPUS_SIZE):
    for i in range(size):
        # Deliberately interleave two dates so ordering has ties to break.
        stamp = "2026-02-01" if i % 2 == 0 else "2026-02-11"
        _write_canon(root, f"python/aging-{i:04d}/py311-linux", stamp)
    _write_canon(root, "rust/fresh/rust1-linux", "2026-08-17")
    _write_canon(root, "go/undated/go1-linux", "not-a-date")
    return root


@pytest.fixture(scope="module")
def corpus(tmp_path_factory):
    """Aging canons, plus a fresh and an undated one. Read-only, so shared."""
    return _build_corpus(tmp_path_factory.mktemp("corpus") / "canons")


class TestLoadAgingCanons:
    def test_only_aging_canons_are_returned(self, corpus):
        entries = load_aging_canons(data_dir=corpus, reference_date=REFERENCE)
        ids = {e["id"] for e in entries}
        assert len(entries) == CORPUS_SIZE
        assert "rust/fresh/rust1-linux" not in ids
        assert "go/undated/go1-linux" not in ids

    def test_ordered_oldest_first_with_stable_tiebreak(self, corpus):
        entries = load_aging_canons(data_dir=corpus, reference_date=REFERENCE)
        ages = [e["age_days"] for e in entries]
        assert ages == sorted(ages, reverse=True)
        # Within one last_confirmed date, ties break on id, not filesystem order.
        oldest = [e["id"] for e in entries if e["last_confirmed"] == "2026-02-01"]
        assert oldest == sorted(oldest)

    def test_empty_corpus_returns_nothing(self, tmp_path):
        (tmp_path / "canons").mkdir()
        assert load_aging_canons(data_dir=tmp_path / "canons", reference_date=REFERENCE) == []


class TestSelectTargets:
    def test_same_seed_is_deterministic(self, corpus):
        first = select_targets("nz", data_dir=corpus, reference_date=REFERENCE)
        second = select_targets("nz", data_dir=corpus, reference_date=REFERENCE)
        assert [e["id"] for e in first] == [e["id"] for e in second]
        assert len(first) == 3

    def test_two_seeds_never_partially_overlap(self, corpus):
        """The invariant that actually prevents merge conflicts.

        Two seeds may collide onto the same bucket, in which case they get the
        *identical* set - obvious immediately. What must never happen is a
        partial overlap, where two PRs share some files and not others: that is
        the shape that conflicts on merge while looking like independent work.
        """
        picks = {
            s: frozenset(
                e["id"] for e in select_targets(s, data_dir=corpus, reference_date=REFERENCE)
            )
            for s in SEEDS
        }
        for a_seed, a in picks.items():
            for b_seed, b in picks.items():
                shared = a & b
                assert shared in (frozenset(), a), f"{a_seed} partially overlaps {b_seed}: {shared}"

    def test_no_partial_overlap_across_differing_corpora(self, corpus, tmp_path):
        """Two cycles never see the same corpus - each branches from its own main.

        Position-based blocks shift their boundaries whenever a merge ages
        canons in or refreshes them, letting two cycles land on overlapping-but-
        not-equal slices. Bucketing by canon ID has to survive that.
        """
        # What a later `main` looks like: some canons refreshed out of the aging
        # set, others newly aged in, at offsets that would move every boundary.
        grown = _build_corpus(tmp_path / "grown")
        for i in range(0, CORPUS_SIZE, 7):
            _write_canon(grown, f"python/aging-{i:04d}/py311-linux", "2026-08-17")
        for i in range(CORPUS_SIZE, CORPUS_SIZE + 40):
            _write_canon(grown, f"python/newly-aged-{i:04d}/py311-linux", "2026-02-05")

        before = {
            s: {e["id"] for e in select_targets(s, data_dir=corpus, reference_date=REFERENCE)}
            for s in SEEDS
        }
        after = {
            s: {e["id"] for e in select_targets(s, data_dir=grown, reference_date=REFERENCE)}
            for s in SEEDS
        }
        assert before != after, "corpora are too similar to prove anything"
        for a_seed, a in before.items():
            for b_seed, b in after.items():
                if seed_bucket(a_seed) == seed_bucket(b_seed):
                    continue  # same bucket: same lane, by design
                assert not a & b, f"{a_seed}@before overlaps {b_seed}@after: {a & b}"

    def test_seeds_spread_across_buckets(self, corpus):
        """Hashing must actually spread; a degenerate mapping would be useless."""
        distinct = {
            frozenset(e["id"] for e in select_targets(s, data_dir=corpus, reference_date=REFERENCE))
            for s in SEEDS
        }
        assert len(distinct) >= 24, f"only {len(distinct)} distinct buckets for {len(SEEDS)} seeds"

    def test_bucket_membership_depends_only_on_the_id(self):
        assert canon_bucket("python/foo/py311-linux") == canon_bucket("python/foo/py311-linux")
        assert canon_bucket("a/b/c", buckets=16) < 16

    def test_selection_stays_inside_the_aging_pool(self, corpus):
        for seed in ("nz", "za", "visa-br"):
            for entry in select_targets(seed, data_dir=corpus, reference_date=REFERENCE):
                assert entry["age_days"] > 180

    def test_excluded_ids_are_skipped_within_the_bucket(self, corpus):
        """A claimed canon is stepped over; the cycle stays in its own lane."""
        block = select_targets("nz", data_dir=corpus, reference_date=REFERENCE)
        moved = select_targets(
            "nz",
            exclude={block[0]["id"]},
            data_dir=corpus,
            reference_date=REFERENCE,
        )
        assert moved
        assert block[0]["id"] not in {e["id"] for e in moved}
        # Still the same bucket, so the survivors carry over rather than jumping.
        assert {e["id"] for e in block[1:]} <= {e["id"] for e in moved}
        bucket = seed_bucket("nz")
        assert all(canon_bucket(e["id"]) == bucket for e in moved)

    def test_everything_excluded_returns_empty(self, corpus):
        every_id = {e["id"] for e in load_aging_canons(data_dir=corpus, reference_date=REFERENCE)}
        assert select_targets(
            "nz", exclude=every_id, data_dir=corpus, reference_date=REFERENCE
        ) == []

    def test_exclusion_applies_to_a_corpus_smaller_than_one_bucket(self, tmp_path):
        """Regression: the short-corpus path used to return before excluding."""
        root = tmp_path / "canons"
        _write_canon(root, "python/only-one/py311-linux", "2026-02-01")
        _write_canon(root, "python/only-two/py311-linux", "2026-02-01")
        assert select_targets(
            "nz",
            exclude={"python/only-one/py311-linux", "python/only-two/py311-linux"},
            data_dir=root,
            reference_date=REFERENCE,
        ) == []

    def test_no_aging_canons_returns_empty(self, tmp_path):
        root = tmp_path / "canons"
        _write_canon(root, "rust/fresh/rust1-linux", "2026-08-17")
        assert select_targets("nz", data_dir=root, reference_date=REFERENCE) == []

    def test_single_canon_corpus_is_returned_only_to_its_own_bucket(self, tmp_path):
        root = tmp_path / "canons"
        _write_canon(root, "python/only-one/py311-linux", "2026-02-01")
        owner = canon_bucket("python/only-one/py311-linux")
        for s in SEEDS:
            picked = [e["id"] for e in select_targets(s, data_dir=root, reference_date=REFERENCE)]
            expected = ["python/only-one/py311-linux"] if seed_bucket(s) == owner else []
            assert picked == expected

    def test_count_below_one_is_rejected(self, corpus):
        with pytest.raises(ValueError):
            select_targets("nz", count=0, data_dir=corpus, reference_date=REFERENCE)

    def test_bucket_count_below_one_is_rejected(self, corpus):
        with pytest.raises(ValueError):
            select_targets("nz", buckets=0, data_dir=corpus, reference_date=REFERENCE)


class TestRealCorpus:
    def test_selection_works_against_the_shipped_dataset(self):
        """Guards against the shipped corpus drifting out of the pool assumptions."""
        picked = select_targets("nz")
        assert picked, "no aging canon fell in the 'nz' bucket"
        assert len(picked) <= 3
        assert all(e["path"].exists() for e in picked)
        assert len({e["id"] for e in picked}) == len(picked)
        assert all(canon_bucket(e["id"]) == seed_bucket("nz") for e in picked)


class TestCanonIdFromPath:
    def test_directory_layout(self):
        assert _canon_id_from_path(
            "data/canons/python/some-error/py311-linux.json"
        ) == "python/some-error/py311-linux"

    def test_flat_file_layout(self):
        assert _canon_id_from_path(
            "data/canons/go/too-many-open-files_go1-linux.json"
        ) == "go/too-many-open-files/go1-linux"

    def test_flat_file_layout_keeps_underscores_in_slug(self):
        assert _canon_id_from_path(
            "data/canons/go/a_b_c_go1-linux.json"
        ) == "go/a_b_c/go1-linux"

    def test_unrecognised_paths_return_none(self):
        assert _canon_id_from_path("README.md") is None
        assert _canon_id_from_path("data/canons/orphan.json") is None


def _run(repo, *args):
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)


@pytest.fixture
def git_repo(tmp_path):
    """A repo with a base ref and one other branch that touches two canons."""
    repo = tmp_path / "repo"
    (repo / "data" / "canons" / "python" / "base").mkdir(parents=True)
    _run(repo.parent, "init", "-q", "-b", "main", str(repo))
    _run(repo, "config", "user.email", "t@example.com")
    _run(repo, "config", "user.name", "t")

    (repo / "data/canons/python/base/py311-linux.json").write_text(
        json.dumps({"id": "python/base/py311-linux"})
    )
    _run(repo, "add", "-A")
    _run(repo, "commit", "-qm", "base")
    _run(repo, "update-ref", "refs/remotes/origin/main", "HEAD")

    _run(repo, "checkout", "-q", "-b", "feature")
    (repo / "data/canons/python/claimed").mkdir(parents=True)
    (repo / "data/canons/python/claimed/py311-linux.json").write_text(
        json.dumps({"id": "python/claimed/py311-linux"})
    )
    # Flat-file layout, and a non-canon file that must be ignored.
    (repo / "data/canons/go/flat_go1-linux.json").parent.mkdir(parents=True, exist_ok=True)
    (repo / "data/canons/go/flat_go1-linux.json").write_text(
        json.dumps({"id": "go/flat/go1-linux"})
    )
    (repo / "README.md").write_text("not a canon")
    _run(repo, "add", "-A")
    _run(repo, "commit", "-qm", "feature")
    _run(repo, "update-ref", "refs/remotes/origin/feature", "HEAD")
    _run(repo, "checkout", "-q", "main")
    return repo


class TestClaimedCanonIds:
    def test_collects_ids_touched_by_other_branches(self, git_repo):
        scan = claimed_canon_ids(repo_root=git_repo)
        assert scan.ok
        assert scan.branches == 1
        assert set(scan.ids) == {"python/claimed/py311-linux", "go/flat/go1-linux"}

    def test_base_ref_itself_is_not_claimed(self, git_repo):
        assert "python/base/py311-linux" not in claimed_canon_ids(repo_root=git_repo).ids

    def test_skip_branch_drops_your_own_claim(self, git_repo):
        scan = claimed_canon_ids(repo_root=git_repo, skip_branch="feature")
        assert scan.ok and scan.ids == frozenset() and scan.branches == 0

    def test_outside_a_git_repo_reports_failure_not_a_clean_scan(self, tmp_path):
        """A scan that could not run must never read as "nothing is claimed"."""
        plain = tmp_path / "plain"
        plain.mkdir()
        scan = claimed_canon_ids(repo_root=plain)
        assert scan.ids == frozenset()
        assert scan.ok is False
        assert scan.reason

    def test_missing_base_ref_reports_failure(self, git_repo):
        scan = claimed_canon_ids(base_ref="origin/nope", repo_root=git_repo)
        assert scan.ok is False
        assert "origin/nope" in scan.reason

    def test_claimed_ids_actually_steer_selection(self, corpus, git_repo):
        """The two halves compose: what git reports is what select_targets skips."""
        scan = claimed_canon_ids(repo_root=git_repo)
        assert scan.ok and scan.ids

        # Seed whichever bucket owns a real claimed canon, then confirm that
        # feeding the scan's IDs in as `exclude` removes it from the picks.
        claimed_id = sorted(scan.ids)[0]
        root = corpus.parent / "composed"
        _write_canon(root, claimed_id, "2026-02-01")
        _write_canon(root, "python/spare-a/py311-linux", "2026-02-01")

        # buckets=1 puts everything in one lane, so the only thing that can
        # remove the claimed canon from the picks is the exclusion itself.
        without = [e["id"] for e in select_targets(
            "nz", buckets=1, data_dir=root, reference_date=REFERENCE)]
        assert claimed_id in without

        with_scan = [e["id"] for e in select_targets(
            "nz", buckets=1, exclude=set(scan.ids), data_dir=root, reference_date=REFERENCE)]
        assert claimed_id not in with_scan
        assert "python/spare-a/py311-linux" in with_scan


class TestCurrentBranch:
    def test_reports_checked_out_branch(self, git_repo):
        assert current_branch(repo_root=git_repo) == "main"

    def test_detached_head_reports_none(self, git_repo):
        _run(git_repo, "checkout", "-q", "--detach", "HEAD")
        assert current_branch(repo_root=git_repo) is None

    def test_outside_a_git_repo_reports_none(self, tmp_path):
        plain = tmp_path / "plain2"
        plain.mkdir()
        assert current_branch(repo_root=plain) is None


class TestClaimScanDegradation:
    """A scan that could not check everything must never read as clean."""

    def test_unreadable_branch_marks_the_scan_incomplete(self, git_repo):
        # An orphan branch has no merge base with main, so `git diff a...b`
        # fails - the same shape a shallow CI clone produces.
        _run(git_repo, "checkout", "-q", "--orphan", "orphan")
        _run(git_repo, "rm", "-rqf", ".")
        (git_repo / "data/canons/python/orphan").mkdir(parents=True)
        (git_repo / "data/canons/python/orphan/py311-linux.json").write_text(
            json.dumps({"id": "python/orphan/py311-linux"})
        )
        _run(git_repo, "add", "-A")
        _run(git_repo, "commit", "-qm", "orphan")
        _run(git_repo, "update-ref", "refs/remotes/origin/orphan", "HEAD")
        _run(git_repo, "checkout", "-q", "main")

        scan = claimed_canon_ids(repo_root=git_repo)
        assert scan.ok is False
        assert "origin/orphan" in scan.reason
        # The branches it *could* read are still reported, not thrown away.
        assert "python/claimed/py311-linux" in scan.ids

    def test_origin_head_is_not_counted_as_a_branch(self, git_repo):
        before = claimed_canon_ids(repo_root=git_repo)
        _run(git_repo, "symbolic-ref", "refs/remotes/origin/HEAD",
             "refs/remotes/origin/main")
        after = claimed_canon_ids(repo_root=git_repo)
        assert after.branches == before.branches
        assert after.ids == before.ids
