# Contributing to deadends.dev

Thanks for helping improve the error knowledge base! Every contribution — whether a new error, a workaround report, or a bug fix — makes AI coding agents smarter.

## Ways to Contribute

### 1. Report a New Error

Found an error that's not in deadends.dev? [Submit it via GitHub Issues](https://github.com/dbwls99706/deadends.dev/issues/new?template=new_error.yml).

Include:
- The exact error message
- What you tried that **didn't** work (dead ends)
- What **actually** fixed it (workaround)
- Your environment (runtime version, OS)

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

Each error entry follows the [ErrorCanon schema](generator/schema.py). Key fields:

| Field | Description |
|-------|-------------|
| `error.signature` | The canonical error message |
| `error.regex` | Regex pattern for matching |
| `dead_ends[]` | Approaches that don't work |
| `workarounds[]` | Approaches that do work |
| `verdict.fix_success_rate` | How often the best workaround succeeds (0.0–1.0) |
| `verdict.confidence` | How confident we are in the data (0.0–1.0) |

## Guidelines

- Keep workarounds actionable and specific
- Document *why* dead ends fail, not just *that* they fail
- Include environment details — an error may behave differently on Python 3.11 vs 3.12
- Prefer verified fixes over theoretical solutions
- One error per canon file; use environment variants for OS/version differences

## Code of Conduct

Be helpful, be honest, be kind. We're all here to save developers from wasting time on known dead ends.
