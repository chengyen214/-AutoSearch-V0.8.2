"""
tests/V9_1/test_chroma_ai_keywords.py

RAG V9.1

用途：

    檢查現有 Chroma Chunk：

        page_content
        ai_keywords

    確認：

        哪些 ai_keywords 不存在於
        該 Chunk 的 page_content。

本 Test：

    只讀取 ChromaDB
    不修改 ChromaDB
    不重新 Embedding
    不重新 Chunking
"""

import json
import os
from pathlib import Path

import chromadb

from rag.chroma.ai_keyword_filter import (
    filter_ai_keywords,
)


PROJECT_ROOT = Path(
    __file__
).resolve().parents[2]


def find_chroma_paths():
    paths = []

    for root, dirs, files in os.walk(
        PROJECT_ROOT
    ):
        if "chroma.sqlite3" in files:
            paths.append(
                Path(root)
            )

    return paths


def main():
    print()
    print(
        "Project Root:"
    )
    print(
        PROJECT_ROOT
    )
    print()

    chroma_paths = (
        find_chroma_paths()
    )

    if not chroma_paths:
        print(
            "No ChromaDB found."
        )
        return

    for chroma_path in chroma_paths:

        print(
            "=" * 80
        )
        print(
            f"Chroma Path: {chroma_path}"
        )
        print(
            "=" * 80
        )

        client = (
            chromadb.PersistentClient(
                path=str(
                    chroma_path
                )
            )
        )

        collections = (
            client.list_collections()
        )

        for collection in collections:

            print()
            print(
                f"Collection: "
                f"{collection.name}"
            )
            print()

            result = collection.get(
                include=[
                    "documents",
                    "metadatas",
                ],
            )

            documents = (
                result.get(
                    "documents",
                    [],
                )
            )

            metadatas = (
                result.get(
                    "metadatas",
                    [],
                )
            )

            total_chunks = len(
                documents
            )

            print(
                f"Total Chunks: "
                f"{total_chunks}"
            )

            chunks_with_keywords = 0
            chunks_with_removed = 0

            total_keywords = 0
            total_removed = 0

            for index, (
                page_content,
                metadata,
            ) in enumerate(
                zip(
                    documents,
                    metadatas,
                ),
                start=1,
            ):

                metadata = (
                    metadata or {}
                )

                raw_keywords = (
                    metadata.get(
                        "ai_keywords"
                    )
                )

                if not raw_keywords:
                    continue

                try:
                    keywords = (
                        json.loads(
                            raw_keywords
                        )
                    )

                except (
                    json.JSONDecodeError,
                    TypeError,
                ):
                    print(
                        f"[Chunk {index}] "
                        "ai_keywords JSON invalid"
                    )
                    continue

                if not keywords:
                    continue

                chunks_with_keywords += 1

                total_keywords += (
                    len(
                        keywords
                    )
                )

                filtered_metadata = (
                    filter_ai_keywords(
                        page_content,
                        metadata,
                    )
                )

                filtered_keywords = (
                    json.loads(
                        filtered_metadata.get(
                            "ai_keywords",
                            "[]",
                        )
                    )
                )

                removed = [
                    keyword
                    for keyword in keywords
                    if keyword
                    not in filtered_keywords
                ]

                if removed:

                    chunks_with_removed += 1

                    total_removed += (
                        len(
                            removed
                        )
                    )

                    print()
                    print(
                        f"[Chunk {index}]"
                    )

                    print(
                        "Title:",
                        metadata.get(
                            "title",
                            "",
                        ),
                    )

                    print(
                        "Document ID:",
                        metadata.get(
                            "document_id",
                            "",
                        ),
                    )

                    print(
                        "Original ai_keywords:",
                        keywords,
                    )

                    print(
                        "Removed:",
                        removed,
                    )

                    print(
                        "Remaining:",
                        filtered_keywords,
                    )

            print()
            print(
                "Chunks with ai_keywords:",
                chunks_with_keywords,
            )

            print(
                "Chunks with keywords to remove:",
                chunks_with_removed,
            )

            print(
                "Total ai_keywords:",
                total_keywords,
            )

            print(
                "Total keywords to remove:",
                total_removed,
            )

            print()
            print(
                "No Chroma data modified."
            )
            print()


if __name__ == "__main__":
    main()