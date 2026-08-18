---
description: Author new country/code canons, open a PR, and merge it once CI is green (one full content-growth cycle)
---

# /add-canon — one content-growth cycle

Goal: **grow indexable, non-duplicate content** on deadends.dev, one small PR at
a time. SEO survival depends on a steady drip of genuinely new, primary-sourced
pages — not bulk dumps of near-identical entries.

Run this end to end. Do not stop after authoring; the cycle is only done when
the PR is **merged** (or you have reported a hard blocker).

Argument (optional): `$ARGUMENTS` may name a target, e.g. `visa jp`,
`banking br`, `emergency pl`, or a domain like `legal`. If empty, pick the gap
yourself in step 3 — but run step 2 either way, so you do not collide with a
cycle already in flight.

---

## 1. Start from a clean, fresh branch

A merged PR is finished — never reuse its branch. Always cut a new one from
`main`:

```bash
git fetch origin main
git checkout -B canon/$(git log -1 --format=%cd --date=format:%Y%m%d origin/main)-$RANDOM origin/main
```

Prefer a descriptive name once you know the topic, e.g.
`canon/visa-jp-work-permit`. Confirm `git config user.email` is
`yujinhong3@gmail.com` before committing.

## 2. Claim a target no open PR is already working on

`main` is not the whole picture. Other cycles may be running right now with
branches already pushed, and their canons will not show up in any count of
`data/canons/`. Three separate PRs once authored New Zealand coverage at the
same time because each of them looked only at `main`.

List the open PRs and the files they touch **before** choosing anything:

```bash
# mcp__github__list_pull_requests (state: open), then for each PR:
# mcp__github__pull_request_read (method: get_files)
```

Treat every country and every canon ID appearing in an open PR as taken. Pick a
different country. Keep the list of touched canon IDs to hand - step 6 needs it.

## 3. Pick a real coverage gap (never duplicate)

Count what already exists, then choose an underserved slice:

```bash
python - <<'PY'
import json, collections, pathlib
root = pathlib.Path("data/canons")
per_country = collections.Counter()
per_domain = collections.Counter()
slugs = set()
for f in root.rglob("*.json"):
    try:
        c = json.loads(f.read_text())
    except Exception:
        continue
    cid = c.get("id", "")
    parts = cid.split("/")
    if len(parts) != 3:
        continue
    domain, slug, env = parts
    slugs.add((domain, slug, env))
    per_domain[domain] += 1
    if len(env) == 2 or (len(env) > 3 and env[2] == "-"):
        per_country[env.split("-")[0]] += 1
print("countries (fewest first):", per_country.most_common()[:-16:-1])
print("domains  (fewest first):", per_domain.most_common()[:-16:-1])
print("total canons:", len(slugs))
PY
```

Selection rules:

- Prefer **country canons** (`visa`, `banking`, `emergency`, `legal`,
  `culture`, `medical`, `food-safety`, `safety`, `policy`, `disaster`,
  `communication`, `mental-health`) over code canons — that is where generic
  LLM answers are wrong and where the site has a defensible moat.
- Target countries near the bottom of the count, or a high-traffic country
  with an obvious untouched topic.
- The country code **must already be in** `SUPPORTED_COUNTRIES`
  (`generator/country_canon_template.py`). If you want a new country, add it
  there in the same PR.

Then check for duplicates **by topic, not by slug**. A different slug describing
the same dead end is still a duplicate, and the site is penalised for it. Read
what the country already has before writing:

```bash
python - <<'PY'
import json, pathlib
CC = "nz"  # your target country
for f in sorted(pathlib.Path("data/canons").rglob(f"{CC}.json")):
    c = json.loads(f.read_text())
    print(c["id"])
    print("   ", c["error"]["signature"])
    print("   ", c["verdict"]["summary"][:160])
PY
```

For each canon you intend to write, name the existing entry it is closest to and
say in one line why yours is a different dead end. If you cannot, drop it. Real
examples of duplicates that got caught only at merge time: an IRD-number canon
about bank interest when `banking/rwt-non-declaration-rate/nz` already covered
it, and a border-declaration canon under `legal/` when
`food-safety/undeclared-biosecurity-goods/nz` already covered it.

When the overlap is partial - your canon has one genuinely new angle and the
rest restates an existing entry - do not ship a competing page. Either narrow
yours to the new angle alone and cross-link the two, or fold the new angle into
the existing canon as an extra `dead_ends[]` / `workarounds[]` entry.

Pick **3–5 canons** for this cycle. Fewer is fine; more than 5 makes review and
sourcing quality slip.

## 4. Research from primary sources

For each canon, find real, current, citable sources before writing a word:

- Use `WebSearch` / `WebFetch`.
- Source priority: **primary government site > embassy/consulate > sector
  regulator > reputable media**. Reddit, personal blogs, and forums may only
  appear inside `condition` or `common_misconception`, never as the sole source
  of a claim.
- Record the actual URL you read. Never invent a citation, a statute number, a
  fee, or a date.
- If you cannot find ≥2 solid sources for a claim, drop that canon and pick
  another topic. An unsourced page is worse than no page.

A good canon captures something an AI would confidently get **wrong**: a
non-obvious dead end, not a fact anyone can restate.

## 5. Author the canons

Use the scaffold:

```python
from generator.country_canon_template import make_country_canon
```

Follow `docs/country-canon-guide.md` and the schema in `CLAUDE.md`. Non-negotiable:

- ID `{domain}/{slug}/{cc}`; slug has **no country name in it**; `url` equals
  `https://deadends.dev/{id}`.
- File at `data/canons/{domain}/{slug}/{cc}.json` (directory style preferred).
- `environment.additional` = `{country, country_name, jurisdiction_level, audience}`.
- `metadata.review_status` = `human_reviewed`; `generation_date` = today;
  `evidence_count` = number of real sources cited.
- Business rules: `resolvable="true"` → `fix_success_rate >= 0.7` **and**
  `confidence >= 0.6`; `resolvable="false"` → `fix_success_rate < 0.2` and
  `confidence >= 0.6`; `evidence_count < 3` → `confidence <= 0.3`.
- At least one `dead_ends[]` entry, with `why_fails` that is specific and
  falsifiable — this is the whole product.
- Fill `transition_graph` only with canon IDs that actually exist (the
  validator enforces this). Empty arrays are fine.
- `error.regex` must be a valid, ReDoS-safe pattern (no `(a+)+`, no `(a|b)+`)
  that matches how someone would phrase the problem.

## 6. Re-verify your assigned slice of aging canons

Roughly a thousand canons sit past the 180-day aging threshold, so each cycle
refreshes a few. Do **not** pick "the oldest three" - that rule is deterministic,
every parallel cycle lands on the same files, and whichever PR merges first
leaves the rest conflicting on exactly the date fields they came to update. That
is what stalled PRs #165, #166, #168, and #172.

Ask for your slice instead. Seed it with your target country code, and exclude
whatever the open PRs from step 2 already touch:

```bash
python -m generator.reverify --seed <cc>
python -m generator.reverify --seed <cc> --exclude id1,id2,id3   # IDs from step 2
```

Blocks are disjoint by construction, so two cycles either get the same block or
share nothing - never a partial overlap. `--exclude` turns "unlikely to collide"
into "cannot collide", so pass it whenever any PR is open.

Then actually re-verify, in this order:

1. Open every `sources[]` URL on the canon and read it.
2. If a URL moved, update it to the new canonical location. If the claim no
   longer holds, fix the claim - a wrong canon is worse than a stale one.
3. Only then bump `last_confirmed`, `verdict.last_updated`, and
   `metadata.last_verification`.

Never bump a date you did not earn by re-reading the source. A refreshed date on
an unchecked canon is a silent lie to every agent that reads it.

If a source contradicts the canon, say so explicitly in the PR body - that
finding is worth more than the new pages.

## 7. Validate — must be clean before committing

```bash
ruff check generator/ tests/
python -m pytest tests/ -q
python -m generator.validate --data-only
python -m generator.build_site
python -m generator.validate --site-only
```

Fix every failure. Do not commit red. If the build emits new warnings for your
files, resolve them too.

## 8. Commit and push

```bash
git add data/ generator/
git commit -m "content: add N <domain> canons for <country>"
git push -u origin <branch>
```

On network failure only, retry up to 4 times with backoff (2s, 4s, 8s, 16s).

## 9. Open the PR

Use `mcp__github__create_pull_request` against `main`. Body should state:

- which country/domain gap this fills and the counts before/after,
- one line per canon: ID + the dead end it documents,
- the primary sources used,
- confirmation that `validate --data-only`, tests, and lint pass locally.

End the body with the attribution footer:

```
---
_Generated by [Claude Code](https://claude.ai/code)_
```

## 10. Drive to green, then merge

1. Read CI status with `mcp__github__pull_request_read` (`get_status`).
2. If checks are still running, wait with the `Monitor` tool (never a foreground
   `sleep`) and re-check. Bound it to ~10 minutes of polling.
3. If a check fails: pull the logs (`mcp__github__get_job_logs`), fix the cause,
   push again, and repeat. Do not merge red, and do not disable a check to get
   green.
4. Once all checks pass, merge with `mcp__github__merge_pull_request` using
   **squash**, and delete the branch.
5. If CI is red for a reason that also fails on `main` (pre-existing breakage),
   say so explicitly in the PR and stop — that one is not yours to force.

## 11. Report

Finish with a short summary: canons added (IDs), the PR number and merge state,
and the new total canon count. If anything was skipped for lack of sources, say
which topic and why.

---

### Hard rules

- **Never** invent facts, sources, dates, fees, or legal citations. Content that
  is wrong is a worse SEO outcome than content that is missing.
- **Never** push directly to `main`; always go through a PR.
- **Never** edit `site/` by hand — it is generated.
- Duplicate or near-duplicate pages actively hurt indexing. If the only thing
  you can produce this cycle is a rewording of an existing canon, produce
  nothing and report that instead.
- **Never** bump `last_confirmed` on a canon whose sources you did not re-read.
- **Never** re-verify by "oldest first" — always take the block
  `python -m generator.reverify --seed <cc>` assigns you.
