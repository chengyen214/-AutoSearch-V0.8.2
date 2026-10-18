"""
tests/V9_2/test_paper_pdf_to_chunk.py

AutoSearch V9

P1 Paper PDF -> Chunk Integration Test
"""

import os

from dotenv import load_dotenv
from pymongo import MongoClient
from gridfs import GridFS

from rag.paper_pdf_chunking import PaperPDFChunking


load_dotenv()

REQUIRED_METADATA = [
    "document_id",
    "page_number",
    "source_type",
    "chunk_id",
    "chunk_index",
    "source",
    "title",
]


def validate_chunks(chunks, document_id):
    if not chunks:
        raise AssertionError(
            f"No chunks generated: {document_id}"
        )

    for chunk in chunks:
        metadata = chunk.metadata

        if not chunk.page_content.strip():
            raise AssertionError(
                f"Empty chunk content: {document_id}"
            )

        for field in REQUIRED_METADATA:
            if field not in metadata:
                raise AssertionError(
                    f"Missing metadata '{field}': "
                    f"{document_id}"
                )

            if metadata[field] is None or metadata[field] == "":
                raise AssertionError(
                    f"Empty metadata '{field}': "
                    f"{document_id}"
                )

        if metadata["document_id"] != document_id:
            raise AssertionError(
                f"Incorrect document_id: {document_id}"
            )

        if not isinstance(metadata["page_number"], int):
            raise AssertionError(
                f"Invalid page_number type: {document_id}"
            )

        if metadata["page_number"] < 1:
            raise AssertionError(
                f"Invalid page_number: {document_id}"
            )

        if metadata["source_type"] != "paper_pdf":
            raise AssertionError(
                f"Invalid source_type: {document_id}"
            )

        if not isinstance(metadata["chunk_index"], int):
            raise AssertionError(
                f"Invalid chunk_index type: {document_id}"
            )

        if metadata["chunk_index"] < 0:
            raise AssertionError(
                f"Invalid chunk_index: {document_id}"
            )

        if not isinstance(metadata["chunk_id"], str):
            raise AssertionError(
                f"Invalid chunk_id type: {document_id}"
            )

        expected_chunk_id = (
            f"{document_id}:{metadata['chunk_index']}"
        )

        if metadata["chunk_id"] != expected_chunk_id:
            raise AssertionError(
                f"Incorrect chunk_id: {document_id}"
            )

        if not isinstance(metadata["source"], str):
            raise AssertionError(
                f"Invalid source type: {document_id}"
            )

        if not isinstance(metadata["title"], str):
            raise AssertionError(
                f"Invalid title type: {document_id}"
            )


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

    passed = 0
    failed = 0
    total_pages = 0
    total_chunks = 0
    total_characters = 0

    print("P1 Paper PDF -> Chunk")
    print("-" * 60)

    try:
        db = client[database_name]
        db.command("ping")

        gridfs = GridFS(db)
        raw_html = db[raw_html_name]
        paper_chunking = PaperPDFChunking()

        records = list(
            raw_html.find(
                {
                    "document_id": {
                        "$regex": "^openalex:"
                    }
                },
                {
                    "document_id": 1,
                    "url": 1,
                    "resolved_url": 1,
                    "title": 1,
                    "created_at": 1,
                },
            ).sort("created_at", -1).limit(10)
        )

        pdf_records = []

        for record in records:
            document_id = record.get("document_id")

            pdf_file = gridfs.find_one(
                {
                    "metadata.document_id": document_id
                }
            )

            if pdf_file is not None:
                pdf_records.append(
                    (record, pdf_file)
                )

        print(f"Paper Records: {len(records)}")
        print(f"PDF Records: {len(pdf_records)}")
        print("-" * 60)

        if not pdf_records:
            raise SystemExit(
                "No matching Paper PDFs found in GridFS."
            )

        for record, pdf_file in pdf_records:
            document_id = record["document_id"]

            try:
                pdf_bytes = pdf_file.read()

                if not pdf_bytes:
                    raise AssertionError(
                        "PDF content is empty"
                    )

                gridfs_document_id = (
                    pdf_file.metadata.get("document_id")
                )

                if gridfs_document_id != document_id:
                    raise AssertionError(
                        "GridFS document_id mismatch"
                    )

                source_url = (
                    record.get("resolved_url")
                    or record.get("url")
                )

                title = record.get("title")

                if not source_url:
                    raise AssertionError(
                        "Paper source URL is missing"
                    )

                if not title:
                    raise AssertionError(
                        "Paper title is missing"
                    )

                chunks = paper_chunking.chunk_pdf(
                    pdf_bytes=pdf_bytes,
                    document_id=document_id,
                    source_url=source_url,
                    title=title,
                )

                validate_chunks(chunks, document_id)

                pages = {
                    chunk.metadata["page_number"]
                    for chunk in chunks
                }

                characters = sum(
                    len(chunk.page_content)
                    for chunk in chunks
                )

                total_pages += len(pages)
                total_chunks += len(chunks)
                total_characters += characters
                passed += 1

                print(
                    f"[PASS] {document_id} | "
                    f"Pages={len(pages)} | "
                    f"Chunks={len(chunks)} | "
                    f"Characters={characters} | "
                    f"Metadata=OK"
                )

            except Exception as exc:
                failed += 1
                print(
                    f"[FAIL] {document_id} | "
                    f"{type(exc).__name__}: {exc}"
                )

        print("-" * 60)
        print(f"Passed Papers: {passed}/{len(pdf_records)}")
        print(f"Failed Papers: {failed}/{len(pdf_records)}")
        print(f"Total Pages: {total_pages}")
        print(f"Total Chunks: {total_chunks}")
        print(f"Total Chunk Characters: {total_characters}")

        if failed:
            raise SystemExit(1)

        print(
            "[PASS] All Paper Chunk and Metadata checks passed."
        )

    finally:
        client.close()


if __name__ == "__main__":
    main()