"""
tests/V9_1/test_chroma_matched_ai_keywords.py

驗證 Chroma matched_ai_keywords。
"""

import json

import chromadb

from rag.chroma.ai_keyword_filter import (
    MATCHED_AI_KEYWORDS_FIELD,
    filter_document_metadata,
)


CHROMA_PATH = "chroma_db"
COLLECTION_NAME = "autosearch_knowledge"


def test_matched_ai_keywords():
    client = chromadb.PersistentClient(
        path=CHROMA_PATH,
    )

    collection = client.get_collection(
        name=COLLECTION_NAME,
    )

    total = collection.count()

    result = collection.get(
        include=[
            "documents",
            "metadatas",
        ],
        limit=total,
    )

    ids = result.get(
        "ids",
        [],
    )

    documents = result.get(
        "documents",
        [],
    )

    metadatas = result.get(
        "metadatas",
        [],
    )

    missing_count = 0
    mismatch_count = 0
    empty_count = 0

    for record_id, document, metadata in zip(
        ids,
        documents,
        metadatas,
    ):
        metadata = metadata or {}

        matched_value = metadata.get(
            MATCHED_AI_KEYWORDS_FIELD
        )

        if matched_value is None:
            missing_count += 1

            print(
                f"MISSING: {record_id}"
            )

            continue

        try:
            matched_keywords = json.loads(
                matched_value
            )
        except (TypeError, json.JSONDecodeError):
            mismatch_count += 1

            print(
                f"INVALID JSON: {record_id}"
            )

            continue

        if not matched_keywords:
            empty_count += 1

        expected_metadata = filter_document_metadata(
            document,
            metadata,
        )

        expected_keywords = json.loads(
            expected_metadata[
                MATCHED_AI_KEYWORDS_FIELD
            ]
        )

        if matched_keywords != expected_keywords:
            mismatch_count += 1

            print(
                f"MISMATCH: {record_id}"
            )

    print()
    print(
        f"Total records: {total}"
    )
    print(
        f"Missing matched_ai_keywords: {missing_count}"
    )
    print(
        f"Empty matched_ai_keywords: {empty_count}"
    )
    print(
        f"Mismatch: {mismatch_count}"
    )

    assert missing_count == 0
    assert mismatch_count == 0


if __name__ == "__main__":
    test_matched_ai_keywords()