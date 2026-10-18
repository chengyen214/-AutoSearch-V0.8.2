"""
tests/V9_5/test_paddleocr_paper_retrieval.py

AutoSearch V9

PaddleOCR-VL-1.6 Paper Retrieval Tests
"""

from unittest.mock import MagicMock, patch

import pytest

from rag.paddleocr_paper_retrieval import (
    DEFAULT_TOP_K,
    PADDLEOCR_COLLECTION_NAME,
    PaddleOCRPaperRetrieval,
)


@pytest.fixture
def retrieval():
    """建立使用 Mock 的 PaddleOCR Paper Retrieval。"""

    embedder = MagicMock()
    embedder.embed_chunk.return_value = [0.1, 0.2, 0.3]

    storage = MagicMock()
    storage.get_collection_name.return_value = (
        PADDLEOCR_COLLECTION_NAME
    )

    collection = MagicMock()
    collection.query.return_value = {
        "ids": [["chunk_1", "chunk_2"]],
        "documents": [
            [
                "First relevant chunk.",
                "Second relevant chunk.",
            ]
        ],
        "metadatas": [
            [
                {
                    "document_id": "openalex:W7221558939",
                    "chunk_index": 0,
                    "page_number": 1,
                    "source_type": "paddleocr_vl_1_6",
                },
                {
                    "document_id": "openalex:W7221558939",
                    "chunk_index": 1,
                    "page_number": 2,
                    "source_type": "paddleocr_vl_1_6",
                },
            ]
        ],
        "distances": [[0.12, 0.28]],
    }

    storage.get_collection.return_value = collection

    instance = PaddleOCRPaperRetrieval(
        embedder=embedder,
        storage=storage,
    )

    return instance, embedder, storage, collection


def test_default_top_k():
    """確認預設 Top-K。"""

    assert DEFAULT_TOP_K == 5


def test_default_collection_name():
    """確認 PaddleOCR 專用 Collection 名稱。"""

    assert (
        PADDLEOCR_COLLECTION_NAME
        == "autosearch_papers_paddleocr_vl16"
    )


def test_default_dependencies():
    """確認預設初始化使用正確的 Embedding 與 Collection。"""

    with (
        patch(
            "rag.paddleocr_paper_retrieval.PaperEmbedding"
        ) as mock_embedder,
        patch(
            "rag.paddleocr_paper_retrieval.PaperChromaStorage"
        ) as mock_storage,
    ):
        PaddleOCRPaperRetrieval()

    mock_embedder.assert_called_once_with()
    mock_storage.assert_called_once_with(
        collection_name=PADDLEOCR_COLLECTION_NAME
    )


def test_retrieve_returns_chunks(retrieval):
    """確認檢索結果格式正確。"""

    instance, embedder, storage, collection = retrieval

    with patch(
        "rag.paddleocr_paper_retrieval.PaperQueryFilter.build",
        return_value=None,
    ):
        result = instance.retrieve(
            "What are the main contributions?",
            top_k=2,
        )

    embedder.embed_chunk.assert_called_once_with(
        "What are the main contributions?"
    )
    storage.get_collection.assert_called_once_with()

    collection.query.assert_called_once_with(
        query_embeddings=[[0.1, 0.2, 0.3]],
        n_results=2,
        include=[
            "documents",
            "metadatas",
            "distances",
        ],
    )

    assert result["query"] == (
        "What are the main contributions?"
    )
    assert result["collection_name"] == (
        PADDLEOCR_COLLECTION_NAME
    )
    assert result["total_results"] == 2

    assert result["results"][0] == {
        "chunk_id": "chunk_1",
        "text": "First relevant chunk.",
        "metadata": {
            "document_id": "openalex:W7221558939",
            "chunk_index": 0,
            "page_number": 1,
            "source_type": "paddleocr_vl_1_6",
        },
        "distance": 0.12,
    }

    assert result["results"][1]["chunk_id"] == "chunk_2"
    assert result["results"][1]["distance"] == 0.28


def test_retrieve_strips_query_whitespace(retrieval):
    """確認 Query 前後空白會被移除。"""

    instance, embedder, _, _ = retrieval

    with patch(
        "rag.paddleocr_paper_retrieval.PaperQueryFilter.build",
        return_value=None,
    ):
        result = instance.retrieve("  semiconductor research  ")

    assert result["query"] == "semiconductor research"
    embedder.embed_chunk.assert_called_once_with(
        "semiconductor research"
    )


@pytest.mark.parametrize(
    "query",
    [
        "",
        " ",
        "\t",
        "\n",
    ],
)
def test_retrieve_rejects_empty_query(retrieval, query):
    """空白 Query 必須被拒絕。"""

    instance, embedder, storage, _ = retrieval

    with pytest.raises(
        ValueError,
        match="query cannot be empty",
    ):
        instance.retrieve(query)

    embedder.embed_chunk.assert_not_called()
    storage.get_collection.assert_not_called()


@pytest.mark.parametrize(
    "query",
    [
        None,
        123,
        ["semiconductor"],
        {"query": "semiconductor"},
    ],
)
def test_retrieve_rejects_non_string_query(retrieval, query):
    """非字串 Query 必須被拒絕。"""

    instance, embedder, _, _ = retrieval

    with pytest.raises(
        TypeError,
        match="query must be a string",
    ):
        instance.retrieve(query)

    embedder.embed_chunk.assert_not_called()


@pytest.mark.parametrize(
    "top_k",
    [
        0,
        -1,
        1.5,
        "5",
        None,
        True,
    ],
)
def test_retrieve_rejects_invalid_top_k(retrieval, top_k):
    """無效 Top-K 必須被拒絕。"""

    instance, embedder, _, _ = retrieval

    with pytest.raises(
        ValueError,
        match="top_k must be a positive integer",
    ):
        instance.retrieve(
            "semiconductor research",
            top_k=top_k,
        )

    embedder.embed_chunk.assert_not_called()


def test_retrieve_applies_document_id_filter(retrieval):
    """確認單一論文篩選條件會傳入 ChromaDB。"""

    instance, _, _, collection = retrieval

    where_filter = {
        "document_id": "openalex:W7221558939"
    }

    with patch(
        "rag.paddleocr_paper_retrieval.PaperQueryFilter.build",
        return_value=where_filter,
    ) as mock_filter:
        instance.retrieve(
            "semiconductor research",
            document_id="openalex:W7221558939",
        )

    mock_filter.assert_called_once_with(
        document_id="openalex:W7221558939",
        document_ids=None,
        source_type=None,
        page_number=None,
    )

    assert collection.query.call_args.kwargs["where"] == (
        where_filter
    )


def test_retrieve_applies_multiple_filters(retrieval):
    """確認多種 Metadata Filter 可以一起使用。"""

    instance, _, _, collection = retrieval

    where_filter = {
        "$and": [
            {
                "document_id": {
                    "$in": [
                        "openalex:W7221558939",
                        "openalex:W7221458118",
                    ]
                }
            },
            {
                "source_type": "paddleocr_vl_1_6"
            },
            {
                "page_number": 2
            },
        ]
    }

    with patch(
        "rag.paddleocr_paper_retrieval.PaperQueryFilter.build",
        return_value=where_filter,
    ) as mock_filter:
        instance.retrieve(
            "semiconductor research",
            document_ids=[
                "openalex:W7221558939",
                "openalex:W7221458118",
            ],
            source_type="paddleocr_vl_1_6",
            page_number=2,
        )

    mock_filter.assert_called_once_with(
        document_id=None,
        document_ids=[
            "openalex:W7221558939",
            "openalex:W7221458118",
        ],
        source_type="paddleocr_vl_1_6",
        page_number=2,
    )

    assert collection.query.call_args.kwargs["where"] == (
        where_filter
    )


def test_retrieve_omits_where_without_filter(retrieval):
    """沒有篩選條件時不應傳入 where。"""

    instance, _, _, collection = retrieval

    with patch(
        "rag.paddleocr_paper_retrieval.PaperQueryFilter.build",
        return_value=None,
    ):
        instance.retrieve("semiconductor research")

    assert "where" not in collection.query.call_args.kwargs


def test_retrieve_handles_empty_results(retrieval):
    """沒有匹配 Chunk 時應回傳空結果。"""

    instance, _, _, collection = retrieval

    collection.query.return_value = {
        "ids": [[]],
        "documents": [[]],
        "metadatas": [[]],
        "distances": [[]],
    }

    with patch(
        "rag.paddleocr_paper_retrieval.PaperQueryFilter.build",
        return_value=None,
    ):
        result = instance.retrieve(
            "unmatched research topic"
        )

    assert result["total_results"] == 0
    assert result["results"] == []


def test_retrieve_handles_missing_metadata(retrieval):
    """Metadata 為 None 時應回傳空字典。"""

    instance, _, _, collection = retrieval

    collection.query.return_value = {
        "ids": [["chunk_1"]],
        "documents": [["Chunk without metadata."]],
        "metadatas": [[None]],
        "distances": [[0.2]],
    }

    with patch(
        "rag.paddleocr_paper_retrieval.PaperQueryFilter.build",
        return_value=None,
    ):
        result = instance.retrieve("research topic")

    assert result["results"][0]["metadata"] == {}