
"""
tests/V9_4/test_paper_ocr_mongo.py

AutoSearch V9

Paper OCR MongoDB Result Test
"""

import argparse

from database.mongo_connection import get_mongo_database


COLLECTION_NAME = "paper_ocr_results"
DEFAULT_DOCUMENT_ID = "openalex:W7221471520"


def main():
    parser = argparse.ArgumentParser(
        description="Inspect Paper OCR results in MongoDB."
    )
    parser.add_argument(
        "--document-id",
        default=DEFAULT_DOCUMENT_ID,
        help="Paper document ID to inspect.",
    )
    args = parser.parse_args()

    database = get_mongo_database()
    collection = database[COLLECTION_NAME]

    result = collection.find_one(
        {"document_id": args.document_id}
    )

    if result is None:
        print(f"NOT FOUND: {args.document_id}")
        return

    page_results = sorted(
        result.get("page_results", []),
        key=lambda item: item.get("page", 0),
    )

    total_pages = result.get("total_pages", 0)
    processed_pages = result.get("processed_pages", 0)
    review_items = result.get("review_items", [])

    print("===== PAPER OCR MONGODB TEST =====")
    print(f"Document ID: {result.get('document_id')}")
    print(f"Status: {result.get('status')}")
    print(f"PDF File ID: {result.get('pdf_file_id')}")
    print(f"OCR Model: {result.get('ocr_model')}")
    print(f"Total pages: {total_pages}")
    print(f"Processed pages: {processed_pages}")
    print(f"Page result records: {len(page_results)}")
    print(f"OCR text characters: {len(result.get('ocr_text', ''))}")
    print(
        f"Raw OCR text characters: "
        f"{len(result.get('ocr_raw_text', ''))}"
    )
    print(f"Review items: {len(review_items)}")
    print(f"Finished at: {result.get('finished_at')}")

    print("\n===== PAGE DETAILS =====")

    for item in page_results:
        text = item.get("text", "")
        reasons = item.get("review_reasons", [])

        print(
            f"Page {item.get('page')}/{total_pages} | "
            f"Characters: {len(text)} | "
            f"Tokens: {item.get('generated_tokens')} | "
            f"EOS: {item.get('ended_with_eos')} | "
            f"Token limit: {item.get('token_limit_reached')} | "
            f"Warnings: {'; '.join(reasons) or 'None'}"
        )

    print("\n===== OCR TEXT PREVIEW =====")

    for item in page_results:
        if item.get("page") in (1, 12, total_pages):
            print(f"\n--- PAGE {item.get('page')} ---")
            print(item.get("text", "")[:500])

    missing_pages = [
        page
        for page in range(1, total_pages + 1)
        if not any(
            item.get("page") == page
            and item.get("text", "").strip()
            for item in page_results
        )
    ]

    print("\n===== VALIDATION =====")
    print(
        "Status DONE: "
        f"{result.get('status') == 'DONE'}"
    )
    print(
        "Page count matches: "
        f"{processed_pages == total_pages == len(page_results)}"
    )
    print(f"Missing or empty pages: {missing_pages}")
    print(
        "OCR text stored: "
        f"{bool(result.get('ocr_text', '').strip())}"
    )


if __name__ == "__main__":
    main()
