
"""
tests/V9_4/inspect_paper_pdf.py

AutoSearch V9

Paper PDF Text Inspection
"""

import pymupdf
from gridfs import GridFS

from database.mongo_connection import get_mongo_database


DOCUMENT_ID = "openalex:W7221570648"
PREVIEW_CHARS = 5000


def get_pdf_bytes(document_id):
    """從 MongoDB GridFS 取得論文 PDF。"""

    database = get_mongo_database()
    gridfs = GridFS(database)

    file_info = database["fs.files"].find_one(
        {
            "metadata.document_id": document_id,
            "contentType": "application/pdf",
        },
        sort=[("uploadDate", -1)],
    )

    if file_info is None:
        file_info = database["fs.files"].find_one(
            {"metadata.document_id": document_id},
            sort=[("uploadDate", -1)],
        )

    if file_info is None:
        raise FileNotFoundError(
            f"No GridFS PDF found for document_id={document_id}"
        )

    pdf_bytes = gridfs.get(file_info["_id"]).read()

    if not pdf_bytes:
        raise ValueError("Retrieved PDF is empty.")

    print(f"GridFS file ID: {file_info['_id']}")
    print(f"PDF filename: {file_info.get('filename', '(unknown)')}")
    print(f"PDF size: {len(pdf_bytes):,} bytes")

    return pdf_bytes


def inspect_pdf(pdf_bytes):
    """統計 PDF 每頁原生文字量。"""

    with pymupdf.open(
        stream=pdf_bytes,
        filetype="pdf",
    ) as pdf:
        total_pages = len(pdf)

        if total_pages == 0:
            raise ValueError("PDF contains no pages.")

        print(f"Document ID: {DOCUMENT_ID}")
        print(f"Total pages: {total_pages}")

        page_texts = []
        total_chars = 0
        empty_pages = 0

        print("\n========== Page Text Statistics ==========")

        for page_number, page in enumerate(pdf, start=1):
            text = page.get_text("text")
            char_count = len(text)
            total_chars += char_count

            if not text.strip():
                empty_pages += 1

            page_texts.append(text)

            print(
                f"Page {page_number:3}/{total_pages}: "
                f"{char_count:6,} characters"
            )

        print("\n========== Summary ==========")
        print(f"Total pages: {total_pages}")
        print(f"Total native characters: {total_chars:,}")
        print(
            f"Average characters per page: "
            f"{total_chars / total_pages:,.1f}"
        )
        print(f"Pages without native text: {empty_pages}")

        print("\n========== Page 1 Native Text Preview ==========")
        print(page_texts[0][:PREVIEW_CHARS])

        print("\n========== Page 1 Layout ==========")
        page = pdf[0]
        print(f"Page size: {page.rect.width:.1f} x {page.rect.height:.1f} pt")
        print(f"Embedded images: {len(page.get_images(full=True))}")

        print("\n========== Longest Pages ==========")
        ranked_pages = sorted(
            enumerate(page_texts, start=1),
            key=lambda item: len(item[1]),
            reverse=True,
        )

        for page_number, text in ranked_pages[:5]:
            print(
                f"Page {page_number}: "
                f"{len(text):,} native characters"
            )


def main():
    pdf_bytes = get_pdf_bytes(DOCUMENT_ID)
    inspect_pdf(pdf_bytes)


if __name__ == "__main__":
    main()
