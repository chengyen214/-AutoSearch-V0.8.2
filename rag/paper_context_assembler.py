"""
rag/paper_context_assembler.py

AutoSearch V9

P5.3 Context Assembly

功能：

    1. 移除重複 Chunk
    2. 依文件與 Chunk 順序排列
    3. 限制 Context 最大字元數
    4. 保留來源 Metadata
    5. 回傳組裝後的 Context

不負責：

    1. Vector Retrieval
    2. Chunk Expansion
    3. Embedding
    4. LLM Generation
"""

DEFAULT_MAX_CONTEXT_CHARS = 6000


class PaperContextAssembler:
    """Paper RAG Context Assembly。"""

    def __init__(
        self,
        max_context_chars=DEFAULT_MAX_CONTEXT_CHARS,
    ):
        self._validate_max_context_chars(
            max_context_chars
        )
        self.max_context_chars = max_context_chars

    @staticmethod
    def _validate_max_context_chars(value):
        """驗證 Context 字元數上限。"""

        if (
            not isinstance(value, int)
            or isinstance(value, bool)
            or value < 1
        ):
            raise ValueError(
                "max_context_chars must be a positive integer."
            )

    @staticmethod
    def _validate_results(retrieval_result):
        """驗證 Retrieval Results。"""

        if not isinstance(retrieval_result, dict):
            raise TypeError(
                "retrieval_result must be a dictionary."
            )

        results = retrieval_result.get("results")

        if not isinstance(results, list):
            raise ValueError(
                "retrieval_result must contain a results list."
            )

        return results

    @staticmethod
    def _sort_key(item):
        """依文件 ID 與 Chunk 索引排序。"""

        metadata = item["metadata"]

        return (
            metadata["document_id"],
            metadata["chunk_index"],
            item["chunk_id"],
        )

    @staticmethod
    def _build_header(item):
        """建立 Chunk 來源標頭。"""

        metadata = item["metadata"]

        document_id = metadata["document_id"]
        chunk_index = metadata["chunk_index"]
        page_number = metadata.get("page_number")

        header = (
            f"[document_id={document_id}"
            f" | chunk_index={chunk_index}"
        )

        if page_number is not None:
            header += f" | page_number={page_number}"

        return header + "]\n"

    @staticmethod
    def _deduplicate(results):
        """依 chunk_id 去除重複結果。"""

        unique = {}
        duplicate_count = 0

        for item in results:
            if not isinstance(item, dict):
                raise ValueError(
                    "Each retrieval result must be a dictionary."
                )

            chunk_id = item.get("chunk_id")
            text = item.get("text")
            metadata = item.get("metadata")

            if not isinstance(chunk_id, str) or not chunk_id:
                raise ValueError(
                    "Each result must have a valid chunk_id."
                )

            if not isinstance(text, str):
                raise ValueError(
                    "Each result must have string text."
                )

            if not isinstance(metadata, dict):
                raise ValueError(
                    "Each result must have metadata."
                )

            document_id = metadata.get("document_id")
            chunk_index = metadata.get("chunk_index")

            if not isinstance(document_id, str) or not document_id:
                raise ValueError(
                    "Each result must have a valid document_id."
                )

            if (
                not isinstance(chunk_index, int)
                or isinstance(chunk_index, bool)
                or chunk_index < 0
            ):
                raise ValueError(
                    "chunk_index must be a non-negative integer."
                )

            if chunk_id in unique:
                duplicate_count += 1
                continue

            unique[chunk_id] = {
                **item,
                "metadata": dict(metadata),
            }

        return list(unique.values()), duplicate_count

    def assemble(
        self,
        retrieval_result,
        max_context_chars=None,
    ):
        """
        組裝 Retrieval Results。

        Args:
            retrieval_result: PaperRetrieval.retrieve() 回傳結果。
            max_context_chars: 可選的 Context 字元數上限。

        Returns:
            dict:
                query
                context
                total_chars
                max_context_chars
                total_chunks
                input_chunks
                duplicates_removed
                truncated
                chunks
        """

        if max_context_chars is None:
            max_context_chars = self.max_context_chars

        self._validate_max_context_chars(
            max_context_chars
        )

        results = self._validate_results(
            retrieval_result
        )

        unique_results, duplicate_count = (
            self._deduplicate(results)
        )

        unique_results.sort(key=self._sort_key)

        context_parts = []
        assembled_chunks = []
        total_chars = 0
        truncated = False

        for item in unique_results:
            header = self._build_header(item)
            text = item["text"].strip()

            if not text:
                continue

            separator = "\n\n" if context_parts else ""
            prefix = separator + header

            remaining = (
                max_context_chars
                - total_chars
                - len(prefix)
            )

            if remaining <= 0:
                truncated = True
                break

            if len(text) > remaining:
                text = text[:remaining]
                truncated = True

            block = prefix + text
            context_parts.append(block)
            total_chars += len(block)

            assembled_chunks.append({
                "chunk_id": item["chunk_id"],
                "text": text,
                "metadata": item["metadata"],
                "truncated": (
                    len(text) < len(item["text"].strip())
                ),
            })

            if truncated:
                break

        return {
            "query": retrieval_result.get("query"),
            "context": "".join(context_parts),
            "total_chars": total_chars,
            "max_context_chars": max_context_chars,
            "total_chunks": len(assembled_chunks),
            "input_chunks": len(results),
            "duplicates_removed": duplicate_count,
            "truncated": truncated,
            "chunks": assembled_chunks,
        }


__all__ = [
    "PaperContextAssembler",
    "DEFAULT_MAX_CONTEXT_CHARS",
]