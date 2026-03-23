"""Tests for the site build process."""

from pathlib import Path

from generator.build_site import (
    ENV_REDIRECTS,
    REDIRECT_MAP,
    _generate_variations,
    _is_safe_url,
    _safe_json_ld,
    _sanitize_sources,
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

    def test_rejects_file_url(self):
        assert _is_safe_url("file:///etc/passwd") is False

    def test_rejects_ftp_url(self):
        assert _is_safe_url("ftp://example.com/file") is False

    def test_rejects_localhost(self):
        assert _is_safe_url("http://localhost/admin") is False

    def test_rejects_127_0_0_1(self):
        assert _is_safe_url("http://127.0.0.1:8080/secret") is False

    def test_rejects_0_0_0_0(self):
        assert _is_safe_url("http://0.0.0.0/") is False

    def test_rejects_ipv6_loopback(self):
        assert _is_safe_url("http://[::1]/") is False

    def test_rejects_private_10_x(self):
        assert _is_safe_url("http://10.0.0.1/internal") is False

    def test_rejects_private_192_168(self):
        assert _is_safe_url("http://192.168.1.1/router") is False

    def test_rejects_private_172_16(self):
        assert _is_safe_url("http://172.16.0.1/") is False

    def test_allows_172_outside_private(self):
        assert _is_safe_url("http://172.15.0.1/") is True
        assert _is_safe_url("http://172.32.0.1/") is True

    def test_rejects_link_local_metadata(self):
        """Block 169.254.x.x (AWS metadata endpoint attack vector)."""
        assert _is_safe_url("http://169.254.169.254/latest/meta-data/") is False

    def test_rejects_no_host(self):
        assert _is_safe_url("https://") is False

    def test_rejects_ipv6_mapped_ipv4(self):
        """Block IPv6-mapped IPv4 addresses (SSRF bypass vector)."""
        assert _is_safe_url("http://[::ffff:127.0.0.1]/") is False

    def test_rejects_octal_ip(self):
        """Block octal IP notation (e.g. 0177.0.0.1 = 127.0.0.1)."""
        assert _is_safe_url("http://0177.0.0.1/") is False


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

    def test_redirect_has_security_header(self, tmp_path):
        import generator.build_site as bs
        original = bs.SITE_DIR
        bs.SITE_DIR = tmp_path
        try:
            _write_redirect_html("redir/test", "https://deadends.dev/target/")
            content = (tmp_path / "redir" / "test" / "index.html").read_text()
            assert "X-Content-Type-Options" in content
        finally:
            bs.SITE_DIR = original


class TestSafeJsonLd:
    """Tests for JSON-LD escaping."""

    def test_basic_serialization(self):
        result = _safe_json_ld({"name": "test"})
        assert '"name"' in result
        assert '"test"' in result

    def test_escapes_script_breakout(self):
        result = _safe_json_ld({"text": "</script>"})
        assert "</script>" not in result
        assert r"<\/script>" in result

    def test_escapes_html_comment(self):
        result = _safe_json_ld({"text": "<!--injected-->"})
        assert "<!--" not in result
        assert "\\u003C!--" in result

    def test_ensure_ascii(self):
        """Non-ASCII chars should become \\uXXXX escapes."""
        result = _safe_json_ld({"text": "한글"})
        assert "한글" not in result  # should be escaped
        assert "\\u" in result

    def test_valid_json_output(self):
        """Output should be valid JSON after unescaping <\\/."""
        import json
        result = _safe_json_ld({"text": "</script>", "comment": "<!-- hi -->"})
        # Replace our custom escapes back for JSON parsing
        parseable = result.replace(r"<\/", "</")
        data = json.loads(parseable)
        assert data["text"] == "</script>"


class TestSanitizeSources:
    """Tests for source URL filtering."""

    def test_filters_javascript_urls(self):
        sources = ["https://example.com", "javascript:alert(1)"]
        assert len(_sanitize_sources(sources)) == 1

    def test_filters_data_urls(self):
        sources = ["data:text/html,<script>alert(1)</script>"]
        assert len(_sanitize_sources(sources)) == 0

    def test_filters_localhost(self):
        sources = ["http://localhost/admin", "https://example.com"]
        assert len(_sanitize_sources(sources)) == 1

    def test_filters_metadata_endpoint(self):
        sources = ["http://169.254.169.254/latest/meta-data/"]
        assert len(_sanitize_sources(sources)) == 0


class TestGenerateVariations:
    """Tests for _generate_variations null/type guard."""

    def test_none_signature_returns_empty(self):
        assert _generate_variations(None, ".*", "python") == []

    def test_empty_signature_returns_empty(self):
        assert _generate_variations("", ".*", "python") == []

    def test_non_string_returns_empty(self):
        assert _generate_variations(123, ".*", "python") == []

    def test_valid_signature_returns_list(self):
        result = _generate_variations("ModuleNotFoundError", "Module.*", "python")
        assert isinstance(result, list)
