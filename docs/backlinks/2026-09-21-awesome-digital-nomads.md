# Backlink kit: cbovis/awesome-digital-nomads

**Status:** drafted, awaiting human submission (this session's GitHub access
is scoped to `dbwls99706/*` repos and cannot fork or PR into someone else's
repo - see `docs/backlinks/README.md`).

## Target

Repo: [`cbovis/awesome-digital-nomads`](https://github.com/cbovis/awesome-digital-nomads)
("Awesome Digital Nomads" - a `sindresorhus/awesome`-badged curated list,
single `README.md`, default branch `master`, 1.1k stars / 108 forks)

Section: **`## Travel Planning`**

## Why this fits

This list's four prior kits all targeted developer/agent-tooling lists
(MCP servers, llms.txt, Claude Code, AI devtools) plus one incident-response
list (awesome-sre). deadends.dev is not only a coding-error database though
- roughly half its 54 domains are country-scoped real-world content (visa,
banking, emergency, legal, food-safety, culture, disaster, mental-health,
policy, safety, communication across 52 countries), which is exactly this
list's subject, not a stretch into it.

The `Travel Planning` section already holds general-purpose,
country-spanning travel-information resources that are the direct
comparison for what deadends.dev is:

> **VisaHQ** - "Easily find visa requirements for most countries around the
> world."

> **Numbeo** - "The world's largest database of user contributed data about
> cities and countries. Find information such as cost of living, housing
> indicators, health care, traffic, crime and pollution for your next
> destination."

> **The Basetrip** - "Essential information for your next destination and
> how it compares to your home country."

deadends.dev is the same shape - a lookup database spanning many
countries - but for a gap none of those three cover: primary-source-cited
*mistakes travelers and AI assistants make* (e.g. "you cannot buy an
anonymous prepaid SIM in Morocco," "Vietnam has no SMS disaster alert, it's
a Zalo app," "a WhatsApp customs-fee PIX request is always a scam in
Brazil") rather than baseline visa/cost/crime stats. The list's own
`Travel Visas` section (currently a single Brazil-only entry) shows country
bureaucracy content is in scope too, but `Travel Planning` is the better
fit since deadends.dev spans more than visas.

**Honest caveat for the human to weigh:** the repo shows roughly 50 open
pull requests and no visible recent-commit timestamp - the maintainer may
be slow, so this may sit unmerged for a while longer than the other kits.
That's a merge-speed risk, not a fit problem; the content match above holds
regardless.

## Exact line to add

Format matches `contributing.md` and every existing entry (`[name](link) -
Description.`, hyphen separator, capitalized start, period end):

```
- [deadends.dev](https://deadends.dev) - Structured, source-cited database of country-specific travel pitfalls - visa traps, SIM/banking registration rules, real emergency numbers, food-safety and cultural risks - across 52 countries, free to search or query via API/MCP.
```

## Where to insert it

At the bottom of `## Travel Planning`, immediately after the last current
entry and before the `## Insurance` header:

```
- [Quanto Custa Viajar](https://quantocustaviajar.com/) - Information about how much it costs to travel for a specific place. In PT-BR.
+ [deadends.dev](https://deadends.dev) - Structured, source-cited database of country-specific travel pitfalls - visa traps, SIM/banking registration rules, real emergency numbers, food-safety and cultural risks - across 52 countries, free to search or query via API/MCP.
```

## PR title

```
Add deadends.dev to Travel Planning
```

No agent fast-track marker is documented for this repo - use a plain title,
matching the contributing guide's own instruction: "a useful title and
include a link to the thing you're submitting and why it should be
included."

## PR description (suggested)

```
Adds deadends.dev to Travel Planning: a structured, source-cited database
of country-specific travel dead ends - visa caveats, banking/SIM
registration quirks, real (not assumed) emergency numbers, food-safety and
cultural-taboo rules, cited to primary government/embassy sources - across
52 countries. Free to browse, and queryable via a JSON API / MCP server for
travelers using AI assistants.

Comparable in shape to VisaHQ and Numbeo already in this section, but
focused on primary-sourced mistakes/misconceptions rather than baseline
visa or cost-of-living stats.
```

## Fork-and-edit URL

https://github.com/cbovis/awesome-digital-nomads/edit/master/README.md

(Opening this while signed in auto-forks the repo and opens `README.md` in
the web editor at the right file/branch - scroll to `## Travel Planning`,
add the line above the `## Insurance` header, then "Propose changes" to
open the PR.)

## Execution checklist for the human

- [ ] Read the merge-speed caveat above (roughly 50 open PRs already)
- [ ] Open the fork-and-edit URL, add the line in the right spot
- [ ] Title and description as above
- [ ] Update the status row in `docs/backlinks/README.md` to `submitted,
      awaiting review` (or `merged`/`rejected` once known) on the next
      weekly pass
