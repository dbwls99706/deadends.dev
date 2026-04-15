# Contributing to deadends.dev

Thanks for helping improve the dead-end knowledge base! Every contribution —
whether a new code error, a country-specific taboo / rule, a workaround
report, or a bug fix — makes AI agents more useful.

deadends.dev now covers **two complementary tracks**:

- **Code errors** — LLM-bulk-generated + human-reviewed (2,089 entries)
- **Country-scoped real-world dead ends** — 100% manually authored from
  primary sources (visa, banking, legal, cultural, medical, food-safety,
  etc.). See [`docs/country-canon-guide.md`](docs/country-canon-guide.md)
  for the authoring standard.

## Ways to Contribute

### 1. Report a New Code Error

Found a code error that's not in deadends.dev? [Submit it via GitHub Issues](https://github.com/dbwls99706/deadends.dev/issues/new?template=new_error.yml).

Include:
- The exact error message
- What you tried that **didn't** work (dead ends)
- What **actually** fixed it (workaround)
- Your environment (runtime version, OS)

### 1b. Add a Country-Specific Dead End

Noticed an AI assistant giving country-wrong advice (tipping, visa rules,
legal red lines, cultural taboos, food safety)? Open an issue or PR with:

- What an AI would wrongly say (the dead end)
- Why it's wrong in that country
- What the right answer actually is (workaround)
- **Primary source** — government site, embassy, published regulation, or
  established ethnographic source. Reddit / personal blogs alone are not
  accepted; they may supplement but not anchor the claim.
- ISO alpha-2 country code for the `env` segment

Skeleton:
```python
from generator.country_canon_template import make_country_canon
canon = make_country_canon(
    domain="culture",
    slug="chopsticks-in-rice-funeral",
    country="jp",
    signature="...",
    regex=r"...",
    category="etiquette_violation",
    summary="...",
)
# Fill in canon["dead_ends"], canon["workarounds"], canon["metadata"]["evidence_count"]
```

### 2. Report a Workaround Result

Tried a workaround from deadends.dev? Tell us if it worked: [Report a workaround result](https://github.com/dbwls99706/deadends.dev/issues/new?template=update_workaround.yml).

This directly improves our `fix_success_rate` scores and helps other developers avoid dead ends.

### 3. Use the MCP Tool

If you're using deadends.dev via MCP, you can report outcomes programmatically:

```
report_outcome(error_id="python/modulenotfounderror/py311-linux", workaround_action="Create venv and reinstall", success=true)
```

### 4. Fix or Improve Canon Data

Canon JSON files live in `data/canons/{domain}/`. To edit:

1. Fork and clone the repo
2. Edit the canon JSON file
3. Validate: `python -m generator.validate --data-only`
4. Submit a pull request

### 5. Code Contributions

```bash
# Setup
git clone https://github.com/dbwls99706/deadends.dev.git
cd deadends.dev
pip install -e ".[dev]"

# Validate data
python -m generator.validate --data-only

# Run tests
python -m pytest tests/ -v

# Lint
ruff check generator/ tests/

# Full pipeline
python -m generator.pipeline --build
```

## Canon JSON Format

Each entry follows the [ErrorCanon schema](generator/schema.py). Key fields:

| Field | Description |
|-------|-------------|
| `error.signature` | The canonical error / dead-end description |
| `error.regex` | Regex pattern for matching queries |
| `error.domain` | One of 54 domains (code + country-scoped) |
| `environment.additional.country` | ISO alpha-2 code (country canons only) |
| `environment.additional.audience` | `traveler` \| `foreigner-resident` \| `citizen` \| `business` |
| `dead_ends[]` | Approaches that don't work — *what AI wrongly says* |
| `workarounds[]` | Approaches that do work — *what should be said instead* |
| `verdict.fix_success_rate` | How often the best workaround succeeds (0.0–1.0) |
| `verdict.confidence` | How confident we are in the data (0.0–1.0) |

## Guidelines

### All canons
- Keep workarounds actionable and specific
- Document *why* dead ends fail, not just *that* they fail
- Prefer verified fixes over theoretical solutions
- One topic per canon file; use env variants for OS / country differences

### Code canons
- Include environment details — an error may behave differently on Python
  3.11 vs 3.12, Linux vs macOS

### Country canons (country-canon-guide.md is the full standard)
- Source order: primary government > embassy > regulator / treaty text >
  reputable media. Reddit/blogs cannot be sole source.
- Confidence calibration: 0.85+ requires black-letter law or single
  regulator's documented procedure verified this quarter. Cultural claims
  that admit individual exceptions belong at 0.40–0.60.
- Business rules: `resolvable="true"` → `fix_success_rate >= 0.7 && confidence >= 0.6`.
  `evidence_count < 3` → `confidence <= 0.3`.
- The `dead_ends[]` must describe *the plausible-sounding global answer
  that is wrong here* — not a code error or a random mistake.

## Code of Conduct

Be helpful, be honest, be kind. We're all here to save developers —
and travelers, residents, and business counterparts — from wasting time
or getting hurt by known dead ends.
