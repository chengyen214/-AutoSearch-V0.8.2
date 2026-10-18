"""
tests/V9_2/test_clear_paper_data.py

AutoSearch V9

Clear Existing Paper Data
"""

import os

from dotenv import load_dotenv
from pymongo import MongoClient
from gridfs import GridFS


load_dotenv()

PAPER_DOCUMENT_FILTER = {
    "document_id": {
        "$regex": r"^openalex:",
        "$options": "i",
    }
}


def main():
    mongo_uri = os.getenv(
        "MONGO_URI",
        "mongodb://localhost:27017",
    )
    database_name = os.getenv(
        "MONGO_DATABASE",
        "autosearch",
    )
    raw_html_name = os.getenv(
        "MONGO_RAW_HTML_COLLECTION",
        "raw_html",
    )

    client = MongoClient(
        mongo_uri,
        serverSelectionTimeoutMS=5000,
    )

    try:
        db = client[database_name]
        db.command("ping")

        raw_html = db[raw_html_name]
        gridfs = GridFS(db)

        html_count = raw_html.count_documents(
            PAPER_DOCUMENT_FILTER
        )

        pdf_query = {
            "metadata.document_id": {
                "$regex": r"^openalex:",
                "$options": "i",
            }
        }
        pdf_count = db["fs.files"].count_documents(
            pdf_query
        )

        print("Clear Existing Paper Data")
        print("-" * 60)
        print(f"Database: {database_name}")
        print(f"Raw HTML collection: {raw_html_name}")
        print(f"Paper HTML records found: {html_count}")
        print(f"Paper PDF files found: {pdf_count}")
        print("-" * 60)

        deleted_html = raw_html.delete_many(
            PAPER_DOCUMENT_FILTER
        ).deleted_count

        deleted_pdf = 0

        pdf_files = list(
            gridfs.find(pdf_query)
        )

        for pdf_file in pdf_files:
            gridfs.delete(pdf_file._id)
            deleted_pdf += 1

        remaining_html = raw_html.count_documents(
            PAPER_DOCUMENT_FILTER
        )
        remaining_pdf = db["fs.files"].count_documents(
            pdf_query
        )

        print("-" * 60)
        print(f"Total HTML documents deleted: {deleted_html}")
        print(f"Total PDF files deleted: {deleted_pdf}")
        print(f"Remaining Paper HTML records: {remaining_html}")
        print(f"Remaining Paper PDF files: {remaining_pdf}")
        print("Cleanup completed.")

    finally:
        client.close()


if __name__ == "__main__":
    main()