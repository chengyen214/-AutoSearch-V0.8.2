"""
tests/V9_1/test_rag_ranking_exact_date.py

AutoSearch V7

RAG Ranking Exact Date Test
"""

from rag.retriever.ranking import (
    RetrievalRanking,
)


def create_result():
    return {
        "ids": [
            ["doc-0927", "doc-0928-a", "doc-0929", "doc-0928-b"],
        ],
        "documents": [
            [
                "2026-09-27 article",
                "2026-09-28 article A",
                "2026-09-29 article",
                "2026-09-28 article B",
            ],
        ],
        "metadatas": [
            [
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
        ],
        "distances": [
            [0.01, 0.20, 0.001, 0.30],
        ],
    }


def test_exact_date_query_filters_outside_dates():
    ranking = RetrievalRanking()

    result = ranking.rank(
        create_result(),
        query="2026年9月28日 DIGITIMES有哪些重要消息？",
    )

    assert result["ids"] == [
        "doc-0928-a",
        "doc-0928-b",
    ]


def test_exact_date_query_keeps_only_target_date():
    ranking = RetrievalRanking()

    result = ranking.rank(
        create_result(),
        query="2026-09-28",
    )

    assert result["ids"] == [
        "doc-0928-a",
        "doc-0928-b",
    ]


def test_exact_date_query_does_not_allow_high_similarity_outside_date():
    ranking = RetrievalRanking()

    result = ranking.rank(
        create_result(),
        query="2026/09/28 TSMC",
    )

    ids = result["ids"]

    assert "doc-0927" not in ids
    assert "doc-0929" not in ids

    assert set(ids) == {
        "doc-0928-a",
        "doc-0928-b",
    }