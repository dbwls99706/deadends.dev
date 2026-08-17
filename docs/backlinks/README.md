# Backlink Submission Tracker

One kit is produced per weekly SEO run (see `docs/SEO_OPERATIONS_GUIDE.md` §5 -
backlinks are the dominant factor in Google's indexing decisions for a young
site, more so than any code-level SEO fix). The GitHub session this runs in is
scoped to `dbwls99706/*` repos only, so kits are executed by hand off this
tracker - see each kit file for the exact fork-and-edit link.

| Date | Target | Status | Kit |
| --- | --- | --- | --- |
| 2026-08-17 | punkpeye/awesome-mcp-servers (Knowledge & Memory) | drafted, awaiting human submission | [2026-08-17-awesome-mcp-servers.md](2026-08-17-awesome-mcp-servers.md) |

## Status values

- `drafted, awaiting human submission` - kit produced this run, PR not yet opened
- `submitted, awaiting review` - human opened the PR, no maintainer response yet
- `merged`
- `rejected` - note the reason so we don't retry the same pitch

## One-time channel (not part of the weekly drip)

**MCP Server Registry** (`registry.modelcontextprotocol.io`) has **not** been
published to yet as of 2026-08-17. Unlike everything above, this isn't a PR to
someone else's repo - the official `modelcontextprotocol/servers` README
retired its third-party list in favor of this registry, and publishing is a
CLI flow (`mcp-publish` / the registry's own CLI) against deadends.dev's own
package, authenticated via the PyPI verification path since deadends.dev ships
on PyPI. That makes it the one high-value channel not blocked by this
session's cross-owner GitHub scoping. Flagging once here as a to-do for a
human or a future session with registry-publish tooling; do not attempt it as
part of the weekly drip.
