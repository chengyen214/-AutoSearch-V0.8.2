"""
tests/V9_2/test_paper_metadata_source.py

AutoSearch V9

Paper Metadata Source Diagnostic
"""

import os

from dotenv import load_dotenv
from pymongo import MongoClient


load_dotenv()


def main():
    client = MongoClient(
        os.getenv("MONGO_URI", "mongodb://localhost:27017"),
        serverSelectionTimeoutMS=5000,
    )

    try:
        db = client[
            os.getenv("MONGO_DATABASE", "autosearch")
        ]

        raw_html = db[
            os.getenv("MONGO_RAW_HTML_COLLECTION", "raw_html")
        ]

        db.command("ping")

        records = raw_html.find(
            {
                "document_id": {
                    "$regex": "^openalex:"
                }
            },
            {
                "document_id": 1,
                "title": 1,
                "keyword": 1,
                "url": 1,
                "resolved_url": 1,
                "pdf_url": 1,
                "created_at": 1,
            },
        ).sort("created_at", -1).limit(10)

        records = list(records)

        print(f"Found Paper Records: {len(records)}")

        if not records:
            print("No OpenAlex Paper records found.")
            return

        for record in records:
            document_id = record.get("document_id")

            print(f"\nDocument ID: {document_id}")
            print(f"Fields: {list(record.keys())}")
            print(f"title: {record.get('title')!r}")
            print(f"keyword: {record.get('keyword')!r}")
            print(f"url: {record.get('url')!r}")
            print(
                f"resolved_url: {record.get('resolved_url')!r}"
            )
            print(f"pdf_url: {record.get('pdf_url')!r}")
            print(f"created_at: {record.get('created_at')!r}")

            required_fields = [
                "title",
                "keyword",
                "url",
                "pdf_url",
            ]

            missing_fields = [
                field
                for field in required_fields
                if field not in record
            ]

            if missing_fields:
                print(f"Missing Fields: {missing_fields}")
            else:
                print("Required Fields: PASS")

            if not record.get("title"):
                print("Warning: title is empty.")

            if not record.get("keyword"):
                print("Warning: keyword is empty.")

            if not record.get("url"):
                print("Warning: url is empty.")

            if not record.get("pdf_url"):
                print("PDF URL: Not available")

    finally:
        client.close()


if __name__ == "__main__":
    main()