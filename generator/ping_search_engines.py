"""Ping search engines to notify them of sitemap updates.

Sends HTTP GET requests to Bing's sitemap ping endpoints
to trigger immediate crawling of the updated sitemap.

Usage:
    python -m generator.ping_search_engines              # Ping all
    python -m generator.ping_search_engines --dry-run    # Preview only

Note: Google deprecated their ping endpoint in 2023 but Bing's still works.
IndexNow (submit_indexnow.py) is the preferred method for both.
"""

import sys
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

BASE_URL = "https://deadends.dev"
SITEMAP_URL = f"{BASE_URL}/sitemap.xml"

PING_ENDPOINTS = [
    {
        "name": "Bing",
        "url": f"https://www.bing.com/ping?sitemap={SITEMAP_URL}",
    },
    {
        "name": "IndexNow (Bing)",
        "url": f"https://www.bing.com/indexnow?url={BASE_URL}/&key=deadend-dev-indexnow-key",
    },
]


def ping(endpoint: dict, dry_run: bool = False) -> bool:
    """Send a ping to a search engine endpoint."""
    name = endpoint["name"]
    url = endpoint["url"]

    if dry_run:
        print(f"  [DRY RUN] Would ping {name}: {url}")
        return True

    try:
        with urlopen(url, timeout=15) as resp:
            status = resp.status
            if status == 200:
                print(f"  Pinged {name}: OK (HTTP {status})")
                return True
            else:
                print(f"  Pinged {name}: HTTP {status}")
                return False
    except HTTPError as e:
        print(f"  Ping {name} failed: HTTP {e.code}")
        return False
    except URLError as e:
        print(f"  Ping {name} failed: {e.reason}")
        return False


def main():
    dry_run = "--dry-run" in sys.argv
    print(f"Pinging search engines with sitemap: {SITEMAP_URL}")
    if dry_run:
        print("  Mode: DRY RUN\n")
    else:
        print()

    ok = 0
    for ep in PING_ENDPOINTS:
        if ping(ep, dry_run):
            ok += 1

    print(f"\n{ok}/{len(PING_ENDPOINTS)} pings successful.")


if __name__ == "__main__":
    main()
