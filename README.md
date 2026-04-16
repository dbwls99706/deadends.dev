# deadends.dev

<!-- mcp-name: dev.deadends/deadends-dev -->

[![Precision@1](https://img.shields.io/badge/Precision%401-90%25-brightgreen)](https://deadends.dev/dashboard/)
[![MRR](https://img.shields.io/badge/MRR-0.935-brightgreen)](https://deadends.dev/dashboard/)
[![Entries](https://img.shields.io/badge/entries-2204-blue)](https://deadends.dev)
[![Domains](https://img.shields.io/badge/domains-54-green)](https://deadends.dev)
[![Countries](https://img.shields.io/badge/countries-39%2B-orange)](https://deadends.dev/country/)
[![MCP Tools](https://img.shields.io/badge/MCP_tools-11-purple)](https://smithery.ai/server/deadend/deadends-dev)
[![PyPI](https://img.shields.io/pypi/v/deadends-dev)](https://pypi.org/project/deadends-dev/)
[![License](https://img.shields.io/badge/license-MIT%20%2F%20CC%20BY%204.0-lightgrey)](LICENSE)

**Stop AI agents from repeating known failures — in code AND in the real world.**

AI assistants reliably fumble two kinds of problems: known-failed code fixes, and
country-specific real-world rules they've never been exposed to in training.
deadends.dev now covers both:

- **Code errors** (2,089 entries, 51 domains): what NOT to try when an agent
  hits `ModuleNotFoundError`, `CUDA OOM`, `CrashLoopBackOff`, etc.
- **Country-scoped dead ends** (56+ entries across 20+ countries): visa rules,
  banking requirements, legal red lines (lèse-majesté, §86a, Article 301),
  cultural taboos (chopsticks in rice, clock gifts in China, red-ink names in
  Korea), food safety, emergency numbers, driving norms, housing contracts —
  all the friction where a plausible-sounding global answer is wrong locally.

> **Why the expansion?** Coding dead ends are largely solved by a good LLM.
> Country-specific friction — Japanese hanko requirements, Schengen 90/180
> math, Ramadan business hours, Saudi alcohol ban, Indian beef taboos — is
> where generic AI advice breaks hardest. The codebase and schema are
> identical; the env segment just carries a country code.

> **90% Precision@1** · **0.935 MRR** · [Data Quality Dashboard](https://deadends.dev/dashboard/)

> **Website:** [deadends.dev](https://deadends.dev) · **MCP Server:** [Smithery](https://smithery.ai/server/deadend/deadends-dev) · **PyPI:** [deadends-dev](https://pypi.org/project/deadends-dev/) · **API:** [/api/v1/index.json](https://deadends.dev/api/v1/index.json)
> **Repository:** [https://github.com/dbwls99706/deadends.dev](https://github.com/dbwls99706/deadends.dev)

## Why Use This?

| Without deadends.dev | With deadends.dev |
|---------------------|-------------------|
| Agent tries `sudo pip install` → breaks system Python → wastes 3 retries | Agent sees "dead end: sudo pip — fails 70%" → skips it immediately |
| Agent tells user to tip 15% at a Tokyo restaurant | Agent knows tipping is refused in Japan (`culture/tipping-refused/jp`) |
| Agent drafts a Thai social post referencing King Rama X | Agent stops: Article 112 lèse-majesté risk (`legal/lese-majeste-article-112/th`) |
| Agent fixes error A, gets confused by error B | Agent knows "A leads to B 78% of the time" → handles both |
| Agent tells unmarried couple to kiss publicly in Dubai | Agent flags UAE public decency law (`legal/unmarried-public-affection/ae`) |

**What makes this different from asking an LLM?**
- **Deterministic**: Same query → same answer, every time. No hallucination.
- **Country-scoped**: ID format `{domain}/{slug}/{env}` — env holds the country
  code (`kr`, `jp`, `us`, `de`...) so the same taboo can be answered
  differently for different jurisdictions.
- **Primary-sourced**: Every country canon cites government sites, embassies,
  or verifiable reporting. No "based on general knowledge" answers.
- **Community-validated**: Fix success rates updated from real outcome reports.
- **Sub-millisecond**: Local regex matching, no API roundtrip.

### 현실적인 한계 (운영 관점)

- 모든 에러를 다 커버하지는 못합니다. 없는 케이스는 이슈/PR/`report_outcome`로 빠르게 보완합니다.
- 설명의 깊이보다 **실전 해결 우선**(dead end/workaround 중심)으로 설계되어 있습니다.
- 신뢰성은 도메인/케이스마다 다를 수 있으므로, 고위험 변경은 공식 문서/벤더 가이드와 교차 검증을 권장합니다.

## Quick Start (30 seconds)

```bash
pip install deadends-dev
deadends "CUDA error: out of memory"
```

### MCP Server (Claude Desktop / Cursor)

Add to `~/.claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "deadend": {
      "command": "python",
      "args": ["-m", "mcp.server"],
      "cwd": "/path/to/deadends.dev"
    }
  }
}
```

Or install via [Smithery](https://smithery.ai/server/deadend/deadends-dev) (no local setup):

```bash
npx -y @smithery/cli@latest install deadend/deadends-dev --client claude
```

#### MCP `Unauthorized` 빠른 해결 가이드 (사람용)

`deadend: calling "initialize": sending "initialize": Unauthorized` 에러가 보이면 아래를 **순서대로 그대로 실행/확인**하세요.

1) 로컬 서버 모드인지, 원격(Smithery) 모드인지 하나만 사용
```bash
# 로컬 서버 확인 (정상 시 툴 목록이 출력됨)
python -m mcp.server --help
```

2) Claude Desktop 설정 파일 점검 (`cwd`는 실제 경로여야 함)
```bash
cat ~/.claude/claude_desktop_config.json
```

3) 로컬 서버 직접 실행 테스트
```bash
cd /path/to/deadends.dev
python -m mcp.server
```

4) Smithery 모드라면 재설치(토큰/설정 꼬임 복구)
```bash
npx -y @smithery/cli@latest uninstall deadend/deadends-dev --client claude
npx -y @smithery/cli@latest install deadend/deadends-dev --client claude
```

5) 마지막으로 Claude Desktop 완전 재시작
```bash
# macOS 예시
osascript -e 'quit app "Claude"'
open -a Claude
```

> 팁: `Unauthorized`는 보통 잘못된 `cwd`, 중복 서버 설정(로컬+원격 동시), 또는 만료된 인증 상태에서 발생합니다.

### Antigravity (Google AI IDE)

Add as a remote MCP server — no authentication required:

```json
{
  "mcpServers": {
    "deadend": {
      "serverUrl": "https://deadends.dev/mcp",
      "type": "http"
    }
  }
}
```

> **Note:** Antigravity uses `serverUrl` (not `url`). If you get `Unauthorized`, remove any existing deadend entries from the MCP Store and re-add manually using the config above. See the [Antigravity MCP auth guide](https://discuss.ai.google.dev/t/guide-fixing-authentication-for-the-google-developer-knowledge-mcp-server-and-other-cloud-servers-in-antigravity/136601) for general troubleshooting.

### Python SDK

```python
from generator.lookup import lookup, batch_lookup, search

# Single error lookup
result = lookup("ModuleNotFoundError: No module named 'torch'")

# What NOT to try (saves tokens and time)
for d in result["dead_ends"]:
    print(f"AVOID: {d['action']} — fails {int(d['fail_rate']*100)}%")

# What actually works
for w in result["workarounds"]:
    print(f"TRY: {w['action']} — works {int(w['success_rate']*100)}%")

# Batch lookup (multiple errors at once)
results = batch_lookup(["error1", "error2", "error3"])
```

### Example Response

```
## ModuleNotFoundError: No module named 'X' (Python 3.11+)
Resolvable: true | Fix rate: 0.88

### Dead Ends (DO NOT TRY):
- pip install X with system Python (fails 70%): venv not activated

### Workarounds (TRY THESE):
- Create venv, activate, then pip install (works 95%)
- Use python -m pip install instead of bare pip (works 90%)
```

## MCP Tools (11)

| Tool | Description |
|------|-------------|
| `lookup_error` | Match an error message against 2000+ known patterns |
| `get_error_detail` | Full canon by ID |
| `list_error_domains` | All 54 domains with counts |
| `search_errors` | TF-IDF keyword search across all domains |
| `list_errors_by_domain` | All errors in a domain |
| `list_errors_by_country` | All country-scoped dead ends for an ISO alpha-2 code |
| `get_country_summary` | Country-level summary (entries, fix rate, domain mix) |
| `batch_lookup` | Look up multiple errors at once (max 10) |
| `get_domain_stats` | Domain quality metrics and confidence levels |
| `get_error_chain` | Traverse the error transition graph |
| `report_outcome` | Report whether a workaround worked (feeds back into success rates) |

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| [`/api/v1/match.json`](https://deadends.dev/api/v1/match.json) | Lightweight regex matching (fits in context window) |
| [`/api/v1/index.json`](https://deadends.dev/api/v1/index.json) | Full error index with metadata (entries include `country` field for country canons) |
| [`/api/v1/{id}.json`](https://deadends.dev/api/v1/python/modulenotfounderror/py311-linux.json) | Individual ErrorCanon |
| [`/api/v1/countries.json`](https://deadends.dev/api/v1/countries.json) | Country index with counts and update dates |
| [`/api/v1/country/{cc}.json`](https://deadends.dev/api/v1/country/kr.json) | Per-country aggregate (one call returns all entries for that country) |
| [`/api/v1/openapi.json`](https://deadends.dev/api/v1/openapi.json) | OpenAPI 3.1 spec |
| [`/api/v1/stats.json`](https://deadends.dev/api/v1/stats.json) | Dataset quality metrics by domain |
| [`/api/v1/errors.ndjson`](https://deadends.dev/api/v1/errors.ndjson) | NDJSON streaming |
| [`/llms.txt`](https://deadends.dev/llms.txt) | LLM-optimized listing ([llmstxt.org](https://llmstxt.org)) |
| [`/dashboard/`](https://deadends.dev/dashboard/) | Data quality dashboard |

## Covered Domains (54)

### Code error domains (51)

| Domain | Errors | Examples |
|--------|--------|----------|
| Python | 88 | ModuleNotFoundError, TypeError, KeyError, MemoryError, RecursionError |
| Node | 70 | ERR_MODULE_NOT_FOUND, EACCES, EADDRINUSE, heap OOM, ERR_REQUIRE_ESM |
| Docker | 65 | no space left, exec format error, bind address in use, healthcheck |
| Kubernetes | 61 | CrashLoopBackOff, ImagePullBackOff, OOMKilled, RBAC forbidden, HPA |
| Git | 60 | failed to push, merge conflicts, detached HEAD, stash apply, tags |
| CUDA | 57 | OOM, device-side assert, NCCL, cuDNN, tensor device mismatch |
| Go | 54 | nil pointer, unused import, interface conversion, slice out of range |
| Java | 54 | NullPointerException, ClassNotFound, OutOfMemoryError, connection pool |
| Database | 52 | deadlock, connection pool, slow query, replication lag |
| AWS | 51 | AccessDenied, S3 NoSuchBucket, Lambda timeout, CloudFormation rollback |
| .NET | 50 | NullReferenceException, LINQ translation, DI circular, EF concurrency |
| ROS 2 | 50 | node spin, launch error, QoS mismatch, tf2 transform |
| TypeScript | 49 | TS2307, TS2322, TS2345, TS2532, TS7053 |
| Rust | 48 | E0382 borrow, E0308 mismatch, E0277 trait, E0106 lifetime |
| + 37 more domains | 40+ each | CI/CD, PHP, Terraform, Networking, Next.js, React, pip, Android, ... |

### Country-scoped real-world domains (new, growing)

| Domain | Covers | Example dead ends |
|--------|--------|-------------------|
| `visa` | Pre-travel authorization, overstay, re-entry bans | ESTA 90-day rule (US), K-ETA (KR), ETIAS/EES (Schengen), Schengen 90/180 (DE) |
| `banking` | Account opening, KYC, foreigner rules | ARC required (KR), residence card 6-month (JP), SSN/ITIN (US) |
| `emergency` | Correct emergency numbers, transit | 112 not 911 (DE), 999/101/111 (UK) |
| `medical` | Insurance, Rx import, coverage | Shaho/Kokuho (JP), NHIS 6-month (KR), EHIC ineligibility (DE), Adderall import ban (JP) |
| `legal` | Criminal liability, contract norms | §86a Nazi symbols (DE), Article 112 (TH), Article 301 (TR), alcohol ban (SA), key money (JP) |
| `culture` | Etiquette, taboos, social norms | Chopsticks in rice (JP), clock gifts (CN), Tiananmen silence, red ink names (KR), bonjour (FR) |
| `food-safety` | Water, pathogens, religious taboos | Tap water (MX), fugu license (JP), beef in India, pork in Indonesia |
| `communication` | Language register, terminology | Honorifics (KR), American War framing (VN), 'gringo' (MX), Cantonese vs Mandarin (HK) |
| `safety` | Driving, public-safety norms | Left-side drive (JP), Autobahn rules (DE), horn-language (IN) |

## Data Quality

All metrics are publicly available on the [Data Quality Dashboard](https://deadends.dev/dashboard/):

- **2,204** canon entries across **54** domains and **39+** countries
- **Benchmark**: 90% Precision@1, 95% Precision@3, 0.935 MRR (on code scenarios)
- **Error transition graph**: 4,330+ edges connecting related errors
- **Community feedback loop**: `report_outcome` updates fix success rates from real usage
- **Country canons**: every entry cites primary gov/embassy/regulator sources,
  reviewed by humans (`review_status: human_reviewed`), no LLM bulk generation

### Country coverage (39 countries as of v0.9)

`kr` · `jp` · `us` · `de` · `uk` · `fr` · `it` · `es` · `cn` · `hk` · `tw` ·
`th` · `in` · `vn` · `id` · `sg` · `ph` · `my` · `pk` · `sa` · `ae` · `tr` ·
`il` · `ru` · `br` · `mx` · `ar` · `co` · `pe` · `au` · `nz` · `eg` · `ma` ·
`et` · `ng` · `ke` · `ca` · `pl` · `at`

See [/country/](https://deadends.dev/country/) hub or
[/api/v1/countries.json](https://deadends.dev/api/v1/countries.json) for the
authoritative list with counts.

See [`docs/country-canon-guide.md`](docs/country-canon-guide.md) for the
authoring workflow, sourcing requirements, and confidence calibration.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for full details.
- GitHub 자동 수집 운영안: [`docs/GITHUB_DATA_COLLECTION_STRATEGY.md`](docs/GITHUB_DATA_COLLECTION_STRATEGY.md)
- 자동 수집 주기: 6시간마다(하루 4회), 기본 품질 필터: `min_score=2`
- 수집 데이터는 후보이며, 최종 반영은 maintainer 검수 후 진행

- [Submit a new error](https://github.com/dbwls99706/deadends.dev/issues/new?template=new_error.yml)
- [Report a workaround result](https://github.com/dbwls99706/deadends.dev/issues/new?template=update_workaround.yml)
- Use `report_outcome` via MCP after trying a workaround

## Development

```bash
pip install -e ".[dev]"

python -m generator.pipeline          # Full pipeline
python -m generator.build_site        # Build static site
python -m generator.validate          # Validate data + site
python -m pytest tests/ -v            # Run tests
ruff check generator/ tests/          # Lint
python benchmarks/run_benchmark.py    # Run benchmarks
```

## SEO 점검 가이드 (모든 페이지 공통)

아래 명령은 템플릿에 핵심 SEO 신호가 있는지 빠르게 점검합니다.

```bash
python - <<'PY'
from pathlib import Path
files=[
  'generator/templates/index.html',
  'generator/templates/domain.html',
  'generator/templates/error_summary.html',
  'generator/templates/page.html',
  'generator/templates/search.html',
  'generator/templates/dashboard.html',
]
required=[
  '<title',
  'meta name="description"',
  'meta name="robots"',
  'link rel="canonical"',
  'meta property="og:title"',
  'meta name="twitter:card"',
]
for f in files:
    txt=Path(f).read_text()
    missing=[r for r in required if r not in txt]
    print(f'✅ {f}' if not missing else f'❌ {f} missing: {", ".join(missing)}')
PY
```

실제 빌드 결과물까지 확인하려면:
```bash
python -m generator.build_site
python -m http.server -d public 8080
```

그 후 브라우저에서 아래를 점검:
- `view-source:http://localhost:8080/search/`
- `view-source:http://localhost:8080/dashboard/`
- canonical / og / twitter / JSON-LD 유효성

## Changelog

### v0.9.0 — Country pivot
- **New axis**: country-scoped real-world dead ends alongside code errors
- **56+ country canons** across 20+ countries — visa, banking, legal red
  lines, cultural taboos, food safety, emergency numbers, driving norms
- **3 new domains**: `visa`, `banking`, `emergency` (plus extended use of
  existing `legal`, `culture`, `medical`, `communication`, `food-safety`,
  `safety` domains with country env segment)
- **Per-country landing pages** at `/country/{cc}/` (e.g.
  [/country/jp/](https://deadends.dev/country/jp/))
- **`generator.country_canon_template`** helper for authoring new country
  canons with validated env-segment + audience + jurisdiction metadata
- **`docs/country-canon-guide.md`**: sourcing standards (primary > embassy
  > reputable media), confidence calibration, slug/regex conventions
- Schema unchanged (backward-compatible enum extensions); existing 2,089
  code canons preserved

### v0.8.0
- **Benchmark suite**: 20 error scenarios, Precision@1=90%, MRR=0.935
- **Data quality dashboard** at `/dashboard/` — transparent metrics
- **Outcome feedback loop**: `report_outcome` → aggregated stats → fix_success_rate updates
- **Usage analytics**: anonymous tool usage tracking (domain/match only, no PII)
- **Community contribution**: GitHub Issue templates for new errors and workaround reports
- **TF-IDF search**: improved relevance with smoothed IDF scoring
- **Error transition graph**: materialized graph with 4,330+ edges, hub node analysis
- **9 MCP tools** (added `report_outcome`)

### v0.7.0
- Expanded to **2089 error entries** across **51 domains** (from 1028/20)
- Added 23 new domains
- Fixed 73 regex patterns that didn't match their own signatures

### v0.5.0
- `page_url` field added to index.json, errors.ndjson, and all SDK/MCP responses
- SEO fixes for canonical summary URLs

### v0.4.0
- Initial public release with 1028 error entries across 20 domains

## License

MIT (code) · CC BY 4.0 (data)

## Ops Docs

- SEO 운영 가이드: [`docs/SEO_OPERATIONS_GUIDE.md`](docs/SEO_OPERATIONS_GUIDE.md)
- PyPI 릴리즈 매뉴얼: [`docs/PYPI_RELEASE_MANUAL.md`](docs/PYPI_RELEASE_MANUAL.md)

<!-- mcp-name: io.github.dbwls99706/deadends-dev -->
