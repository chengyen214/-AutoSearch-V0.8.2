"""
tests/V9_1/test_crawl_service_real.py

AutoSearch V9.1

CrawlService Real Test
"""

import time

from services.crawl_service import CrawlService


TARGET_URL = (
    "https://techorange.com/2025/12/05/2026-semiconductor/"
)

def log(message):
    elapsed = time.perf_counter() - START_TIME
    print(f"[{elapsed:8.2f}s] {message}", flush=True)


def main():
    global START_TIME
    START_TIME = time.perf_counter()

    print("=" * 70, flush=True)
    print("AutoSearch V9.1 - CrawlService Real Test", flush=True)
    print(f"Target URL: {TARGET_URL}", flush=True)
    print("=" * 70, flush=True)

    service = None

    try:
        log("[1/3] Initializing CrawlService")

        service = CrawlService(
            save_raw_html=True,
        )

        log("[2/3] Starting real crawl")
        log("Waiting for CrawlService.crawl() to complete...")

        crawl_start = time.perf_counter()

        result = service.crawl(TARGET_URL)

        crawl_elapsed = time.perf_counter() - crawl_start

        log(f"Crawl finished in {crawl_elapsed:.2f}s")

        print()
        log("[3/3] Crawl Result")
        print("-" * 70, flush=True)

        print(f"Success       : {result.success}", flush=True)
        print(f"Original URL  : {result.url}", flush=True)
        print(f"Resolved URL  : {result.resolved_url}", flush=True)
        print(f"HTML Length   : {len(result.html or '')}", flush=True)
        print(f"Content Hash  : {result.content_hash}", flush=True)
        print(f"Has Hash      : {result.has_hash}", flush=True)
        print(f"Has Resources : {result.has_resources}", flush=True)
        print(
            f"CSS Count     : {len(result.resources.get('css', []))}",
            flush=True,
        )
        print(
            f"Image Count   : {len(result.resources.get('images', []))}",
            flush=True,
        )
        print(f"Error         : {result.error}", flush=True)
        print(f"Crawl Time    : {result.crawl_time}", flush=True)

        print()
        log("Validating crawl result")

        checks = {
            "Crawl succeeded": result.success,
            "HTML exists": bool(result.html),
            "Content hash exists": bool(result.content_hash),
            "Content hash is 64 characters": (
                bool(result.content_hash)
                and len(result.content_hash) == 64
            ),
            "Resources is a dictionary": isinstance(
                result.resources, dict
            ),
            "CSS resources field exists": (
                isinstance(result.resources, dict)
                and "css" in result.resources
            ),
            "Image resources field exists": (
                isinstance(result.resources, dict)
                and "images" in result.resources
            ),
        }

        all_passed = True

        for name, passed in checks.items():
            status = "PASS" if passed else "FAIL"
            log(f"[{status}] {name}")

            if not passed:
                all_passed = False

        print()
        print("=" * 70, flush=True)

        if all_passed:
            log("[PASS] CrawlService Real Test completed.")
        else:
            log("[FAIL] One or more validations failed.")

        log(f"Total elapsed time: {time.perf_counter() - START_TIME:.2f}s")
        print("=" * 70, flush=True)

        return all_passed

    except KeyboardInterrupt:
        log("[INTERRUPTED] Test stopped by user.")
        return False

    except Exception as exc:
        log(f"[ERROR] {type(exc).__name__}: {exc}")
        raise


if __name__ == "__main__":
    START_TIME = time.perf_counter()
    passed = main()
    raise SystemExit(0 if passed else 1)