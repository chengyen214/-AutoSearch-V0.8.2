"""
rag/context/formatter.py

AutoSearch V7

RAG-6.2

Context Formatting

功能：

    將 RAG-5 Retriever 產生的 RetrievalResult
    轉換成標準化的 Context。

資料流程：

    RAG-5 Retriever
            ↓
    List[RetrievalResult]
            ↓
    ContextFormatter
            ↓
    Context
            ↓
    RAG-6.3 Metadata Handling

本檔案負責：

    1. 接收 RetrievalResult
    2. 建立 Context Entry
    3. 建立 Context Text
    4. 使用 RAG-6.1 Context Configuration

本檔案不負責：

    1. Retrieval
    2. ChromaDB
    3. Embedding
    4. Similarity Calculation
    5. Retrieval Ordering
    6. Metadata Filtering
    7. LLM
    8. Prompt
"""

from rag.retriever.retrieval_result import (
    RetrievalResult
)

from rag.context.config import (
    MAX_CONTEXT_CHUNKS,
    MAX_CONTEXT_CHARACTERS,
    SOURCE_SEPARATOR,
)


class ContextFormatter:
    """
    RAG-6.2 Context Formatter。

    將 RetrievalResult 轉換成標準化 Context。

    輸入：

        List[RetrievalResult]

    輸出：

        Context dictionary
    """

    def __init__(
        self,
        max_context_chunks=None,
        max_context_characters=None,
        source_separator=None,
    ):
        self.max_context_chunks = (
            max_context_chunks
            if max_context_chunks is not None
            else MAX_CONTEXT_CHUNKS
        )

        self.max_context_characters = (
            max_context_characters
            if max_context_characters is not None
            else MAX_CONTEXT_CHARACTERS
        )

        self.source_separator = (
            source_separator
            if source_separator is not None
            else SOURCE_SEPARATOR
        )

        if self.max_context_chunks <= 0:
            raise ValueError(
                "max_context_chunks must be greater than 0."
            )

        if self.max_context_characters <= 0:
            raise ValueError(
                "max_context_characters must be greater than 0."
            )

        if not isinstance(
            self.source_separator,
            str,
        ):
            raise TypeError(
                "source_separator must be a string."
            )

    def format(
        self,
        retrieval_results,
    ):
        """
        將 RetrievalResult 清單轉換成 Context。

        Parameters
        ----------
        retrieval_results:
            List[RetrievalResult]

        Returns
        -------
        dict
            標準化 Context。
        """

        if retrieval_results is None:
            raise ValueError(
                "retrieval_results cannot be None."
            )

        if not isinstance(
            retrieval_results,
            (list, tuple),
        ):
            raise TypeError(
                "retrieval_results must be a list or tuple."
            )

        selected_results = list(
            retrieval_results[
                :self.max_context_chunks
            ]
        )

        entries = []

        for index, result in enumerate(
            selected_results,
            start=1,
        ):
            entry = self._format_entry(
                result=result,
                source_index=index,
            )

            entries.append(entry)

        context_text = self._build_context_text(
            entries
        )

        return {
            "entries": entries,
            "context_text": context_text,
            "count": len(entries),
        }

    def _format_entry(
        self,
        result,
        source_index,
    ):
        """
        將單一 RetrievalResult
        轉換成 Context Entry。
        """

        if not isinstance(
            result,
            RetrievalResult,
        ):
            raise TypeError(
                "Each retrieval result must be "
                "a RetrievalResult."
            )

        metadata = result.metadata or {}

        return {
            "source_index": source_index,
            "document_id": result.document_id,
            "chunk_index": result.chunk_index,
            "title": metadata.get(
                "title"
            ),
            "url": metadata.get(
                "url"
            ),
            "content": result.chunk,
            "metadata": dict(metadata),
        }

    def _build_context_text(
        self,
        entries,
    ):
        """
        將 Context Entry 組合成 Context Text。
        """

        formatted_sources = []

        for entry in entries:
            metadata = entry.get(
                "metadata",
                {}
            )

            source_text = (
                f"[Source {entry['source_index']}]\n"
                f"Title: {entry['title'] or ''}\n"
                f"URL: {entry['url'] or ''}\n"
                f"Crawl Time: "
                f"{metadata.get('crawl_time') or ''}\n"
                f"Content:\n"
                f"{entry['content']}"
            )

            formatted_sources.append(
                source_text
            )

        context_text = self.source_separator.join(
            formatted_sources
        )

        if len(context_text) > (
            self.max_context_characters
        ):
            context_text = (
                context_text[
                    :self.max_context_characters
                ]
            )

        return context_text


__all__ = [
    "ContextFormatter",
]