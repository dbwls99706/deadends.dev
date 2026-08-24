# Backlink kit: thedaviddias/llms-txt-hub

**Status:** drafted, awaiting human submission (this session's GitHub access
is scoped to `dbwls99706/*` repos and cannot fork or PR into someone else's
repo - see `docs/backlinks/README.md`).

## Target

Repo: [`thedaviddias/llms-txt-hub`](https://github.com/thedaviddias/llms-txt-hub)
(powers [llmstxthub.com](https://llmstxthub.com), a directory of sites that
publish an `llms.txt` file)

Entry location: a new `.mdx` file under
`packages/content/data/websites/` (per `.github/CONTRIBUTING.md`: *"Only add
or edit `.mdx` files under `packages/content/data/websites/`."* - the
sibling `data/websites.json` is auto-generated from these files at build
time and must not be hand-edited).

## Why this fits

deadends.dev ships both `https://deadends.dev/llms.txt` (index) and
`https://deadends.dev/llms-full.txt` (full data dump) - this isn't an
after-the-fact fit, it's literally the format this directory exists to
index. The hub's own scope, from its README: a catalog of "AI-ready
documentation" sites that implement the llms.txt standard, organized by
category.

Comparable existing entries confirm the format and a fitting category:

- `supabase-llms-txt.mdx` - category `developer-tools`, a developer-facing
  platform with both a normal product site and an `llms.txt`. deadends.dev
  is the same shape: a developer tool (MCP server + JSON API) consumed by
  AI coding agents, with its own `llms.txt`.
- `anthropic-llms-txt.mdx` - category `ai-ml`, also a plausible fit given
  deadends.dev's target audience is AI agents specifically.

`developer-tools` is the better-fitting of the two: deadends.dev is a
lookup/reference tool developers and their agents call into (like
Supabase's docs/API), not an AI model or research org (like Anthropic).

## Exact file to add

Path: `packages/content/data/websites/deadends-dev-llms-txt.mdx`

(Filename convention observed across existing entries is `{slugified
name}-llms-txt.mdx`, e.g. `abstract-api-llms-txt.mdx` for Abstract API,
`supabase-llms-txt.mdx` for Supabase. `deadends-dev` mirrors the site's own
name including its `.dev` TLD, which is how the project refers to itself
everywhere else (READMEs, package name). This is a naming convention, not a
schema-checked field - a maintainer renaming it on merge would not be a
rejection.)

Content (matches the frontmatter shape and body style of the sampled
entries above):

```mdx
---
name: 'deadends.dev'
description: 'Structured, source-cited database of coding and real-world dead ends for AI agents - what NOT to try and why, plus workarounds with fix-success rates.'
website: 'https://deadends.dev'
llmsUrl: 'https://deadends.dev/llms.txt'
llmsFullUrl: 'https://deadends.dev/llms-full.txt'
category: 'developer-tools'
publishedAt: '2026-08-24'
---

# deadends.dev

deadends.dev is a structured failure-knowledge database for AI agents:
2,393+ source-cited ErrorCanon entries across 51 code-error domains
(Python, Docker, CUDA, Kubernetes, Terraform, and more) plus
country-specific real-world dead ends (visa, banking, legal, medical) across
52 countries.

## Key Focus Areas

- Structured error/dead-end lookup for AI coding agents
- Country-specific real-world administrative and legal dead ends
- Fix-success-rate-scored workarounds, not just search results

## About llms.txt Implementation

Serves both `llms.txt` (index) and `llms-full.txt` (full data dump), plus a
free hosted MCP server at `https://deadends.dev/mcp` exposing 11 read tools
for error and country lookup. Also installable locally via
`pip install -e ".[mcp]"`.
```

## PR title

```
Add deadends.dev to developer-tools
```

No agent fast-track marker applies here (unlike `punkpeye/awesome-mcp-servers`,
this repo's `.github/CONTRIBUTING.md` does not document one) - use a normal
PR title.

## PR description (suggested)

```
Adds deadends.dev to the directory: a structured, source-cited
failure-knowledge database for AI agents (2,393+ entries) covering code
errors across 51 domains plus country-specific real-world dead ends across
52 countries. Ships both llms.txt and llms-full.txt, per this project's
scope.

Category: developer-tools (alongside comparable entries like Supabase -
a developer-facing tool with its own llms.txt, rather than an AI model/
research org like the ai-ml category).
```

## Two submission paths (per `.github/CONTRIBUTING.md`)

1. **Web form (recommended by the project):** submit via
   [llmstxthub.com](https://llmstxthub.com) after GitHub login - the site
   handles opening the PR itself.
2. **GitHub PR directly:** use the fork-and-edit URL below.

## Fork-and-edit URL

https://github.com/thedaviddias/llms-txt-hub/new/main/packages/content/data/websites?filename=deadends-dev-llms-txt.mdx

(Opening this URL while signed in prompts GitHub to auto-fork the repo and
open a new file at that exact path/name in the web editor - paste the mdx
content above and commit.)

## Execution checklist for the human

- [ ] Prefer the web form at llmstxthub.com if logging in there is easy;
      otherwise use the fork-and-edit URL above
- [ ] Paste the file content above, confirm the fork, commit
- [ ] Open the PR back to `thedaviddias/llms-txt-hub`, title and description
      as above
- [ ] Update the status row in `docs/backlinks/README.md` to `submitted,
      awaiting review` (or `merged`/`rejected` once known) on the next
      weekly pass
