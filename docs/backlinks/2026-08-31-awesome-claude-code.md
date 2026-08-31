# Backlink kit: hesreallyhim/awesome-claude-code

**Status:** drafted, awaiting human submission (this session's GitHub access
is scoped to `dbwls99706/*` repos and cannot fork or PR into someone else's
repo - see `docs/backlinks/README.md`). This target is also unusual in that
the maintainer requires the **web issue form**, not a PR at all - see below.

## Target

Repo: [`hesreallyhim/awesome-claude-code`](https://github.com/hesreallyhim/awesome-claude-code)
- a curated "Awesome Claude Code" list of slash-commands, CLAUDE.md files,
  workflows, MCP servers, and knowledge resources for Claude Code users.

Entry location: **not a file edit.** Per `CONTRIBUTING.md`:

> "NOTE: ALL RECOMMENDATIONS MUST BE MADE USING THE WEB UI ISSUE FORM
> TEMPLATE, OR YOU RISK BEING RESTRICTED FROM INTERACTING WITH THIS
> REPOSITORY TEMPORARILY." / "Do not open a PR. Just fill out the form."

A bot reads the issue form and updates the README itself - there is no
markdown to hand-author here, only form fields (below).

## Why this fits

Category dropdown value (exact text from the issue template):
`Documentation, Knowledge & Learning`

deadends.dev is exactly that: a structured, source-cited knowledge base an
AI coding agent queries before attempting a fix, shipped as both an MCP
server and a JSON API - which is the delivery shape this category already
rewards. The closest existing entry in that same category is:

> **NotebookLM MCP** by Romain Peyrichou - "A mature MCP server (plus a
> 33-endpoint REST API) that drives Google NotebookLM for citation-backed
> Q&A and full Studio generation... Notably well-maintained and
> security-attentive."

deadends.dev is the same shape - an MCP server plus REST/JSON API providing
citation-backed answers - just for "what NOT to try and why" instead of
NotebookLM Q&A. If a citation-backed MCP knowledge server belongs in this
list once, a second one in the same category is not a stretch.

Maturity bar (issue form requires one of the two):
- 14+ days of active development with commits beyond day one - the repo
  (`dbwls99706/deadends.dev`) was created 2026-02-10 and has had commits
  multiple times a week since, so this is clearly met.
- (100+ stars is the alternative path; current star count is 0, so the repo
  qualifies on activity, not stars - don't claim the stars criterion.)

## Exact form fields to submit

Open the issue form (link below) and fill in:

| Field | Value |
| --- | --- |
| Display Name | `deadends.dev` |
| Category | `Documentation, Knowledge & Learning` |
| Link | `https://github.com/dbwls99706/deadends.dev` |
| Author Name | `dbwls99706` |
| Author Link | `https://github.com/dbwls99706` |
| Description | see below |

Description (1-3 sentences, 10-500 chars, descriptive not promotional, per
the form's own rule - this is 353 chars):

```
A structured, source-cited database of 2,393+ coding and country-specific real-world dead ends, served via an MCP server and JSON API. Covers 51 code-error domains (Python, Docker, Kubernetes, Terraform) and real-world entries (visa, banking, legal, medical) across 52 countries, each with dead-end actions, sourced workarounds, and fix-success rates.
```

The form also has a required checklist (personally reviewed the repo,
verified the link works, verified Claude Code relevance, read
CONTRIBUTING.md, attesting honesty) - the human submitter checks these
after actually opening the linked repo, not blindly.

## No PR title / fast-track marker applies

Unlike `punkpeye/awesome-mcp-servers`, this project explicitly forbids PRs
for this purpose - the three-robots marker convention doesn't apply here at
all, and using it would violate this repo's contribution rule.

## Fork-and-edit URL (not applicable) / issue form URL

https://github.com/hesreallyhim/awesome-claude-code/issues/new?template=recommend-resource.yml

## Execution checklist for the human

- [ ] Open the issue form URL above (requires being signed into GitHub)
- [ ] Fill in the five fields exactly as in the table above
- [ ] Check the confirmation checklist only after actually visiting
      `github.com/dbwls99706/deadends.dev` and confirming the link resolves
- [ ] Submit - a bot validates formatting and (per CONTRIBUTING.md) a
      maintainer merges it into the README from there, no further PR step
- [ ] Update the status row in `docs/backlinks/README.md` to `submitted,
      awaiting review` (or `merged`/`rejected` once known) on the next
      weekly pass
