# Backlink kit: punkpeye/awesome-remote-mcp-servers

**Status:** drafted, awaiting human submission (this session's GitHub access
is scoped to `dbwls99706/*` repos and cannot fork or PR into someone else's
repo - see `docs/backlinks/README.md`).

## Target

Repo: [`punkpeye/awesome-remote-mcp-servers`](https://github.com/punkpeye/awesome-remote-mcp-servers)
(~2.4k stars; the remote-server sibling of `punkpeye/awesome-mcp-servers`,
which already lists deadends.dev). Different list, different README: this one
only takes *hosted* servers reachable over a URL.

Section: **`### 🧠 Knowledge & Memory`** (README line ~2561).

## Why this fits

`CONTRIBUTING.md`, "What belongs here":

> This list is for **remote** MCP servers: servers the provider hosts, that
> you connect to over a URL.

deadends.dev runs a public, anonymous, Streamable-HTTP MCP endpoint (Vercel
function `api/mcp.py`) serving a read-only failure-knowledge base. Each
requirement checked on 2026-11-02:

| Requirement | Status |
| --- | --- |
| Answers an MCP `initialize` over a public URL | Yes at `https://deadends-dev.vercel.app/mcp/` (HTTP 200, `serverInfo.name = deadends-dev`). **See endpoint warning below.** |
| Usable by anyone | Yes, no sign-up, no key (🔓) |
| Streamable HTTP or SSE | Yes, JSON-RPC over POST |
| Listed as a Glama connector | Yes, `https://glama.ai/mcp/connectors/dev.deadends/deadends-dev` (page and `badges/score.svg` both return 200) |

Comparable entries already in Knowledge & Memory: **Agents Handbook**
("sourced playbooks for real jobs done with AI agents: ... known failures and
fixes"), **AIeph** ("a shared cache of past answers to programming
questions"), **AbuzzHive** (Q&A boards for problems agents are stuck on).

Honest caveat: deadends.dev is a curated read-only knowledge base, not a
user-writable memory store. The three comparables above are the same shape, so
the category fits; if the maintainer prefers another section (Developer
Tools), move it rather than argue.

## ENDPOINT WARNING - read before submitting

`https://deadends.dev/mcp` (the URL in `server.json`, the MCP Registry entry,
the README and every earlier kit) **does not work**. `deadends.dev` is served by
GitHub Pages: `GET /mcp` returns 404 and `POST /mcp` returns `405 Not Allowed`
from GitHub's edge. The Vercel function only answers on:

```
https://deadends-dev.vercel.app/mcp/      (trailing slash required; without it: 308)
https://deadends-dev.vercel.app/api/mcp/
```

This list's CI posts `initialize` to the endpoint on every PR, so the entry
below uses the Vercel URL. Longer term, either point a `mcp.` subdomain at
Vercel and update `server.json` + the registry entry, or remove the
`https://deadends.dev/mcp` remote. Until then the earlier kits (awesome-mcp-servers
family, best-of-mcp-servers) should not be submitted with the dead URL either.

## Pre-flight

1. Star the repository with the account that opens the PR - **PRs from
   unstarred accounts are not merged.**
2. `deadends` appears nowhere in the README as of 2026-11-02 (searched the raw
   file). Re-search before submitting.
3. Re-run the `initialize` POST above if more than a few days pass.

## PR title

`CONTRIBUTING.md` fast-tracks agent PRs whose title ends in `🤖🤖🤖`. A human
opening the PR does not need it; add it only if an agent opens the PR.

```
Add deadends.dev
```

(or `Add deadends.dev 🤖🤖🤖` for an agent-opened PR)

## Entry to add (3 lines, exact format)

```markdown
- [deadends.dev](https://deadends.dev) `https://deadends-dev.vercel.app/mcp/`
  [![deadends.dev MCP connector](https://glama.ai/mcp/connectors/dev.deadends/deadends-dev/badges/score.svg)](https://glama.ai/mcp/connectors/dev.deadends/deadends-dev)
  🔓 - Look up known dead ends and verified workarounds for code errors and country-specific rules before acting.
```

(Description is 106 characters, under the 120 limit, ends with a period.)

## Where to insert

Alphabetical, case-insensitive. Insert **after** the `ctxstore` entry
(3 lines; README ~lines 2608-2610, ending
`... one memory across every model.`) and **before** `Detextit`.

## Fork-and-edit URL

https://github.com/punkpeye/awesome-remote-mcp-servers/edit/main/README.md

(GitHub forks on first save. Search the page for `ctxstore`.)
