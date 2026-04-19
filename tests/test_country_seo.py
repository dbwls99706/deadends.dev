"""Tests for the country-axis SEO infrastructure: hub page, API aggregates,
sitemap inclusion, MCP country tools, and country breadcrumb on page.html."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from generator.build_site import (
    _build_country_faq,
    _canon_country_info,
    build_country_api,
    build_country_og_images,
    build_country_pages,
    country_stats,
)

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "canons"


def _load_country_canons() -> list[dict]:
    out: list[dict] = []
    for path in DATA_DIR.rglob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("environment", {}).get("additional", {}).get("country"):
            out.append(data)
    return out


# --- _canon_country_info -----------------------------------------------------


def test_canon_country_info_lowercases():
    canon = {
        "environment": {
            "additional": {"country": "JP", "country_name": "Japan"}
        }
    }
    assert _canon_country_info(canon) == ("jp", "Japan")


def test_canon_country_info_returns_none_when_missing_name():
    canon = {"environment": {"additional": {"country": "jp"}}}
    assert _canon_country_info(canon) is None


# --- _build_country_faq ------------------------------------------------------


def test_build_country_faq_emits_qa_pairs():
    canons = _load_country_canons()
    if not canons:
        pytest.skip("No country canons present")
    # pick canons for one country
    by_country: dict[str, list[dict]] = {}
    for c in canons:
        by_country.setdefault(
            c["environment"]["additional"]["country"], []
        ).append(c)
    code, country_canons = next(iter(by_country.items()))
    name = country_canons[0]["environment"]["additional"]["country_name"]
    faq = _build_country_faq(country_canons, name)
    assert isinstance(faq, list)
    assert all("question" in i and "answer" in i for i in faq)
    assert len(faq) <= 8


def test_build_country_faq_handles_empty_workarounds():
    canons = [
        {
            "error": {"signature": "test sig"},
            "verdict": {"fix_success_rate": 0.9},
            "dead_ends": [
                {"action": "do bad", "why_fails": "because", "fail_rate": 0.9}
            ],
            "workarounds": [],
        }
    ]
    faq = _build_country_faq(canons, "Nowhereland")
    # At minimum the dead-end Q is included
    assert len(faq) >= 1
    assert "Nowhereland" in faq[0]["question"]


# --- country_stats aggregation ----------------------------------------------


def test_country_stats_sorts_by_count_desc():
    canons = [
        {"environment": {"additional": {"country": "kr", "country_name": "South Korea"}}}
    ] * 3 + [
        {"environment": {"additional": {"country": "jp", "country_name": "Japan"}}}
    ] * 5
    stats = country_stats(canons)
    assert stats[0]["slug"] == "jp"
    assert stats[0]["count"] == 5
    assert stats[1]["slug"] == "kr"


# --- build_country_pages, build_country_api, build_country_og_images ---------


def test_country_builders_run_e2e(tmp_path, monkeypatch):
    """End-to-end: build country pages, API, OG images into a tmp SITE_DIR."""
    from jinja2 import Environment, FileSystemLoader
    from markupsafe import Markup

    import generator.build_site as bs
    from generator.domains import domain_display_name

    canons = _load_country_canons()
    if not canons:
        pytest.skip("No country canons present")

    monkeypatch.setattr(bs, "SITE_DIR", tmp_path)

    template_dir = (
        Path(__file__).resolve().parent.parent
        / "generator" / "templates"
    )
    env = Environment(loader=FileSystemLoader(str(template_dir)), autoescape=True)
    env.globals["base_path"] = ""
    env.globals["base_url"] = "https://deadends.dev"
    env.filters["display_name"] = domain_display_name

    def _json_escape(s: str) -> Markup:
        if not isinstance(s, str):
            s = str(s) if s is not None else ""
        dumped = json.dumps(s)
        escaped = dumped[1:-1] if len(dumped) >= 2 else ""
        escaped = escaped.replace("</", r"<\/").replace("<!--", "\\u003C!--")
        return Markup(escaped)
    env.filters["json_escape"] = _json_escape

    build_country_pages(canons, env)
    build_country_api(canons)
    build_country_og_images(canons)

    # Hub page must exist
    assert (tmp_path / "country" / "index.html").exists()
    hub = (tmp_path / "country" / "index.html").read_text(encoding="utf-8")
    assert "Browse" in hub or "country" in hub.lower()

    # At least one per-country page + OG + JSON
    code = canons[0]["environment"]["additional"]["country"].lower()
    page = tmp_path / "country" / code / "index.html"
    api = tmp_path / "api" / "v1" / "country" / f"{code}.json"
    og = tmp_path / "country" / code / "og.svg"
    countries = tmp_path / "api" / "v1" / "countries.json"
    assert page.exists(), f"Missing per-country page for {code}"
    assert api.exists(), f"Missing per-country API for {code}"
    assert og.exists(), f"Missing per-country OG for {code}"
    assert countries.exists(), "Missing /api/v1/countries.json"

    # Per-country API must have the right shape
    api_data = json.loads(api.read_text(encoding="utf-8"))
    assert api_data["country"] == code
    assert isinstance(api_data["entries"], list)
    assert api_data["total_entries"] == len(api_data["entries"])

    # countries.json index must list all countries
    idx = json.loads(countries.read_text(encoding="utf-8"))
    assert idx["total_countries"] >= 1
    listed_codes = {c["country"] for c in idx["countries"]}
    assert code in listed_codes


def test_per_country_page_has_faqpage_and_speakable(tmp_path, monkeypatch):
    """Country pages must include FAQPage and speakable JSON-LD for AI Overviews."""
    from jinja2 import Environment, FileSystemLoader
    from markupsafe import Markup

    import generator.build_site as bs
    from generator.domains import domain_display_name

    canons = _load_country_canons()
    if not canons:
        pytest.skip("No country canons present")

    monkeypatch.setattr(bs, "SITE_DIR", tmp_path)

    template_dir = (
        Path(__file__).resolve().parent.parent
        / "generator" / "templates"
    )
    env = Environment(loader=FileSystemLoader(str(template_dir)), autoescape=True)
    env.globals["base_path"] = ""
    env.globals["base_url"] = "https://deadends.dev"
    env.filters["display_name"] = domain_display_name

    def _json_escape(s: str) -> Markup:
        if not isinstance(s, str):
            s = str(s) if s is not None else ""
        dumped = json.dumps(s)
        escaped = dumped[1:-1] if len(dumped) >= 2 else ""
        escaped = escaped.replace("</", r"<\/").replace("<!--", "\\u003C!--")
        return Markup(escaped)
    env.filters["json_escape"] = _json_escape

    build_country_pages(canons, env)

    code = canons[0]["environment"]["additional"]["country"].lower()
    page_html = (tmp_path / "country" / code / "index.html").read_text(encoding="utf-8")
    assert "FAQPage" in page_html, "Country page missing FAQPage JSON-LD"
    assert "speakable" in page_html, "Country page missing speakable spec"
    assert "spatialCoverage" in page_html, "Country page missing spatialCoverage"
    assert '"spatialCoverage": {"@type": "Place"' in page_html, (
        "spatialCoverage must use Place type (Country triggers GSC Dataset warnings)"
    )
    # Country aggregate API alternate
    assert (
        f"/api/v1/country/{code}.json" in page_html
    ), "Country page missing alternate to country aggregate JSON"


# --- MCP country tools --------------------------------------------------------


def test_mcp_list_errors_by_country():
    from mcp import server as mcp_server

    canons = _load_country_canons()
    if not canons:
        pytest.skip("No country canons present")
    code = canons[0]["environment"]["additional"]["country"].lower()
    result = mcp_server.handle_request(
        "tools/call",
        {"name": "list_errors_by_country", "arguments": {"country": code}},
        canons,
    )
    text = result["content"][0]["text"]
    assert code in text.lower() or "entr" in text.lower()


def test_mcp_get_country_summary():
    from mcp import server as mcp_server

    canons = _load_country_canons()
    if not canons:
        pytest.skip("No country canons present")
    code = canons[0]["environment"]["additional"]["country"].lower()
    result = mcp_server.handle_request(
        "tools/call",
        {"name": "get_country_summary", "arguments": {"country": code}},
        canons,
    )
    text = result["content"][0]["text"]
    assert "Total entries" in text
    assert "Domain breakdown" in text


def test_mcp_country_tools_listed_in_tools_list():
    from mcp import server as mcp_server

    result = mcp_server.handle_request("tools/list", {}, [])
    tool_names = {t["name"] for t in result["tools"]}
    assert "list_errors_by_country" in tool_names
    assert "get_country_summary" in tool_names


# --- Sitemap country inclusion -----------------------------------------------


def test_sitemap_main_includes_country_urls(tmp_path, monkeypatch):
    """build_sitemap must include /country/ hub + each /country/{cc}/ URL."""
    import generator.build_site as bs

    canons = _load_country_canons()
    if not canons:
        pytest.skip("No country canons present")

    monkeypatch.setattr(bs, "SITE_DIR", tmp_path)
    bs.build_sitemap(canons, summary_urls=[])
    sm = (tmp_path / "sitemap-main.xml").read_text(encoding="utf-8")
    assert "/country/</loc>" in sm.replace("\n", "")  # hub
    code = canons[0]["environment"]["additional"]["country"].lower()
    assert f"/country/{code}/" in sm


# --- Stats / OpenAPI / robots / HTML sitemap / api-mcp mirror ---------------


def test_stats_json_includes_country_breakdown(tmp_path, monkeypatch):
    import generator.build_site as bs

    canons = _load_country_canons()
    if not canons:
        pytest.skip("No country canons present")

    monkeypatch.setattr(bs, "SITE_DIR", tmp_path)
    bs.build_stats_json(canons)
    stats = json.loads(
        (tmp_path / "api" / "v1" / "stats.json").read_text(encoding="utf-8")
    )
    assert "total_countries" in stats
    assert "total_country_entries" in stats
    assert "countries" in stats
    assert isinstance(stats["countries"], dict)
    assert stats["total_countries"] >= 1


def test_openapi_documents_country_endpoints(tmp_path, monkeypatch):
    import generator.build_site as bs

    canons = _load_country_canons()
    if not canons:
        pytest.skip("No country canons present")

    monkeypatch.setattr(bs, "SITE_DIR", tmp_path)
    bs.build_openapi_spec(canons)
    spec = json.loads(
        (tmp_path / "api" / "v1" / "openapi.json").read_text(encoding="utf-8")
    )
    assert "/api/v1/countries.json" in spec["paths"]
    assert "/api/v1/country/{country}.json" in spec["paths"]
    assert "CountrySummary" in spec["components"]["schemas"]
    assert "CountryAggregate" in spec["components"]["schemas"]


def test_robots_allows_country_paths(tmp_path, monkeypatch):
    import generator.build_site as bs

    monkeypatch.setattr(bs, "SITE_DIR", tmp_path)
    bs.build_robots_txt()
    robots = (tmp_path / "robots.txt").read_text(encoding="utf-8")
    assert "Allow: /country/" in robots
    assert "Allow: /api/v1/country/" in robots


def test_api_mcp_mirror_has_country_tools():
    """api/mcp.py (Vercel serverless) must mirror MCP country tools."""
    import importlib.util

    p = Path(__file__).resolve().parent.parent / "api" / "mcp.py"
    spec = importlib.util.spec_from_file_location("api_mcp", p)
    api_mcp = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_mcp)
    tool_names = {t["name"] for t in api_mcp.TOOLS}
    assert "list_errors_by_country" in tool_names
    assert "get_country_summary" in tool_names


def test_index_json_includes_country_for_country_canons(tmp_path, monkeypatch):
    import generator.build_site as bs

    canons = _load_country_canons()
    if not canons:
        pytest.skip("No country canons present")

    monkeypatch.setattr(bs, "SITE_DIR", tmp_path)
    bs.build_api_index(canons)
    idx = json.loads(
        (tmp_path / "api" / "v1" / "index.json").read_text(encoding="utf-8")
    )
    # Find any country entry
    country_entries = [e for e in idx["errors"] if "country" in e]
    assert country_entries, "No country entries in index.json"
    e = country_entries[0]
    assert e["country"] == e["country"].lower()
    assert e["country_url"].endswith(f"/country/{e['country']}/")
    assert e["country_api_url"].endswith(f"/country/{e['country']}.json")


def test_match_json_includes_country_compact_field(tmp_path, monkeypatch):
    import generator.build_site as bs

    canons = _load_country_canons()
    if not canons:
        pytest.skip("No country canons present")

    monkeypatch.setattr(bs, "SITE_DIR", tmp_path)
    bs.build_match_json(canons)
    match = json.loads(
        (tmp_path / "api" / "v1" / "match.json").read_text(encoding="utf-8")
    )
    country_patterns = [p for p in match["patterns"] if "c" in p]
    assert country_patterns, "No country-tagged patterns in match.json"
    # Compact key 'c' is intentional for context-window efficiency
    assert all(len(p["c"]) == 2 for p in country_patterns)


# --- S-grade additions -------------------------------------------------------


def test_country_aggregate_enriched_with_entity(tmp_path, monkeypatch):
    """Per-country aggregate JSON must carry currency / emergency / language entity."""
    import generator.build_site as bs

    canons = _load_country_canons()
    if not canons:
        pytest.skip("No country canons present")
    monkeypatch.setattr(bs, "SITE_DIR", tmp_path)
    bs.build_country_api(canons)
    # Pick jp (rich metadata)
    jp_path = tmp_path / "api" / "v1" / "country" / "jp.json"
    if not jp_path.exists():
        pytest.skip("jp canon not present")
    agg = json.loads(jp_path.read_text(encoding="utf-8"))
    assert "entity" in agg
    assert agg["entity"]["currency"]["code"] == "JPY"
    assert "emergency" in agg["entity"]
    assert "gov_url" in agg["entity"]
    assert "faq_url" in agg
    assert "llms_txt_url" in agg
    assert "agents_md_url" in agg
    assert "source_urls" in agg
    assert isinstance(agg["source_urls"], list)


def test_country_faq_endpoint_generated(tmp_path, monkeypatch):
    """Per-country FAQ endpoint /api/v1/country/{cc}-faq.json must be schema.org FAQPage."""
    import generator.build_site as bs

    canons = _load_country_canons()
    if not canons:
        pytest.skip("No country canons present")
    monkeypatch.setattr(bs, "SITE_DIR", tmp_path)
    bs.build_country_api(canons)
    code = canons[0]["environment"]["additional"]["country"].lower()
    faq_path = tmp_path / "api" / "v1" / "country" / f"{code}-faq.json"
    assert faq_path.exists(), f"Missing FAQ endpoint for {code}"
    faq = json.loads(faq_path.read_text(encoding="utf-8"))
    assert faq["@type"] == "FAQPage"
    assert "mainEntity" in faq
    if faq["mainEntity"]:  # some countries may have no FAQ
        assert faq["mainEntity"][0]["@type"] == "Question"


def test_country_errors_ndjson_stream(tmp_path, monkeypatch):
    """NDJSON stream for country canons must exist and parse line-by-line."""
    import generator.build_site as bs

    canons = _load_country_canons()
    if not canons:
        pytest.skip("No country canons present")
    monkeypatch.setattr(bs, "SITE_DIR", tmp_path)
    bs.build_country_api(canons)
    ndjson_path = tmp_path / "api" / "v1" / "country-errors.ndjson"
    assert ndjson_path.exists(), "Missing country-errors.ndjson"
    lines = ndjson_path.read_text(encoding="utf-8").strip().split("\n")
    # Every non-empty line must be valid JSON with a country field
    for line in lines:
        obj = json.loads(line)
        assert obj["environment"]["additional"].get("country")


def test_per_country_llms_txt_and_agents_md(tmp_path, monkeypatch):
    """Per-country /country/{cc}/llms.txt + AGENTS.md must exist and be substantive."""
    from jinja2 import Environment, FileSystemLoader
    from markupsafe import Markup

    import generator.build_site as bs
    from generator.domains import domain_display_name

    canons = _load_country_canons()
    if not canons:
        pytest.skip("No country canons present")
    monkeypatch.setattr(bs, "SITE_DIR", tmp_path)

    # Need Jinja env for build_country_pages which runs first in real flow
    template_dir = (
        Path(__file__).resolve().parent.parent / "generator" / "templates"
    )
    env = Environment(loader=FileSystemLoader(str(template_dir)), autoescape=True)
    env.globals["base_path"] = ""
    env.globals["base_url"] = "https://deadends.dev"
    env.filters["display_name"] = domain_display_name

    def _json_escape(s: str) -> Markup:
        if not isinstance(s, str):
            s = str(s) if s is not None else ""
        dumped = json.dumps(s)
        escaped = dumped[1:-1] if len(dumped) >= 2 else ""
        escaped = escaped.replace("</", r"<\/").replace("<!--", "\\u003C!--")
        return Markup(escaped)
    env.filters["json_escape"] = _json_escape

    bs.build_country_pages(canons, env)
    bs.build_per_country_llms_and_agents(canons)

    code = canons[0]["environment"]["additional"]["country"].lower()
    llms_path = tmp_path / "country" / code / "llms.txt"
    agents_path = tmp_path / "country" / code / "AGENTS.md"
    assert llms_path.exists(), f"Missing /country/{code}/llms.txt"
    assert agents_path.exists(), f"Missing /country/{code}/AGENTS.md"
    llms_text = llms_path.read_text(encoding="utf-8")
    agents_text = agents_path.read_text(encoding="utf-8")
    # llms.txt should include entity facts + integration URLs
    assert "Currency:" in llms_text or "currency" in llms_text.lower()
    assert f"/api/v1/country/{code}.json" in llms_text
    # AGENTS.md should include task instructions
    assert "When responding" in agents_text
    assert f"/api/v1/country/{code}.json" in agents_text


def test_mcp_resources_list_includes_country_aggregates():
    from mcp import server as mcp_server

    canons = _load_country_canons()
    if not canons:
        pytest.skip("No country canons present")
    result = mcp_server.handle_request("resources/list", {}, canons)
    uris = {r["uri"] for r in result["resources"]}
    assert "https://deadends.dev/api/v1/countries.json" in uris
    # At least one per-country resource
    assert any("/api/v1/country/" in u for u in uris)
    assert any("/llms.txt" in u for u in uris)


def test_mcp_prompts_list_includes_country_prompts():
    from mcp import server as mcp_server

    result = mcp_server.handle_request("prompts/list", {}, [])
    prompt_names = {p["name"] for p in result["prompts"]}
    assert "country_pre_travel_check" in prompt_names
    assert "country_business_etiquette" in prompt_names
    assert "country_legal_red_lines" in prompt_names


def test_mcp_prompts_get_returns_country_scoped_template():
    from mcp import server as mcp_server

    result = mcp_server.handle_request(
        "prompts/get",
        {
            "name": "country_pre_travel_check",
            "arguments": {"country_code": "jp"},
        },
        [],
    )
    assert "messages" in result
    assert result["messages"]
    text = result["messages"][0]["content"]["text"]
    assert "/api/v1/country/jp.json" in text


def test_transition_graph_cross_links_exist_for_related_country_canons():
    """Related country canons should cross-reference each other via
    frequently_confused_with to help AI agents traverse related
    jurisdictions."""
    canons = _load_country_canons()
    by_id = {c["id"]: c for c in canons}
    # SG cannabis must reference ID / AE drug laws
    sg = by_id.get("legal/cannabis-prohibition-misuse/sg")
    if sg:
        refs = {
            r["error_id"]
            for r in sg["transition_graph"]["frequently_confused_with"]
        }
        assert any("drug-death-penalty/id" in r or "khat" in r for r in refs)
    # DE nazi-symbols should reference AT Verbotsgesetz
    de = by_id.get("legal/nazi-symbols-stgb-86a/de")
    if de:
        refs = {
            r["error_id"]
            for r in de["transition_graph"]["frequently_confused_with"]
        }
        assert any("verbotsgesetz/at" in r for r in refs)
