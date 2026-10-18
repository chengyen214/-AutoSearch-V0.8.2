
"""
rag/paddleocr_paper_generation.py

AutoSearch V9

P5.5 PaddleOCR-VL-1.6 LLM Generation

功能：

    1. 執行 PaddleOCR Paper Retrieval
    2. 組裝 Retrieved Context
    3. 建立 LLM Prompt
    4. 呼叫 LLM 生成答案
    5. 解析答案與來源引用
    6. 回傳問答結果與執行資訊
"""

from rag.paddleocr_paper_retrieval import PaddleOCRPaperRetrieval
from rag.paper_context_assembler import PaperContextAssembler
from rag.generation.prompt_builder import PromptBuilder
from rag.generation.llm_invoker import LLMInvoker
from rag.generation.answer_generator import AnswerGenerator


class PaddleOCRPaperGeneration:
    """PaddleOCR-VL-1.6 Paper RAG 問答生成流程。"""

    def __init__(
        self,
        retrieval=None,
        context_assembler=None,
        prompt_builder=None,
        llm_invoker=None,
        answer_generator=None,
    ):
        self.retrieval = (
            retrieval
            if retrieval is not None
            else PaddleOCRPaperRetrieval()
        )

        self.context_assembler = (
            context_assembler
            if context_assembler is not None
            else PaperContextAssembler()
        )

        self.prompt_builder = (
            prompt_builder
            if prompt_builder is not None
            else PromptBuilder()
        )

        self.llm_invoker = (
            llm_invoker
            if llm_invoker is not None
            else LLMInvoker()
        )

        self.answer_generator = (
            answer_generator
            if answer_generator is not None
            else AnswerGenerator()
        )

    @staticmethod
    def _build_generation_context(assembled_context):
        """轉換 Context Assembly 結果供 Generation 使用。"""

        entries = []

        for source_index, chunk in enumerate(
            assembled_context["chunks"],
            start=1,
        ):
            metadata = chunk["metadata"]

            entries.append({
                "source_index": source_index,
                "document_id": metadata["document_id"],
                "chunk_index": metadata["chunk_index"],
                "title": metadata.get("title") or "",
                "url": (
                    metadata.get("source_url")
                    or metadata.get("url")
                    or metadata.get("source")
                    or ""
                ),
                "page_number": metadata.get("page_number"),
                "content": chunk["text"],
            })

        context_parts = []

        for entry in entries:
            context_parts.append(
                f"[Source {entry['source_index']}]\n"
                f"document_id: {entry['document_id']}\n"
                f"chunk_index: {entry['chunk_index']}\n"
                f"page_number: {entry['page_number']}\n"
                f"title: {entry['title']}\n"
                f"url: {entry['url']}\n"
                f"{entry['content']}"
            )

        return {
            "context_text": "\n\n".join(context_parts),
            "entries": entries,
            "count": len(entries),
        }

    @staticmethod
    def _empty_result(
        query,
        retrieval_result,
        assembled_context,
    ):
        """建立沒有可用 Context 時的結果。"""

        return {
            "query": query,
            "answer_text": "目前檢索到的論文內容不足以回答這個問題。",
            "source_references": [],
            "retrieval": retrieval_result,
            "context": assembled_context,
            "status": "NO_CONTEXT",
        }

    def generate(
        self,
        query,
        top_k=5,
        document_id=None,
        document_ids=None,
        source_type=None,
        page_number=None,
    ):
        """執行 PaddleOCR Paper RAG 問答。"""

        if not isinstance(query, str):
            raise TypeError("query must be a string.")

        query = query.strip()

        if not query:
            raise ValueError("query cannot be empty.")

        retrieval_result = self.retrieval.retrieve(
            query=query,
            top_k=top_k,
            document_id=document_id,
            document_ids=document_ids,
            source_type=source_type,
            page_number=page_number,
        )

        assembled_context = self.context_assembler.assemble(
            retrieval_result
        )

        if not assembled_context["context"].strip():
            return self._empty_result(
                query=query,
                retrieval_result=retrieval_result,
                assembled_context=assembled_context,
            )

        generation_context = self._build_generation_context(
            assembled_context
        )

        prompt = self.prompt_builder.build(
            query=query,
            context=generation_context,
        )

        llm_response = self.llm_invoker.invoke(prompt)

        answer_result = self.answer_generator.generate(
            llm_response=llm_response,
            context=generation_context,
        )

        return {
            "query": query,
            "answer_text": answer_result["answer_text"],
            "source_references": answer_result["source_references"],
            "retrieval": retrieval_result,
            "context": assembled_context,
            "status": "DONE",
        }


__all__ = [
    "PaddleOCRPaperGeneration",
]
