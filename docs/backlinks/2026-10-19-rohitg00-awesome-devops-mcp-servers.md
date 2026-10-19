# Backlink kit: rohitg00/awesome-devops-mcp-servers

**Status:** drafted, awaiting human submission (this session's GitHub access
is scoped to `dbwls99706/*` repos and cannot fork or PR into someone else's
repo - see `docs/backlinks/README.md`).

## Target

Repo: [`rohitg00/awesome-devops-mcp-servers`](https://github.com/rohitg00/awesome-devops-mcp-servers)
(a DevOps-focused MCP list, distinct from the three general `awesome-mcp-servers`
lists already used).

Section: **`## AI Agent Infrastructure` > `### 🧠 Memory & Context`**
(README line ~359).

## Why this fits (and where it is weaker)

The section's scope line: *"Tools for persistent memory, context management, and
knowledge retention for AI agents."* deadends.dev is a read-only knowledge base
agents query over MCP for failed approaches and verified workarounds. Comparable
entries already there are agent-knowledge servers, e.g. `vectorize-io/hindsight`
and `eidetic-works/nucleus-mcp` ("persistent memory and execution context ... for
AI IDEs").

Honest caveat: CONTRIBUTING requires "DevOps focus". deadends.dev is not
DevOps-only (about half the corpus is country-scoped real-world rules). The
DevOps-relevant slice is real, though: docker, kubernetes, terraform, aws, cicd,
git, nginx, kafka, redis and cloud canons. The line below leads with that slice.
If a maintainer pushes back on scope, drop it rather than argue.

Not present in the README as of 2026-10-19 (`grep -ci deadends` = 0).

## Line to add

Format per CONTRIBUTING: `[name](link) language_icon scope_icon - Description`.
Legend: 🐍 Python, 🏠 local service. The section is not alphabetical; append
after the last bullet (`qualixar/superlocalmemory`), before `### 💰 API Cost Management`.

```markdown
- [dbwls99706/deadends.dev](https://github.com/dbwls99706/deadends.dev) 🐍 🏠 - Read-only knowledge base of documented dead ends (what NOT to try) and verified workarounds for AI agents. Covers DevOps failures (Docker, Kubernetes, Terraform, AWS, CI/CD, nginx, Kafka) plus country-specific real-world rules. Install: `pip install deadends-dev`, run `deadends-mcp` (stdio). Official Registry: `dev.deadends/deadends-dev`.
```

## PR title

`Add deadends.dev to Memory & Context`

(No opt-in marker defined by this repo.)

## Fork-and-edit URL

https://github.com/rohitg00/awesome-devops-mcp-servers/edit/main/README.md

## Also worth five minutes (no PR needed)

`wong2/awesome-mcp-servers` states "We do not accept PRs"; submissions go through
the form at https://mcpservers.org/submit. Not tracked as a kit; submit by hand if
not already listed.
