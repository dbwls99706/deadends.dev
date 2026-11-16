# Backlink kit: MobinX/awesome-mcp-list (Knowledge & Memory)

Status: drafted, awaiting human submission (2026-11-16)

## Target

- Repo: https://github.com/MobinX/awesome-mcp-list
- File / section: `README.md`, `### 🧠 Knowledge & Memory` (README line ~688)
- Rules: https://github.com/MobinX/awesome-mcp-list/blob/main/CONTRIBUTING.md

## Why it fits

- CONTRIBUTING scope, verbatim: "Real **MCP servers** that people can run or
  connect to", "A **public GitHub repository** for the server (required)",
  "One clear category fit in the existing README sections".
  deadends.dev qualifies on all three: `mcp/server.py` (stdio, `pip install deadends-dev`)
  plus the hosted endpoint, public repo, and it is a knowledge base agents query.
- Comparable entries already in Knowledge & Memory:
  - `claimidx/claimidx`: "Prior-art failure index for coding agents."
  - `forecall/forecall-mcp`: "Stdio relay to the Forecall Failure KB, where
    agents look up known MCP tool failures and their workarounds..."
  Both are failure / workaround indexes for agents, which is what deadends.dev is.
- `deadends` does not appear in the README (searched the raw file 2026-11-16).
  Search again before you submit. CONTRIBUTING closes duplicates.

## Entry to add (exact format from CONTRIBUTING: three spaces after `-`, bold owner/repo, stars badge)

```markdown
-   **[dbwls99706/deadends.dev](https://github.com/dbwls99706/deadends.dev)** [![GitHub stars](https://img.shields.io/github/stars/dbwls99706/deadends.dev?style=social)](https://github.com/dbwls99706/deadends.dev): Structured failure knowledge for AI agents: known dead ends and working workarounds for code errors and country-specific rules (visas, banking, emergency numbers), with primary-source citations.
```

## Where to insert

The section is not alphabetical; new entries go at the end. Add the line as the
last bullet, **after**:

```
-   **[worktable/worktable-dev](https://github.com/worktable/worktable-dev)** ... Workspace for people and agents to create and revise docs, interactive HTML, drawings, records, and threads.
```

and before the blank line + `### ⚖️ Legal & Compliance`. If newer bullets have
landed since, append after whatever is last in the section. The diff must be
that single line, with no other edits.

## PR title (format from CONTRIBUTING: `Add owner/repo to <Category>`)

```
Add dbwls99706/deadends.dev to Knowledge & Memory
```

PR body (CONTRIBUTING asks for: what it does, repo URL, category chosen):

```
Adds dbwls99706/deadends.dev, an MCP server (stdio via `pip install deadends-dev`,
plus a hosted endpoint) that lets agents look up known dead ends and working
workarounds for code errors and country-specific rules, with primary-source citations.

Repo: https://github.com/dbwls99706/deadends.dev
Category: Knowledge & Memory (next to claimidx and forecall-mcp, which are also failure indexes for agents)
```

## Fork-and-edit URL

https://github.com/MobinX/awesome-mcp-list/edit/main/README.md

(GitHub forks on first save. Search the page for `worktable/worktable-dev`.)

## Notes

- If you mention the hosted endpoint, use `https://deadends-dev.vercel.app/mcp/`
  (the trailing slash is required). `https://deadends.dev/mcp` is dead; see the README.md tracker.
- Ruled out this run:
  - `jaw9c/awesome-remote-mcp-servers`: its Quality Criteria require OAuth 2.0
    or an API key and prefer "official" company servers, so an open endpoint on a
    vercel.app host would be a stretch.
  - `wong2/awesome-mcp-servers`: "We do not accept PRs". Its web form at
    https://mcpservers.org/submit is still open as a manual one-off.
  - `habitoai/awesome-mcp-servers`: has a Knowledge and Memory section and is a
    possible future target. Read its contribution rules first.
