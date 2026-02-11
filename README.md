# deadends.dev

**Structured failure knowledge for AI coding agents.**

143 error entries across 14 domains. When AI agents encounter errors, they waste tokens on approaches that are known to fail. deadends.dev tells agents what NOT to try, what actually works, and what error comes next.

## Installation

```bash
pip install deadends-dev
```

**Requirements:** Python 3.10+

## MCP Server

The MCP server exposes 3 tools for AI coding agents:

| Tool | Description |
|------|-------------|
| `lookup_error` | Match an error message against 143 known patterns. Returns dead ends, workarounds, and error chains. |
| `get_error_detail` | Get full details for a specific error by ID (e.g., `python/modulenotfounderror/py311-linux`). |
| `list_error_domains` | List all 14 error domains and their counts. |

### Local (Claude Desktop / Cursor)

Add to `~/.claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "deadend": {
      "command": "python",
      "args": ["-m", "mcp.server"],
      "cwd": "/path/to/deadend.dev"
    }
  }
}
```

### Hosted (Smithery)

Available on [Smithery](https://smithery.ai/server/deadend/deadends-dev) — no local setup required.

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
from generator.lookup import lookup

result = lookup("ModuleNotFoundError: No module named 'torch'")

# What NOT to try (saves tokens and time)
for d in result["dead_ends"]:
    print(f"AVOID: {d['action']} — fails {int(d['fail_rate']*100)}%")

# What actually works
for w in result["workarounds"]:
    print(f"TRY: {w['action']} — works {int(w['success_rate']*100)}%")
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
| [`/api/v1/index.json`](https://deadends.dev/api/v1/index.json) | Full error index with all metadata |
| `/api/v1/{domain}/{slug}/{env}.json` | Individual error canon |
| [`/api/v1/openapi.json`](https://deadends.dev/api/v1/openapi.json) | OpenAPI 3.1 spec |
| [`/llms.txt`](https://deadends.dev/llms.txt) | LLM-optimized error listing ([llmstxt.org](https://llmstxt.org) standard) |
| [`/llms-full.txt`](https://deadends.dev/llms-full.txt) | Complete database dump |
| [`/.well-known/ai-plugin.json`](https://deadends.dev/.well-known/ai-plugin.json) | AI plugin manifest |

## Covered Domains (14)

| Domain | Errors | Examples |
|--------|--------|----------|
| python | 33 | ModuleNotFoundError, TypeError, KeyError, MemoryError, AttributeError |
| node | 17 | ERR_MODULE_NOT_FOUND, EACCES, EADDRINUSE, ECONNREFUSED, heap OOM |
| docker | 14 | permission denied, no space left, exec format error, context too large |
| cuda | 11 | OOM, version mismatch, device-side assert, NCCL timeout, cuDNN |
| git | 10 | failed to push, merge conflicts, detached HEAD, cannot lock ref |
| pip | 8 | build wheel failed, conflicting deps, externally-managed-environment |
| go | 7 | undefined reference, declared not used, cannot convert, nil pointer |
| kubernetes | 7 | CrashLoopBackOff, ImagePullBackOff, OOMKilled, Evicted, ConfigError |
| typescript | 7 | TS2307, TS2322, TS2339, TS2304, TS2741, TS2345, TS7006 |
| aws | 6 | AccessDenied, ExpiredToken, NoCredentials, InvalidClientTokenId |
| react | 6 | invalid hook call, too many re-renders, unique key, objects not valid |
| rust | 6 | E0382 borrow, E0308 mismatch, E0277 trait, E0502, E0425, E0599 |
| terraform | 6 | state lock, provider not present, cycle, plugin crashed, invalid ref |
| nextjs | 5 | hydration failed, module not found, dynamic server, searchParams |

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

## AI Agent Integration

Every page on deadends.dev includes 8 machine-readable formats:

1. **JSON API** — RESTful error data at `/api/v1/{id}.json`
2. **match.json** — Compact regex-only file (load entire DB into context)
3. **JSON-LD** — Schema.org TechArticle + FAQPage in every `<head>`
4. **ai-summary** — `<pre id="ai-summary">` with KEY=VALUE pairs
5. **llms.txt** — [llmstxt.org](https://llmstxt.org) standard
6. **OpenAPI** — Full API specification
7. **ai-plugin.json** — Plugin discovery manifest
8. **robots.txt** — All AI crawlers explicitly welcomed

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

## License

MIT (code) · CC BY 4.0 (data)
