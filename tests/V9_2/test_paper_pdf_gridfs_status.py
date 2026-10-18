"""
tests/V9_2/test_paper_pdf_gridfs_status.py

AutoSearch V9

Paper PDF GridFS Status Diagnostic
"""

import os

from dotenv import load_dotenv
from pymongo import MongoClient
from gridfs import GridFS


load_dotenv()


def main():
    client = MongoClient(
        os.getenv(
            "MONGO_URI",
            "mongodb://localhost:27017",
        ),
        serverSelectionTimeoutMS=5000,
    )

    try:
        db = client[
            os.getenv(
                "MONGO_DATABASE",
                "autosearch",
            )
        ]

        raw_html = db[
            os.getenv(
                "MONGO_RAW_HTML_COLLECTION",
                "raw_html",
            )
        ]

        gridfs = GridFS(db)

        db.command("ping")

        pipeline = [
            {
                "$match": {
                    "document_id": {
                        "$regex": "^openalex:"
                    }
                }
            },
            {
                "$sort": {
                    "created_at": -1,
                    "_id": -1,
                }
            },
            {
                "$group": {
                    "_id": "$document_id",
                    "record": {
                        "$first": "$$ROOT"
                    },
                }
            },
            {
                "$replaceRoot": {
                    "newRoot": "$record"
                }
            },
            {
                "$sort": {
                    "created_at": -1,
                    "_id": -1,
                }
            },
            {
                "$limit": 8
            },
            {
                "$project": {
                    "document_id": 1,
                    "title": 1,
                    "url": 1,
                    "pdf_url": 1,
                    "created_at": 1,
                }
            },
        ]

        records = list(raw_html.aggregate(pipeline))

        print("Paper PDF GridFS Status")
        print("-" * 80)
        print(f"Unique Paper Records: {len(records)}")

        paper_with_pdf = 0
        paper_without_pdf = 0
        papers_with_multiple_pdfs = 0
        total_pdf_files = 0
        duplicate_pdf_files = 0
        pdf_read_failures = 0

        for record in records:
            document_id = record.get("document_id")

            pdf_files = list(
                gridfs.find(
                    {
                        "metadata.document_id": document_id
                    }
                ).sort("uploadDate", 1)
            )

            pdf_count = len(pdf_files)
            total_pdf_files += pdf_count

            print(f"\nDocument ID: {document_id}")
            print(f"Title: {record.get('title')!r}")
            print(f"PDF URL: {record.get('pdf_url')!r}")
            print(f"GridFS PDF Count: {pdf_count}")

            if not pdf_files:
                paper_without_pdf += 1
                print("GridFS Status: PDF NOT FOUND")
                continue

            paper_with_pdf += 1

            if pdf_count > 1:
                papers_with_multiple_pdfs += 1
                duplicate_pdf_files += pdf_count - 1
                print("Warning: Multiple PDF records found.")

            for index, pdf_file in enumerate(pdf_files, start=1):
                metadata = pdf_file.metadata or {}

                print(f"  PDF #{index}")
                print(f"    GridFS ID: {pdf_file._id}")
                print(f"    Upload Date: {pdf_file.upload_date}")
                print(f"    Filename: {pdf_file.filename}")
                print(f"    Length: {pdf_file.length}")
                print(
                    f"    Metadata document_id: "
                    f"{metadata.get('document_id')!r}"
                )
                print(
                    f"    Metadata pdf_url: "
                    f"{metadata.get('pdf_url')!r}"
                )
                print(
                    f"    Metadata final_url: "
                    f"{metadata.get('final_url')!r}"
                )

                try:
                    content = pdf_file.read()
                    valid = bool(content)

                    print(f"    Read Bytes: {len(content)}")
                    print(
                        "    Read Status: "
                        + ("PASS" if valid else "FAIL: Empty PDF")
                    )

                    if not valid:
                        pdf_read_failures += 1

                except Exception as exc:
                    pdf_read_failures += 1
                    print(
                        f"    Read Status: FAIL: "
                        f"{type(exc).__name__}: {exc}"
                    )

        print("\n" + "-" * 80)
        print(f"Unique Paper Records: {len(records)}")
        print(f"Papers with PDF: {paper_with_pdf}")
        print(f"Papers without PDF: {paper_without_pdf}")
        print(f"Total PDF Files: {total_pdf_files}")
        print(f"Papers with Multiple PDFs: {papers_with_multiple_pdfs}")
        print(f"Extra PDF Files: {duplicate_pdf_files}")
        print(f"PDF Read Failures: {pdf_read_failures}")

    finally:
        client.close()


if __name__ == "__main__":
    main()