"""
tests/V9_1/test_rag_retriever_real.py

AutoSearch V9.1

RAG Retriever Real Data Test
"""

from rag.retriever.retriever import (
    RAGRetriever,
)


class TestRAGRetrieverReal:
    """
    使用實際 ChromaDB 資料驗證完整 Retrieval Pipeline。
    """

    @staticmethod
    def _create_retriever():
        return RAGRetriever()

    @staticmethod
    def _print_results(
        query,
        results,
    ):
        print()
        print(f"Query: {query}")
        print(f"Result Count: {len(results)}")

        for index, result in enumerate(
            results,
            start=1,
        ):
            metadata = result.get_metadata()

            print()
            print(f"#{index}")
            print(f"title: {metadata.get('title')}")
            print(f"url: {metadata.get('url')}")
            print(
                f"crawl_time: "
                f"{metadata.get('crawl_time')}"
            )
            print(
                f"matched_ai_keywords: "
                f"{metadata.get('matched_ai_keywords')}"
            )
            print(
                f"distance: "
                f"{result.get_distance()}"
            )

    def test_real_general_query(self):
        """
        驗證一般 Query 使用真實 ChromaDB
        完成完整 Retrieval。
        """

        retriever = self._create_retriever()

        results = retriever.search(
            query="台積電"
        )

        self._print_results(
            "台積電",
            results,
        )

        assert isinstance(
            results,
            list,
        )

        assert len(results) <= (
            retriever.get_top_k()
        )

        for result in results:
            assert result.get_chunk()
            assert result.get_document_id()
            assert isinstance(
                result.get_metadata(),
                dict,
            )

    def test_real_recent_query(self):
        """
        驗證最近 Query 使用真實 ChromaDB
        執行時間相關 Ranking。
        """

        retriever = self._create_retriever()

        results = retriever.search(
            query="最近台積電"
        )

        self._print_results(
            "最近台積電",
            results,
        )

        assert isinstance(
            results,
            list,
        )

        assert len(results) <= (
            retriever.get_top_k()
        )

        for result in results:
            metadata = result.get_metadata()

            assert result.get_chunk()
            assert isinstance(
                metadata,
                dict,
            )

    def test_real_specific_month_query(self):
        """
        驗證指定年月 Query 使用真實 ChromaDB
        執行時間範圍 Ranking。
        """

        retriever = self._create_retriever()

        results = retriever.search(
            query="2026年9月 台積電"
        )

        self._print_results(
            "2026年9月 台積電",
            results,
        )

        assert isinstance(
            results,
            list,
        )

        assert len(results) <= (
            retriever.get_top_k()
        )

        for result in results:
            metadata = result.get_metadata()

            assert result.get_chunk()
            assert isinstance(
                metadata,
                dict,
            )