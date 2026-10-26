# Backlink kit: tolkonepiu/best-of-mcp-servers

**Status:** drafted, awaiting human submission (this session's GitHub access
is scoped to `dbwls99706/*` repos and cannot fork or PR into someone else's
repo - see `docs/backlinks/README.md`).

## Target

Repo: [`tolkonepiu/best-of-mcp-servers`](https://github.com/tolkonepiu/best-of-mcp-servers)
(a "best-of" list of 400 MCP servers, ranked automatically by a project-quality
score from GitHub/PyPI metrics). Different from the awesome-mcp-servers lists
already used: entries live in `projects.yaml`, and the README is generated.

Category: **`knowledge-and-memory`** (README section "Knowledge & Memory",
subtitle *"MCP servers for knowledge graphs and memory management"*).

## Why this fits (and where it is weaker)

The category subtitle is the scope: *"MCP servers for knowledge graphs and
memory management."* deadends.dev is a read-only MCP server (hosted at
`https://deadends.dev/mcp` and runnable locally from PyPI) serving a curated
knowledge base of failed approaches and verified workarounds. Comparable
entries already in the category: `apecloud/ApeRAG` (knowledge-graph RAG for
"Context Engineering") and `chopratejas/headroom` (context layer for AI agents).

Honest caveats:
- It is a curated knowledge base, not a user-writable memory store. If the
  maintainer wants memory-store semantics only, withdraw rather than argue.
- The list ranks by quality score, so a young repo will land low in the
  section. That is fine; the goal is the crawlable link.
- `CONTRIBUTING.md` says to edit `projects.yaml` only, never `README.md`.

## Pre-flight

`deadends` appears nowhere in `projects.yaml` or the README as of 2026-10-26.
Re-search before submitting.

## PR title

CONTRIBUTING requires `Add project: project-name`:

```
Add project: dbwls99706/deadends.dev
```

(One project per PR; no opt-in marker is defined by this project.)

## Entry to add (`projects.yaml`)

```yaml
  - name: dbwls99706/deadends.dev
    github_id: dbwls99706/deadends.dev
    pypi_id: deadends-dev
    description: >-
      Structured failure-knowledge database for AI agents: source-cited dead
      ends (what not to try, and why) and workarounds with fix-success rates
      for code errors and country-specific real-world rules. Hosted endpoint
      at https://deadends.dev/mcp.
    category: knowledge-and-memory
```

## Where to insert

In the `projects:` list, directly after the `chopratejas/headroom` block
(ends with `category: knowledge-and-memory`) and before
`- name: entanglr/zettelkasten-mcp` (around line 1766 of the file).

## Fork-and-edit URL

https://github.com/tolkonepiu/best-of-mcp-servers/edit/main/projects.yaml
(GitHub offers to fork and open the PR from the editor.)
