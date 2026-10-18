"""
tests/V9_1/test_chroma_chunk_structure.py

RAG V9.1

用途：

    讀取現有 ChromaDB。

確認：

    1. 單一 Chunk 結構
    2. Chunk metadata 欄位數量
    3. Metadata 欄位名稱
    4. Metadata 型別
    5. ai_keywords 是否存在
    6. 同一 document 的 Chunk metadata 是否一致
    7. Chunk page_content 長度
    8. Chroma record id

本 Test：

    只讀取資料
    不修改 ChromaDB
    不重新 Embedding
    不重新 Chunking
"""

import json
import os
from pathlib import Path

import chromadb


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def find_chroma_paths():
    paths = []

    for root, dirs, files in os.walk(PROJECT_ROOT):
        if "chroma.sqlite3" in files:
            paths.append(Path(root))

    return paths


def print_value(name, value):
    print(f"{name}:")
    print(
        json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            default=str,
        )
    )
    print()


def main():
    print()
    print("Project Root:")
    print(PROJECT_ROOT)
    print()

    chroma_paths = find_chroma_paths()

    if not chroma_paths:
        print("No ChromaDB found.")
        return

    for chroma_path in chroma_paths:
        print("=" * 80)
        print(f"Chroma Path: {chroma_path}")
        print("=" * 80)
        print()

        client = chromadb.PersistentClient(
            path=str(chroma_path)
        )

        collections = client.list_collections()

        if not collections:
            print("No collections found.")
            print()
            continue

        for collection in collections:
            print(f"Collection: {collection.name}")
            print()

            result = collection.get(
                limit=1,
                include=[
                    "documents",
                    "metadatas",
                ],
            )

            ids = result.get("ids", [])
            documents = result.get("documents", [])
            metadatas = result.get("metadatas", [])

            if not ids:
                print("Collection is empty.")
                print()
                continue

            record_id = ids[0]
            page_content = (
                documents[0]
                if documents
                else None
            )
            metadata = (
                metadatas[0]
                if metadatas
                else {}
            )

            print("Single Chunk")
            print("-" * 40)

            print(
                f"Record ID: {record_id}"
            )

            print(
                f"page_content type: "
                f"{type(page_content).__name__}"
            )

            print(
                f"page_content length: "
                f"{len(page_content) if page_content else 0}"
            )

            print()

            print(
                f"Metadata Field Count: "
                f"{len(metadata)}"
            )

            print()

            print("Metadata Fields:")

            for index, key in enumerate(
                metadata.keys(),
                start=1,
            ):
                value = metadata[key]

                print(
                    f"{index}. "
                    f"{key} "
                    f"({type(value).__name__})"
                )

            print()

            print("Metadata Values:")

            for key, value in metadata.items():
                print(
                    f"{key}: "
                    f"{json.dumps(value, ensure_ascii=False, default=str)}"
                )

            print()

            ai_keywords = metadata.get(
                "ai_keywords"
            )

            print(
                "ai_keywords exists:",
                "ai_keywords" in metadata
            )

            print(
                "ai_keywords type:",
                type(ai_keywords).__name__
                if ai_keywords is not None
                else None,
            )

            print(
                "ai_keywords value:"
            )

            print(
                json.dumps(
                    ai_keywords,
                    ensure_ascii=False,
                    indent=2,
                    default=str,
                )
            )

            print()

            document_id = metadata.get(
                "document_id"
            )

            if document_id:
                print(
                    "Document ID:"
                )
                print(document_id)
                print()

                document_chunks = (
                    collection.get(
                        where={
                            "document_id": document_id
                        },
                        include=[
                            "documents",
                            "metadatas",
                        ],
                    )
                )

                chunk_ids = (
                    document_chunks.get(
                        "ids",
                        []
                    )
                )

                chunk_metadatas = (
                    document_chunks.get(
                        "metadatas",
                        []
                    )
                )

                chunk_documents = (
                    document_chunks.get(
                        "documents",
                        []
                    )
                )

                print(
                    "Same Document Chunk Count:"
                )
                print(
                    len(chunk_ids)
                )
                print()

                print(
                    "ai_keywords per Chunk:"
                )

                for index, chunk_metadata in enumerate(
                    chunk_metadatas,
                    start=1,
                ):
                    keywords = (
                        chunk_metadata.get(
                            "ai_keywords"
                        )
                    )

                    print(
                        f"Chunk {index}: "
                        f"{json.dumps(keywords, ensure_ascii=False, default=str)}"
                    )

                print()

                keyword_presence = [
                    "ai_keywords" in item
                    for item in chunk_metadatas
                ]

                print(
                    "ai_keywords present in all chunks:",
                    all(keyword_presence),
                )

                print(
                    "ai_keywords missing chunk count:",
                    keyword_presence.count(False),
                )

                print()

                metadata_keys = set()

                for chunk_metadata in chunk_metadatas:
                    metadata_keys.update(
                        chunk_metadata.keys()
                    )

                print(
                    "All Metadata Fields Used "
                    "By This Document:"
                )

                for index, key in enumerate(
                    sorted(metadata_keys),
                    start=1,
                ):
                    print(
                        f"{index}. {key}"
                    )

                print()

                print(
                    "Metadata Field Count "
                    "Across This Document:"
                )
                print(
                    len(metadata_keys)
                )

                print()

                print(
                    "Chunk Content Length:"
                )

                for index, content in enumerate(
                    chunk_documents,
                    start=1,
                ):
                    print(
                        f"Chunk {index}: "
                        f"{len(content) if content else 0}"
                    )

                print()

            print(
                "Test completed. "
                "No Chroma data modified."
            )

            print()


if __name__ == "__main__":
    main()