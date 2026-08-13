"""Tests for the Search Console report's URL selection and shortlist."""

import json

import pytest

from generator import gsc_report


@pytest.fixture
def sitemap_dir(tmp_path, monkeypatch):
    """Point the report at a throwaway site/ directory."""
    monkeypatch.setattr(gsc_report, "SITE_DIR", tmp_path)
    return tmp_path


def _write_sitemap(directory, name, urls):
    locs = "".join(f"<loc>{u}</loc>" for u in urls)
    (directory / name).write_text(f"<urlset>{locs}</urlset>", encoding="utf-8")


class TestCollectUrls:
    def test_hubs_come_before_detail_pages(self, sitemap_dir):
        _write_sitemap(
            sitemap_dir,
            "sitemap-visa.xml",
            [
                "https://deadends.dev/visa/some-slug/",
                "https://deadends.dev/visa/",
                "https://deadends.dev/",
            ],
        )
        assert gsc_report.collect_urls() == [
            "https://deadends.dev/",
            "https://deadends.dev/visa/",
            "https://deadends.dev/visa/some-slug/",
        ]

    def test_shallower_hubs_rank_first(self, sitemap_dir):
        _write_sitemap(
            sitemap_dir,
            "sitemap-main.xml",
            ["https://deadends.dev/country/jp/", "https://deadends.dev/country/"],
        )
        assert gsc_report.collect_urls()[0] == "https://deadends.dev/country/"

    def test_duplicates_across_sitemaps_appear_once(self, sitemap_dir):
        _write_sitemap(sitemap_dir, "sitemap-a.xml", ["https://deadends.dev/visa/"])
        _write_sitemap(sitemap_dir, "sitemap-b.xml", ["https://deadends.dev/visa/"])
        assert gsc_report.collect_urls() == ["https://deadends.dev/visa/"]

    def test_missing_sitemaps_exits_with_guidance(self, sitemap_dir):
        with pytest.raises(SystemExit) as exc:
            gsc_report.collect_urls()
        assert "build_site" in str(exc.value)


class TestPrintReport:
    def _result(self, url, coverage):
        return {"url": url, "coverage": coverage}

    def test_shortlist_excludes_indexed_urls(self):
        results = [
            self._result("https://deadends.dev/", gsc_report.INDEXED_STATE),
            self._result("https://deadends.dev/visa/", "Crawled - currently not indexed"),
        ]
        assert gsc_report.print_report(results, {}) == ["https://deadends.dev/visa/"]

    def test_shortlist_puts_hubs_first(self):
        results = [
            self._result("https://deadends.dev/visa/deep-slug/", "URL is unknown to Google"),
            self._result("https://deadends.dev/visa/", "URL is unknown to Google"),
        ]
        assert gsc_report.print_report(results, {})[0] == "https://deadends.dev/visa/"

    def test_shortlist_is_capped_at_the_daily_quota(self):
        results = [
            self._result(f"https://deadends.dev/d{i}/", "URL is unknown to Google")
            for i in range(25)
        ]
        # Google caps manual indexing requests at roughly ten a day, so handing
        # back more than that would just be noise.
        assert len(gsc_report.print_report(results, {})) == 10

    def test_urls_that_errored_are_not_offered_for_indexing(self):
        results = [{"url": "https://deadends.dev/visa/", "error": "quota exceeded"}]
        assert gsc_report.print_report(results, {}) == []


class TestLoadPrevious:
    def test_missing_file_is_not_an_error(self, tmp_path, monkeypatch):
        monkeypatch.setattr(gsc_report, "OUTPUT_FILE", tmp_path / "absent.json")
        assert gsc_report.load_previous() == {}

    def test_corrupt_file_is_not_an_error(self, tmp_path, monkeypatch):
        path = tmp_path / "gsc_report.json"
        path.write_text("{not json", encoding="utf-8")
        monkeypatch.setattr(gsc_report, "OUTPUT_FILE", path)
        assert gsc_report.load_previous() == {}

    def test_previous_timestamp_survives_a_round_trip(self, tmp_path, monkeypatch):
        path = tmp_path / "gsc_report.json"
        path.write_text(json.dumps({"generated_at": "2026-08-13T00:00:00+00:00"}))
        monkeypatch.setattr(gsc_report, "OUTPUT_FILE", path)
        assert gsc_report.load_previous()["generated_at"] == "2026-08-13T00:00:00+00:00"
