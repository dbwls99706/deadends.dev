"""Title, social-card and search-index behaviour that keeps every indexable
page unique and lightweight for search engines."""

import json

import pytest

import generator.build_site as bs
from generator.build_site import (
    country_list_phrase,
    country_page_title,
    env_title_contexts,
    humanize_slug,
    render_card_png,
    seo_title_plain,
    short_env_label,
    title_disambiguators,
)


class TestHumanizeSlug:
    def test_words_and_case(self):
        assert humanize_slug("tap-water-not-potable") == "Tap water not potable"

    def test_known_initialisms_keep_casing(self):
        assert humanize_slug("eu-roaming-like-at-home") == "EU roaming like at home"
        assert humanize_slug("eta-required-before-boarding") == "eTA required before boarding"
        assert humanize_slug("112-eu-emergency") == "112 EU emergency"

    def test_empty(self):
        assert humanize_slug("") == ""


class TestCountryTitles:
    def test_phrase_forms(self):
        assert country_list_phrase(["Japan"]) == "Japan"
        assert country_list_phrase(["Japan", "Chile"]) == "Japan and Chile"
        assert country_list_phrase(["A", "B", "C"]) == "A, B and C"
        assert country_list_phrase(["A", "B", "C", "D", "E"]) == "A, B, C and 2 more"

    def test_single_country_title(self):
        assert country_page_title("tap-water-not-potable", ["Mexico"]) == (
            "Tap water not potable in Mexico"
        )

    def test_country_name_survives_long_rule(self):
        title = country_page_title(
            "a-very-long-rule-name-that-goes-on-and-on-and-on-forever-more",
            ["the United Arab Emirates"],
        )
        assert title.endswith(" in the United Arab Emirates")
        assert len(seo_title_plain(title)) <= bs.PLAIN_TITLE_MAX_LEN

    def test_multi_country_shrinks_list_to_fit(self):
        names = ["Austria", "Belgium", "Denmark", "Finland", "France", "Germany"]
        title = country_page_title("health-insurance-deadline-not-retroactive", names)
        assert "more" in title
        assert len(seo_title_plain(title)) <= bs.PLAIN_TITLE_MAX_LEN

    def test_plain_title_has_suffix(self):
        assert seo_title_plain("Short").endswith(" | deadends.dev")


def _canon(cid, signature, env=None, country=None):
    environment = env or {"runtime": {"name": "python", "version_range": ">=3.11"}, "os": "linux"}
    if country:
        environment = {
            "runtime": {"name": "ai-agent", "version_range": ">=1.0"},
            "os": "any",
            "additional": {"country": country[0], "country_name": country[1]},
        }
    return {"id": cid, "error": {"signature": signature, "domain": cid.split("/")[0]},
            "environment": environment}


class TestTitleDisambiguators:
    LONG = "An error occurred (AccessDenied) when calling the GetObject operation: Access Denied"

    def test_no_collision_no_disambiguator(self):
        canons = [_canon("aws/a/x", "Sig A"), _canon("aws/b/x", "Sig B")]
        assert title_disambiguators(canons) == {}

    def test_truncated_prefix_collision_uses_slug(self):
        canons = [
            _canon("aws/s3-access-denied/x", self.LONG),
            _canon("aws/iam-access-denied/x", self.LONG + " for IAM"),
        ]
        d = title_disambiguators(canons)
        assert d["aws/s3-access-denied"] == "S3 access denied"
        assert d["aws/iam-access-denied"] == "IAM access denied"

    def test_same_slug_in_two_domains_uses_domain(self):
        canons = [_canon("cuda/nccl-timeout/x", "NCCL timeout"),
                  _canon("pytorch/nccl-timeout/x", "NCCL timeout")]
        d = title_disambiguators(canons)
        assert d["cuda/nccl-timeout"] == "CUDA"
        assert d["pytorch/nccl-timeout"] == "PyTorch"

    def test_country_canons_are_skipped(self):
        canons = [_canon("visa/a/jp", "AI tells X", country=("jp", "Japan")),
                  _canon("visa/b/kr", "AI tells X", country=("kr", "South Korea"))]
        assert title_disambiguators(canons) == {}


class TestEnvTitleContexts:
    def test_short_label(self):
        canon = _canon("python/x/py311-linux", "s", env={
            "runtime": {"name": "cpython", "version_range": ">=3.11,<3.12"},
            "os": "linux", "python": ">=3.11,<3.12",
        })
        assert short_env_label(canon) == "cpython 3.11 · linux"

    def test_any_values_are_dropped(self):
        canon = _canon("x/y/z", "s", env={
            "runtime": {"name": "transformers", "version_range": ">=4.30"},
            "hardware": {"gpu": "any"}, "os": "any",
        })
        assert short_env_label(canon) == "transformers 4.30"

    def test_identical_labels_fall_back_to_env_segment(self):
        env = {"runtime": {"name": "docker", "version_range": ">=20,<26"}, "os": "linux"}
        canons = [_canon("docker/net/docker24-linux", "s", env=env),
                  _canon("docker/net/docker24-vpn", "s", env=env)]
        ctx = env_title_contexts(canons)
        assert ctx["docker/net/docker24-linux"] == "docker24-linux"
        assert ctx["docker/net/docker24-vpn"] == "docker24-vpn"


class TestSocialCards:
    def test_png_written(self, tmp_path):
        out = tmp_path / "og" / "card.png"
        render_card_png(out, title="Python dead ends", eyebrow="deadends.dev", stat="83",
                        stat_label="issues")
        data = out.read_bytes()
        assert data[:8] == b"\x89PNG\r\n\x1a\n"
        # IHDR: 1200x630
        import struct
        width, height = struct.unpack(">II", data[16:24])
        assert (width, height) == (1200, 630)

    def test_fallback_without_pillow(self, tmp_path, monkeypatch):
        import builtins

        real_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name == "PIL" or name.startswith("PIL."):
                raise ImportError("no PIL")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", fake_import)
        out = tmp_path / "card.png"
        assert render_card_png(out, title="x") is False
        assert out.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"

    def test_domain_cards_and_site_card(self, tmp_path, monkeypatch):
        monkeypatch.setattr(bs, "SITE_DIR", tmp_path)
        canons = [_canon("python/a/x", "s"), _canon("docker/b/x", "s")]
        for c in canons:
            c["dead_ends"] = [{"action": "a"}]
        bs.build_og_image(canons)
        bs.build_domain_og_images(canons)
        assert (tmp_path / "og-image.png").exists()
        assert (tmp_path / "og" / "python.png").exists()
        assert (tmp_path / "og" / "docker.png").exists()

    def test_accent_is_deterministic(self):
        assert bs._stable_accent("kr") == bs._stable_accent("kr")
        assert bs._stable_accent("kr") in bs.OG_PALETTE


class TestSearchIndexFile:
    @pytest.fixture
    def built(self, tmp_path, monkeypatch, valid_canon):
        import copy

        from jinja2 import Environment, FileSystemLoader
        from markupsafe import Markup

        monkeypatch.setattr(bs, "SITE_DIR", tmp_path)
        env = Environment(loader=FileSystemLoader(str(bs.TEMPLATE_DIR)), autoescape=True)
        env.globals["base_url"] = bs.BASE_URL
        env.globals["base_path"] = bs.BASE_PATH
        env.filters["display_name"] = bs.domain_display_name
        env.filters["json_escape"] = lambda s: Markup(json.dumps(s)[1:-1])
        canons = []
        for i in range(3):
            c = copy.deepcopy(valid_canon)
            c["id"] = f"python/slug-{i}/py311-linux"
            c["error"]["signature"] = f"Signature {i}"
            canons.append(c)
        bs.build_search_page(canons, env)
        return tmp_path

    def test_index_is_a_separate_file_and_page_is_small(self, built):
        data = json.loads((built / bs.SEARCH_DATA_FILE).read_text(encoding="utf-8"))
        assert len(data) == 3
        assert {"id", "signature", "regex", "page_url"} <= set(data[0])
        page = (built / "search" / "index.html").read_text(encoding="utf-8")
        assert 'type="application/json" id="search-data"' not in page
        assert f"/{bs.SEARCH_DATA_FILE}" in page
        assert "Signature 0" not in page  # no inlined index
        assert "search-input" in page

    def test_robots_keeps_web_search_crawlers_out_of_the_index(self, tmp_path, monkeypatch):
        monkeypatch.setattr(bs, "SITE_DIR", tmp_path)
        bs.build_robots_txt()
        robots = (tmp_path / "robots.txt").read_text(encoding="utf-8")
        google = robots[robots.index("User-agent: Googlebot\n"):]
        google = google[: google.index("\n\n")]
        assert f"Disallow: /{bs.SEARCH_DATA_FILE}" in google
        assert "Disallow: /llms-full" in google
        assert "Disallow: /llms.txt" in google
