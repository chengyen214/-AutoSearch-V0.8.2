"""
rag/context/context_builder.py

AutoSearch V7

RAG-6.6

Context Builder

功能：

    建立 RAG-6 Context Builder Pipeline。

資料流程：

    RAG-5 Retriever
            ↓
    List[RetrievalResult]
            ↓
    ContextBuilder
            ↓
    ContextFormatter
            ↓
    MetadataHandler
            ↓
    ContextOrdering
            ↓
    ContextValidator
            ↓
    Context
            ↓
    RAG-7 LLM Generation

本檔案負責：

    1. 統一管理 RAG-6 Context Pipeline
    2. 呼叫 Context Formatter
    3. 呼叫 Metadata Handler
    4. 呼叫 Context Ordering
    5. 呼叫 Context Validator
    6. 回傳標準化 Context

本檔案不負責：

    1. Retrieval
    2. ChromaDB
    3. Embedding
    4. Similarity Calculation
    5. LLM
    6. Prompt
"""

from rag.context.formatter import (
    ContextFormatter,
)

from rag.context.metadata import (
    MetadataHandler,
)

from rag.context.ordering import (
    ContextOrdering,
)

from rag.context.validation import (
    ContextValidator,
)


class ContextBuilder:
    """
    RAG-6 Context Builder Pipeline。

    統一串接：

        Formatter
            ↓
        Metadata
            ↓
        Ordering
            ↓
        Validation
    """

    def __init__(
        self,
        formatter=None,
        metadata_handler=None,
        ordering=None,
        validator=None,
    ):
        self.formatter = (
            formatter
            if formatter is not None
            else ContextFormatter()
        )

        self.metadata_handler = (
            metadata_handler
            if metadata_handler is not None
            else MetadataHandler()
        )

        self.ordering = (
            ordering
            if ordering is not None
            else ContextOrdering()
        )

        self.validator = (
            validator
            if validator is not None
            else ContextValidator()
        )

    def build(
        self,
        retrieval_results,
    ):
        """
        建立完整 RAG-6 Context。

        Pipeline：

            RetrievalResult
                    ↓
                Ordering
                    ↓
                Formatting
                    ↓
                Metadata
                    ↓
                Validation

        回傳：

            dict
        """

        ordered_results = self.ordering.order(
            retrieval_results
        )

        context = self.formatter.format(
            ordered_results
        )

        context = self._apply_metadata(
            context
        )

        self.validator.validate(
            context
        )

        return context

    def _apply_metadata(
        self,
        context,
    ):
        """
        將 Formatter 建立的 Entry
        加入標準化 Metadata。

        保留原本 Context 結構：

            entries
            context_text
            count
        """

        entries = context["entries"]

        for entry in entries:
            metadata = self.metadata_handler.handle(
                entry.get("metadata", {})
            )

            entry["source_metadata"] = (
                metadata["source"]
            )

            entry["ai_metadata"] = (
                metadata["ai"]
            )

        return context


__all__ = [
    "ContextBuilder",
]