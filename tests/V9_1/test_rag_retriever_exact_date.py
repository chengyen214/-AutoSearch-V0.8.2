"""
tests/V9_1/test_rag_retriever_exact_date.py

AutoSearch V9

RAG Retriever Exact Date Integration Test
"""

from unittest.mock import Mock

from rag.retriever.retriever import (
    RAGRetriever,
)


def create_chroma_result():
    return {
        "ids": [
            "doc-0927",
            "doc-0928-a",
            "doc-0929",
            "doc-0928-b",
        ],
        "documents": [
            "2026-09-27 article",
            "2026-09-28 article A",
            "2026-09-29 article",
            "2026-09-28 article B",
        ],
        "metadatas": [
            {
                "title": "Sep 27",
                "url": "https://example.com/0927",
                "crawl_time": "2026-09-27T08:00:00+08:00",
                "matched_ai_keywords": '["TSMC"]',
            },
            {
                "title": "Sep 28 A",
                "url": "https://example.com/0928-a",
                "crawl_time": "2026-09-28T08:00:00+08:00",
                "matched_ai_keywords": '["TSMC"]',
            },
            {
                "title": "Sep 29",
                "url": "https://example.com/0929",
                "crawl_time": "2026-09-29T08:00:00+08:00",
                "matched_ai_keywords": '["TSMC"]',
            },
            {
                "title": "Sep 28 B",
                "url": "https://example.com/0928-b",
                "crawl_time": "2026-09-28T12:00:00+08:00",
                "matched_ai_keywords": '["TSMC"]',
            },
        ],
        "distances": [
            0.01,
            0.20,
            0.001,
            0.30,
        ],
    }


def create_retriever():
    chroma_retrieval = Mock()
    ranking = Mock()
    top_k_retrieval = Mock()
    retrieval_result_builder = Mock()

    retriever = RAGRetriever(
        chroma_retrieval=chroma_retrieval,
        ranking=ranking,
        top_k_retrieval=top_k_retrieval,
        retrieval_result_builder=retrieval_result_builder,
    )

    return (
        retriever,
        chroma_retrieval,
        ranking,
        top_k_retrieval,
        retrieval_result_builder,
    )


def test_retriever_passes_query_and_urls_to_chroma():
    (
        retriever,
        chroma_retrieval,
        ranking,
        top_k_retrieval,
        retrieval_result_builder,
    ) = create_retriever()

    chroma_result = create_chroma_result()

    chroma_retrieval.retrieve.return_value = chroma_result
    ranking.rank.return_value = {
        "ids": [],
        "documents": [],
        "metadatas": [],
        "distances": [],
    }
    top_k_retrieval.select.return_value = {
        "ids": [[]],
        "documents": [[]],
        "metadatas": [[]],
        "distances": [[]],
    }
    retrieval_result_builder.build.return_value = []

    urls = [
        "https://example.com/0928-a",
        "https://example.com/0928-b",
    ]

    retriever.search(
        query="2026年9月28日 DIGITIMES",
        urls=urls,
    )

    chroma_retrieval.retrieve.assert_called_once_with(
        "2026年9月28日 DIGITIMES",
        urls=urls,
    )


def test_retriever_passes_exact_date_query_to_ranking():
    (
        retriever,
        chroma_retrieval,
        ranking,
        top_k_retrieval,
        retrieval_result_builder,
    ) = create_retriever()

    chroma_result = create_chroma_result()

    chroma_retrieval.retrieve.return_value = chroma_result

    ranking_result = {
        "ids": [
            "doc-0928-a",
            "doc-0928-b",
        ],
        "documents": [
            "2026-09-28 article A",
            "2026-09-28 article B",
        ],
        "metadatas": [
            chroma_result["metadatas"][1],
            chroma_result["metadatas"][3],
        ],
        "distances": [
            0.20,
            0.30,
        ],
    }

    ranking.rank.return_value = ranking_result

    top_k_result = {
        "ids": [
            "doc-0928-a",
            "doc-0928-b",
        ],
        "documents": [
            "2026-09-28 article A",
            "2026-09-28 article B",
        ],
        "metadatas": [
            chroma_result["metadatas"][1],
            chroma_result["metadatas"][3],
        ],
        "distances": [
            0.20,
            0.30,
        ],
    }

    top_k_retrieval.select.return_value = top_k_result
    retrieval_result_builder.build.return_value = []

    query = "2026年9月28日 DIGITIMES有哪些重要消息？"

    retriever.search(
        query=query,
        urls=[
            "https://example.com/0928-a",
            "https://example.com/0928-b",
        ],
    )

    ranking.rank.assert_called_once_with(
        chroma_result,
        query=query,
    )


def test_retriever_preserves_exact_date_ranking_result():
    (
        retriever,
        chroma_retrieval,
        ranking,
        top_k_retrieval,
        retrieval_result_builder,
    ) = create_retriever()

    chroma_result = create_chroma_result()
    chroma_retrieval.retrieve.return_value = chroma_result

    ranking_result = {
        "ids": [
            "doc-0928-a",
            "doc-0928-b",
        ],
        "documents": [
            "2026-09-28 article A",
            "2026-09-28 article B",
        ],
        "metadatas": [
            chroma_result["metadatas"][1],
            chroma_result["metadatas"][3],
        ],
        "distances": [
            0.20,
            0.30,
        ],
    }

    ranking.rank.return_value = ranking_result
    top_k_retrieval.select.return_value = {
        "ids": [
            "doc-0928-a",
            "doc-0928-b",
        ],
        "documents": [
            "2026-09-28 article A",
            "2026-09-28 article B",
        ],
        "metadatas": [
            chroma_result["metadatas"][1],
            chroma_result["metadatas"][3],
        ],
        "distances": [
            0.20,
            0.30,
        ],
    }
    retrieval_result_builder.build.return_value = []

    retriever.search(
        query="2026年9月28日 DIGITIMES",
        urls=[
            "https://example.com/0928-a",
            "https://example.com/0928-b",
        ],
    )

    nested_result = top_k_retrieval.select.call_args[0][0]

    assert nested_result["ids"] == [
        [
            "doc-0928-a",
            "doc-0928-b",
        ]
    ]

    assert nested_result["metadatas"] == [
        [
            chroma_result["metadatas"][1],
            chroma_result["metadatas"][3],
        ]
    ]