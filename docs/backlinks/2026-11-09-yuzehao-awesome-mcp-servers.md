# Backlink kit: YuzeHao2023/Awesome-MCP-Servers (Research & Data)

Status: drafted, awaiting human submission (2026-11-09)

## Target

- Repo: https://github.com/YuzeHao2023/Awesome-MCP-Servers (~1.1k stars)
- File / section: `README.md`, `## Category: Research & Data (🧬)` (README line ~436)

## Why it fits

- Section scope, verbatim: "Papers, datasets, and domain data."
- deadends.dev is a structured, primary-source-cited dataset (failure
  knowledge for code errors and country-specific rules) exposed over MCP, i.e.
  "domain data".
- Comparable entries already in the section: `OpenNutrition` (nutrition
  dataset), `Congress (legislative data)`, `ArXiv`.
- The README states no inclusion criteria or CONTRIBUTING file (CONTRIBUTING.md
  returns 404 as of 2026-11-09), so there is no auth/"official" gate like
  jaw9c/awesome-remote-mcp-servers has. That list was considered and rejected
  today: its Quality Criteria require OAuth or API key, and deadends.dev's
  endpoint is open.
- `deadends` does not appear in the README (searched raw file 2026-11-09).
  Re-search before submitting.

## Entry to add (format: `- Name — URL`, em dash, no description)

```markdown
- deadends.dev (failure knowledge: dead ends & workarounds) — https://github.com/dbwls99706/deadends.dev
```

(If the maintainer prefers a plain name, shorten to `- deadends.dev — https://github.com/dbwls99706/deadends.dev`.)

## Where to insert

The section is not alphabetical. Append as the last bullet, **after**
`- Congress (legislative data) — https://github.com/amurshak/congressMCP` and
before the blank line + `---` that precedes `## Category: Development Tools`.

## PR title

```
Add deadends.dev to Research & Data
```

## Fork-and-edit URL

https://github.com/YuzeHao2023/Awesome-MCP-Servers/edit/main/README.md

(GitHub forks on first save. Search the page for `congressMCP`.)

## Notes

- The README lists the repo URL for most entries; remote endpoint, if wanted
  instead, is `https://deadends-dev.vercel.app/mcp/` (trailing slash required;
  `https://deadends.dev/mcp` is dead - see README.md tracker).
- Also checked and ruled out today: `wong2/awesome-mcp-servers` ("We do not
  accept PRs" - submission is the web form at https://mcpservers.org/submit,
  a possible manual one-off for the human); `yzfly/Awesome-MCP-ZH` (Chinese-language list).
