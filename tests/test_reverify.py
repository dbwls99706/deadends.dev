"""Tests for disjoint re-verification target selection."""

import json
from datetime import date

import pytest

from generator.reverify import load_aging_canons, select_targets

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


@pytest.fixture
def corpus(tmp_path):
    """300 canons past the aging threshold, plus fresh and undated ones.

    Sized to mirror production: the window yields 100 blocks, so the spread
    assertions below exercise the same arithmetic the real corpus does.
    """
    root = tmp_path / "canons"
    for i in range(300):
        # Deliberately interleave two dates so ordering has ties to break.
        stamp = "2026-02-01" if i % 2 == 0 else "2026-02-11"
        _write_canon(root, f"python/aging-{i:03d}/py311-linux", stamp)
    _write_canon(root, "rust/fresh/rust1-linux", "2026-08-17")
    _write_canon(root, "go/undated/go1-linux", "not-a-date")
    return root


class TestLoadAgingCanons:
    def test_only_aging_canons_are_returned(self, corpus):
        entries = load_aging_canons(data_dir=corpus, reference_date=REFERENCE)
        ids = {e["id"] for e in entries}
        assert len(entries) == 300
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

        Two cycles may collide onto the same block - hashing makes that
        unlikely, not impossible, which is what `exclude` is for. What must
        never happen is a *partial* overlap, where two PRs share some files and
        not others: that is the shape that conflicts on merge while looking
        like independent work.
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

    def test_seeds_spread_across_the_pool(self, corpus):
        """Hashing must actually spread; a degenerate mapping would be useless."""
        distinct = {
            frozenset(e["id"] for e in select_targets(s, data_dir=corpus, reference_date=REFERENCE))
            for s in SEEDS
        }
        # 30 seeds over 100 blocks: uniform hashing predicts ~26 distinct.
        assert len(distinct) >= 24, f"only {len(distinct)} distinct blocks for {len(SEEDS)} seeds"

    def test_selection_stays_inside_the_aging_pool(self, corpus):
        for seed in ("nz", "za", "visa-br"):
            for entry in select_targets(seed, data_dir=corpus, reference_date=REFERENCE):
                assert entry["age_days"] > 180

    def test_excluded_ids_push_selection_to_another_block(self, corpus):
        block = select_targets("nz", data_dir=corpus, reference_date=REFERENCE)
        moved = select_targets(
            "nz",
            exclude={block[0]["id"]},
            data_dir=corpus,
            reference_date=REFERENCE,
        )
        assert moved
        assert not {e["id"] for e in moved} & {e["id"] for e in block}

    def test_everything_excluded_returns_empty(self, corpus):
        every_id = {e["id"] for e in load_aging_canons(data_dir=corpus, reference_date=REFERENCE)}
        assert select_targets(
            "nz", exclude=every_id, data_dir=corpus, reference_date=REFERENCE
        ) == []

    def test_no_aging_canons_returns_empty(self, tmp_path):
        root = tmp_path / "canons"
        _write_canon(root, "rust/fresh/rust1-linux", "2026-08-17")
        assert select_targets("nz", data_dir=root, reference_date=REFERENCE) == []

    def test_corpus_smaller_than_one_block_returns_what_exists(self, tmp_path):
        root = tmp_path / "canons"
        _write_canon(root, "python/only-one/py311-linux", "2026-02-01")
        picked = select_targets("nz", data_dir=root, reference_date=REFERENCE)
        assert [e["id"] for e in picked] == ["python/only-one/py311-linux"]

    def test_count_below_one_is_rejected(self, corpus):
        with pytest.raises(ValueError):
            select_targets("nz", count=0, data_dir=corpus, reference_date=REFERENCE)


class TestRealCorpus:
    def test_selection_works_against_the_shipped_dataset(self):
        """Guards against the shipped corpus drifting out of the pool assumptions."""
        picked = select_targets("nz")
        assert len(picked) == 3
        assert all(e["path"].exists() for e in picked)
        assert len({e["id"] for e in picked}) == 3
