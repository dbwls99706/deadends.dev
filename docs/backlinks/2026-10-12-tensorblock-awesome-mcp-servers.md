# Backlink kit: TensorBlock/awesome-mcp-servers

**Status:** drafted, awaiting human submission (this session's GitHub access
is scoped to `dbwls99706/*` repos and cannot fork or PR into someone else's
repo - see `docs/backlinks/README.md`).

## Target

Repo: [`TensorBlock/awesome-mcp-servers`](https://github.com/TensorBlock/awesome-mcp-servers)
(a third, separate list from `punkpeye/` (merged) and `appcypher/` (drafted);
it backs a hosted MCP Index API, so listings are also machine-consumed).

Section: **`docs/knowledge-management--memory.md`** ("Knowledge Management &
Memory"). The README holds no entries itself; they live in `docs/*.md`.

## Why this fits

The section's scope line reads: *"Servers connecting to personal knowledge
bases, flashcard apps, building/querying knowledge graphs, or providing
persistent memory for LLMs."* deadends.dev is a read-only knowledge base that
agents query over MCP for what NOT to try plus verified workarounds. It is not
personal memory, but the section already lists the same kind of entry:

> `claimidx/claimidx` - "Prior-art failure index for agents - a signed claim index of failures other agents have already paid to solve."
> `masondelan/selvedge` - "Record and retrieve coding decisions, reasons, and rejected approaches..."
> `Dedale-Project/remnant-connect` - "Search prior technical agent experience ... failed approaches, and reported outcomes before trying a solution."

Not found in the file as of 2026-10-12 (`grep -i deadends` = 0 hits).

Repo rules (README "How to Participate"): one markdown bullet in the best
category page, format
`- [Server Name](https://github.com/owner/repo): description. Install: ...`;
search for duplicates first; open a PR. An issue form
(`add-mcp-server.yml`) is the alternative and auto-drafts the PR.

## Line to add

Entries are not alphabetical; recent ones sit at the top. Insert directly
after the section's intro line (line 3) and its blank line, as the first
bullet, before `marstudio360/vibedna-journal-mcp`:

```markdown
- [deadends.dev](https://github.com/dbwls99706/deadends.dev): Read-only knowledge base of documented dead ends (what NOT to try) and verified workarounds, about 2,600 primary-source-cited entries covering code errors and country-specific real-world rules. Install: `pip install deadends-dev`; launch: `deadends-mcp`. Transport: stdio. Auth: none. Official Registry: `dev.deadends/deadends-dev`. Site: https://deadends.dev.
```

(Check `pyproject.toml` for the license and append it if the list wants it. `https://deadends.dev/mcp` returned 404 on 2026-10-12, so the hosted endpoint is deliberately left out.)

## PR title

`Add deadends.dev to Knowledge Management & Memory`

(No opt-in marker defined by this repo.)

## Fork-and-edit URL

https://github.com/TensorBlock/awesome-mcp-servers/edit/main/docs/knowledge-management--memory.md

Alternative with no fork: https://github.com/TensorBlock/awesome-mcp-servers/issues/new?template=add-mcp-server.yml
