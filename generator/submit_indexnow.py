"""Submit URLs to search engines via IndexNow API.

Reads the generated indexnow-urls.txt and submits URLs in batches
to Bing (which shares with Google, Yandex, Seznam, Naver).

Usage:
    python -m generator.submit_indexnow              # Submit all URLs
    python -m generator.submit_indexnow --dry-run    # Preview without submitting
    python -m generator.submit_indexnow --limit 100  # Submit first 100 URLs only

IndexNow API spec: https://www.indexnow.org/documentation
- Max 10,000 URLs per batch submission
- Bing endpoint shares with all participating search engines
"""

import json
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

SITE_DIR = Path(__file__).parent.parent / "site"
BASE_URL = "https://deadends.dev"
INDEXNOW_KEY = "deadend-dev-indexnow-key"
INDEXNOW_ENDPOINT = "https://api.indexnow.org/indexnow"
BATCH_SIZE = 10000  # IndexNow max per request


def load_urls(limit: int = 0) -> list[str]:
    """Load URL list from generated indexnow-urls.txt."""
    url_file = SITE_DIR / "indexnow-urls.txt"
    if not url_file.exists():
        print(f"ERROR: {url_file} not found. Run 'python -m generator.build_site' first.")
        sys.exit(1)
    urls = [
        line.strip()
        for line in url_file.read_text().splitlines()
        if line.strip() and line.startswith("http")
    ]
    if limit > 0:
        urls = urls[:limit]
    return urls


def submit_batch(urls: list[str], dry_run: bool = False) -> bool:
    """Submit a batch of URLs via IndexNow API."""
    payload = {
        "host": "deadends.dev",
        "key": INDEXNOW_KEY,
        "keyLocation": f"{BASE_URL}/{INDEXNOW_KEY}.txt",
        "urlList": urls,
    }

    if dry_run:
        print(f"  [DRY RUN] Would submit {len(urls)} URLs to {INDEXNOW_ENDPOINT}")
        print(f"  First 5: {urls[:5]}")
        return True

    data = json.dumps(payload).encode("utf-8")
    req = Request(
        INDEXNOW_ENDPOINT,
        data=data,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )

    try:
        with urlopen(req, timeout=30) as resp:
            status = resp.status
            if status in (200, 202):
                print(f"  Submitted {len(urls)} URLs (HTTP {status})")
                return True
            else:
                print(f"  Unexpected response: HTTP {status}")
                return False
    except HTTPError as e:
        # 200=OK, 202=Accepted, 429=TooManyRequests, 422=Invalid
        if e.code == 429:
            print("  Rate limited (HTTP 429). Try again later.")
        elif e.code == 422:
            print(f"  Invalid request (HTTP 422): {e.read().decode()}")
        else:
            print(f"  HTTP error {e.code}: {e.reason}")
        return False
    except URLError as e:
        print(f"  Network error: {e.reason}")
        return False


def main():
    dry_run = "--dry-run" in sys.argv
    limit = 0
    if "--limit" in sys.argv:
        idx = sys.argv.index("--limit")
        if idx + 1 < len(sys.argv):
            limit = int(sys.argv[idx + 1])

    urls = load_urls(limit)
    if not urls:
        print("No URLs to submit.")
        return

    print(f"IndexNow submission: {len(urls)} URLs")
    print(f"  Endpoint: {INDEXNOW_ENDPOINT}")
    print(f"  Key: {INDEXNOW_KEY}")
    if dry_run:
        print("  Mode: DRY RUN (no actual submission)")
    print()

    # Submit in batches
    total_ok = 0
    for i in range(0, len(urls), BATCH_SIZE):
        batch = urls[i : i + BATCH_SIZE]
        print(f"Batch {i // BATCH_SIZE + 1}: {len(batch)} URLs...")
        if submit_batch(batch, dry_run):
            total_ok += len(batch)

    print(f"\nDone. {total_ok}/{len(urls)} URLs submitted successfully.")


if __name__ == "__main__":
    main()
