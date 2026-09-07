# Backlink kit: dastergon/awesome-sre

**Status:** drafted, awaiting human submission (this session's GitHub access
is scoped to `dbwls99706/*` repos and cannot fork or PR into someone else's
repo - see `docs/backlinks/README.md`).

## Target

Repo: [`dastergon/awesome-sre`](https://github.com/dastergon/awesome-sre)
Section: **`## Post-Mortem`** (`README.md`)

## Why this section fits

The section is not about postmortem *process* articles exclusively - it
already hosts structured collections of "what actually failed and why," e.g.:

> `[Collection of Kubernetes Failure Stories](https://github.com/hjacobs/kubernetes-failure-stories)`

That entry is a curated repo of real Kubernetes production incidents with
root causes - unstructured prose, one incident per write-up, single domain.
deadends.dev is the same genre at a structured, machine-readable scale:
source-cited entries covering *what not to try and why* plus *what actually
works*, across kubernetes/docker/terraform/networking and 50 other domains,
plus country-specific real-world dead ends. An SRE reading this list for
"collections of known failure modes" is the exact audience this section
already serves via the Kubernetes-failure-stories entry - deadends.dev just
isn't limited to one cloud-native subsystem.

## Exact line to add

Insert at the bottom of the `## Post-Mortem` section (per `CONTRIBUTING.md`:
*"Additions should go at the bottom of the relevant category"*), immediately
after the last existing entry:

```markdown
* [deadends.dev - a structured, source-cited database of coding and country-specific dead ends](https://deadends.dev)
```

**Line to insert after** (for diff/patch context - currently the last line in
the section):

```markdown
* [A collection of postmortem templates](https://github.com/dastergon/postmortem-templates)
```

**Line that follows the section** (do not insert past this):

```markdown
## Capacity Planning
```

Style note: entries in this section carry no separate description text past
the link title itself (e.g. `[Collection of Kubernetes Failure Stories](...)`,
`[Blameless PostMortems and a Just Culture](...)`) - the new line follows
that same convention rather than adding a trailing ` - description`.

## PR title

```
Add deadends.dev to Post-Mortem
```

No fast-track marker is documented in this repo's `CONTRIBUTING.md` - unlike
`punkpeye/awesome-mcp-servers`, there is no opt-in agent-PR convention here,
so don't invent one.

## PR description (suggested)

```
Adds deadends.dev to Post-Mortem: a structured, source-cited database of
2,393+ "dead end" entries - failure knowledge in the same spirit as
hjacobs/kubernetes-failure-stories (already listed in this section), but
spanning 51 code-error domains (kubernetes, docker, terraform, networking,
cicd...) plus country-specific real-world dead ends, each entry citing
primary sources for both the dead end and the working alternative.

One suggestion per PR per CONTRIBUTING.md; inserted at the bottom of the
category as instructed.
```

## Fork-and-edit URL

https://github.com/dastergon/awesome-sre/edit/master/README.md

(Opening this URL while signed in to a GitHub account prompts GitHub to
auto-fork the repo and open `README.md` directly in the web editor - search
for `postmortem-templates` to find the insertion point in the Post-Mortem
section.)

## Execution checklist for the human

- [ ] Open the fork-and-edit URL above, confirm the fork
- [ ] Find `A collection of postmortem templates` (Post-Mortem section),
      paste the new line immediately after it, before `## Capacity Planning`
- [ ] Commit directly on the fork's default branch (or a new branch) with
      message `Add deadends.dev to Post-Mortem`
- [ ] Open the PR back to `dastergon/awesome-sre`, title and description as
      above
- [ ] Update the status row in `docs/backlinks/README.md` to `submitted,
      awaiting review` (or `merged`/`rejected` once known) on the next
      weekly pass
