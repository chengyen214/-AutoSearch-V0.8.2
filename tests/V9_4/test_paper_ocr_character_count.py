
"""
tests/V9_4/test_paper_ocr_character_count.py

AutoSearch V9

Compare Native PDF Text and OCR Character Counts
"""

import pymupdf
from gridfs import GridFS

from database.mongo_connection import get_mongo_database


DOCUMENT_ID = "openalex:W7221471520"


def main():
    database = get_mongo_database()

    result = database["paper_ocr_results"].find_one(
        {"document_id": DOCUMENT_ID}
    )

    if result is None:
        raise FileNotFoundError(
            f"OCR result not found: {DOCUMENT_ID}"
        )

    pdf_file_id = result["pdf_file_id"]
    pdf_bytes = GridFS(database).get(pdf_file_id).read()

    with pymupdf.open(
        stream=pdf_bytes,
        filetype="pdf",
    ) as pdf:
        native_pages = [
            page.get_text()
            for page in pdf
        ]

    native_count = sum(len(text) for text in native_pages)
    ocr_pages = sorted(
        result.get("page_results", []),
        key=lambda item: item["page"],
    )
    ocr_count = sum(
        len(item.get("text", ""))
        for item in ocr_pages
    )

    difference = ocr_count - native_count
    difference_percent = (
        difference / native_count * 100
        if native_count
        else None
    )

    print("===== CHARACTER COUNT COMPARISON =====")
    print(f"Document ID: {DOCUMENT_ID}")
    print(f"PDF pages: {len(native_pages)}")
    print(f"Native PDF characters: {native_count:,}")
    print(f"OCR characters: {ocr_count:,}")
    print(f"Difference (OCR - native): {difference:+,}")

    if difference_percent is not None:
        print(
            f"Difference relative to native: "
            f"{difference_percent:+.2f}%"
        )
    else:
        print(
            "Cannot calculate percentage: "
            "native PDF text extraction is empty."
        )

    print("\n===== PER-PAGE COMPARISON =====")

    for index, native_text in enumerate(native_pages, start=1):
        ocr_item = next(
            (
                item for item in ocr_pages
                if item.get("page") == index
            ),
            {},
        )
        native_chars = len(native_text)
        ocr_chars = len(ocr_item.get("text", ""))

        print(
            f"Page {index:2}/{len(native_pages)} | "
            f"Native: {native_chars:5,} | "
            f"OCR: {ocr_chars:5,} | "
            f"Difference: {ocr_chars - native_chars:+,}"
        )


if __name__ == "__main__":
    main()
