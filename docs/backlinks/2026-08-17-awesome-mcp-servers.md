# Backlink kit: punkpeye/awesome-mcp-servers

**Status:** drafted, awaiting human submission (this session's GitHub access
is scoped to `dbwls99706/*` repos and cannot fork or PR into someone else's
repo - see `docs/backlinks/README.md`).

## Target

Repo: [`punkpeye/awesome-mcp-servers`](https://github.com/punkpeye/awesome-mcp-servers)
Section: **`🧠 Knowledge & Memory`** (`README.md`, `<a name="knowledge--memory">`, currently starts around line 2195)

## Why this section fits

The section's own blurb is broader in practice than its one-line description
("Persistent memory storage using knowledge graph structures. Enables AI
models to maintain and query structured information across sessions.") -
it already hosts several entries that are shared, cross-session knowledge
bases of failure/dead-end information rather than single-agent session
memory, e.g.:

- `cg3-llc/prior_mcp`: *"Shared knowledge base where AI agents exchange
  proven solutions — including failed approaches, so your agent skips the
  dead ends."*
- `Ikalus1988/MisakaNet`: *"Agent failure memory network. Search 235+
  verified debugging lessons from real engineering sessions."*
- `andreas-roennestad/openhive-mcp`: *"Shared knowledge base where AI agents
  search and post problem-solution pairs."*

deadends.dev is the same category at a larger, curated scale: 2,393+
structured, source-cited entries (not agent-submitted/unverified) across 51
code-error domains plus 52 countries of non-code dead ends, served over a
free hosted MCP endpoint. `prior_mcp` in particular is the closest comparable
- same "skip the dead ends" pitch - which is why the insertion point below
sits right next to it.

## Exact line to add

Insert as a new line immediately **after** the `cg3-llc/prior_mcp` line (the
section is not strictly alphabetized in practice - see note below - so this
placement was chosen for topical adjacency to the closest comparable entry,
not alphabetical order):

```markdown
- [dbwls99706/deadends.dev](https://github.com/dbwls99706/deadends.dev) 🐍 ☁️ 🏠 - Structured failure-knowledge database for AI agents: 2,393+ source-cited error canons across 51 code-error domains (Python, Docker, CUDA, Kubernetes, Terraform...) plus country-specific real-world dead ends (visa, banking, legal, medical) across 52 countries. Tools return dead ends (what NOT to try, and why) and workarounds with fix-success rates, not just search results. Free hosted endpoint, no signup: `https://deadends.dev/mcp`. Also runs locally via `pip install -e ".[mcp]"`.
```

**Line to insert after** (for the diff / patch context):

```markdown
- [cg3-llc/prior_mcp](https://github.com/cg3-llc/prior_mcp) [![cg3-llc/prior_mcp MCP server](https://glama.ai/mcp/servers/cg3-llc/prior_mcp/badges/score.svg)](https://glama.ai/mcp/servers/cg3-llc/prior_mcp) 📇 ☁️ - Shared knowledge base where AI agents exchange proven solutions — including failed approaches, so your agent skips the dead ends. Smaller models get instant access to frontier-model discoveries. Free to search indefinitely when feedback is provided on results. [Website](https://prior.cg3.io)
```

No glama.ai score badge is included in the new line - deadends.dev is not
listed on glama.ai, and a badge pointing at a nonexistent glama entry would
render broken. Several existing entries in this same section (e.g.
`0xshellming/mcp-summarizer`, `agentic-mcp-tools/memora`) omit the badge for
the same reason, so this is within the section's existing convention.

Emoji legend used (from the README's own `## Legend`): 🐍 = Python codebase,
☁️ = cloud service, 🏠 = local service (deadends.dev's MCP server ships as a
stdio Python package **and** is hosted as a Vercel serverless endpoint, so
both apply).

## Note on alphabetical order

`CONTRIBUTING.md` states *"maintain alphabetical order within each category
of servers"*, but the actual `Knowledge & Memory` section is not
alphabetized in practice (sampled consecutive entries: `cdeust`,
`contradictory-body`, `celiums`, `cg3-llc`, `CanopyHQ`, `Cavinooo`,
`chatmcp`, `vshulcz`, `ZengLiangYi`, `CheMiguel23`...). Placing the new line
next to its closest topical comparable (`prior_mcp`) is a reasonable,
defensible choice; a maintainer doing a pass on order would not have grounds
to reject on this basis alone since the surrounding list already violates
the stated rule.

## PR title

```
Add deadends.dev - structured dead-end knowledge base for AI agents 🤖🤖🤖
```

The trailing `🤖🤖🤖` is `CONTRIBUTING.md`'s documented opt-in marker: *"If you
are an automated agent, we have a streamlined process for merging agent PRs.
Just add `🤖🤖🤖` to the end of the PR title to opt-in. Merging your PR will be
fast-tracked."* Only use this marker if the human submitting genuinely wants
the fast-tracked-agent-PR review path; drop it for a normal human review if
preferred.

## PR description (suggested)

```
Adds deadends.dev to Knowledge & Memory: a structured, source-cited
failure-knowledge database (2,393+ entries) for AI coding agents - code
error dead ends across 51 domains plus country-specific real-world dead
ends across 52 countries. MCP server exposes 11 read tools (lookup, search,
domain/country stats, error transition graph) plus one write tool
(report_outcome). Free hosted endpoint at https://deadends.dev/mcp, MIT
licensed, also installable via `pip install -e ".[mcp]"` for local stdio use.

Inserted in Knowledge & Memory next to cg3-llc/prior_mcp, the closest
existing comparable ("shared knowledge base... so your agent skips the dead
ends").
```

## Fork-and-edit URL

https://github.com/punkpeye/awesome-mcp-servers/edit/main/README.md

(Opening this URL while signed in to a GitHub account prompts GitHub to
auto-fork the repo and open the file directly in the web editor at the
insertion point - scroll/search for `cg3-llc/prior_mcp` to find line ~2263.)

## Execution checklist for the human

- [ ] Open the fork-and-edit URL above, confirm the fork
- [ ] Find `cg3-llc/prior_mcp`, paste the new line immediately after it
- [ ] Commit directly on the fork's default branch (or a new branch, either
      works with GitHub's edit-in-place flow) with message `Add new deadends.dev server`
- [ ] Open the PR back to `punkpeye/awesome-mcp-servers`, title and
      description as above
- [ ] Update the status row in `docs/backlinks/README.md` to `submitted,
      awaiting review` (or `merged`/`rejected` once known) on the next
      weekly pass
