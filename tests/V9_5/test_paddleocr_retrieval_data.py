
"""
tests/V9_5/test_paddleocr_retrieval_data.py

AutoSearch V9

P5.4 Retrieval Evaluation
PaddleOCR ChromaDB Data Verification
"""

from rag.paper_chroma_storage import PaperChromaStorage


COLLECTION_NAME = "autosearch_papers_paddleocr_vl16"

EXPECTED_PAPERS = {
    "openalex:W7221458118": {
        "title": (
            "Scalable low-thermal-budget fabrication of "
            "suspended silicon nanowire devices"
        ),
        "chunks": 85,
    },
    "openalex:W7221469030": {
        "title": (
            "CardioNeural-SoC: An Indigenous "
            "RISC-V-Based Mixed-Signal System-on-Chip"
        ),
        "chunks": 39,
    },
    "openalex:W7221558939": {
        "title": (
            "g-C3N4-based smart nanocatalysts for "
            "photocatalytic cancer therapy"
        ),
        "chunks": 226,
    },
}


def main():
    storage = PaperChromaStorage(
        collection_name=COLLECTION_NAME
    )
    collection = storage.get_collection()

    print("===== P5.4 Retrieval Evaluation =====")
    print(f"Collection: {COLLECTION_NAME}")
    print(f"Total Chunks: {collection.count()}")

    total_expected = sum(
        paper["chunks"]
        for paper in EXPECTED_PAPERS.values()
    )

    all_passed = True

    for document_id, expected in EXPECTED_PAPERS.items():
        result = collection.get(
            where={"document_id": document_id},
            include=["documents", "metadatas"],
        )

        ids = result.get("ids", [])
        documents = result.get("documents", [])
        metadatas = result.get("metadatas", [])

        actual_count = len(ids)
        nonempty_count = sum(
            isinstance(text, str) and bool(text.strip())
            for text in documents
        )

        metadata_valid = all(
            metadata.get("document_id") == document_id
            and isinstance(metadata.get("chunk_index"), int)
            and isinstance(metadata.get("page_number"), int)
            for metadata in metadatas
        )

        passed = (
            actual_count == expected["chunks"]
            and nonempty_count == actual_count
            and metadata_valid
        )

        all_passed = all_passed and passed

        print(f"\nDocument ID: {document_id}")
        print(f"Title: {expected['title']}")
        print(f"Expected Chunks: {expected['chunks']}")
        print(f"Actual Chunks: {actual_count}")
        print(f"Non-empty Chunks: {nonempty_count}")
        print(f"Metadata Valid: {metadata_valid}")
        print(f"Result: {'PASS' if passed else 'FAIL'}")

    print("\n===== Summary =====")
    print(f"Expected Total Chunks: {total_expected}")
    print(
        f"Overall Result: "
        f"{'PASS' if all_passed else 'FAIL'}"
    )

    if not all_passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
