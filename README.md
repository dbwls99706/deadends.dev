# deadends.dev

<!-- mcp-name: dev.deadends/deadends-dev -->

[![Errors](https://img.shields.io/badge/errors-2089-blue)](https://deadends.dev)
[![Domains](https://img.shields.io/badge/domains-51-green)](https://deadends.dev)
[![MCP Tools](https://img.shields.io/badge/MCP_tools-8-purple)](https://smithery.ai/server/deadend/deadends-dev)
[![PyPI](https://img.shields.io/pypi/v/deadends-dev)](https://pypi.org/project/deadends-dev/)
[![License](https://img.shields.io/badge/license-MIT%20%2F%20CC%20BY%204.0-lightgrey)](LICENSE)

**Structured failure knowledge for AI coding agents.**

2000+ error entries across 51 domains. When AI coding agents encounter errors, they waste tokens on approaches that are known to fail. deadends.dev tells agents what NOT to try, what actually works, and what error comes next.

> **Website:** [deadends.dev](https://deadends.dev) · **MCP Server:** [Smithery](https://smithery.ai/server/deadend/deadends-dev) · **PyPI:** [deadends-dev](https://pypi.org/project/deadends-dev/) · **API:** [/api/v1/index.json](https://deadends.dev/api/v1/index.json)

## Installation

```bash
pip install deadends-dev
```

**Requirements:** Python 3.10+

## MCP Server

The MCP server exposes 8 tools for AI coding agents:

| Tool | Description |
|------|-------------|
| `lookup_error` | Match an error message against 2000+ known patterns. Returns dead ends, workarounds, and error chains. |
| `get_error_detail` | Get full details for a specific error by ID (e.g., `python/modulenotfounderror/py311-linux`). |
| `list_error_domains` | List all 50 error domains and their counts. |
| `search_errors` | Fuzzy keyword search across all domains (e.g., "memory limit", "permission denied"). |
| `list_errors_by_domain` | List all errors in a specific domain, sorted by fix rate, name, or confidence. |
| `batch_lookup` | Look up multiple error messages at once (max 10). |
| `get_domain_stats` | Get quality metrics for a domain: avg fix rate, resolvability, confidence breakdown. |
| `get_error_chain` | Traverse the error transition graph: what errors follow, precede, or get confused with this one. |

### Local (Claude Desktop / Cursor)

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

### Hosted (Smithery — no local setup)

Install via [Smithery](https://smithery.ai/server/deadend/deadends-dev):

```bash
# Claude Code
npx -y @smithery/cli@latest install deadend/deadends-dev --client claude

# Cursor
npx -y @smithery/cli@latest install deadend/deadends-dev --client cursor
```

Or connect directly: `https://server.smithery.ai/deadend/deadends-dev`

### Example Response

When an agent encounters `ModuleNotFoundError: No module named 'torch'`, the `lookup_error` tool returns:

```
## ModuleNotFoundError: No module named 'X' (Python 3.11+)
Resolvable: true | Fix rate: 0.88

### Dead Ends (DO NOT TRY):
- pip install X with system Python (fails 70%): venv not activated

### Workarounds (TRY THESE):
- Create venv, activate, then pip install (works 95%)
- Use python -m pip install instead of bare pip (works 90%)
```

## Quick Start — Python SDK

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

# result["url"] is the canonical summary page URL (e.g. /python/modulenotfounderror/)
print(result["url"])

# Batch lookup (multiple errors at once)
results = batch_lookup([
    "ModuleNotFoundError: No module named 'torch'",
    "CUDA error: out of memory",
    "CrashLoopBackOff",
])

# Keyword search
hits = search("memory limit", domain="docker", limit=5)
```

## Quick Start — CLI

```bash
pip install deadends-dev
deadends "CUDA error: out of memory"
deadends --list  # show all known errors
```

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| [`/api/v1/match.json`](https://deadends.dev/api/v1/match.json) | Lightweight regex matching (fits in context window) |
| [`/api/v1/index.json`](https://deadends.dev/api/v1/index.json) | Full error index — includes `page_url` (canonical summary page) |
| [`/api/v1/{domain}/{slug}/{env}.json`](https://deadends.dev/api/v1/python/modulenotfounderror/py311-linux.json) | Individual ErrorCanon ([example](https://deadends.dev/api/v1/python/modulenotfounderror/py311-linux.json)) |
| [`/api/v1/openapi.json`](https://deadends.dev/api/v1/openapi.json) | OpenAPI 3.1 spec with response examples |
| [`/api/v1/stats.json`](https://deadends.dev/api/v1/stats.json) | Dataset quality metrics by domain |
| [`/api/v1/errors.ndjson`](https://deadends.dev/api/v1/errors.ndjson) | NDJSON streaming — includes `page_url` (canonical summary page) |
| [`/api/v1/version.json`](https://deadends.dev/api/v1/version.json) | Service metadata and endpoint directory |
| [`/llms.txt`](https://deadends.dev/llms.txt) | LLM-optimized error listing ([llmstxt.org](https://llmstxt.org) standard) |
| [`/llms-full.txt`](https://deadends.dev/llms-full.txt) | Complete database dump |
| [`/.well-known/ai-plugin.json`](https://deadends.dev/.well-known/ai-plugin.json) | AI plugin manifest |
| [`/.well-known/agent-card.json`](https://deadends.dev/.well-known/agent-card.json) | Google A2A agent card |
| [`/.well-known/security.txt`](https://deadends.dev/.well-known/security.txt) | Security contact (RFC 9116) |

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
| Database | 52 | deadlock, connection pool, slow query, replication lag, constraint violation |
| AWS | 51 | AccessDenied, S3 NoSuchBucket, Lambda timeout, CloudFormation rollback |
| .NET | 50 | NullReferenceException, LINQ translation, DI circular, EF concurrency |
| ROS 2 | 50 | node spin, launch error, QoS mismatch, tf2 transform, action server |
| TypeScript | 49 | TS2307, TS2322, TS2345, TS2532, TS7053, TS2769, TS18048 |
| Rust | 48 | E0382 borrow, E0308 mismatch, E0277 trait, E0106 lifetime, E0507 |
| CI/CD | 47 | GitHub Actions timeout, secret not found, Docker rate limit, cache miss |
| PHP | 47 | headers already sent, too many connections, autoload, memory exhaustion |
| Terraform | 46 | state lock, cycle, provider not found, moved block, backend init |
| Networking | 44 | connection refused, ECONNRESET, SSL certificate, DNS timeout, EPIPE |
| Next.js | 44 | hydration failed, dynamic server, server-only import, RSC serialization |
| React | 44 | invalid hook call, too many re-renders, unique key, context, act() |
| pip | 41 | build wheel failed, conflicting deps, externally-managed, hash mismatch |
| Android | 40 | Gradle OOM, AAPT2, manifest merger, ProGuard, Jetifier |
| API | 40 | rate limiting, CORS, 413 payload, GraphQL N+1, pagination |
| Cloud | 40 | IAM denied, VPC peering, NAT gateway, auto-scaling, CDN cache |
| CMake | 40 | find_package, target link, CXX standard, toolchain, FetchContent |
| Communication | 40 | WebSocket close, MQTT disconnect, gRPC deadline, AMQP channel |
| Data | 40 | schema evolution, CDC lag, Spark shuffle, Parquet type mismatch |
| Elasticsearch | 40 | circuit breaker, mapping explosion, split brain, shard allocation |
| Embedded | 40 | stack overflow, HardFault, SPI/I2C error, watchdog reset, DMA |
| Flutter | 40 | setState disposed, RenderFlex overflow, Gradle build, platform channel |
| gRPC | 40 | UNAVAILABLE, DEADLINE_EXCEEDED, TLS handshake, message size |
| Hugging Face | 40 | model load OOM, tokenizer mismatch, PEFT, flash attention |
| Kafka | 40 | rebalance, offset commit, ISR shrink, schema registry, KRaft |
| LLM | 40 | prompt injection, token limit, hallucination, rate limit, embedding dimension |
| MongoDB | 40 | BSON size, write concern, oplog, aggregation memory, change stream |
| Nginx | 40 | upstream timeout, proxy_pass, SSL config, try_files, location order |
| OpenCV | 40 | assertion failed, codec error, channel mismatch, DNN inference |
| Policy | 40 | rate limit, quota exceeded, size limit, API version, billing |
| PyTorch | 40 | CUDA OOM, tensor device, DDP init, autocast, checkpoint load |
| Redis | 40 | CLUSTERDOWN, memory limit, persistence, ACL, pub/sub message loss |
| Security | 40 | CSP violation, XSS, SQL injection, SSRF, JWT none algorithm |
| TensorFlow | 40 | shape mismatch, GPU memory, SavedModel, mixed precision NaN |
| Unity | 40 | NullReference, shader compile, asset bundle, NavMesh, physics |
| Culture | 67 | cultural taboos, political sensitivity, etiquette violations, identity |
| Safety | 7 | grease fire, chemical mixing, CPR, choking, electrical shock, tourniquet |
| Medical | 3 | drug interactions, folk remedies, allergic reactions |
| Mental Health | 2 | suicide response protocol, depression toxic positivity |
| Food Safety | 2 | raw chicken washing, rice room temperature |
| Disaster | 2 | earthquake doorframe myth, tornado overpass myth |
| Legal | 2 | self-defense law variation, copyright fair use myth |
| Pet Safety | 2 | dog toxic foods, cat toxic plants |

## ErrorCanon Data Format

Each error is a JSON file with:

```json
{
  "error": { "signature": "...", "regex": "...", "domain": "..." },
  "verdict": { "resolvable": "true|partial|false", "fix_success_rate": 0.88 },
  "dead_ends": [{ "action": "...", "why_fails": "...", "fail_rate": 0.75 }],
  "workarounds": [{ "action": "...", "success_rate": 0.92, "how": "..." }],
  "transition_graph": { "leads_to": [...], "preceded_by": [...] }
}
```

## AI Coding Agent Integration — 18 Discovery Formats

Every page on deadends.dev includes machine-readable data in 18 formats:

| Format | Location | Purpose |
|--------|----------|---------|
| JSON API | `/api/v1/{id}.json` | RESTful error data per ErrorCanon |
| match.json | `/api/v1/match.json` | Compact regex-only file (load entire DB into context) |
| index.json | `/api/v1/index.json` | Master error index with metadata; each entry has `page_url` pointing to the canonical summary page |
| stats.json | `/api/v1/stats.json` | Dataset quality metrics per domain |
| errors.ndjson | `/api/v1/errors.ndjson` | Streaming NDJSON for batch processing; each record has `page_url` for the canonical summary page |
| OpenAPI | `/api/v1/openapi.json` | Full API spec with response examples |
| JSON-LD | Every `<head>` | Schema.org TechArticle + FAQPage |
| ai-summary | Every page | `<pre id="ai-summary">` KEY=VALUE blocks |
| llms.txt | `/llms.txt` | llmstxt.org standard |
| llms-full.txt | `/llms-full.txt` | Complete database dump |
| ai-plugin.json | `/.well-known/` | OpenAI plugin manifest |
| agent-card.json | `/.well-known/` | Google A2A protocol |
| security.txt | `/.well-known/` | RFC 9116 security contact |
| robots.txt | `/robots.txt` | 34 AI crawlers explicitly welcomed |
| CLAUDE.md | `/CLAUDE.md` | Claude Code instructions |
| AGENTS.md | `/AGENTS.md` | OpenAI Codex CLI instructions |
| .clinerules | `/.clinerules` | Cline AI instructions |

## Development

```bash
pip install -e ".[dev]"

# Full pipeline (validate → generate → build → test)
python -m generator.pipeline

# Individual steps
python -m generator.bulk_generate     # Generate canons from seeds
python -m generator.build_site        # Build static site
python -m generator.validate          # Validate data + site
python -m pytest tests/ -v            # Run tests
```

## Contributing

Add error definitions to `generator/bulk_generate.py` or create JSON files directly in `data/canons/`.

```bash
python -m generator.validate --data-only  # Validate before submitting
```

## Changelog

### v0.7.0
- Expanded to **2089 error entries** across **51 domains** (from 1028/20)
- Added 23 new domains: Android, API, Cloud, CMake, Communication, Data, Elasticsearch, Embedded, Flutter, gRPC, Hugging Face, Kafka, LLM, MongoDB, Nginx, OpenCV, Policy, PyTorch, Redis, ROS 2, Security, TensorFlow, Unity
- All domains now have 40+ error entries each
- Fixed 73 regex patterns that didn't match their own signatures

### v0.5.0
- **`page_url` field** added to `index.json`, `errors.ndjson`, and all SDK/MCP responses — always points to the canonical summary page (`/domain/slug/`), distinct from the env-specific `url` field
- **Lookup SDK** `url` return value now points to the canonical summary page instead of the env-specific page
- **MCP tools** (`match_error`, `get_error_detail`) now return canonical summary URLs
- **SEO fixes**: Atom feed, IndexNow submissions, JSON-LD TechArticle, and Open Graph tags all corrected to use canonical summary URLs
- **Error chain links** in HTML templates corrected to point to summary pages rather than noindex env pages

### v0.4.0
- Initial public release with 1028 error entries across 20 domains

## License

MIT (code) · CC BY 4.0 (data)

<!-- mcp-name: io.github.dbwls99706/deadends-dev -->
