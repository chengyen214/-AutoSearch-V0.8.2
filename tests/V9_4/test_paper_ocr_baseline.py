
"""
tests/V9_4/test_paper_ocr_baseline.py

AutoSearch V9

Paper OCR Baseline Test
"""

from database.mongo_connection import get_mongo_database


COLLECTION_NAME = "paper_ocr_results"

BASELINE_PAPERS = [
    {
        "document_id": "openalex:W7221458118",
        "title": (
            "Scalable low-thermal-budget fabrication of "
            "suspended silicon nanowire devices"
        ),
        "chunks": 85,
    },
    {
        "document_id": "openalex:W7221469030",
        "title": "CardioNeural-SoC",
        "chunks": 39,
    },
    {
        "document_id": "openalex:W7221558939",
        "title": (
            "g-C₃N₄-based smart nanocatalysts for "
            "photocatalytic cancer therapy"
        ),
        "chunks": 226,
    },
]


def check_paper(collection, paper):
    document_id = paper["document_id"]
    result = collection.find_one(
        {"document_id": document_id}
    )

    print(f"\n{'=' * 72}")
    print(f"Paper: {paper['title']}")
    print(f"Document ID: {document_id}")
    print(f"Existing Chunks: {paper['chunks']}")

    if result is None:
        print("OCR Status: MISSING")
        print("Result: FAIL - No OCR record found.")
        return False

    status = result.get("status", "UNKNOWN")
    total_pages = result.get("total_pages", 0)
    processed_pages = result.get("processed_pages", 0)
    page_results = result.get("page_results", [])
    review_items = result.get("review_items", [])

    pages_by_number = {
        item.get("page"): item
        for item in page_results
        if isinstance(item, dict)
    }

    missing_pages = [
        page
        for page in range(1, total_pages + 1)
        if page not in pages_by_number
    ]

    empty_pages = [
        page
        for page, item in pages_by_number.items()
        if not str(item.get("text") or "").strip()
    ]

    page_count_matches = (
        total_pages > 0
        and processed_pages == total_pages
        and len(pages_by_number) == total_pages
        and not missing_pages
    )

    all_pages_have_text = (
        page_count_matches
        and not empty_pages
    )

    passed = (
        status == "DONE"
        and page_count_matches
        and all_pages_have_text
        and bool(str(result.get("ocr_text") or "").strip())
    )

    print(f"OCR Status: {status}")
    print(f"Processed Pages: {processed_pages}/{total_pages}")
    print(f"Page Results: {len(pages_by_number)}")
    print(f"Missing Pages: {missing_pages or 'None'}")
    print(f"Empty OCR Pages: {empty_pages or 'None'}")
    print(f"Quality Warnings: {len(review_items)}")

    for item in review_items:
        print(
            f"  - Page {item.get('page')}: "
            f"{item.get('reason', 'Unspecified warning')}"
        )

    if passed:
        print("Result: PASS")
    else:
        print("Result: FAIL - OCR completion checks did not pass.")

    return passed


def main():
    database = get_mongo_database()
    collection = database[COLLECTION_NAME]

    print("AutoSearch V9 - Paper OCR Baseline Test")
    print(f"MongoDB Collection: {COLLECTION_NAME}")
    print(f"Baseline Papers: {len(BASELINE_PAPERS)}")

    results = []

    for paper in BASELINE_PAPERS:
        try:
            passed = check_paper(collection, paper)
        except Exception as exc:
            print(
                f"\nERROR: {paper['document_id']}: "
                f"{type(exc).__name__}: {exc}"
            )
            passed = False

        results.append((paper["document_id"], passed))

    passed_count = sum(passed for _, passed in results)
    failed_count = len(results) - passed_count

    print(f"\n{'=' * 72}")
    print("===== BASELINE OCR SUMMARY =====")
    print(f"Total Papers: {len(results)}")
    print(f"Passed: {passed_count}")
    print(f"Failed: {failed_count}")

    for document_id, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"{status}: {document_id}")

    if failed_count:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
