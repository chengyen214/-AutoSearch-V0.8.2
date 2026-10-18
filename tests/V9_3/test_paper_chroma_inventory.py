
from collections import defaultdict
from pathlib import Path

import chromadb


def test_paper_chroma_inventory():
    persist_directory = (
        Path(__file__).resolve().parents[2]
        / "chroma_db"
        / "papers"
    )
    collection_name = "autosearch_papers_qwen3"
    target_document_id = "openalex:W7221570648"

    print(f"\nDatabase path: {persist_directory}")
    print(f"Collection: {collection_name}")

    if not persist_directory.is_dir():
        raise FileNotFoundError(
            f"Paper ChromaDB directory not found: {persist_directory}"
        )

    client = chromadb.PersistentClient(
        path=str(persist_directory)
    )

    collections = client.list_collections()
    collection_names = [
        item if isinstance(item, str) else item.name
        for item in collections
    ]

    if collection_name not in collection_names:
        raise LookupError(
            f"Collection '{collection_name}' not found. "
            f"Existing collections: {collection_names}"
        )

    collection = client.get_collection(
        name=collection_name
    )
    total_chunks = collection.count()

    papers = defaultdict(
        lambda: {
            "title": "",
            "source": "",
            "chunks": 0,
        }
    )
    missing_document_id_chunks = 0

    for offset in range(0, total_chunks, 500):
        result = collection.get(
            limit=500,
            offset=offset,
            include=["metadatas"],
        )

        for metadata in result.get("metadatas") or []:
            metadata = metadata or {}
            document_id = metadata.get("document_id")

            if not document_id:
                missing_document_id_chunks += 1
                document_id = "(missing document_id)"

            paper = papers[document_id]
            paper["chunks"] += 1

            if not paper["title"]:
                paper["title"] = (
                    metadata.get("title") or "(no title)"
                )

            if not paper["source"]:
                paper["source"] = metadata.get("source") or ""

    print("\n========== Paper ChromaDB Inventory ==========")
    print(f"Collection: {collection_name}")
    print(f"Total chunks: {total_chunks}")
    print(f"Unique document IDs: {len(papers)}")
    print(
        f"Chunks missing document_id: "
        f"{missing_document_id_chunks}"
    )

    print("\n========== Papers ==========")

    for index, (document_id, paper) in enumerate(
        sorted(papers.items()),
        start=1,
    ):
        print(f"\n{index}. {paper['title']}")
        print(f"   document_id: {document_id}")
        print(f"   chunks: {paper['chunks']}")

        if paper["source"]:
            print(f"   source: {paper['source']}")

    print("\n========== Target Paper Lookup ==========")

    paper = papers.get(target_document_id)

    if paper is None:
        print(f"Not found in ChromaDB: {target_document_id}")
    else:
        print(f"Title: {paper['title']}")
        print(f"Document ID: {target_document_id}")
        print(f"Chunks: {paper['chunks']}")
        print(f"Source: {paper['source'] or '(no source)'}")

    assert total_chunks > 0, "Paper Collection is empty."


if __name__ == "__main__":
    test_paper_chroma_inventory()
