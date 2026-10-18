"""
tests/V9_3/inspect_paper_eval_chunks.py

AutoSearch V9

Paper Retrieval Evaluation
Candidate Chunk Inspection
"""

from pathlib import Path
import json

from rag.paper_chroma_storage import PaperChromaStorage


OUTPUT_PATH = Path(
    "tests/V9_3/fixtures/paper_eval_candidates.json"
)

DOCUMENT_IDS = [
    "openalex:W4248373384",
    "openalex:W7221458118",
    "openalex:W7221558939",
    "openalex:W7221570648",
    "openalex:W7221469030",
    "openalex:W7221471520",
]

CANDIDATES_PER_DOCUMENT = 5


def select_candidates(chunks):
    """依 Chunk 順序選取分布於全文的候選內容。"""

    ids = chunks.get("ids") or []
    documents = chunks.get("documents") or []
    metadatas = chunks.get("metadatas") or []

    items = []

    for chunk_id, document, metadata in zip(
        ids,
        documents,
        metadatas,
    ):
        if not isinstance(document, str) or not document.strip():
            continue

        metadata = metadata or {}

        items.append({
            "chunk_id": chunk_id,
            "document_id": metadata.get("document_id"),
            "chunk_index": metadata.get("chunk_index"),
            "page_number": metadata.get("page_number"),
            "source_type": metadata.get("source_type"),
            "text": document,
        })

    items.sort(
        key=lambda item: (
            item["chunk_index"]
            if isinstance(item["chunk_index"], int)
            else -1
        )
    )

    if len(items) <= CANDIDATES_PER_DOCUMENT:
        return items

    indexes = [
        round(
            i * (len(items) - 1)
            / (CANDIDATES_PER_DOCUMENT - 1)
        )
        for i in range(CANDIDATES_PER_DOCUMENT)
    ]

    return [items[index] for index in indexes]


def main():
    storage = PaperChromaStorage()
    candidates = []

    for document_id in DOCUMENT_IDS:
        chunks = storage.get_document_chunks(document_id)
        selected = select_candidates(chunks)

        print(f"\n{document_id}: {len(selected)} candidates")

        for item in selected:
            print(
                f"  chunk_index={item['chunk_index']}, "
                f"page_number={item['page_number']}, "
                f"chunk_id={item['chunk_id']}"
            )

        candidates.extend(selected)

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_PATH.write_text(
        json.dumps(
            {
                "collection": storage.get_collection_name(),
                "total_candidates": len(candidates),
                "candidates": candidates,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"\nTotal candidates: {len(candidates)}")
    print(f"Output: {OUTPUT_PATH}")
def print_candidates(start=0, count=5):
    """分批檢視候選 Chunk 的文字內容。"""

    data = json.loads(
        OUTPUT_PATH.read_text(encoding="utf-8")
    )

    candidates = data["candidates"]
    selected = candidates[start:start + count]

    for item in selected:
        print("\n" + "=" * 60)
        print("Chunk ID:", item["chunk_id"])
        print("Document ID:", item["document_id"])
        print("Chunk Index:", item["chunk_index"])
        print("Page Number:", item["page_number"])
        print("-" * 60)
        print(item["text"])



if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--count", type=int, default=5)
    parser.add_argument(
        "--generate",
        action="store_true",
        help="從 ChromaDB 重新產生候選 Chunk",
    )
    args = parser.parse_args()

    if args.generate or not OUTPUT_PATH.is_file():
        main()

    print_candidates(args.start, args.count)
