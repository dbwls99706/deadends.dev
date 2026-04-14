# deadends.dev

Structured failure knowledge database for AI agents — covering both code
errors AND country-specific real-world dead ends. **2,145+ ErrorCanon JSON
entries across 54 domains**:

- **51 code-error domains** (2,089 entries): python, node, docker, cuda,
  git, pip, typescript, rust, go, kubernetes, terraform, aws, nextjs,
  react, java, database, cicd, php, dotnet, networking, android, api,
  cloud, cmake, elasticsearch, embedded, flutter, grpc, huggingface,
  kafka, llm, mongodb, nginx, opencv, pytorch, redis, ros2, tensorflow,
  unity, + quirk domains (communication, culture, data, disaster,
  food-safety, legal, medical, mental-health, pet-safety, policy,
  safety, security).
- **3 new country-scoped domains** (`visa`, `banking`, `emergency`) plus
  existing non-code domains extended with country-scoped canons. ID
  format `{domain}/{slug}/{country}` where country is an ISO 3166-1
  alpha-2 code (`kr`, `jp`, `us`, `de`, `uk`, `fr`, `cn`, `hk`, `tw`,
  `th`, `in`, `vn`, `id`, `sg`, `ph`, `sa`, `ae`, `tr`, `il`, `ru`, `br`,
  `mx`, ...). **20+ countries, 56+ country-scoped entries** as of v0.9.

**Country-canon rationale**: coding dead ends are largely solved by modern
LLMs. Country-specific rules (visa caveats, jurisdictional laws, cultural
taboos, food safety, emergency numbers, housing contract quirks) are where
generic AI advice is most often wrong. The expansion fills this gap with
primary-source-cited structured entries.

## Architecture

```
data/
  canons/              # ErrorCanon JSON files (source of truth, 2145+ files)
    {domain}/          # One directory per domain (54 domains)
      {slug}_{env}.json          # Flat-file format (code: env = runtime-os)
      {slug}/{env}.json          # Directory-style format
                                  # For country canons: env = ISO alpha-2 code (kr, jp, ...)
  environments/        # Environment matrix (env_matrix.json)
  graph/               # Error transition graph data
  signatures/          # Error signature data

generator/
  __init__.py
  build_site.py        # Static site builder (Jinja2 templates → site/)
  bulk_generate.py     # Generate canon JSON from seed definitions (current version)
  bulk_generate_v2-v16.py  # Historical bulk generation versions (excluded from linting)
  collect_evidence.py  # Evidence collection utilities
  collect_signatures.py # Signature collection utilities
  domains.py           # Domain constants: KEYWORD_MAP, DOMAIN_DISPLAY_NAMES, suggest_domains()
  generate_canons.py   # Canon generation logic
  generate_pairs.py    # Pair generation utilities
  lookup.py            # Programmatic error lookup SDK (lookup, lookup_all, search, batch_lookup)
  ping_search_engines.py  # Search engine ping on deploy
  pipeline.py          # Unified pipeline: validate → generate → build → test
  schema.py            # ErrorCanon JSON Schema (ERRORCANON_SCHEMA)
  submit_indexnow.py   # IndexNow submission on deploy
  templates/           # Jinja2 HTML templates
    index.html         # Homepage
    domain.html        # Domain listing page
    error_summary.html # Error summary page (groups environments)
    page.html          # Individual error page (per environment)
    search.html        # Search page
  validate.py          # Validation: schema, business rules, HTML, cross-refs, staleness

mcp/
  server.py            # MCP server (JSON-RPC over stdio) — 8 tools for AI agents

api/
  mcp.py               # Vercel serverless MCP endpoint

site/                  # Generated static site output (DO NOT edit directly)
tests/                 # pytest test suite
```

## Key Commands

```bash
# Full pipeline (validate → generate → build → test)
python -m generator.pipeline

# Build static site only
python -m generator.build_site

# Generate canon JSON from seeds (requires anthropic API key)
python -m generator.bulk_generate

# Validate data only (fast — use after editing canon JSON)
python -m generator.validate --data-only

# Validate generated HTML only
python -m generator.validate --site-only

# Validate everything (data + site)
python -m generator.validate

# Run tests
python -m pytest tests/ -v

# Lint (ruff)
ruff check generator/ tests/

# Look up an error (CLI)
python -m generator.lookup "error message"

# List all errors
python -m generator.lookup --list

# Run MCP server (stdio mode)
python -m mcp.server

# Pipeline shortcuts
python -m generator.pipeline --build   # Build only (skip generation)
python -m generator.pipeline --gen     # Generate canons only
```

## Installation

```bash
pip install -e ".[dev]"       # Development (pytest, ruff, jsonschema)
pip install -e ".[mcp]"       # MCP server only
pip install -e ".[pipeline]"  # Full pipeline (includes anthropic SDK)
```

Requires Python >= 3.10. Core dependency: jinja2 >= 3.1.

## ErrorCanon Schema

Each canon JSON file has these top-level required fields:

- `schema_version` — Semver string (e.g., "1.0.0")
- `id` — Pattern: `{domain}/{slug}/{env}` (e.g., `python/modulenotfounderror/py311-linux`)
- `url` — Must equal `https://deadends.dev/{id}`
- `error` — `signature` (string), `regex` (valid regex), `domain` (enum of 51 domains + 3 reserved), `category`, optional `first_seen`/`last_confirmed` dates
- `environment` — `runtime` (name + version_range), `os`, optional `hardware`/`python`/`additional`
- `verdict` — `resolvable` ("true"|"partial"|"false"), `fix_success_rate` (0.0–1.0), `confidence` (0.0–1.0), `last_updated`, `summary`
- `dead_ends[]` — At least 1 item. Each: `action`, `why_fails`, `fail_rate`, optional `condition`/`common_misconception`/`sources`
- `workarounds[]` — Each: `action`, `success_rate`, optional `how`/`tradeoff`/`condition`/`sources`
- `transition_graph` — `leads_to[]`, `preceded_by[]`, `frequently_confused_with[]` (references to other canon IDs)
- `metadata` — `generated_by`, `generation_date`, `review_status` (auto_generated|human_reviewed|community_verified), `evidence_count`, optional `page_views`/`ai_agent_hits`/`human_hits`

### Business Rules (enforced by validator)

- `verdict.resolvable == "true"` requires `fix_success_rate >= 0.7` and `confidence >= 0.6`
- `verdict.resolvable == "false"` requires `fix_success_rate < 0.2` and `confidence >= 0.6`
- `evidence_count < 3` requires `confidence <= 0.3`
- All cross-referenced `error_id`s must exist in the dataset
- All canon IDs must be unique (no flat-file vs directory-style duplicates)
- Staleness warnings at 180+ days since `last_confirmed`, errors at 365+ days

## Conventions

- Canon IDs: `{domain}/{slug}/{env}` — all lowercase, hyphens for slugs.
  - Code canons: env = `{runtime}-{os}` (e.g., `python/modulenotfounderror/py311-linux`)
  - Country canons: env = ISO 3166-1 alpha-2 country code (e.g., `legal/hanko-seal-required/jp`, `visa/esta-90-day-no-extension/us`). Sub-region allowed as `kr-seoul`.
- Always validate after data changes: `python -m generator.validate --data-only`
- Bulk-generated (LLM) code canons go in `generator/bulk_generate.py`
- Country canons are **manually authored** from primary sources — use
  `generator.country_canon_template.make_country_canon()` for the scaffold
- Templates use Jinja2 with autoescape enabled
- All HTML pages include machine-readable `<pre id="ai-summary">` blocks and JSON-LD structured data
- API responses at `/api/v1/{id}.json` mirror the canon JSON exactly
- Per-country landing pages render at `/country/{cc}/` (template: `generator/templates/country.html`)
- Lint with ruff: `ruff check .` (line-length 100, target py310, selects E/F/W/I)
- Ruff excludes `generator/bulk_generate*.py` and `api/` from linting
- The `site/` directory is generated output — never edit manually

## Authoring Country Canons

See [`docs/country-canon-guide.md`](docs/country-canon-guide.md) for full
sourcing standards and confidence calibration. Quick reference:

- `environment.additional`: `{country, country_name, jurisdiction_level, audience}`
- `review_status`: `human_reviewed` (or `community_verified` after vetting)
- Sources: primary government > embassy > regulator > reputable media.
  Reddit / personal blogs may appear inside `condition` or
  `common_misconception` but never as sole source of a claim.
- Respect business rules: `resolvable="true"` → `fix_success_rate >= 0.7` and
  `confidence >= 0.6`; `evidence_count < 3` → `confidence <= 0.3`.
- `SUPPORTED_COUNTRIES` list in
  `generator/country_canon_template.py` gates new country codes — add there
  first before writing canons for a new country.

## Security

When editing canon JSON files or templates, follow these rules:

- **Regex safety**: Avoid nested quantifiers like `(a+)+` or quantified alternation `(a|b)+` — these are vulnerable to ReDoS. The validator warns on common patterns but cannot catch all cases.
- **Source URLs**: Only use `https://` URLs from reputable sources. The build rejects `javascript:`, `data:`, `file:`, localhost, private IPs (10.x, 172.x, 192.168.x), and cloud metadata endpoints (169.254.x).
- **Error IDs**: Must match `{domain}/{slug}/{env}` — all lowercase, alphanumeric + hyphens. IDs containing `..` are rejected at build time.
- **Template escaping**: Inside `<script type="application/ld+json">` blocks, always use `{{ value | json_escape }}` for user-derived data — never rely on Jinja2 auto-escaping (which produces HTML entities, not valid JSON).
- **Secrets**: Verification codes and API keys should be set via environment variables (`GOOGLE_VERIFICATION`, `BING_VERIFICATION`, `INDEXNOW_KEY`), not hardcoded.
- **CI/CD**: GitHub Actions are pinned by SHA hash in `.github/workflows/build.yml`. When updating, always pin by full SHA and add a version comment.

## Deployment

- **Static site**: GitHub Pages via GitHub Actions (`.github/workflows/build.yml`)
  - On push to `main`: lint → test → validate data → build site → validate HTML → deploy
  - IndexNow submission and search engine pings run on main only
- **MCP endpoint**: Vercel serverless function (`api/mcp.py` via `vercel.json`)
  - Routes: `/mcp`, `/api/mcp`, `/.well-known/mcp/server-card.json`
  - CORS enabled for `/api/v1/*` endpoints

### Build Environment Variables

Optional overrides for `generator/build_site.py` (defaults work out of the box):

- `GOOGLE_VERIFICATION` — Google Search Console verification code
- `BING_VERIFICATION` — Bing Webmaster verification code
- `INDEXNOW_KEY` — IndexNow API key for instant indexing

## MCP Server

The MCP server exposes 8 read-only tools over stdio (JSON-RPC):

1. `lookup_error` — Match error message against regex patterns
2. `get_error_detail` — Full canon by ID
3. `list_error_domains` — All domains with counts
4. `search_errors` — Fuzzy keyword search
5. `list_errors_by_domain` — All errors in a domain
6. `batch_lookup` — Look up multiple errors at once (max 10)
7. `get_domain_stats` — Domain statistics and confidence levels
8. `get_error_chain` — Traverse error transition graph

Configuration via environment variables:
- `DEADENDS_PREFERRED_DOMAINS` — Comma-separated domain boost list
- `DEADENDS_MAX_RESULTS` — Max results (1–20, default 10)
- `DEADENDS_VERBOSE` — Show detailed workarounds (default true)

## Error Lookup SDK (for AI agents working in this repo)

When encountering errors (code or real-world) while developing, use the
lookup SDK:
```python
from generator.lookup import lookup, lookup_all, search, batch_lookup

# Single best match — works for both code and country queries
result = lookup("your error message")
# result["dead_ends"] = what NOT to try
# result["workarounds"] = what works

# All matches (sorted by relevance)
results = lookup_all("CUDA error: out of memory")
results = lookup_all("Japanese bank account as tourist")

# Keyword search (fuzzy) — filter by domain
results = search("memory limit", domain="docker", limit=5)
results = search("lese majeste", domain="legal", limit=5)

# Batch lookup
results = batch_lookup(["error1", "error2", "error3"])
```

## Testing

Tests are in `tests/` using pytest. Key test files:
- `test_schema.py` — Schema validation tests
- `test_validate.py` — Business rule and validation tests
- `test_build.py` — Site builder unit tests
- `test_build_integration.py` — Integration tests for full site build
- `test_pipeline.py` — Pipeline tests

Shared fixtures in `conftest.py`: `valid_canon` (deep copy of a valid canon) and `make_canon` (factory with overrides).
