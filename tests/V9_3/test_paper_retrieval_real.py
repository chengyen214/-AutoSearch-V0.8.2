"""
tests/V9_3/test_paper_retrieval_real.py

AutoSearch V9

P5.2 Real Retrieval Test

測試：

    1. 驗證既有 Paper ChromaDB 索引
    2. 驗證 Query Embedding
    3. 執行真實 Vector Retrieval
    4. 驗證 Retrieval Metadata
    5. 驗證 document_id Filter

注意：

    只讀取既有索引，不新增或修改資料。
"""

import pytest

from rag.paper_embedding import PaperEmbedding
from rag.paper_chroma_storage import PaperChromaStorage
from rag.paper_retrieval import PaperRetrieval


EXPECTED_COLLECTION_NAME = "autosearch_papers_qwen3"
EXPECTED_MIN_CHUNKS = 624
DEFAULT_TOP_K = 5

TEST_QUERY = (
    "What are the challenges and recent advances "
    "in semiconductor technology?"
)


@pytest.fixture(scope="module")
def retrieval():
    embedder = PaperEmbedding()
    storage = PaperChromaStorage()

    return PaperRetrieval(
        embedder=embedder,
        storage=storage,
    )


def test_real_collection_exists(retrieval):
    storage = retrieval.storage

    assert storage.get_collection_name() == (
        EXPECTED_COLLECTION_NAME
    )

    total_chunks = storage.count()

    print(f"\nCollection: {storage.get_collection_name()}")
    print(f"Total chunks: {total_chunks}")

    assert total_chunks >= EXPECTED_MIN_CHUNKS


def test_real_query_embedding(retrieval):
    embedding = retrieval.embedder.embed_chunk(
        TEST_QUERY
    )

    assert isinstance(embedding, list)
    assert len(embedding) == 1024
    assert all(
        isinstance(value, (int, float))
        for value in embedding
    )

    print(f"\nQuery embedding dimension: {len(embedding)}")


def test_real_vector_retrieval(retrieval):
    result = retrieval.retrieve(
        query=TEST_QUERY,
        top_k=DEFAULT_TOP_K,
    )

    print(f"\nQuery: {result['query']}")
    print(f"Collection: {result['collection_name']}")
    print(f"Results: {result['total_results']}")

    assert result["collection_name"] == (
        EXPECTED_COLLECTION_NAME
    )
    assert 1 <= result["total_results"] <= DEFAULT_TOP_K

    for index, item in enumerate(result["results"], start=1):
        metadata = item["metadata"]

        print(f"\nResult {index}")
        print(f"Chunk ID: {item['chunk_id']}")
        print(f"Document ID: {metadata.get('document_id')}")
        print(f"Chunk Index: {metadata.get('chunk_index')}")
        print(f"Page Number: {metadata.get('page_number')}")
        print(f"Distance: {item['distance']}")
        print(f"Text: {item['text'][:200]}")

        assert isinstance(item["text"], str)
        assert item["text"].strip()
        assert isinstance(metadata, dict)
        assert metadata.get("document_id")
        assert metadata.get("chunk_id") == item["chunk_id"]
        assert isinstance(item["distance"], float)


def test_real_document_filter(retrieval):
    collection = retrieval.storage.get_collection()

    sample = collection.get(
        limit=1,
        include=["metadatas"],
    )

    ids = sample.get("ids", [])
    metadatas = sample.get("metadatas", [])

    assert ids
    assert metadatas

    document_id = metadatas[0].get("document_id")

    assert isinstance(document_id, str)
    assert document_id.strip()

    result = retrieval.retrieve(
        query=TEST_QUERY,
        top_k=DEFAULT_TOP_K,
        document_id=document_id,
    )

    print(f"\nFiltered document: {document_id}")
    print(f"Filtered results: {result['total_results']}")

    assert result["total_results"] >= 1

    for item in result["results"]:
        assert item["metadata"]["document_id"] == document_id