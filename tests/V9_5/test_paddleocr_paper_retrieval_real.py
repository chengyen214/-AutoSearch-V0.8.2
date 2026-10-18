"""
tests/V9_5/test_paddleocr_paper_retrieval_real.py

AutoSearch V9

PaddleOCR-VL-1.6 Paper Retrieval Real Test
"""

import pytest

from rag.paddleocr_paper_retrieval import (
    PADDLEOCR_COLLECTION_NAME,
    PaddleOCRPaperRetrieval,
)


DOCUMENT_ID = "openalex:W7221469030"

QUERY = (
    "What are the main contributions and system architecture "
    "of CardioNeural-SoC?"
)

TOP_K = 5


@pytest.fixture(scope="module")
def retrieval():
    """初始化真實 PaddleOCR Paper Retrieval。"""

    return PaddleOCRPaperRetrieval()


def test_real_collection_name(retrieval):
    """確認使用 PaddleOCR 專用 Collection。"""

    collection_name = (
        retrieval.storage.get_collection_name()
    )

    assert collection_name == PADDLEOCR_COLLECTION_NAME
    assert (
        collection_name
        == "autosearch_papers_paddleocr_vl16"
    )


def test_real_document_exists(retrieval):
    """確認指定論文已建立向量索引。"""

    collection = retrieval.storage.get_collection()

    response = collection.get(
        where={
            "document_id": DOCUMENT_ID,
        },
        include=["metadatas"],
    )

    count = len(response.get("ids", []))

    assert count > 0, (
        f"No indexed chunks found for {DOCUMENT_ID}"
    )

    print(f"Document ID: {DOCUMENT_ID}")
    print(f"Indexed chunks: {count}")

def test_real_retrieval(retrieval):
    """使用真實 Embedding 與 ChromaDB 執行 Top-K 檢索。"""

    result = retrieval.retrieve(
        query=QUERY,
        top_k=TOP_K,
        document_id=DOCUMENT_ID,
    )

    print(f"\nCollection: {result['collection_name']}")
    print(f"Document ID: {DOCUMENT_ID}")
    print(f"Query: {result['query']}")
    print(f"Results: {result['total_results']}")

    assert result["collection_name"] == (
        PADDLEOCR_COLLECTION_NAME
    )

    assert result["total_results"] > 0
    assert result["total_results"] <= TOP_K

    for rank, item in enumerate(result["results"], start=1):
        metadata = item["metadata"]

        print(f"\nRank {rank}")
        print(f"Chunk ID: {item['chunk_id']}")
        print(f"Distance: {item['distance']:.4f}")
        print(f"Metadata: {metadata}")
        print(f"Text:\n{item['text']}")

        assert item["chunk_id"]
        assert isinstance(item["text"], str)
        assert item["text"].strip()
        assert isinstance(item["distance"], float)
        assert metadata.get("document_id") == DOCUMENT_ID


def test_real_retrieval_respects_document_filter(retrieval):
    """確認檢索結果全部屬於指定論文。"""

    result = retrieval.retrieve(
        query=QUERY,
        top_k=TOP_K,
        document_id=DOCUMENT_ID,
    )

    assert result["results"]

    assert all(
        item["metadata"].get("document_id") == DOCUMENT_ID
        for item in result["results"]
    )


def test_real_retrieval_distance_is_valid(retrieval):
    """確認 Cosine Distance 為有效數值。"""

    result = retrieval.retrieve(
        query=QUERY,
        top_k=TOP_K,
        document_id=DOCUMENT_ID,
    )

    assert result["results"]

    for item in result["results"]:
        distance = item["distance"]

        assert distance == distance, (
            "Distance must not be NaN."
        )

        assert distance != float("inf")
        assert distance != float("-inf")