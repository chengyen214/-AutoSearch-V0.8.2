
"""
tests/V9_5/test_paddleocr_chroma_inventory.py

AutoSearch V9

PaddleOCR ChromaDB Index Inventory
"""

from collections import Counter

from rag.paper_chroma_storage import PaperChromaStorage


COLLECTION_NAME = "autosearch_papers_paddleocr_vl16"


def main():
    storage = PaperChromaStorage(
        collection_name=COLLECTION_NAME
    )
    collection = storage.get_collection()

    result = collection.get(
        include=["metadatas"],
    )

    ids = result.get("ids", [])
    metadatas = result.get("metadatas", [])

    counts = Counter()
    chunk_indices = {}
    missing_document_ids = 0
    missing_chunk_indices = 0
    missing_page_numbers = 0

    for chunk_id, metadata in zip(ids, metadatas):
        document_id = metadata.get("document_id")

        if not document_id:
            missing_document_ids += 1
            continue

        counts[document_id] += 1

        chunk_index = metadata.get("chunk_index")

        if not isinstance(chunk_index, int):
            missing_chunk_indices += 1
        else:
            chunk_indices.setdefault(
                document_id, []
            ).append(chunk_index)

        page_number = metadata.get("page_number")

        if not isinstance(page_number, int):
            missing_page_numbers += 1

    print("===== PaddleOCR ChromaDB Inventory =====")
    print(f"Collection: {COLLECTION_NAME}")
    print(f"Collection Count: {collection.count()}")
    print(f"Retrieved IDs: {len(ids)}")
    print(f"Retrieved Metadata: {len(metadatas)}")

    print("\n===== Documents =====")

    for document_id, count in sorted(counts.items()):
        indices = chunk_indices.get(document_id, [])
        duplicate_indices = sorted(
            index
            for index, frequency in Counter(indices).items()
            if frequency > 1
        )

        print(f"\nDocument ID: {document_id}")
        print(f"Chunk Count: {count}")
        print(f"Unique Chunk Indices: {len(set(indices))}")
        print(f"Duplicate Chunk Indices: {duplicate_indices}")

        if indices:
            print(f"Min Chunk Index: {min(indices)}")
            print(f"Max Chunk Index: {max(indices)}")

    print("\n===== Metadata Issues =====")
    print(f"Missing document_id: {missing_document_ids}")
    print(f"Invalid chunk_index: {missing_chunk_indices}")
    print(f"Invalid page_number: {missing_page_numbers}")


if __name__ == "__main__":
    main()
