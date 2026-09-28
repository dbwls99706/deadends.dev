# Backlink kit: alihesari/awesome-relocation

**Status:** drafted, awaiting human submission (this session's GitHub access
is scoped to `dbwls99706/*` repos and cannot fork or PR into someone else's
repo - see `docs/backlinks/README.md`).

## Target

Repo: [`alihesari/awesome-relocation`](https://github.com/alihesari/awesome-relocation)
("A curated list of practical resources for tech workers moving abroad:
visa-sponsored job boards, housing, banking, tax, healthcare and country
guides" - `sindresorhus/awesome`-badged, single `README.md`, default branch
`main`)

Section: **`## Country Guides`**

## Why this fits

The repo's own scope line is: *"A curated list of practical resources for
tech workers moving to another country: job boards, sponsor lists, housing,
banking, tax, healthcare and country guides."* deadends.dev's country-scoped
domains - visa, banking, legal, medical, emergency, food-safety, culture,
disaster, mental-health, policy, safety, communication across 52 countries -
map directly onto exactly that list of concerns (banking, tax/legal,
healthcare) rather than a tangential category like "Communities" or
"Language and Integration."

`CONTRIBUTING.md` states the inclusion bar plainly: resources must "help
with the move itself: finding a sponsoring employer, or settling in once
you arrive." deadends.dev's entire country-canon content is about exactly
the "settling in" mistakes that cost people time or money (e.g. Morocco
SIM registration, Japan hanko requirements, US ESTA 90-day limits) - it is
squarely inside that bar, not a stretch.

Comparable entries already in `## Country Guides`:

> **Handbook Germany** - "Government-funded guide to work, housing, health
> and paperwork in Germany."

> **Citizens Information** - "Irish public service explaining rights,
> benefits, housing and healthcare."

**Honest caveat for the human to weigh:** every existing entry in this
section is a single-country official/government portal, while deadends.dev
is a third-party, multi-country structured database (52 countries) rather
than an official source for any one of them. The fit is on subject matter
and "settling-in" purpose, not on being a government site - flagging this
so the human can judge whether the maintainer draws that line strictly.
Separately, the repo itself is small (0 stars, 1 fork, 1 open PR as of this
run) - real topical fit, but this link carries less domain authority than
some of the earlier weekly picks (e.g. awesome-mcp-servers, 1.1k+ stars).
Low PR volume does mean less competition and a plausibly faster review.

## Exact line to add

Format matches `CONTRIBUTING.md` (`- [Name](https://link) - One sentence
ending in a period.`, alphabetical order, description must not start with
the entry name, plain English, no marketing copy, only claims the linked
page itself makes):

```
- [deadends.dev](https://deadends.dev) - Source-cited database of country-specific pitfalls covering visas, banking, legal rules, healthcare and emergencies across 52 countries.
```

## Where to insert it

Alphabetically between `Citizens Information` and `Foreign Residents
Support Portal` (`d` sorts after `C` and before `F`):

```
- [Citizens Information](https://www.citizensinformation.ie) - Irish public service explaining rights, benefits, housing and healthcare.
+ [deadends.dev](https://deadends.dev) - Source-cited database of country-specific pitfalls covering visas, banking, legal rules, healthcare and emergencies across 52 countries.
- [Foreign Residents Support Portal](https://www.moj.go.jp/isa/support/portal/index.html) - Japanese government portal for foreign residents, with multilingual life information.
```

## PR title

```
Add deadends.dev to Country Guides
```

No agent fast-track marker is documented for this repo; `CONTRIBUTING.md`
gives no PR-title format requirement beyond the entry format itself, so a
plain descriptive title is correct.

## PR description (suggested)

```
Adds deadends.dev to Country Guides: a source-cited, structured database of
country-specific "dead ends" - visa caveats, banking/SIM registration
quirks, legal rules, healthcare payment norms, and real emergency numbers -
across 52 countries, built primarily from government and embassy sources.
Free to browse, plus a JSON API and MCP server for AI assistants helping
someone relocate.

One resource per this PR, per CONTRIBUTING.md. Description follows the
required format (does not start with the name, no marketing language,
ends in a period) and the entry is placed in alphabetical order.
```

## Fork-and-edit URL

https://github.com/alihesari/awesome-relocation/edit/main/README.md

(Opening this while signed in auto-forks the repo and opens `README.md` in
the web editor at the right file/branch - scroll to `## Country Guides`,
insert the line between `Citizens Information` and `Foreign Residents
Support Portal`, then "Propose changes" to open the PR.)

## Execution checklist for the human

- [ ] Read the two honest caveats above (official-source norm in this
      section; low star count on the target repo)
- [ ] Open the fork-and-edit URL, add the line in the right spot
- [ ] Title and description as above
- [ ] Update the status row in `docs/backlinks/README.md` to `submitted,
      awaiting review` (or `merged`/`rejected` once known) on the next
      weekly pass
