"""
tests/V9_1/test_rag_ranking.py

AutoSearch V7

RAG Retrieval Ranking Test

測試：

    1. Similarity
    2. matched_ai_keywords
    3. General Query Ranking
    4. Recent Query Ranking
    5. This Month Query
    6. Previous Month Query
    7. Specific Month Query
    8. Recent N Days Query
    9. Recent N Weeks Query
    10. Exact Date Query
    11. Invalid crawl_time
    12. Original Result Preservation
    13. Result Alignment
"""

import copy
from datetime import (
    datetime,
    timezone,
    timedelta,
)

from rag.retriever.ranking import (
    RetrievalRanking,
)


LOCAL_TIMEZONE = timezone(
    timedelta(hours=8)
)


class TestRetrievalRanking:

    def setup_method(self):
        self.ranking = RetrievalRanking()

        self.now = datetime(
            2026,
            10,
            7,
            12,
            0,
            0,
            tzinfo=LOCAL_TIMEZONE,
        )

    @staticmethod
    def _build_result(
        items
    ):
        return {
            "ids": [
                [
                    item["id"]
                    for item in items
                ]
            ],
            "documents": [
                [
                    item["document"]
                    for item in items
                ]
            ],
            "metadatas": [
                [
                    item["metadata"]
                    for item in items
                ]
            ],
            "distances": [
                [
                    item["distance"]
                    for item in items
                ]
            ],
        }

    def test_similarity_from_distance(self):
        similarity = (
            self.ranking._similarity_from_distance(
                0.2
            )
        )

        assert similarity == 0.8

    def test_similarity_is_clamped(self):
        assert (
            self.ranking._similarity_from_distance(
                -0.5
            )
            == 1.0
        )

        assert (
            self.ranking._similarity_from_distance(
                1.5
            )
            == 0.0
        )

    def test_keyword_score_with_matched_keywords(self):
        metadata = {
            "matched_ai_keywords": [
                "TSMC",
                "CoWoS",
            ]
        }

        score = (
            self.ranking._keyword_score(
                metadata
            )
        )

        assert score == 1.0

    def test_keyword_score_without_matched_keywords(self):
        metadata = {
            "matched_ai_keywords": []
        }

        score = (
            self.ranking._keyword_score(
                metadata
            )
        )

        assert score == 0.0

    def test_keyword_score_json_string(self):
        metadata = {
            "matched_ai_keywords": (
                '["TSMC", "CoWoS"]'
            )
        }

        score = (
            self.ranking._keyword_score(
                metadata
            )
        )

        assert score == 1.0

    def test_general_query_is_not_time_query(self):
        query = (
            "台積電 CoWoS 技術"
        )

        assert (
            self.ranking._is_time_query(
                query
            )
            is False
        )

    def test_recent_query_is_time_query(self):
        query = (
            "最近台積電有哪些消息"
        )

        assert (
            self.ranking._is_time_query(
                query
            )
            is True
        )

    def test_month_query_is_time_query(self):
        query = (
            "這個月有哪些半導體新聞"
        )

        assert (
            self.ranking._is_time_query(
                query
            )
            is True
        )

    def test_year_month_query_is_time_query(self):
        query = (
            "2026 年 9 月有哪些半導體新聞"
        )

        assert (
            self.ranking._is_time_query(
                query
            )
            is True
        )

    def test_exact_date_query_is_time_query(self):
        query = (
            "2026年9月28日"
        )

        assert (
            self.ranking._is_time_query(
                query
            )
            is True
        )

    def test_parse_exact_date_range(self):
        start, end = (
            self.ranking._parse_time_range(
                "2026年9月28日",
                now=self.now,
            )
        )

        assert start == datetime(
            2026,
            9,
            28,
            tzinfo=LOCAL_TIMEZONE,
        )

        assert end == datetime(
            2026,
            9,
            29,
            tzinfo=LOCAL_TIMEZONE,
        )

    def test_parse_exact_date_dash_range(self):
        start, end = (
            self.ranking._parse_time_range(
                "2026-09-28",
                now=self.now,
            )
        )

        assert start == datetime(
            2026,
            9,
            28,
            tzinfo=LOCAL_TIMEZONE,
        )

        assert end == datetime(
            2026,
            9,
            29,
            tzinfo=LOCAL_TIMEZONE,
        )

    def test_parse_exact_date_slash_range(self):
        start, end = (
            self.ranking._parse_time_range(
                "2026/09/28",
                now=self.now,
            )
        )

        assert start == datetime(
            2026,
            9,
            28,
            tzinfo=LOCAL_TIMEZONE,
        )

        assert end == datetime(
            2026,
            9,
            29,
            tzinfo=LOCAL_TIMEZONE,
        )

    def test_parse_recent_time_range(self):
        start, end = (
            self.ranking._parse_time_range(
                "最近台積電消息",
                now=self.now,
            )
        )

        assert end == self.now

        assert start == (
            self.now
            - timedelta(days=30)
        )

    def test_parse_this_month_range(self):
        start, end = (
            self.ranking._parse_time_range(
                "這個月有哪些半導體新聞",
                now=self.now,
            )
        )

        assert start == datetime(
            2026,
            10,
            1,
            tzinfo=LOCAL_TIMEZONE,
        )

        assert end == self.now

    def test_parse_previous_month_range(self):
        start, end = (
            self.ranking._parse_time_range(
                "上個月有哪些半導體新聞",
                now=self.now,
            )
        )

        assert start == datetime(
            2026,
            9,
            1,
            tzinfo=LOCAL_TIMEZONE,
        )

        assert end == datetime(
            2026,
            10,
            1,
            tzinfo=LOCAL_TIMEZONE,
        )

    def test_parse_specific_month_range(self):
        start, end = (
            self.ranking._parse_time_range(
                "2026 年 9 月有哪些半導體新聞",
                now=self.now,
            )
        )

        assert start == datetime(
            2026,
            9,
            1,
            tzinfo=LOCAL_TIMEZONE,
        )

        assert end == datetime(
            2026,
            10,
            1,
            tzinfo=LOCAL_TIMEZONE,
        )

    def test_parse_recent_days_range(self):
        start, end = (
            self.ranking._parse_time_range(
                "近 7 天有哪些消息",
                now=self.now,
            )
        )

        assert start == (
            self.now
            - timedelta(days=7)
        )

        assert end == self.now

    def test_parse_recent_weeks_range(self):
        start, end = (
            self.ranking._parse_time_range(
                "近三週有哪些消息",
                now=self.now,
            )
        )

        assert start == (
            self.now
            - timedelta(weeks=3)
        )

        assert end == self.now

    def test_parse_recent_query_time_score(self):
        crawl_time = (
            self.now
            - timedelta(days=5)
        )

        score = (
            self.ranking._time_range_score(
                crawl_time,
                self.now - timedelta(days=30),
                self.now,
                now=self.now,
            )
        )

        assert score == 1.0

    def test_outside_time_range_score(self):
        crawl_time = (
            self.now
            - timedelta(days=45)
        )

        score = (
            self.ranking._time_range_score(
                crawl_time,
                self.now - timedelta(days=30),
                self.now,
                now=self.now,
            )
        )

        assert score == 0.0

    def test_invalid_crawl_time_score(self):
        crawl_time = (
            self.ranking._parse_crawl_time(
                "invalid-date"
            )
        )

        assert crawl_time is None

        score = (
            self.ranking._time_range_score(
                crawl_time,
                self.now - timedelta(days=30),
                self.now,
                now=self.now,
            )
        )

        assert score == 0.0

    def test_general_query_ranking(self):
        items = [
            {
                "id": "chunk_1",
                "document": "Document 1",
                "metadata": {
                    "matched_ai_keywords": []
                },
                "distance": 0.10,
            },
            {
                "id": "chunk_2",
                "document": "Document 2",
                "metadata": {
                    "matched_ai_keywords": [
                        "CoWoS"
                    ]
                },
                "distance": 0.20,
            },
            {
                "id": "chunk_3",
                "document": "Document 3",
                "metadata": {
                    "matched_ai_keywords": []
                },
                "distance": 0.40,
            },
        ]

        result = self._build_result(
            items
        )

        ranked = self.ranking.rank(
            result,
            "台積電 CoWoS 技術",
        )

        assert ranked["ids"] == [
            "chunk_2",
            "chunk_1",
            "chunk_3",
        ]

    def test_recent_query_prefers_recent_documents(self):
        items = [
            {
                "id": "old",
                "document": "Old",
                "metadata": {
                    "matched_ai_keywords": [],
                    "crawl_time": (
                        "2026-09-20T12:00:00+08:00"
                    ),
                },
                "distance": 0.05,
            },
            {
                "id": "recent",
                "document": "Recent",
                "metadata": {
                    "matched_ai_keywords": [],
                    "crawl_time": (
                        "2026-10-06T12:00:00+08:00"
                    ),
                },
                "distance": 0.10,
            },
        ]

        result = self._build_result(
            items
        )

        ranked = self.ranking.rank(
            result,
            "最近有哪些半導體消息",
        )

        assert ranked["ids"] == [
            "recent",
            "old",
        ]

    def test_previous_month_ranking(self):
        items = [
            {
                "id": "september",
                "document": "September",
                "metadata": {
                    "matched_ai_keywords": [],
                    "crawl_time": (
                        "2026-09-20T12:00:00+08:00"
                    ),
                },
                "distance": 0.20,
            },
            {
                "id": "october",
                "document": "October",
                "metadata": {
                    "matched_ai_keywords": [],
                    "crawl_time": (
                        "2026-10-05T12:00:00+08:00"
                    ),
                },
                "distance": 0.05,
            },
        ]

        result = self._build_result(
            items
        )

        ranked = self.ranking.rank(
            result,
            "上個月有哪些半導體新聞",
        )

        assert ranked["ids"] == [
            "september",
            "october",
        ]

    def test_specific_month_ranking(self):
        items = [
            {
                "id": "target_month",
                "document": "Target Month",
                "metadata": {
                    "matched_ai_keywords": [],
                    "crawl_time": (
                        "2026-09-15T12:00:00+08:00"
                    ),
                },
                "distance": 0.20,
            },
            {
                "id": "other_month",
                "document": "Other Month",
                "metadata": {
                    "matched_ai_keywords": [],
                    "crawl_time": (
                        "2026-08-15T12:00:00+08:00"
                    ),
                },
                "distance": 0.05,
            },
        ]

        result = self._build_result(
            items
        )

        ranked = self.ranking.rank(
            result,
            "2026 年 9 月有哪些半導體新聞",
        )

        assert ranked["ids"] == [
            "target_month",
            "other_month",
        ]

    def test_time_query_combines_similarity_keyword_and_time(self):
        items = [
            {
                "id": "recent_keyword",
                "document": "Recent Keyword",
                "metadata": {
                    "matched_ai_keywords": [
                        "CoWoS"
                    ],
                    "crawl_time": (
                        "2026-10-06T12:00:00+08:00"
                    ),
                },
                "distance": 0.30,
            },
            {
                "id": "similar_old",
                "document": "Similar Old",
                "metadata": {
                    "matched_ai_keywords": [],
                    "crawl_time": (
                        "2026-08-01T12:00:00+08:00"
                    ),
                },
                "distance": 0.05,
            },
        ]

        result = self._build_result(
            items
        )

        ranked = self.ranking.rank(
            result,
            "最近 CoWoS 有哪些消息",
        )

        assert ranked["ids"] == [
            "recent_keyword",
            "similar_old",
        ]

    def test_original_result_is_not_modified(self):
        items = [
            {
                "id": "chunk_1",
                "document": "Document 1",
                "metadata": {
                    "matched_ai_keywords": [
                        "CoWoS"
                    ],
                    "crawl_time": (
                        "2026-10-06T12:00:00+08:00"
                    ),
                },
                "distance": 0.20,
            },
            {
                "id": "chunk_2",
                "document": "Document 2",
                "metadata": {
                    "matched_ai_keywords": [],
                    "crawl_time": (
                        "2026-09-01T12:00:00+08:00"
                    ),
                },
                "distance": 0.10,
            },
        ]

        result = self._build_result(
            items
        )

        original = copy.deepcopy(
            result
        )

        self.ranking.rank(
            result,
            "最近 CoWoS 消息",
        )

        assert result == original

    def test_result_alignment(self):
        items = [
            {
                "id": "a",
                "document": "Document A",
                "metadata": {
                    "matched_ai_keywords": []
                },
                "distance": 0.30,
            },
            {
                "id": "b",
                "document": "Document B",
                "metadata": {
                    "matched_ai_keywords": [
                        "CoWoS"
                    ]
                },
                "distance": 0.20,
            },
            {
                "id": "c",
                "document": "Document C",
                "metadata": {
                    "matched_ai_keywords": []
                },
                "distance": 0.10,
            },
        ]

        result = self._build_result(
            items
        )

        ranked = self.ranking.rank(
            result,
            "CoWoS 技術",
        )

        for index, chunk_id in enumerate(
            ranked["ids"]
        ):
            if chunk_id == "a":
                assert (
                    ranked["documents"][index]
                    == "Document A"
                )
                assert (
                    ranked["distances"][index]
                    == 0.30
                )

            elif chunk_id == "b":
                assert (
                    ranked["documents"][index]
                    == "Document B"
                )
                assert (
                    ranked["distances"][index]
                    == 0.20
                )

            elif chunk_id == "c":
                assert (
                    ranked["documents"][index]
                    == "Document C"
                )
                assert (
                    ranked["distances"][index]
                    == 0.10
                )


def main():
    print(
        "RetrievalRanking tests are ready."
    )
    print(
        "Run with:"
    )
    print(
        "python -m pytest "
        "tests/V9_1/test_rag_ranking.py -v"
    )


if __name__ == "__main__":
    main()