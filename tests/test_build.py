"""Tests for the site build process."""

from pathlib import Path

from generator.build_site import (
    ENV_REDIRECTS,
    REDIRECT_MAP,
    _is_safe_url,
    _write_redirect_html,
    build_env_summary,
    collect_sources,
    load_canons,
)

DATA_DIR = Path(__file__).parent.parent / "data" / "canons"


class TestLoadCanons:
    def test_loads_all_canons(self):
        canons = load_canons(DATA_DIR)
        assert len(canons) >= 3

    def test_all_canons_have_id(self):
        canons = load_canons(DATA_DIR)
        for canon in canons:
            assert "id" in canon
            assert "/" in canon["id"]


class TestBuildEnvSummary:
    def test_python_cuda_summary(self):
        canon = {
            "environment": {
                "runtime": {"name": "pytorch", "version_range": ">=2.0,<2.3"},
                "hardware": {"gpu": "A100-40GB", "vram_gb": 40},
                "os": "linux",
                "python": ">=3.9,<3.13",
            }
        }
        summary = build_env_summary(canon)
        assert "pytorch" in summary
        assert "A100-40GB" in summary
        assert "linux" in summary

    def test_node_summary(self):
        canon = {
            "environment": {
                "runtime": {"name": "node", "version_range": ">=18,<23"},
                "os": "linux",
                "additional": {"architecture": "arm64"},
            }
        }
        summary = build_env_summary(canon)
        assert "node" in summary
        assert "arm64" in summary

    def test_minimal_summary(self):
        canon = {
            "environment": {
                "runtime": {"name": "python", "version_range": ">=3.10"},
                "os": "linux",
            }
        }
        summary = build_env_summary(canon)
        assert "python" in summary


class TestCollectSources:
    def test_collects_from_dead_ends(self):
        canon = {
            "dead_ends": [
                {"sources": ["https://example.com/a", "https://example.com/b"]},
                {"sources": ["https://example.com/c"]},
            ],
            "workarounds": [],
        }
        sources = collect_sources(canon)
        assert len(sources) == 3

    def test_collects_from_workarounds(self):
        canon = {
            "dead_ends": [{"sources": []}],
            "workarounds": [{"sources": ["https://example.com/d"]}],
        }
        sources = collect_sources(canon)
        assert len(sources) == 1

    def test_deduplicates(self):
        canon = {
            "dead_ends": [{"sources": ["https://example.com/a"]}],
            "workarounds": [{"sources": ["https://example.com/a"]}],
        }
        sources = collect_sources(canon)
        assert len(sources) == 1

    def test_filters_empty_strings(self):
        canon = {
            "dead_ends": [{"sources": ["", "https://example.com/a"]}],
            "workarounds": [],
        }
        sources = collect_sources(canon)
        assert len(sources) == 1


class TestUrlSafety:
    """Tests for URL validation and security."""

    def test_safe_http_url(self):
        assert _is_safe_url("https://example.com") is True

    def test_safe_http_url_no_ssl(self):
        assert _is_safe_url("http://example.com") is True

    def test_rejects_javascript_url(self):
        assert _is_safe_url("javascript:alert(1)") is False

    def test_rejects_data_url(self):
        assert _is_safe_url("data:text/html,<h1>XSS</h1>") is False

    def test_rejects_empty_string(self):
        assert _is_safe_url("") is False


class TestRedirectMap:
    """Tests for redirect configuration integrity."""

    def test_redirect_targets_exist_in_dataset(self):
        """All redirect targets must point to slugs that exist in the dataset."""
        canons = load_canons(DATA_DIR)
        known_slugs = set()
        for canon in canons:
            parts = canon["id"].split("/")
            if len(parts) >= 2:
                known_slugs.add(f"{parts[0]}/{parts[1]}")

        for old_slug, new_slug in REDIRECT_MAP.items():
            assert new_slug in known_slugs, (
                f"Redirect target '{new_slug}' (from '{old_slug}') "
                f"does not exist in the dataset"
            )

    def test_env_redirect_targets_exist(self):
        """All env-specific redirect targets must exist."""
        canons = load_canons(DATA_DIR)
        known_slugs = set()
        for canon in canons:
            parts = canon["id"].split("/")
            if len(parts) >= 2:
                known_slugs.add(f"{parts[0]}/{parts[1]}")

        for old_path, new_slug in ENV_REDIRECTS.items():
            assert new_slug in known_slugs, (
                f"Env redirect target '{new_slug}' (from '{old_path}') "
                f"does not exist"
            )

    def test_redirect_old_slugs_do_not_conflict_with_current(self):
        """Old redirect slugs must not collide with existing canon slugs."""
        canons = load_canons(DATA_DIR)
        current_slugs = set()
        for canon in canons:
            parts = canon["id"].split("/")
            if len(parts) >= 2:
                current_slugs.add(f"{parts[0]}/{parts[1]}")

        for old_slug in REDIRECT_MAP:
            assert old_slug not in current_slugs, (
                f"Redirect source '{old_slug}' conflicts with an existing "
                f"canon slug — would overwrite a live page"
            )

    def test_redirect_map_not_empty(self):
        assert len(REDIRECT_MAP) > 0

    def test_redirect_map_values_are_lowercase(self):
        for old, new in REDIRECT_MAP.items():
            assert old == old.lower(), f"Redirect key '{old}' must be lowercase"
            assert new == new.lower(), f"Redirect value '{new}' must be lowercase"

    def test_no_redirect_chain(self):
        """Redirect target must not itself be a redirect source (no chains)."""
        sources = set(REDIRECT_MAP.keys())
        for target in REDIRECT_MAP.values():
            assert target not in sources, (
                f"Redirect chain detected: '{target}' is both a source and target"
            )


class TestWriteRedirectHtml:
    """Tests for redirect HTML generation."""

    def test_creates_redirect_page(self, tmp_path):
        import generator.build_site as bs
        original = bs.SITE_DIR
        bs.SITE_DIR = tmp_path
        try:
            _write_redirect_html("old/slug", "https://deadends.dev/new/slug/")
            page = tmp_path / "old" / "slug" / "index.html"
            assert page.exists()
            content = page.read_text()
            assert 'http-equiv="refresh"' in content
            assert "https://deadends.dev/new/slug/" in content
            assert 'rel="canonical"' in content
            assert 'noindex' in content
        finally:
            bs.SITE_DIR = original

    def test_does_not_overwrite_real_page(self, tmp_path):
        import generator.build_site as bs
        original = bs.SITE_DIR
        bs.SITE_DIR = tmp_path
        try:
            # Create a "real" page first
            page_dir = tmp_path / "existing" / "page"
            page_dir.mkdir(parents=True)
            (page_dir / "index.html").write_text("<html>real page</html>")

            _write_redirect_html(
                "existing/page", "https://deadends.dev/other/"
            )
            content = (page_dir / "index.html").read_text()
            assert "real page" in content  # unchanged
            assert "refresh" not in content
        finally:
            bs.SITE_DIR = original
