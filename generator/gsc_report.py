"""Google Search Console indexing report.

Answers the only SEO question that matters for this site: are the pages we
publish actually getting indexed by Google?

What this can and cannot do (Google's API surface, not our choice):

- Sitemap (re)submission          -> automatable, done here
- Per-URL index status            -> automatable via URL Inspection API, done here
- "Request indexing" button       -> NOT automatable. The Indexing API is limited
                                     to JobPosting and BroadcastEvent pages, so
                                     this script instead prints a ranked shortlist
                                     to paste into Search Console by hand.
- "Validate fix" button           -> NOT automatable, UI only.

Usage:
    python -m generator.gsc_report                    # full report
    python -m generator.gsc_report --limit 50         # inspect fewer URLs
    python -m generator.gsc_report --submit-sitemap   # resubmit sitemap too
    python -m generator.gsc_report --dry-run          # show the URL plan, no API calls

Credentials (a service account that is added as a Search Console property user):
    In CI, none - Workload Identity Federation supplies Application Default
    Credentials, so there is no key to leak. Locally, either:
    GSC_SA_KEY        raw service-account JSON, or
    GSC_SA_KEY_FILE   path to the service-account JSON file
    GSC_PROPERTY      Search Console property identifier, default sc-domain:deadends.dev
                      (deadends.dev is verified as a Domain property, not a
                      URL-prefix property - the sc-domain: prefix is required or
                      every API call 403s with "You do not own this site")

Requires the optional extra:  pip install -e ".[seo]"
"""

import json
import os
import re
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
SITE_DIR = PROJECT_ROOT / "site"
OUTPUT_DIR = PROJECT_ROOT / "data" / "seo"
OUTPUT_FILE = OUTPUT_DIR / "gsc_report.json"

DEFAULT_PROPERTY = "sc-domain:deadends.dev"
SITEMAP_PATH = "https://deadends.dev/sitemap.xml"

# URL Inspection allows 2000 queries/day and 600/minute per property. Stay well
# under both - this runs weekly and a partial sample is enough to see the trend.
DEFAULT_LIMIT = 120
CALL_SPACING_SEC = 0.15

# Anything other than this means Google has the URL but has not indexed it.
INDEXED_STATE = "Submitted and indexed"

SCOPES = ["https://www.googleapis.com/auth/webmasters"]


def load_credentials():
    """Resolve credentials, or exit with guidance.

    Order: explicit key material first, then Application Default Credentials.
    ADC is how the keyless path works - in CI, GOOGLE_APPLICATION_CREDENTIALS
    points at a Workload Identity Federation config rather than a key file, so
    no long-lived secret exists anywhere. Service-account keys are supported
    only as a local convenience; organizations often disable creating them
    (iam.disableServiceAccountKeyCreation), which is why ADC is the default.
    """
    raw = os.environ.get("GSC_SA_KEY")
    key_file = os.environ.get("GSC_SA_KEY_FILE")

    if raw:
        try:
            from google.oauth2 import service_account
        except ImportError:
            sys.exit('ERROR: missing dependency. Run: pip install -e ".[seo]"')
        try:
            info = json.loads(raw)
        except json.JSONDecodeError as e:
            sys.exit(f"ERROR: GSC_SA_KEY is not valid JSON: {e}")
        return service_account.Credentials.from_service_account_info(info, scopes=SCOPES)

    if key_file:
        try:
            from google.oauth2 import service_account
        except ImportError:
            sys.exit('ERROR: missing dependency. Run: pip install -e ".[seo]"')
        path = Path(key_file)
        if not path.exists():
            sys.exit(f"ERROR: GSC_SA_KEY_FILE not found: {path}")
        return service_account.Credentials.from_service_account_file(str(path), scopes=SCOPES)

    try:
        import google.auth
    except ImportError:
        sys.exit('ERROR: missing dependency. Run: pip install -e ".[seo]"')
    try:
        credentials, _ = google.auth.default(scopes=SCOPES)
    except Exception as e:  # noqa: BLE001 - surface the setup step, not a stack trace
        sys.exit(
            f"ERROR: no usable credentials ({str(e)[:160]}).\n"
            "In CI this comes from Workload Identity Federation; locally set "
            "GSC_SA_KEY_FILE. See docs/gsc-setup.md."
        )
    return credentials


def build_service(credentials):
    try:
        from googleapiclient.discovery import build
    except ImportError:
        sys.exit('ERROR: missing dependency. Run: pip install -e ".[seo]"')
    return build("searchconsole", "v1", credentials=credentials, cache_discovery=False)


def collect_urls() -> list[str]:
    """Read indexable URLs out of the generated sitemaps, hubs first.

    Hub pages are inspected first on purpose: if a hub is not indexed, the detail
    pages below it have little chance, so hubs are where a manual indexing
    request buys the most.
    """
    sitemaps = sorted(SITE_DIR.glob("sitemap-*.xml"))
    if not sitemaps:
        sys.exit(
            f"ERROR: no sitemaps under {SITE_DIR}. Run 'python -m generator.build_site' first."
        )

    urls: list[str] = []
    seen: set[str] = set()
    for sm in sitemaps:
        for m in re.finditer(r"<loc>([^<]+)</loc>", sm.read_text(encoding="utf-8")):
            url = m.group(1).strip()
            if url not in seen:
                seen.add(url)
                urls.append(url)

    def depth(url: str) -> int:
        return url.rstrip("/").count("/")

    hubs = [u for u in urls if depth(u) <= 3]
    details = [u for u in urls if depth(u) > 3]
    return sorted(hubs, key=depth) + details


def inspect_url(service, site_url: str, url: str) -> dict:
    """Inspect one URL. Returns a flat dict; never raises."""
    body = {"inspectionUrl": url, "siteUrl": site_url}
    try:
        resp = service.urlInspection().index().inspect(body=body).execute()
    except Exception as e:  # noqa: BLE001 - one bad URL must not kill the run
        return {"url": url, "error": str(e)[:200]}

    result = resp.get("inspectionResult", {})
    index_status = result.get("indexStatusResult", {})
    return {
        "url": url,
        "coverage": index_status.get("coverageState", "unknown"),
        "indexing_state": index_status.get("indexingState", "unknown"),
        "robots": index_status.get("robotsTxtState", "unknown"),
        "fetch": index_status.get("pageFetchState", "unknown"),
        "last_crawl": index_status.get("lastCrawlTime"),
        "canonical_google": index_status.get("googleCanonical"),
        "verdict": result.get("verdict", "unknown"),
    }


def submit_sitemap(service, site_url: str, dry_run: bool = False) -> bool:
    if dry_run:
        print(f"  [DRY RUN] Would resubmit {SITEMAP_PATH}")
        return True
    try:
        service.sitemaps().submit(siteUrl=site_url, feedpath=SITEMAP_PATH).execute()
        print(f"  Resubmitted {SITEMAP_PATH}")
        return True
    except Exception as e:  # noqa: BLE001
        print(f"  Sitemap resubmission failed: {str(e)[:200]}")
        return False


def load_previous() -> dict:
    if OUTPUT_FILE.exists():
        try:
            return json.loads(OUTPUT_FILE.read_text())
        except json.JSONDecodeError:
            return {}
    return {}


def print_report(results: list[dict], previous: dict) -> list[str]:
    """Print the summary and return the manual-request shortlist."""
    ok = [r for r in results if r.get("coverage") == INDEXED_STATE]
    errors = [r for r in results if r.get("error")]
    pending = [r for r in results if not r.get("error") and r.get("coverage") != INDEXED_STATE]

    print(f"\n  Inspected: {len(results)}")
    print(f"  Indexed:   {len(ok)}")
    print(f"  Not yet:   {len(pending)}")
    if errors:
        print(f"  Errors:    {len(errors)}")

    prev_ok = previous.get("indexed_count")
    if isinstance(prev_ok, int):
        delta = len(ok) - prev_ok
        sign = "+" if delta >= 0 else ""
        print(f"  Change since last run: {sign}{delta}")

    by_state: dict[str, int] = {}
    for r in pending:
        by_state[r.get("coverage", "unknown")] = by_state.get(r.get("coverage", "unknown"), 0) + 1
    if by_state:
        print("\n  Not-indexed breakdown:")
        for state, n in sorted(by_state.items(), key=lambda x: -x[1]):
            print(f"    {n:5d}  {state}")

    # Shallowest URLs first: hubs pass crawl equity down to detail pages.
    shortlist = [r["url"] for r in sorted(pending, key=lambda r: r["url"].rstrip("/").count("/"))]
    shortlist = shortlist[:10]
    if shortlist:
        print("\n  Request indexing by hand in Search Console (URL Inspection),")
        print("  highest value first - Google caps this at ~10/day:\n")
        for i, url in enumerate(shortlist, 1):
            print(f"    {i:2d}. {url}")

    return shortlist


def main():
    argv = sys.argv[1:]
    dry_run = "--dry-run" in argv
    do_sitemap = "--submit-sitemap" in argv
    limit = DEFAULT_LIMIT
    if "--limit" in argv:
        idx = argv.index("--limit")
        if idx + 1 < len(argv):
            limit = int(argv[idx + 1])

    site_url = os.environ.get("GSC_PROPERTY", DEFAULT_PROPERTY)
    urls = collect_urls()[:limit]

    print(f"GSC indexing report for {site_url}")
    print(f"  URLs to inspect: {len(urls)}")

    if dry_run:
        print("  Mode: DRY RUN (no API calls)\n")
        for url in urls[:20]:
            print(f"    {url}")
        if len(urls) > 20:
            print(f"    ... and {len(urls) - 20} more")
        return

    service = build_service(load_credentials())

    if do_sitemap:
        print("\n  Sitemap:")
        submit_sitemap(service, site_url)

    results = []
    for i, url in enumerate(urls, 1):
        results.append(inspect_url(service, site_url, url))
        if i % 25 == 0:
            print(f"  ...inspected {i}/{len(urls)}")
        time.sleep(CALL_SPACING_SEC)

    previous = load_previous()
    shortlist = print_report(results, previous)

    # Timestamps matter here: indexing requests take days to show up, so a
    # reader needs to know whether a report predates the requests it is being
    # compared against. previous_generated_at makes the interval between two
    # runs explicit rather than assumed to be a week.
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    print(f"  Generated: {generated_at}")
    if previous.get("generated_at"):
        print(f"  Previous run: {previous['generated_at']}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(
        json.dumps(
            {
                "property": site_url,
                "generated_at": generated_at,
                "previous_generated_at": previous.get("generated_at"),
                "inspected_count": len(results),
                "indexed_count": sum(1 for r in results if r.get("coverage") == INDEXED_STATE),
                "coverage_breakdown": dict(
                    Counter(r.get("coverage", "error") for r in results).most_common()
                ),
                "manual_request_shortlist": shortlist,
                "results": results,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n"
    )
    print(f"\n  Written: {OUTPUT_FILE.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
