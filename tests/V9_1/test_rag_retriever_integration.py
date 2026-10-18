"""
tests/V9_1/test_rag_retriever_integration.py

AutoSearch V9.1

RAG Retriever Integration Test
"""

from rag.retriever.retriever import (
    RAGRetriever,
)


class FakeChromaRetrieval:
    """
    模擬 ChromaDB Candidate Retrieval。
    """

    def retrieve(
        self,
        query,
        urls=None,
    ):
        return {
            "ids": [
                [
                    "doc1::chunk_0",
                    "doc2::chunk_0",
                    "doc3::chunk_0",
                ]
            ],
            "documents": [
                [
                    "TSMC semiconductor technology.",
                    "Recent TSMC semiconductor news.",
                    "IC semiconductor research.",
                ]
            ],
            "metadatas": [
                [
                    {
                        "document_id": "doc1",
                        "url": "https://example.com/1",
                        "title": "TSMC Technology",
                        "crawl_time": "2026-09-01T10:00:00+08:00",
                        "matched_ai_keywords": '["TSMC"]',
                    },
                    {
                        "document_id": "doc2",
                        "url": "https://example.com/2",
                        "title": "Recent TSMC News",
                        "crawl_time": "2026-10-01T10:00:00+08:00",
                        "matched_ai_keywords": '["TSMC"]',
                    },
                    {
                        "document_id": "doc3",
                        "url": "https://example.com/3",
                        "title": "Semiconductor Research",
                        "crawl_time": "2026-08-01T10:00:00+08:00",
                        "matched_ai_keywords": "[]",
                    },
                ]
            ],
            "distances": [
                [
                    0.10,
                    0.20,
                    0.30,
                ]
            ],
        }

    def get_candidate_k(self):
        return 20


class FakeRanking:
    """
    驗證 RAGRetriever 是否實際呼叫 Ranking。
    """

    def __init__(self):
        self.called = False
        self.received_query = None

    def rank(
        self,
        result,
        query,
    ):
        self.called = True
        self.received_query = query

        ids = result["ids"][0]
        documents = result["documents"][0]
        metadatas = result["metadatas"][0]
        distances = result["distances"][0]

        return {
            "ids": ids,
            "documents": documents,
            "metadatas": metadatas,
            "distances": distances,
        }


class FakeTopKRetrieval:
    """
    驗證 Ranking 結果是否傳入 Top-K。
    """

    def __init__(self):
        self.received_result = None

    def select(
        self,
        result,
    ):
        self.received_result = result

        return {
            "ids": result["ids"][0][:2],
            "documents": result["documents"][0][:2],
            "metadatas": result["metadatas"][0][:2],
            "distances": result["distances"][0][:2],
        }

    def get_top_k(self):
        return 5


class TestRAGRetrieverIntegration:
    """
    RAGRetriever Integration Test。
    """

    def test_ranking_is_called_before_top_k(self):
        """
        驗證 Retrieval 流程包含 Ranking。
        """

        chroma_retrieval = (
            FakeChromaRetrieval()
        )

        ranking = FakeRanking()

        top_k_retrieval = (
            FakeTopKRetrieval()
        )

        retriever = RAGRetriever(
            chroma_retrieval=chroma_retrieval,
            ranking=ranking,
            top_k_retrieval=top_k_retrieval,
        )

        results = retriever.search(
            query="最近台積電"
        )

        assert ranking.called is True

        assert (
            ranking.received_query
            == "最近台積電"
        )

        assert (
            top_k_retrieval.received_result
            is not None
        )

        assert len(results) == 2

    def test_retrieval_result_preserves_metadata(self):
        """
        驗證 Ranking 後的 Metadata
        能一路保留到 RetrievalResult。
        """

        retriever = RAGRetriever(
            chroma_retrieval=(
                FakeChromaRetrieval()
            ),
            ranking=FakeRanking(),
            top_k_retrieval=(
                FakeTopKRetrieval()
            ),
        )

        results = retriever.search(
            query="最近台積電"
        )

        assert len(results) == 2

        assert (
            results[0].metadata["url"]
            == "https://example.com/1"
        )

        assert (
            results[0].metadata["crawl_time"]
            == "2026-09-01T10:00:00+08:00"
        )

        assert (
            results[0].metadata[
                "matched_ai_keywords"
            ]
            == '["TSMC"]'
        )

    def test_general_query_goes_through_ranking(self):
        """
        驗證一般 Query 也會經過 Ranking。
        """

        ranking = FakeRanking()

        retriever = RAGRetriever(
            chroma_retrieval=(
                FakeChromaRetrieval()
            ),
            ranking=ranking,
            top_k_retrieval=(
                FakeTopKRetrieval()
            ),
        )

        results = retriever.search(
            query="台積電"
        )

        assert ranking.called is True

        assert (
            ranking.received_query
            == "台積電"
        )

        assert len(results) == 2