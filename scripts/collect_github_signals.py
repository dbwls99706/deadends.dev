#!/usr/bin/env python3
"""
Collect GitHub issue/PR signals into NDJSON files.

Usage:
  python scripts/collect_github_signals.py --repos dbwls99706/deadends.dev --days 1
  python scripts/collect_github_signals.py --repos "dbwls99706/deadends.dev,python/cpython" --days 2
  python scripts/collect_github_signals.py --repos "python/cpython" --days 1 --min-score 2
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import urllib.parse
import urllib.request


def gh_get(url: str, token: str) -> dict:
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def search_items(repo: str, query: str, token: str) -> list[dict]:
    q = urllib.parse.quote_plus(f"repo:{repo} {query}")
    url = f"https://api.github.com/search/issues?q={q}&sort=updated&order=desc&per_page=100"
    payload = gh_get(url, token)
    return payload.get("items", [])


def normalize(item: dict, kind: str, repo: str) -> dict:
    labels = [lb.get("name") for lb in item.get("labels", [])]
    score, reasons = score_item(item, labels)
    return {
        "id": item.get("id"),
        "number": item.get("number"),
        "kind": kind,
        "repo": repo,
        "title": item.get("title"),
        "state": item.get("state"),
        "labels": labels,
        "author": (item.get("user") or {}).get("login"),
        "created_at": item.get("created_at"),
        "updated_at": item.get("updated_at"),
        "url": item.get("html_url"),
        "body": item.get("body"),
        "quality_score": score,
        "quality_reasons": reasons,
    }


def score_item(item: dict, labels: list[str]) -> tuple[int, list[str]]:
    score = 0
    reasons: list[str] = []
    if item.get("state") == "closed":
        score += 1
        reasons.append("closed")
    if (item.get("comments") or 0) >= 2:
        score += 1
        reasons.append("has_multiple_comments")
    lower_labels = [l.lower() for l in labels if l]
    if any(k in lower_labels for k in ["bug", "fix", "regression", "confirmed"]):
        score += 1
        reasons.append("quality_labels")
    body = (item.get("body") or "").lower()
    if "error" in body or "exception" in body or "stack trace" in body:
        score += 1
        reasons.append("has_error_context")
    return score, reasons


def write_ndjson(path: pathlib.Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--repos",
        required=True,
        help="Comma-separated owner/repo list (e.g. a/b,c/d)",
    )
    parser.add_argument("--days", type=int, default=1, help="lookback days")
    parser.add_argument(
        "--min-score",
        type=int,
        default=2,
        help="Minimum quality score to include in output",
    )
    args = parser.parse_args()

    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise SystemExit("GITHUB_TOKEN is required")

    since = (dt.datetime.utcnow() - dt.timedelta(days=args.days)).strftime("%Y-%m-%d")
    repos = [r.strip() for r in args.repos.split(",") if r.strip()]
    issue_query = f"is:issue updated:>={since}"
    pr_query = f"is:pr updated:>={since}"

    issues: list[dict] = []
    prs: list[dict] = []
    for repo in repos:
        issues.extend(normalize(i, "issue", repo) for i in search_items(repo, issue_query, token))
        prs.extend(normalize(i, "pull_request", repo) for i in search_items(repo, pr_query, token))

    issues = [i for i in issues if i.get("quality_score", 0) >= args.min_score]
    prs = [p for p in prs if p.get("quality_score", 0) >= args.min_score]

    today = dt.datetime.utcnow().strftime("%Y-%m-%d")
    base = pathlib.Path("data/raw/github") / today
    write_ndjson(base / "issues.ndjson", issues)
    write_ndjson(base / "prs.ndjson", prs)

    print(
        f"Collected repos={len(repos)} issues={len(issues)} prs={len(prs)} "
        f"min_score={args.min_score} -> {base}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
