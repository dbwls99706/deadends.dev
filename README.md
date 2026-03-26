# deadends.dev

<!-- mcp-name: dev.deadends/deadends-dev -->

[![Precision@1](https://img.shields.io/badge/Precision%401-90%25-brightgreen)](https://deadends.dev/dashboard/)
[![MRR](https://img.shields.io/badge/MRR-0.935-brightgreen)](https://deadends.dev/dashboard/)
[![Errors](https://img.shields.io/badge/errors-2089-blue)](https://deadends.dev)
[![Domains](https://img.shields.io/badge/domains-51-green)](https://deadends.dev)
[![MCP Tools](https://img.shields.io/badge/MCP_tools-9-purple)](https://smithery.ai/server/deadend/deadends-dev)
[![PyPI](https://img.shields.io/pypi/v/deadends-dev)](https://pypi.org/project/deadends-dev/)
[![License](https://img.shields.io/badge/license-MIT%20%2F%20CC%20BY%204.0-lightgrey)](LICENSE)

**Stop AI agents from repeating known failures.**

When AI coding agents hit an error, they waste tokens retrying approaches that are *known* to fail. deadends.dev gives agents instant access to what NOT to try, what actually works, and what error comes next — across 2,089 errors in 51 domains.

> **90% Precision@1** — the top lookup result matches the correct domain 9 out of 10 times.
> **0.935 MRR** — correct results consistently rank first.
> See the full [Data Quality Dashboard](https://deadends.dev/dashboard/).

> **Website:** [deadends.dev](https://deadends.dev) · **MCP Server:** [Smithery](https://smithery.ai/server/deadend/deadends-dev) · **PyPI:** [deadends-dev](https://pypi.org/project/deadends-dev/) · **API:** [/api/v1/index.json](https://deadends.dev/api/v1/index.json)

## Why Use This?

| Without deadends.dev | With deadends.dev |
|---------------------|-------------------|
| Agent tries `sudo pip install` → breaks system Python → wastes 3 retries | Agent sees "dead end: sudo pip — fails 70%" → skips it immediately |
| Agent googles, reads Stack Overflow, tries 4 approaches | Agent gets the 95%-success workaround on the first call |
| Agent fixes error A, gets confused by error B | Agent knows "A leads to B 78% of the time" → handles both |

**What makes this different from asking an LLM?**
- **Deterministic**: Same error → same answer, every time. No hallucination.
- **Community-validated**: Fix success rates are updated from real outcome reports.
- **Error chains**: Conditional probabilities (A→B) that LLMs can't provide.
- **Sub-millisecond**: Local regex matching, no API roundtrip.

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

## MCP Tools (9)

| Tool | Description |
|------|-------------|
| `lookup_error` | Match an error message against 2000+ known patterns |
| `get_error_detail` | Full canon by ID |
| `list_error_domains` | All 51 domains with counts |
| `search_errors` | TF-IDF keyword search across all domains |
| `list_errors_by_domain` | All errors in a domain |
| `batch_lookup` | Look up multiple errors at once (max 10) |
| `get_domain_stats` | Domain quality metrics and confidence levels |
| `get_error_chain` | Traverse the error transition graph |
| `report_outcome` | Report whether a workaround worked (feeds back into success rates) |

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| [`/api/v1/match.json`](https://deadends.dev/api/v1/match.json) | Lightweight regex matching (fits in context window) |
| [`/api/v1/index.json`](https://deadends.dev/api/v1/index.json) | Full error index with metadata |
| [`/api/v1/{id}.json`](https://deadends.dev/api/v1/python/modulenotfounderror/py311-linux.json) | Individual ErrorCanon |
| [`/api/v1/openapi.json`](https://deadends.dev/api/v1/openapi.json) | OpenAPI 3.1 spec |
| [`/api/v1/stats.json`](https://deadends.dev/api/v1/stats.json) | Dataset quality metrics by domain |
| [`/api/v1/errors.ndjson`](https://deadends.dev/api/v1/errors.ndjson) | NDJSON streaming |
| [`/llms.txt`](https://deadends.dev/llms.txt) | LLM-optimized listing ([llmstxt.org](https://llmstxt.org)) |
| [`/dashboard/`](https://deadends.dev/dashboard/) | Data quality dashboard |

## Covered Domains (51)

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

## Data Quality

All metrics are publicly available on the [Data Quality Dashboard](https://deadends.dev/dashboard/):

- **2,089** error entries across **51** domains
- **Benchmark**: 90% Precision@1, 95% Precision@3, 0.935 MRR
- **Error transition graph**: 4,330+ edges connecting related errors
- **Community feedback loop**: `report_outcome` updates fix success rates from real usage

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for full details.

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

## Changelog

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

<!-- mcp-name: io.github.dbwls99706/deadends-dev -->
