# SEO Reference for deadends.dev

Quick reference for SEO decisions made across the site. When adding new
templates, new canon domains, or new country landing pages, check against
this document first.

## Principles

1. **One canonical URL per piece of content.** `{base_url}/{domain}/{slug}/`
   for a canon family, `{base_url}/{id}/` for a single environment,
   `{base_url}/country/{cc}/` for a country landing page. Always set
   `<link rel="canonical">` to this exact URL.
2. **Structured data carries the machine-readable truth** — sub-ms for AI
   agents to load and for Google rich results. JSON-LD preferred over
   microdata (easier to maintain, invisible in rendered output).
3. **No duplicate JSON-LD types on the same URL.** `CollectionPage`
   inherits from `WebPage`; don't publish both as separate scripts (PR #114
   review: fixed duplicate `WebPage` block).
4. **Primary-source citations in canons** themselves build E-E-A-T
   (Experience, Expertise, Authority, Trust). Include `sources[]` arrays
   with gov/embassy/regulator URLs where possible — these propagate into
   JSON-LD citations.

## Required meta tags (every page)

Enforced by the shell script in README.md's "SEO 점검 가이드":

```
<title>
<meta name="description">
<meta name="robots">
<link rel="canonical">
<meta property="og:title">
<meta name="twitter:card">
```

Strongly recommended additions per template:

```
<meta name="author" content="deadends.dev">
<meta property="og:image:alt" content="...context-specific...">
<meta property="og:locale" content="en_US">
<meta name="twitter:image:alt" content="...context-specific...">
```

For multi-language future (not yet live, reserve the structure):

```
<link rel="alternate" hreflang="en" href="{canonical}">
<!-- + hreflang entries per language once translated -->
```

A lone `hreflang="en"` self-reference is a no-op today; it becomes
meaningful once we add a second language.

## Machine-discovery links

Every template should expose the API alongside the HTML:

```
<link rel="alternate" type="application/json" href="/api/v1/index.json" title="Error Index JSON API">
<link rel="alternate" type="application/json" href="/api/v1/match.json" title="Lightweight Error Matching">
<link rel="alternate" type="text/plain"       href="/llms.txt"           title="LLM-optimized error listing">
<link rel="describedby"                       href="/api/v1/openapi.json" type="application/json">
```

Rationale:
- `alternate application/json` — Google Rich Results can pick up structured
  alternates; AI agents use them to fetch canon JSON.
- `describedby` — signals to machines that the OpenAPI spec describes the
  alternate representations.
- `llms.txt` — emerging AI-agent discovery convention (llmstxt.org).

## Structured data per template

### index.html
- `@type: WebSite` with `SearchAction` (site search box in SERP).
- `@type: Organization` with logo.
- `@type: Dataset` — critical: marks deadends.dev as an indexable dataset
  for Google Dataset Search.

### domain.html (`/{domain}/`)
- `@type: BreadcrumbList` (site → domain)
- `@type: CollectionPage` with `mainEntity: ItemList`
- Do NOT add a parallel `WebPage` — CollectionPage IS a WebPage.

### error_summary.html (`/{domain}/{slug}/`)
- `@type: BreadcrumbList` (site → domain → error family)
- `@type: TechArticle` (for code errors) or `@type: Article` (for non-code)
- `mainEntity` Q&A pattern for AI citation — "How do I fix X?" / answer.
- Highwire Press citation metas (`citation_title`, `citation_date`,
  `citation_author`) added in PR #111 for academic/AI-citation engines.

### page.html (`/{domain}/{slug}/{env}/`)
- Same as error_summary plus `speakable` selectors on `#verdict-card`,
  `#fix-guide`, `#ai-summary` so voice assistants and Gemini can extract
  the action items.

### country.html (`/country/{cc}/`)
- `@type: BreadcrumbList` (site → Countries → country)
- `@type: CollectionPage` with `about: Country`, `inLanguage`, `mainEntity:
  ItemList` pointing to each country canon.
- Keywords include country name variants (visa, banking, legal, culture).

## Sitemap policy

`sitemap.xml` is a sitemap INDEX that references per-domain sub-sitemaps +
`sitemap-main.xml`. As of the 0.9 country pivot:

- `sitemap-main.xml` now includes `/country/{cc}/` URLs, `priority: 0.85`,
  `lastmod` = max `last_confirmed` across that country's canons.
- Per-domain sub-sitemaps list summary pages (priority 0.8) and env pages
  (priority 0.6), `lastmod` = canon `last_confirmed`.
- Sitemap index + all sub-sitemaps are pinged via IndexNow on deploy
  (`generator/submit_indexnow.py`).

## Robots / indexability

`build_robots_txt()` emits a canonical robots.txt with the sitemap URL and
explicit Allow for `/api/`. Pages use `noindex, follow` only for:

- The main `/sitemap/` HTML page (the XML version is canonical).
- Deliberate noindex for duplicate pivots (none today).

Every other page renders `index, follow, max-snippet:-1`.

## Image OpenGraph policy

- Site-wide default: `/og-image.png` (1200×630).
- Per-error dynamic: `/{id}/og.png` generated by `build_error_og_images`
  for canons with `verdict.resolvable != "partial"` — higher CTR on social
  because it embeds the error signature + fix rate.
- Per-country: currently uses site default. **Future work**: generate
  country-themed OG images (`/country/{cc}/og.png`) with country name +
  entry count.

## Canon-level SEO decisions

When writing a new canon:

- `error.signature` should contain the phrases an LLM would naturally
  output when giving the WRONG answer. That's what humans search for too.
  Example: `"AI tells a traveler to Japan to stick chopsticks upright in a
  rice bowl"` — when someone asks "is it rude to stick chopsticks in rice
  in Japan?", the regex matches.
- `error.regex` should include local-language terms where plausible —
  improves recall for multilingual queries (Chinese characters, Korean
  Hangul, Japanese kana, Arabic, Cyrillic all accepted).
- `verdict.summary` is the 1-2 sentence rendered as `<meta name="description">`
  in `page.html`. Keep it ≤160 chars when possible (Google's description
  snippet budget).
- `dead_ends[].action` and `workarounds[].action` appear in Google's
  "People Also Ask" extraction via FAQPage JSON-LD. Phrase them as
  standalone actionable sentences.

## Country-canon naming & slug SEO

- Slugs use English keywords, not transliterations. Example:
  `clock-gift-funeral-homophone` (not `sòngzhōng-gift`) — English search
  phrases match better.
- `environment.additional.country` = ISO alpha-2 lowercase. URL is
  `/country/kr/` (not `/country/KR/` or `/country/south-korea/`). Short,
  stable, matches most industry conventions (airline, currency).
- `environment.additional.country_name` is the human display name used in
  `<title>` and JSON-LD. "South Korea", "United States", not "Republic of
  Korea" or "USA".

## Things we explicitly DON'T do

- **Keyword stuffing in `<meta name="keywords">`** — kept but limited to
  5-7 phrases per page; Google ignores but Bing/Yandex partially use.
- **AMP** — dead format as of 2024. Not worth the maintenance cost.
- **Pagination rel=next/prev** — deprecated by Google in 2019; just let
  them crawl naturally.
- **Meta refresh redirects** — use 301s via `build_redirect_pages` if
  needed. Currently no active redirects.
- **hreflang to Wikipedia or translator pages** — these aren't "our"
  translations; wouldn't meet Google's criteria anyway.
- **JSON-LD inside pre-rendered JavaScript** — Googlebot handles it, but
  brittle under caching + AI-agent-scraper assumptions. Keep JSON-LD in
  the initial HTML.

## Validation checks

Before merging any template change:

```bash
# 1. Build the site
python -m generator.build_site

# 2. Verify required SEO tags present on all templates
python - <<'PY'
from pathlib import Path
REQUIRED = ['<title', 'meta name="description"', 'meta name="robots"',
            'link rel="canonical"', 'meta property="og:title"',
            'meta name="twitter:card"']
for f in Path('generator/templates').glob('*.html'):
    t = f.read_text()
    missing = [r for r in REQUIRED if r not in t]
    print(f'{"FAIL" if missing else "OK"} {f.name} {missing}')
PY

# 3. Google Rich Results Test — paste rendered HTML at
#    https://search.google.com/test/rich-results
# 4. Schema.org validator — https://validator.schema.org/

# 5. Full validate + build + tests
python -m generator.validate
python -m pytest tests/ -v
ruff check generator/ tests/
```

## Related docs

- [`docs/SEO_OPERATIONS_GUIDE.md`](SEO_OPERATIONS_GUIDE.md) — cron-level
  deployment + IndexNow + Google Search Console ops.
- [`docs/country-canon-guide.md`](country-canon-guide.md) — authoring
  standard for country canons, including SEO-aware signature/regex.
- [`CLAUDE.md`](../CLAUDE.md) — architecture and schema.
