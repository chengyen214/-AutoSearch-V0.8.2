"""
rag/paper_retrieval.py

AutoSearch V9

P5.2 Query Embedding + Vector Retrieval

功能：

    1. 將使用者 Query 轉換為 Embedding
    2. 執行 Paper ChromaDB 向量搜尋
    3. 支援 Metadata Filter
    4. 回傳 Top-K Chunk Results

不負責：

    1. PDF Chunking
    2. Paper Indexing
    3. Embedding Index
    4. Context Expansion
    5. LLM
"""

from rag.paper_embedding import PaperEmbedding
from rag.paper_chroma_storage import PaperChromaStorage
from rag.paper_query_filter import PaperQueryFilter


DEFAULT_TOP_K = 5


class PaperRetrieval:
    """Paper RAG 向量檢索。"""

    def __init__(
        self,
        embedder=None,
        storage=None,
    ):
        self.embedder = (
            embedder
            if embedder is not None
            else PaperEmbedding()
        )

        self.storage = (
            storage
            if storage is not None
            else PaperChromaStorage()
        )

    @staticmethod
    def _validate_query(query):
        """驗證查詢文字。"""

        if not isinstance(query, str):
            raise TypeError(
                "query must be a string."
            )

        if not query.strip():
            raise ValueError(
                "query cannot be empty."
            )

        return query.strip()

    @staticmethod
    def _validate_top_k(top_k):
        """驗證 Top-K 數量。"""

        if (
            not isinstance(top_k, int)
            or isinstance(top_k, bool)
            or top_k < 1
        ):
            raise ValueError(
                "top_k must be a positive integer."
            )

    def retrieve(
        self,
        query,
        top_k=DEFAULT_TOP_K,
        document_id=None,
        document_ids=None,
        source_type=None,
        page_number=None,
    ):
        """
        執行 Paper Vector Retrieval。

        Args:
            query: 使用者查詢文字。
            top_k: 最多回傳的 Chunk 數量。
            document_id: 指定單一論文。
            document_ids: 指定多篇論文。
            source_type: 指定來源類型。
            page_number: 指定 PDF 頁碼。

        Returns:
            dict:
                query
                collection_name
                total_results
                results
        """

        query = self._validate_query(query)
        self._validate_top_k(top_k)

        where_filter = PaperQueryFilter.build(
            document_id=document_id,
            document_ids=document_ids,
            source_type=source_type,
            page_number=page_number,
        )

        query_embedding = self.embedder.embed_chunk(
            query
        )

        collection = self.storage.get_collection()

        query_kwargs = {
            "query_embeddings": [query_embedding],
            "n_results": top_k,
            "include": [
                "documents",
                "metadatas",
                "distances",
            ],
        }

        if where_filter is not None:
            query_kwargs["where"] = where_filter

        response = collection.query(
            **query_kwargs
        )

        ids = response.get("ids", [[]])[0]
        documents = response.get("documents", [[]])[0]
        metadatas = response.get("metadatas", [[]])[0]
        distances = response.get("distances", [[]])[0]

        results = []

        for record_id, text, metadata, distance in zip(
            ids,
            documents,
            metadatas,
            distances,
        ):
            results.append({
                "chunk_id": record_id,
                "text": text,
                "metadata": metadata or {},
                "distance": float(distance),
            })

        return {
            "query": query,
            "collection_name": (
                self.storage.get_collection_name()
            ),
            "total_results": len(results),
            "results": results,
        }


__all__ = [
    "PaperRetrieval",
    "DEFAULT_TOP_K",
]