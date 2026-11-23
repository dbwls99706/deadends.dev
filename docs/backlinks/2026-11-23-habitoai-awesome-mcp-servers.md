# Backlink kit: habitoai/awesome-mcp-servers (Knowledge and Memory)

Status: drafted, awaiting human submission (2026-11-23)

## Target

- Repo: https://github.com/habitoai/awesome-mcp-servers (24 stars, last push 2026-10-06, not a fork)
- File / section: `README.md`, `### Knowledge and Memory` (README line ~843)
- Rules: https://github.com/habitoai/awesome-mcp-servers/blob/main/CONTRIBUTING.md

## Why it fits

- CONTRIBUTING criteria, verbatim: "It is actively maintained", "It implements
  the Model Context Protocol", "It has documentation", format
  `- [Project Name](link) - Brief description`.
  deadends.dev meets all three: `mcp/server.py` (stdio, `pip install deadends-dev`)
  plus the hosted endpoint, weekly commits, and README + site docs.
- Comparable entries already in Knowledge and Memory:
  - `DrDroidLab/open-index`: "Structured context graph for domain-specific
    agents with hybrid search and validated read/write MCP tools."
  - `stonianua/neither-mcp`: "Hosted company/project context via local stdio MCP
    ... source-backed retrieve. [Homepage](...)"
  Both are curated, source-backed knowledge that agents query over MCP, which is what deadends.dev is.
- Two existing entries (AccInt, Neither) end with a `[Homepage](...)` link, so
  the entry can link deadends.dev directly, not just the GitHub repo. That is
  the part that matters for Google.
- `deadends` does not appear in the README (searched the raw file 2026-11-23).
  CONTRIBUTING asks you to check for duplicates, so search again before you submit.

## Entry to add

```markdown
- [deadends.dev](https://github.com/dbwls99706/deadends.dev) - Structured database of known dead ends for AI agents, covering code errors and country-specific rules (visas, banking, emergency numbers). Each entry lists the fixes that fail, the workarounds that work and primary-source citations. [Homepage](https://deadends.dev)
```

## Where to insert

CONTRIBUTING says "Maintain alphabetical order within sections". Insert the
line directly **after**:

```
- [Basic Memory](https://github.com/basicmachines-co/basic-memory) - Basic Memory is a knowledge management system ...
```

and **before**:

```
- [Goal Story](https://github.com/hichana/goalstory-mcp) - Manages aspirations through narrative-driven goal setting ...
```

(Alphabetically, B < d < G; the existing sort ignores case.) The diff must be
that single line, with no other edits.

## PR title

The repo does not ask for a title format or an agent marker. Use:

```
Add deadends.dev to Knowledge and Memory
```

PR body:

```
Adds deadends.dev, an MCP server (stdio via `pip install deadends-dev`, plus a
hosted Streamable HTTP endpoint at https://deadends-dev.vercel.app/mcp/) that
lets agents look up known dead ends and working workarounds for code errors and
country-specific rules, with primary-source citations. MIT licensed.

Repo: https://github.com/dbwls99706/deadends.dev
Placed alphabetically in Knowledge and Memory.
```

## Fork-and-edit URL

https://github.com/habitoai/awesome-mcp-servers/edit/main/README.md

(GitHub forks on first save. Search the page for `basicmachines-co/basic-memory`.)

## Notes

- If you mention the hosted endpoint, use `https://deadends-dev.vercel.app/mcp/`
  (the trailing slash is required). It answered `tools/list` on 2026-11-23.
  `https://deadends.dev/mcp` is dead; see the README.md tracker.
- Ruled out this run (do not retry without a changed situation):
  - `kyrolabs/awesome-agents` (Memory - Knowledge Management): CONTRIBUTING
    auto-closes repos "without demonstrated traction". `dbwls99706/deadends.dev`
    has **0 stars / 0 forks**, and the smallest comparable in that section has 162.
    Revisit if the repo gains stars. The star count blocks every list with a traction bar.
  - `AlexMili/Awesome-MCP` (AI, Agents & Memory): its "is it really an MCP
    server?" test asks whether the project loses its purpose without the MCP
    server. deadends.dev would not: the site, JSON API and Python SDK stand on
    their own. Off-topic under that rule.
  - `SecretiveShell/Awesome-llms-txt`: a perfect scope fit with no bar. But the entry
    must link `/llms.txt`, which our robots.txt disallows for Googlebot, so it gives
    almost no Google value. It is a low-effort AI-discovery link to add any time,
    after the line for `datadrivenmarketer.me`:
    `- [deadends.dev (full)](https://deadends.dev/llms-full.txt)` then
    `- [deadends.dev](https://deadends.dev/llms.txt)`.
  - `jaw9c/awesome-remote-mcp-servers`: re-checked, and it is still ruled out. CONTRIBUTING
    says auth "Must be OAuth 2.0", and the endpoint is on a `vercel.app` host.
