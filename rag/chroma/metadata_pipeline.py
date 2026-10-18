"""
rag/chroma/metadata_pipeline.py

AutoSearch RAG

Chroma Metadata Pipeline

用途：

    1. 處理未來寫入 Chroma 前的 Chunk metadata
    2. 補齊既有 Chroma 中缺少 matched_ai_keywords 的 records

規則：

    ai_keywords
        = Article-level AI keywords

    matched_ai_keywords
        = 本 Chunk page_content 實際出現的 keywords

注意：

    只更新缺少 matched_ai_keywords 的 records。
    已存在 matched_ai_keywords 的 records 不修改。
"""

import chromadb

from rag.chroma.ai_keyword_filter import (
    MATCHED_AI_KEYWORDS_FIELD,
    filter_document_metadata,
)


CHROMA_PATH = "chroma_db"
COLLECTION_NAME = "autosearch_knowledge"
BATCH_SIZE = 100


def process_metadata(
    page_content,
    metadata,
):
    """
    處理單一 Chunk metadata。
    """

    return filter_document_metadata(
        page_content,
        metadata,
    )


def update_missing_matched_ai_keywords():
    """
    更新既有 Chroma 中缺少 matched_ai_keywords 的 records。
    """

    client = chromadb.PersistentClient(
        path=CHROMA_PATH,
    )

    collection = client.get_collection(
        name=COLLECTION_NAME,
    )

    total = collection.count()

    updated_count = 0
    skipped_count = 0

    for offset in range(
        0,
        total,
        BATCH_SIZE,
    ):
        result = collection.get(
            offset=offset,
            limit=BATCH_SIZE,
            include=[
                "documents",
                "metadatas",
            ],
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

        update_ids = []
        update_metadatas = []

        for record_id, document, metadata in zip(
            ids,
            documents,
            metadatas,
        ):
            metadata = metadata or {}

            if MATCHED_AI_KEYWORDS_FIELD in metadata:
                skipped_count += 1
                continue

            new_metadata = process_metadata(
                document,
                metadata,
            )

            update_ids.append(
                record_id
            )

            update_metadatas.append(
                new_metadata
            )

        if update_ids:
            collection.update(
                ids=update_ids,
                metadatas=update_metadatas,
            )

            updated_count += len(
                update_ids
            )

            print(
                f"Updated: {updated_count}"
            )

    print()
    print(
        f"Total records: {total}"
    )
    print(
        f"Updated records: {updated_count}"
    )
    print(
        f"Skipped records: {skipped_count}"
    )


def main():
    update_missing_matched_ai_keywords()


if __name__ == "__main__":
    main()


__all__ = [
    "process_metadata",
    "update_missing_matched_ai_keywords",
]