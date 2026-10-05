# Backlink kit: appcypher/awesome-mcp-servers

**Status:** drafted, awaiting human submission (this session's GitHub access
is scoped to `dbwls99706/*` repos and cannot fork or PR into someone else's
repo - see `docs/backlinks/README.md`).

## Target

Repo: [`appcypher/awesome-mcp-servers`](https://github.com/appcypher/awesome-mcp-servers)
(a different list from `punkpeye/awesome-mcp-servers`, which is already
merged - separate maintainers, separate audience, default branch `main`)

Section: **`## 🧬 Research & Data`** (README.md, ~line 352)

## Why this fits

The section's own scope line reads: *"Access to research papers, genetic
data, and specialized datasets."* deadends.dev's MCP server (11 read-only
lookup tools; one write tool, `report_outcome`) exposes a specialized,
primary-source-cited dataset (about 2.6k structured "dead end" records: what
not to try, and what works). It is a dataset served over MCP, not a general
dev utility.

Comparable entry already in the section:

> `[OpenNutrition](https://github.com/deadletterq/mcp-opennutrition) - Search 300,000+ foods, nutrition facts, and barcodes from the OpenNutrition database`

Same shape: a domain database queried through MCP tools. Fallback if a
maintainer prefers it: `## 💻 Development Tools`, next to the Mastra
"knowledge base" entry - but Research & Data is the honest primary fit, since
roughly half the corpus is non-code (country rules, legal, medical, etc.).

`CONTRIBUTING.md` rules checked: one PR per suggestion; add to the **bottom**
of the category; succinct description; no trailing whitespace; useful title.
(It also says "alphabetical", but the live section is not sorted - follow the
bottom-of-category rule, as existing entries do.)

## Line to add

Insert as the last bullet of `## 🧬 Research & Data`, immediately after the
`Congress` line and before the `<br />` that precedes `## 🤝 AI Services`:

```markdown
- <img src="https://deadends.dev/favicon.ico" height="14"/> [deadends.dev](https://github.com/dbwls99706/deadends.dev) - Search a database of documented dead ends (what NOT to try) and verified workarounds for code errors and country-specific real-world rules
```

Before submitting, confirm `https://deadends.dev/favicon.ico` resolves (200);
if it does not, drop the `<img>` tag and use a plain `- [deadends.dev](...) - ...`
bullet.

## PR title

`Add deadends.dev to Research & Data`

(No opt-in marker is defined in this repo's CONTRIBUTING.)

## Fork-and-edit URL

https://github.com/appcypher/awesome-mcp-servers/edit/main/README.md

(GitHub forks on first save, then offers "Propose changes" -> open PR.)
