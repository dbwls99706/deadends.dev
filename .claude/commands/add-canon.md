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
yourself in step 2.

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

## 2. Pick a real coverage gap (never duplicate)

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
- Grep before writing so you do not re-author an existing slug:
  `rg -l "your-slug" data/canons/`

Pick **3–5 canons** for this cycle. Fewer is fine; more than 5 makes review and
sourcing quality slip.

## 3. Research from primary sources

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

## 4. Author the canons

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

## 5. Validate — must be clean before committing

```bash
ruff check generator/ tests/
python -m pytest tests/ -q
python -m generator.validate --data-only
python -m generator.build_site
python -m generator.validate --site-only
```

Fix every failure. Do not commit red. If the build emits new warnings for your
files, resolve them too.

## 6. Commit and push

```bash
git add data/ generator/
git commit -m "content: add N <domain> canons for <country>"
git push -u origin <branch>
```

On network failure only, retry up to 4 times with backoff (2s, 4s, 8s, 16s).

## 7. Open the PR

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

## 8. Drive to green, then merge

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

## 9. Report

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
