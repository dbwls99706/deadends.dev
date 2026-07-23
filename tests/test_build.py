"""Tests for the site build process."""

import json
from pathlib import Path

from generator.build_site import (
    ENV_REDIRECTS,
    REDIRECT_MAP,
    _build_domain_faq,
    _domain_top_dead_ends,
    _faq_json_ld,
    _generate_variations,
    _is_safe_url,
    _safe_json_ld,
    _sanitize_sources,
    _write_redirect_html,
    build_env_summary,
    collect_sources,
    load_canons,
    seo_description,
    seo_title,
)
from generator.domains import DOMAIN_INTROS, domain_intro

DATA_DIR = Path(__file__).parent.parent / "data" / "canons"


class TestSeoTitle:
    def test_short_signature_untouched(self):
        title = seo_title("ENOSPC: no space left on device")
        assert title == "Fix ENOSPC: no space left on device | deadends.dev"
        assert len(title) <= 70

    def test_long_signature_truncated_at_word_boundary(self):
        sig = (
            "RuntimeError: CUDA error: out of memory and a very long tail "
            "that keeps going on and on far beyond any sane title length"
        )
        title = seo_title(sig)
        assert len(title) <= 70
        assert title.startswith("Fix RuntimeError: CUDA error:")
        assert title.endswith(" | deadends.dev")
        assert "…" in title
        # No mid-word cut: the char before the ellipsis ends a whole word
        head = title.split("…")[0]
        assert sig.startswith(head[len("Fix "):])

    def test_context_included_when_it_fits(self):
        title = seo_title("ENOSPC", context="node20-linux")
        assert title == "Fix ENOSPC on node20-linux | deadends.dev"

    def test_context_dropped_when_it_crowds_signature(self):
        sig = "Some moderately long signature text here"
        ctx = "a very long environment summary that eats the whole budget"
        title = seo_title(sig, context=ctx)
        assert len(title) <= 70
        assert ctx not in title

    def test_suffix_always_present(self):
        for sig in ("x", "y" * 200):
            assert seo_title(sig).endswith(" | deadends.dev")

    def test_counts_appended_when_short_signature_fits(self):
        title = seo_title("AssertionError", counts=(2, 3))
        assert title == "Fix AssertionError - 2 Dead Ends & 3 Workarounds | deadends.dev"
        assert len(title) <= 70

    def test_counts_singular_forms(self):
        title = seo_title("ENOSPC", counts=(1, 1))
        assert "1 Dead End &" in title
        assert "1 Workaround |" in title

    def test_counts_skipped_when_title_would_exceed_budget(self):
        sig = "AttributeError: 'NoneType' object has no attribute 'foo'"
        title = seo_title(sig, counts=(2, 3))
        assert "Dead End" not in title
        assert len(title) <= 70

    def test_counts_skipped_when_zero(self):
        assert "Dead End" not in seo_title("ENOSPC", counts=(0, 3))
        assert "Workaround" not in seo_title("ENOSPC", counts=(2, 0))

    def test_counts_ignored_when_context_given(self):
        title = seo_title("ENOSPC", context="node20-linux", counts=(2, 3))
        assert title == "Fix ENOSPC on node20-linux | deadends.dev"


def _mini_canon(slug_key, sig, dead_ends, fix_rate=0.8, resolvable="true"):
    return {
        "id": f"{slug_key}/env1",
        "error": {"signature": sig, "domain": slug_key.split("/")[0]},
        "verdict": {"fix_success_rate": fix_rate, "resolvable": resolvable},
        "dead_ends": dead_ends,
        "workarounds": [],
    }


class TestDomainTopDeadEnds:
    def test_ranks_by_fail_rate_and_links_source_entry(self):
        canons = [
            _mini_canon("git/a", "sig-a", [
                {"action": "Low", "why_fails": "w", "fail_rate": 0.3},
            ]),
            _mini_canon("git/b", "sig-b", [
                {"action": "High", "why_fails": "w", "fail_rate": 0.95},
            ]),
        ]
        top = _domain_top_dead_ends(canons)
        assert top[0]["action"] == "High"
        assert top[0]["slug_key"] == "git/b"
        assert top[0]["signature"] == "sig-b"

    def test_dedupes_same_action_keeping_highest_rate(self):
        canons = [
            _mini_canon("git/a", "sig-a", [
                {"action": "Retry it", "why_fails": "w", "fail_rate": 0.5},
            ]),
            _mini_canon("git/b", "sig-b", [
                {"action": "retry it", "why_fails": "w", "fail_rate": 0.9},
            ]),
        ]
        top = _domain_top_dead_ends(canons)
        assert len(top) == 1
        assert top[0]["fail_rate"] == 0.9

    def test_skips_entries_missing_action_or_why(self):
        canons = [
            _mini_canon("git/a", "sig-a", [
                {"action": "", "why_fails": "w", "fail_rate": 0.9},
                {"action": "ok", "why_fails": "", "fail_rate": 0.9},
                {"action": "kept", "why_fails": "reason", "fail_rate": 0.4},
            ]),
        ]
        top = _domain_top_dead_ends(canons)
        assert [d["action"] for d in top] == ["kept"]

    def test_respects_limit(self):
        canons = [
            _mini_canon(f"git/{i}", f"sig-{i}", [
                {"action": f"act-{i}", "why_fails": "w", "fail_rate": 0.5},
            ])
            for i in range(10)
        ]
        assert len(_domain_top_dead_ends(canons, limit=6)) == 6


class TestBuildDomainFaq:
    def _faq(self):
        entries = [
            {"slug_key": "git/easy", "signature": "easy-sig",
             "fix_success_rate": 0.9},
            {"slug_key": "git/hard", "signature": "hard-sig",
             "fix_success_rate": 0.1},
        ]
        top_de = [{"action": "Force push", "why_fails": "Rewrites history.",
                   "fail_rate": 0.85, "signature": "s", "slug_key": "git/x"}]
        return _build_domain_faq(
            "git", entries, total=2, total_de=5, total_wa=4,
            avg_fix_rate=72, resolvable_counts={"true": 1, "partial": 1, "false": 0},
            top_dead_ends=top_de,
        )

    def test_grounded_in_domain_numbers(self):
        faq = self._faq()
        answers = " ".join(item["answer"] for item in faq)
        assert "2 " in answers and "5 " in answers and "72%" in answers

    def test_names_hardest_entry(self):
        faq = self._faq()
        assert any("hard-sig" in item["answer"] for item in faq)

    def test_includes_top_dead_end(self):
        faq = self._faq()
        assert any("Force push" in item["answer"] for item in faq)

    def test_every_item_has_question_and_answer(self):
        for item in self._faq():
            assert item["question"].strip()
            assert item["answer"].strip()


class TestFaqJsonLd:
    def test_empty_items_give_empty_string(self):
        assert _faq_json_ld([]) == ""

    def test_serializes_valid_faqpage(self):
        raw = _faq_json_ld([
            {"question": "Q1?", "answer": 'Answer with "quotes" & <tags>.'},
        ])
        data = json.loads(raw)
        assert data["@type"] == "FAQPage"
        assert data["mainEntity"][0]["name"] == "Q1?"
        assert "</" not in raw  # script-breakout guard from _safe_json_ld


class TestDomainIntros:
    def test_intro_returned_for_known_domain(self):
        assert domain_intro("git")
        assert domain_intro("nonexistent-domain") == ""

    def test_all_data_domains_have_intros(self):
        data_domains = {c["error"]["domain"] for c in load_canons(DATA_DIR)}
        missing = data_domains - set(DOMAIN_INTROS)
        assert not missing, f"domains without hub intro: {sorted(missing)}"

    def test_intros_are_substantial_and_unique(self):
        texts = list(DOMAIN_INTROS.values())
        assert len(set(texts)) == len(texts)  # no copy-paste duplicates
        for text in texts:
            assert len(text.split()) >= 20  # real prose, not a stub


class TestSeoDescription:
    def test_joins_parts(self):
        assert (
            seo_description("First part.", "Second part.")
            == "First part. Second part."
        )

    def test_caps_length(self):
        desc = seo_description("word " * 100, max_len=155)
        assert len(desc) <= 155
        assert desc.endswith("…")

    def test_skips_empty_parts_and_collapses_whitespace(self):
        assert seo_description("a\n b", "", "  ", "c") == "a b c"


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


class TestJsonEscapeFilter:
    """Tests for the _json_escape filter logic (used in JSON-LD <script> blocks).

    The filter is a closure defined inside build_site.build_site(), so we test
    the same algorithm directly.
    """

    @staticmethod
    def _json_escape(s):
        """Mirror of the production _json_escape logic."""
        import json
        if not isinstance(s, str):
            s = str(s) if s is not None else ""
        dumped = json.dumps(s)
        escaped = dumped[1:-1] if len(dumped) >= 2 else ""
        escaped = escaped.replace("</", r"<\/")
        escaped = escaped.replace("<!--", "\\u003C!--")
        return escaped

    def test_normal_string(self):
        assert self._json_escape("hello") == "hello"

    def test_string_with_quotes(self):
        assert '\\"' in self._json_escape('he said "hi"')

    def test_script_breakout(self):
        result = self._json_escape("</script>")
        assert "</script>" not in result
        assert r"<\/script>" in result

    def test_html_comment_injection(self):
        result = self._json_escape("<!-- comment -->")
        assert "<!--" not in result
        assert "\\u003C!--" in result

    def test_none_input(self):
        assert self._json_escape(None) == ""

    def test_integer_input(self):
        assert self._json_escape(123) == "123"

    def test_empty_string(self):
        assert self._json_escape("") == ""

    def test_valid_json_when_quoted(self):
        import json
        result = self._json_escape('test "value" </end>')
        json_str = f'"{result}"'.replace(r"<\/", "</")
        parsed = json.loads(json_str)
        assert parsed == 'test "value" </end>'


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


class TestMcpToolNames:
    """MCP_TOOL_NAMES is the single source of truth for every AI
    discovery surface (llms.txt, ai-plugin.json, agent.json, mcp.json,
    server-card.json, CLAUDE.md, .cursorrules, homepage ai-summary).
    It must never drift from the actual server tool registry."""

    def test_mcp_tool_names_match_server(self):
        from generator.build_site import MCP_TOOL_NAMES
        from mcp.server import TOOLS

        server_tools = [t["name"] for t in TOOLS]
        assert MCP_TOOL_NAMES == server_tools, (
            "generator/build_site.py MCP_TOOL_NAMES is out of sync with "
            "mcp/server.py TOOLS - update MCP_TOOL_NAMES so AI discovery "
            "files advertise the real tool set."
        )
