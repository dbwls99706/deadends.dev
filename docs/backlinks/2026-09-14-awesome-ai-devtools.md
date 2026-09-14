# Backlink kit: jamesmurdza/awesome-ai-devtools

**Status:** drafted, awaiting human submission (this session's GitHub access
is scoped to `dbwls99706/*` repos and cannot fork or PR into someone else's
repo - see `docs/backlinks/README.md`).

## Target

Repo: [`jamesmurdza/awesome-ai-devtools`](https://github.com/jamesmurdza/awesome-ai-devtools)
("Awesome AI-Powered Developer Tools" - a large, actively-maintained curated
list, single `README.md`, default branch `main`)

Section: **`### Configuration & Context Management`** (under `## Agent
Infrastructure`)

## Why this fits

The list's own PR template states the scope directly:

> "This list is for developer tools exclusively. The following are NOT
> valid submissions: General purpose AI agents/assistants, General purpose
> AI frameworks, Data analysis tools."

deadends.dev is none of those three exclusions - it's a developer-focused
structured database, not an agent, a framework, or an analytics tool. The
`Configuration & Context Management` section's own description is "Tools
that manage and sync AI agent configurations, rules, and context across
editors," and in practice the section already holds several context/
knowledge-serving tools that (like deadends.dev) are consumed by agents
rather than being agents themselves:

> **AgentsKB** - "Knowledge base with 39K+ researched technical Q&As
> accessible via MCP server, REST API, or web search. Integrates with
> Claude Code, Cursor, and Cline."

deadends.dev is the same shape: a structured, source-cited knowledge base
(2,393+ entries vs. AgentsKB's 39K+ Q&As) served the same three ways - MCP
server, REST/JSON API - just scoped to *dead ends* (what not to try and
why) with fix-success-rated workarounds, rather than general Q&A. Two other
entries already in this section confirm knowledge-for-agents is an accepted
fit here, not just AgentsKB alone: **ContextMCP** ("self-hosted semantic
search across documentation... for AI agents") and **SwarmVault**
("local-first RAG knowledge vault and MCP server").

**Honest caveat for the human to weigh:** the PR checklist also asks the
submitter to confirm "The entry is a tool that uses AI." deadends.dev is
not itself an AI-*powered* runtime tool the way a code-completion or
review bot is. The honest basis for checking that box is that the
majority of the corpus (2,089 of 2,393+ entries - all 51 code-error
domains) is LLM-bulk-generated per `generator/bulk_generate.py`, and the
site's entire reason to exist is AI-agent consumption via its MCP server.
AgentsKB and SwarmVault, the closest comparables, appear to be accepted on
the same "AI-agent-facing knowledge tool" basis rather than "uses AI
internally" in a narrower sense. If the human reviewing this considers
that too much of a stretch for the checkbox, skip this target rather than
submit - the guide's instruction is not to force a fit that isn't honest.

## Exact line to add

Format matches other entries in the section (`- [Name](url) — Description
covering what it is, key numbers, and how agents access it.`):

```
- [deadends.dev](https://deadends.dev) — Structured, source-cited knowledge base of 2,393+ coding and country-specific real-world dead ends (what NOT to try and why, plus workarounds with fix-success rates) across 51 code-error domains and 52 countries. Free hosted MCP server (11 read tools) and JSON API, no auth required.
```

## Where to insert it

At the bottom of the `Configuration & Context Management` section - new
entries in this list are appended chronologically to the end of each
section rather than alphabetized (confirmed by reading the existing order,
which is not alphabetical). Insert immediately after the last current
entry in that section:

```
- [intelligence-sync](https://github.com/ainova-systems/intelligence-sync) — One source of truth for AI coding rules across every IDE. ...
+ [deadends.dev](https://deadends.dev) — Structured, source-cited knowledge base of 2,393+ coding and country-specific real-world dead ends ...
```

(`intelligence-sync` is the line immediately before the `### Usage
Analytics & Cost Tracking` section header - do not insert past that
header.)

## PR title

```
Add deadends.dev to Configuration & Context Management
```

No agent fast-track marker is documented for this repo (unlike
`punkpeye/awesome-mcp-servers`) - use a plain title.

## PR description (suggested)

```
Adds deadends.dev, a structured, source-cited knowledge base of coding and
country-specific real-world dead ends (2,393+ entries, 51 code-error
domains + 52 countries), served via a free MCP server (11 read tools) and
JSON API for AI coding agents.

Section: Configuration & Context Management, alongside comparable
agent-facing knowledge tools already listed there (AgentsKB, ContextMCP,
SwarmVault).
```

## Fork-and-edit URL

https://github.com/jamesmurdza/awesome-ai-devtools/edit/main/README.md

(Opening this while signed in auto-forks the repo and opens `README.md` in
the web editor at the right file/branch - scroll to the `Configuration &
Context Management` section, add the line above the `Usage Analytics &
Cost Tracking` header, then "Propose changes" to open the PR.)

## Execution checklist for the human

- [ ] Read the honest caveat above and decide whether the "uses AI"
      checkbox is defensible for this submission
- [ ] Open the fork-and-edit URL, add the line in the right spot
- [ ] Title and description as above
- [ ] Check the PR template's checklist items after reviewing the actual
      diff
- [ ] Update the status row in `docs/backlinks/README.md` to `submitted,
      awaiting review` (or `merged`/`rejected` once known) on the next
      weekly pass
