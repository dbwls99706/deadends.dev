# Backlink Submission Tracker

One kit is produced per weekly SEO run (see `docs/SEO_OPERATIONS_GUIDE.md` §5 -
backlinks are the dominant factor in Google's indexing decisions for a young
site, more so than any code-level SEO fix). The GitHub session this runs in is
scoped to `dbwls99706/*` repos only, so kits are executed by hand off this
tracker - see each kit file for the exact fork-and-edit link.

| Date | Target | Status | Kit |
| --- | --- | --- | --- |
| 2026-08-17 | punkpeye/awesome-mcp-servers (Knowledge & Memory) | drafted, awaiting human submission | [2026-08-17-awesome-mcp-servers.md](2026-08-17-awesome-mcp-servers.md) |
| 2026-08-24 | thedaviddias/llms-txt-hub (developer-tools) | drafted, awaiting human submission | [2026-08-24-llms-txt-hub.md](2026-08-24-llms-txt-hub.md) |
| 2026-08-31 | hesreallyhim/awesome-claude-code (Documentation, Knowledge & Learning) | drafted, awaiting human submission | [2026-08-31-awesome-claude-code.md](2026-08-31-awesome-claude-code.md) |

## Status values

- `drafted, awaiting human submission` - kit produced this run, PR not yet opened
- `submitted, awaiting review` - human opened the PR, no maintainer response yet
- `merged`
- `rejected` - note the reason so we don't retry the same pitch

## One-time channel (not part of the weekly drip)

**MCP Server Registry** (`registry.modelcontextprotocol.io`) - **done.** As
of 2026-08-24 the registry lists `dev.deadends/deadends-dev` at v0.9.0
(DNS-verified namespace, PyPI + HTTP transport), which supersedes an earlier
`io.github.dbwls99706/deadends-dev` v0.3.1 entry now marked deprecated in
favor of it. This was flagged "not yet published" as of 2026-08-17; it was
published sometime in the following week, presumably by a human off this
tracker. No further action needed on this channel.
