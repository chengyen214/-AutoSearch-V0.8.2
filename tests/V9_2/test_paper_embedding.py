"""
tests/V9_2/test_paper_embedding.py

AutoSearch V9

P2 Paper Chunks -> Qwen Embedding Test
"""

import os
import math

from dotenv import load_dotenv
from pymongo import MongoClient
from gridfs import GridFS

from rag.paper_pdf_chunking import PaperPDFChunking
from rag.paper_embedding import PaperEmbedding


load_dotenv()


def validate_embedding(
    vector,
    expected_dimension=1024,
):
    if not isinstance(vector, list):
        raise AssertionError(
            "Embedding must be a list."
        )

    if len(vector) != expected_dimension:
        raise AssertionError(
            f"Incorrect dimension: {len(vector)}"
        )

    if not all(
        isinstance(value, (int, float))
        and math.isfinite(value)
        for value in vector
    ):
        raise AssertionError(
            "Embedding contains invalid values."
        )


def validate_normalization(
    vector,
    tolerance=1e-3,
):
    norm = math.sqrt(
        sum(value * value for value in vector)
    )

    normalized = math.isclose(
        norm,
        1.0,
        rel_tol=tolerance,
        abs_tol=tolerance,
    )

    return norm, normalized


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

    print("P2 Paper Chunks -> Qwen Embedding")
    print("-" * 60)

    try:
        db = client[database_name]
        db.command("ping")

        gridfs = GridFS(db)
        raw_html = db[raw_html_name]

        record = raw_html.find_one(
            {
                "document_id": {
                    "$regex": "^openalex:"
                },
                "title": {
                    "$exists": True,
                    "$nin": [None, ""],
                },
                "resolved_url": {
                    "$exists": True,
                    "$nin": [None, ""],
                },
            },
            {
                "document_id": 1,
                "url": 1,
                "resolved_url": 1,
                "title": 1,
                "created_at": 1,
            },
            sort=[("created_at", -1)],
        )

        if record is None:
            raise RuntimeError(
                "No suitable Paper record found."
            )

        document_id = record["document_id"]

        pdf_file = gridfs.find_one(
            {
                "metadata.document_id": document_id
            }
        )

        if pdf_file is None:
            raise RuntimeError(
                f"Paper PDF not found: {document_id}"
            )

        pdf_bytes = pdf_file.read()

        if not pdf_bytes:
            raise RuntimeError(
                f"Paper PDF is empty: {document_id}"
            )

        source_url = (
            record.get("resolved_url")
            or record.get("url")
        )

        title = record["title"]

        print(f"Document ID: {document_id}")
        print(f"Title: {title}")
        print("-" * 60)

        paper_chunking = PaperPDFChunking()

        chunks = paper_chunking.chunk_pdf(
            pdf_bytes=pdf_bytes,
            document_id=document_id,
            source_url=source_url,
            title=title,
        )

        if not chunks:
            raise RuntimeError(
                "No chunks generated."
            )

        print(f"Total Chunks: {len(chunks)}")
        print("-" * 60)

        print("Loading Qwen3 Embedding model...")

        paper_embedding = PaperEmbedding()

        print("Generating Embeddings...")

        embeddings = []
        failed_chunks = []

        for index, chunk in enumerate(chunks, start=1):
            chunk_id = chunk.metadata.get(
                "chunk_id"
            )

            try:
                vector = paper_embedding.embed_chunk(
                    chunk.page_content
                )

                validate_embedding(
                    vector,
                    paper_embedding.embedding_dimension,
                )

                norm, normalized = validate_normalization(
                    vector
                )

                if not normalized:
                    raise ValueError(
                        "Embedding is not normalized. "
                        f"L2 Norm={norm:.8f}"
                    )

                embeddings.append(
                    {
                        "chunk_id": chunk_id,
                        "chunk_index": chunk.metadata.get(
                            "chunk_index",
                            index - 1,
                        ),
                        "page_number": chunk.metadata.get(
                            "page_number"
                        ),
                        "embedding": vector,
                    }
                )

            except Exception as exc:
                failed_chunks.append(
                    {
                        "chunk_id": chunk_id,
                        "error": str(exc),
                    }
                )
                print(
                    f"[ERROR] Chunk {chunk_id}: "
                    f"{type(exc).__name__}: {exc}"
                )

            if index % 10 == 0 or index == len(chunks):
                print(
                    f"Progress: {index}/{len(chunks)} "
                    f"| Success: {len(embeddings)} "
                    f"| Failed: {len(failed_chunks)}"
                )

        print("-" * 60)
        print("Embedding Test Summary")
        print(f"Document ID: {document_id}")
        print(f"Total Chunks: {len(chunks)}")
        print(f"Successful Embeddings: {len(embeddings)}")
        print(f"Failed Embeddings: {len(failed_chunks)}")
        print(
            f"Embedding Dimension: "
            f"{paper_embedding.embedding_dimension}"
        )

        if embeddings:
            first_embedding = embeddings[0]["embedding"]

            first_norm, _ = validate_normalization(
                first_embedding
            )

            print(
                f"First Chunk ID: "
                f"{embeddings[0]['chunk_id']}"
            )
            print(
                f"First Vector Length: "
                f"{len(first_embedding)}"
            )
            print(
                f"First Vector L2 Norm: "
                f"{first_norm:.8f}"
            )
            print(
                f"First 5 Values: "
                f"{first_embedding[:5]}"
            )

        if failed_chunks:
            print("-" * 60)
            print("Failed Chunks:")

            for item in failed_chunks:
                print(
                    f"{item['chunk_id']}: "
                    f"{item['error']}"
                )

            raise RuntimeError(
                f"Embedding failed for "
                f"{len(failed_chunks)} chunk(s)."
            )

        if len(embeddings) != len(chunks):
            raise AssertionError(
                "Embedding count does not match "
                "the total number of chunks."
            )

        print("-" * 60)
        print(
            "[PASS] All Paper Chunks -> "
            "Qwen Embeddings"
        )
        print(
            f"[PASS] Generated {len(embeddings)} "
            f"vectors with dimension "
            f"{paper_embedding.embedding_dimension}."
        )
        print("[PASS] All Embeddings validated.")

    finally:
        client.close()


if __name__ == "__main__":
    main()