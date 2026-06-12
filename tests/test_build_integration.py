"""Integration tests for the full site build process."""

import json
import re
from pathlib import Path

import pytest

from generator.build_site import (
    BASE_URL,
    build_about_page,
    build_domain_pages,
    build_error_pages,
    build_error_summary_pages,
    build_index_page,
    build_search_page,
    build_sitemap,
    load_canons,
)
from generator.validate import validate_all

DATA_DIR = Path(__file__).parent.parent / "data" / "canons"


def _env_counts(canons: list[dict]) -> dict[str, int]:
    """Number of environments per slug_key (domain/slug)."""
    counts: dict[str, int] = {}
    for canon in canons:
        slug_key = canon["id"].rsplit("/", 1)[0]
        counts[slug_key] = counts.get(slug_key, 0) + 1
    return counts


def _is_redirect_stub(content: str) -> bool:
    return 'http-equiv="refresh"' in content


@pytest.fixture(scope="module")
def built_site(tmp_path_factory):
    """Build the full site into a temp directory and return the path."""

    from jinja2 import Environment, FileSystemLoader

    project_root = Path(__file__).parent.parent
    template_dir = project_root / "generator" / "templates"
    site_dir = tmp_path_factory.mktemp("site")

    # Monkey-patch SITE_DIR for the build
    import generator.build_site as bs
    original_site_dir = bs.SITE_DIR
    bs.SITE_DIR = site_dir

    try:
        canons = load_canons(DATA_DIR)
        assert len(canons) >= 3, "Need at least 3 canons for integration test"

        jinja_env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=True,
        )
        jinja_env.globals["base_path"] = bs.BASE_PATH
        jinja_env.globals["base_url"] = bs.BASE_URL
        jinja_env.filters["display_name"] = bs.domain_display_name

        from markupsafe import Markup

        def _json_escape(s: str) -> Markup:
            if not isinstance(s, str):
                s = str(s) if s is not None else ""
            dumped = json.dumps(s)
            escaped = dumped[1:-1] if len(dumped) >= 2 else ""
            escaped = escaped.replace("</", r"<\/")
            escaped = escaped.replace("<!--", "\\u003C!--")
            return Markup(escaped)

        jinja_env.filters["json_escape"] = _json_escape

        build_error_pages(canons, jinja_env)
        build_domain_pages(canons, jinja_env)
        summary_urls = build_error_summary_pages(canons, jinja_env)
        build_search_page(canons, jinja_env)
        build_about_page(canons, jinja_env)
        build_index_page(canons, jinja_env)
        build_sitemap(canons, summary_urls)

        return {
            "site_dir": site_dir,
            "canons": canons,
            "summary_urls": summary_urls,
        }
    finally:
        bs.SITE_DIR = original_site_dir


class TestSiteBuildIntegration:
    def test_error_pages_created(self, built_site):
        """Each canon id resolves to a page: a real env page for multi-env
        slugs, a redirect stub (-> summary) for single-env slugs."""
        site_dir = built_site["site_dir"]
        env_counts = _env_counts(built_site["canons"])
        for canon in built_site["canons"]:
            page_path = site_dir / canon["id"] / "index.html"
            assert page_path.exists(), f"Missing page for {canon['id']}"
            content = page_path.read_text(encoding="utf-8")
            slug_key = canon["id"].rsplit("/", 1)[0]
            if env_counts[slug_key] <= 1:
                assert _is_redirect_stub(content), (
                    f"Single-env page {canon['id']} should be a redirect stub"
                )
            else:
                assert not _is_redirect_stub(content), (
                    f"Multi-env page {canon['id']} must be a real page"
                )

    def test_api_endpoints_created(self, built_site):
        """Each canon should have a JSON API endpoint."""
        site_dir = built_site["site_dir"]
        for canon in built_site["canons"]:
            api_path = site_dir / "api" / "v1" / f"{canon['id']}.json"
            assert api_path.exists(), f"Missing API file for {canon['id']}"

            # Verify the API JSON is valid and matches the canon
            with open(api_path, encoding="utf-8") as f:
                api_data = json.load(f)
            assert api_data["id"] == canon["id"]
            assert api_data["verdict"]["resolvable"] == canon["verdict"]["resolvable"]

            # Verify URL has trailing slash (prevents GitHub Pages redirect)
            assert api_data["url"].endswith("/"), (
                f"API JSON url for {canon['id']} must end with trailing slash"
            )

    def test_domain_pages_created(self, built_site):
        """Each domain should have a listing page."""
        site_dir = built_site["site_dir"]
        domains = {c["error"]["domain"] for c in built_site["canons"]}
        for domain in domains:
            page_path = site_dir / domain / "index.html"
            assert page_path.exists(), f"Missing domain page for {domain}"

    def test_index_page_created(self, built_site):
        """The main index page should exist."""
        assert (built_site["site_dir"] / "index.html").exists()

    def test_index_spatial_coverage_uses_place_type(self, built_site):
        """Dataset.spatialCoverage must use Place, not Country (GSC warning)."""
        html = (built_site["site_dir"] / "index.html").read_text(encoding="utf-8")
        assert '"spatialCoverage": [' in html
        assert '"@type": "Place"' in html
        assert '"@type": "Country"' not in html.split('"spatialCoverage"', 1)[1].split("]", 1)[0]
        # uk slug must be emitted as ISO 3166-1 alpha-2 "GB"
        if "United Kingdom" in html:
            assert '"addressCountry": "GB"' in html
            assert '"addressCountry": "UK"' not in html

    def test_sitemap_created(self, built_site):
        """Sitemap index should exist and reference sub-sitemaps."""
        sitemap_path = built_site["site_dir"] / "sitemap.xml"
        assert sitemap_path.exists()

        content = sitemap_path.read_text(encoding="utf-8")
        assert "sitemapindex" in content
        assert "sitemap-main.xml" in content

        # Summary pages should appear in domain sub-sitemaps
        all_sub_content = ""
        for f in built_site["site_dir"].glob("sitemap-*.xml"):
            all_sub_content += f.read_text(encoding="utf-8")
        for summary in built_site["summary_urls"]:
            assert summary["url"] in all_sub_content, (
                f"Missing URL in sub-sitemap: {summary['url']}"
            )

    def test_sitemap_covers_every_canon(self, built_site):
        """Every canon's slug summary URL must appear in a sub-sitemap.

        Env-specific URLs are intentionally excluded — they canonicalize
        to the slug summary, so listing them in the sitemap creates
        duplicate-content signals in Search Console. Coverage is verified
        at the slug level instead.
        """
        all_sub_content = ""
        for f in built_site["site_dir"].glob("sitemap-*.xml"):
            all_sub_content += f.read_text(encoding="utf-8")
        slug_keys = {
            "/".join(c["id"].split("/")[:2]) for c in built_site["canons"]
        }
        missing = [
            slug_key for slug_key in sorted(slug_keys)
            if f"/{slug_key}/" not in all_sub_content
        ]
        assert not missing, (
            f"{len(missing)} slug summary URL(s) missing from sub-sitemaps "
            f"(first 5: {missing[:5]})"
        )

    def test_sitemap_excludes_single_env_urls(self, built_site):
        """Single-env env URLs must stay out of the sitemap (they
        canonicalize to the summary, so the summary is their canonical URL
        and a sitemap should list canonical URLs only). Multi-env env URLs
        ARE listed because each carries unique per-env content and should
        be indexed independently.
        """
        all_sub_content = ""
        for f in built_site["site_dir"].glob("sitemap-*.xml"):
            all_sub_content += f.read_text(encoding="utf-8")

        env_count: dict[str, int] = {}
        for canon in built_site["canons"]:
            slug_key = canon["id"].rsplit("/", 1)[0]
            env_count[slug_key] = env_count.get(slug_key, 0) + 1

        single_env_leaked = []
        multi_env_missing = []
        for canon in built_site["canons"]:
            slug_key = canon["id"].rsplit("/", 1)[0]
            present = f"/{canon['id']}/</loc>" in all_sub_content
            if env_count[slug_key] <= 1 and present:
                single_env_leaked.append(canon["id"])
            elif env_count[slug_key] > 1 and not present:
                multi_env_missing.append(canon["id"])

        assert not single_env_leaked, (
            f"{len(single_env_leaked)} single-env URL(s) leaked into "
            f"sitemap (first 5: {single_env_leaked[:5]})"
        )
        assert not multi_env_missing, (
            f"{len(multi_env_missing)} multi-env URL(s) missing from "
            f"sitemap (first 5: {multi_env_missing[:5]})"
        )

    def test_html_pages_have_json_ld(self, built_site):
        """Every real (multi-env) error page should contain valid JSON-LD.

        Single-env pages are redirect stubs and carry no JSON-LD; their
        canonical summary page is covered by the summary-page tests.
        """
        site_dir = built_site["site_dir"]
        env_counts = _env_counts(built_site["canons"])
        for canon in built_site["canons"]:
            if env_counts[canon["id"].rsplit("/", 1)[0]] <= 1:
                continue
            page_path = site_dir / canon["id"] / "index.html"
            content = page_path.read_text(encoding="utf-8")

            assert 'application/ld+json' in content, (
                f"Missing JSON-LD in {canon['id']}"
            )

            # Extract and parse JSON-LD
            match = re.search(
                r'<script type="application/ld\+json">\s*(.*?)\s*</script>',
                content,
                re.DOTALL,
            )
            assert match, f"Could not extract JSON-LD from {canon['id']}"
            json_ld = json.loads(match.group(1))
            # JSON-LD uses Schema.org TechArticle with embedded ErrorCanon
            assert json_ld["@type"] == "TechArticle"
            assert json_ld["deadend:errorCanon"]["id"] == canon["id"]

            # Embedded canon URL must have trailing slash (prevent redirect)
            embedded_url = json_ld["deadend:errorCanon"]["url"]
            assert embedded_url.endswith("/"), (
                f"JSON-LD embedded url for {canon['id']} must end with '/'"
            )

    def test_html_pages_have_ai_summary(self, built_site):
        """Every real (multi-env) error page should have an ai-summary."""
        site_dir = built_site["site_dir"]
        env_counts = _env_counts(built_site["canons"])
        for canon in built_site["canons"]:
            if env_counts[canon["id"].rsplit("/", 1)[0]] <= 1:
                continue
            page_path = site_dir / canon["id"] / "index.html"
            content = page_path.read_text(encoding="utf-8")
            assert 'id="ai-summary"' in content, (
                f"Missing ai-summary in {canon['id']}"
            )

    def test_html_pages_have_faq_schema(self, built_site):
        """Real error pages carry FAQPage JSON-LD AND a matching visible
        FAQ section (Google requires structured-data content visible)."""
        site_dir = built_site["site_dir"]
        env_counts = _env_counts(built_site["canons"])
        for canon in built_site["canons"]:
            if env_counts[canon["id"].rsplit("/", 1)[0]] <= 1:
                continue
            page_path = site_dir / canon["id"] / "index.html"
            content = page_path.read_text(encoding="utf-8")
            assert "FAQPage" in content, (
                f"Missing FAQPage schema in {canon['id']}"
            )
            if canon["dead_ends"]:
                assert 'id="faq"' in content, (
                    f"Missing visible FAQ section in {canon['id']}"
                )

    def test_error_summary_pages_created(self, built_site):
        """Each unique error slug should have a summary page."""
        site_dir = built_site["site_dir"]
        slugs = set()
        for canon in built_site["canons"]:
            parts = canon["id"].rsplit("/", 1)
            if len(parts) == 2:
                slugs.add(parts[0])
        for slug in slugs:
            page_path = site_dir / slug / "index.html"
            assert page_path.exists(), f"Missing summary page for {slug}"

    def test_env_page_canonicals(self, built_site):
        """Single-env env URLs are redirect stubs (meta refresh + noindex +
        canonical -> summary, the static-host 301 equivalent). Multi-env
        env pages are real, self-canonical and indexable (no noindex).
        """
        site_dir = built_site["site_dir"]
        env_count = _env_counts(built_site["canons"])

        violations = []
        for canon in built_site["canons"]:
            slug_key = canon["id"].rsplit("/", 1)[0]
            content = (site_dir / canon["id"] / "index.html").read_text(
                encoding="utf-8"
            )
            if env_count[slug_key] <= 1:
                summary_url = f"{BASE_URL}/{slug_key}/"
                if not _is_redirect_stub(content):
                    violations.append(f"{canon['id']}: not a redirect stub")
                if f'<link rel="canonical" href="{summary_url}">' not in content:
                    violations.append(f"{canon['id']}: wrong stub canonical")
                if 'content="noindex"' not in content:
                    violations.append(f"{canon['id']}: stub missing noindex")
                if f'url={summary_url}' not in content:
                    violations.append(f"{canon['id']}: wrong refresh target")
            else:
                expected = (
                    f'<link rel="canonical" href="{BASE_URL}/{canon["id"]}/">'
                )
                if expected not in content:
                    violations.append(f"{canon['id']}: wrong self-canonical")
                if 'name="robots" content="noindex' in content:
                    violations.append(f"{canon['id']}: multi-env noindex")

        assert not violations, (
            f"{len(violations)} env page violation(s) "
            f"(first 5: {violations[:5]})"
        )

    def test_summary_omits_env_link_when_single_env(self, built_site):
        """When a slug has only one environment, the summary page must
        not render the redundant 'Environments' link list — that link
        targets the env duplicate (which canonicalizes back to this
        summary) and wastes crawl budget.
        """
        site_dir = built_site["site_dir"]
        slug_canons: dict[str, list[dict]] = {}
        for canon in built_site["canons"]:
            slug_canons.setdefault(
                canon["id"].rsplit("/", 1)[0], []
            ).append(canon)

        for slug_key, group in slug_canons.items():
            if len(group) != 1:
                continue
            env_id = group[0]["id"]
            summary_html = (site_dir / slug_key / "index.html").read_text(
                encoding="utf-8"
            )
            assert f'href="/{env_id}/"' not in summary_html, (
                f"Summary for {slug_key} still links to its only env page"
            )

    def test_summary_pages_have_visible_faq(self, built_site):
        """Summary pages with FAQPage JSON-LD must render a visible FAQ
        section with one <details> entry per JSON-LD Question."""
        site_dir = built_site["site_dir"]
        checked = 0
        for summary in built_site["summary_urls"]:
            content = (site_dir / summary["slug_key"] / "index.html").read_text(
                encoding="utf-8"
            )
            if '"@type": "FAQPage"' not in content:
                continue
            assert 'id="faq"' in content, (
                f"{summary['slug_key']}: FAQPage JSON-LD without visible FAQ"
            )
            blocks = re.findall(
                r'<script type="application/ld\+json">\s*(.*?)\s*</script>',
                content,
                re.DOTALL,
            )
            faq_ld = next(
                (
                    json.loads(b)
                    for b in blocks
                    if '"FAQPage"' in b
                ),
                None,
            )
            assert faq_ld is not None
            faq_section = content.split('id="faq"', 1)[1].split("</section>", 1)[0]
            details_count = faq_section.count("<details")
            assert details_count == len(faq_ld["mainEntity"]), (
                f"{summary['slug_key']}: visible FAQ has {details_count} "
                f"entries but JSON-LD has {len(faq_ld['mainEntity'])}"
            )
            checked += 1
        assert checked > 0, "No summary page with FAQPage JSON-LD found"

    def test_summary_titles_are_bounded(self, built_site):
        """Generated <title> tags must stay within ~70 visible chars so
        Google doesn't truncate/rewrite them sitewide."""
        import html as html_mod

        site_dir = built_site["site_dir"]
        violations = []
        for summary in built_site["summary_urls"]:
            content = (site_dir / summary["slug_key"] / "index.html").read_text(
                encoding="utf-8"
            )
            m = re.search(r"<title>(.*?)</title>", content, re.DOTALL)
            assert m, f"{summary['slug_key']}: missing <title>"
            title = html_mod.unescape(m.group(1))
            if len(title) > 70:
                violations.append(f"{summary['slug_key']} ({len(title)} chars)")
        assert not violations, (
            f"{len(violations)} summary title(s) exceed 70 chars "
            f"(first 5: {violations[:5]})"
        )

    def test_summary_pages_have_intro(self, built_site):
        """Summary pages carry the generated intro paragraph."""
        site_dir = built_site["site_dir"]
        for summary in built_site["summary_urls"][:25]:
            content = (site_dir / summary["slug_key"] / "index.html").read_text(
                encoding="utf-8"
            )
            assert 'class="intro"' in content, (
                f"{summary['slug_key']}: missing intro paragraph"
            )

    def test_homepage_links_no_single_env_urls(self, built_site):
        """The homepage must link canonical summary URLs, never single-env
        URLs (those are redirect stubs)."""
        html = (built_site["site_dir"] / "index.html").read_text(
            encoding="utf-8"
        )
        env_counts = _env_counts(built_site["canons"])
        single_env_ids = {
            c["id"]
            for c in built_site["canons"]
            if env_counts[c["id"].rsplit("/", 1)[0]] <= 1
        }
        hrefs = set(re.findall(r'href="/([^"]+)/"', html))
        leaked = sorted(h for h in hrefs if h in single_env_ids)
        assert not leaked, (
            f"Homepage links {len(leaked)} single-env stub URL(s) "
            f"(first 5: {leaked[:5]})"
        )

    def test_about_page_created(self, built_site):
        """The /about/ methodology page exists, self-canonicals, and is
        listed in the main sitemap."""
        about = built_site["site_dir"] / "about" / "index.html"
        assert about.exists()
        content = about.read_text(encoding="utf-8")
        assert f'<link rel="canonical" href="{BASE_URL}/about/">' in content
        main_sitemap = (built_site["site_dir"] / "sitemap-main.xml").read_text(
            encoding="utf-8"
        )
        assert f"{BASE_URL}/about/" in main_sitemap

    def test_search_page_created(self, built_site):
        """The search page should exist and contain search data."""
        search_path = built_site["site_dir"] / "search" / "index.html"
        assert search_path.exists()
        content = search_path.read_text(encoding="utf-8")
        assert "search-input" in content
        assert "regex" in content

    def test_sitemap_includes_search_and_summaries(self, built_site):
        """Sub-sitemaps should include search page and summary pages."""
        main_path = built_site["site_dir"] / "sitemap-main.xml"
        main_content = main_path.read_text(encoding="utf-8")
        assert "/search/" in main_content

        all_sub_content = ""
        for f in built_site["site_dir"].glob("sitemap-*.xml"):
            all_sub_content += f.read_text(encoding="utf-8")
        for summary in built_site["summary_urls"]:
            assert summary["url"] in all_sub_content


class TestDataValidation:
    def test_all_canons_pass_validation(self):
        """All canon JSON files should pass validation."""
        success = validate_all(data_dir=DATA_DIR, site_dir=None)
        assert success, "Canon data validation failed"
