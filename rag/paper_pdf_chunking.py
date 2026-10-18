"""
rag/paper_pdf_chunking.py

AutoSearch V9

P1 Paper PDF -> Chunk

功能：

    1. 擷取 PDF 每頁文字
    2. 建立 LangChain Documents
    3. 保留 Paper Metadata
    4. 使用既有 DocumentChunking
    5. 建立 Chunk 識別資訊

不負責：

    1. Embedding
    2. ChromaDB
    3. LLM
    4. PDF 全文永久儲存
"""

import pymupdf

from langchain_core.documents import Document

from rag.chunking.document_chunking import (
    DocumentChunking,
)


class PaperPDFChunking:
    """Paper PDF 文字擷取與 Chunking。"""

    def __init__(
        self,
        document_chunking=None,
    ):
        self.document_chunking = (
            document_chunking
            if document_chunking is not None
            else DocumentChunking()
        )

    @staticmethod
    def _validate_pdf(
        pdf_bytes,
        document_id,
    ):
        if not isinstance(
            pdf_bytes,
            bytes,
        ):
            raise TypeError(
                "pdf_bytes must be bytes."
            )

        if not pdf_bytes:
            raise ValueError(
                "PDF content cannot be empty."
            )

        if not document_id:
            raise ValueError(
                "document_id cannot be empty."
            )

    @staticmethod
    def _extract_pages(
        pdf_bytes,
        document_id,
        source_url=None,
        title=None,
    ):
        documents = []

        with pymupdf.open(
            stream=pdf_bytes,
            filetype="pdf",
        ) as pdf:

            for page_index, page in enumerate(
                pdf
            ):
                text = page.get_text("text").strip()

                if not text:
                    continue

                metadata = {
                    "document_id": document_id,
                    "page_number": page_index + 1,
                    "source_type": "paper_pdf",
                }

                if source_url:
                    metadata["source"] = source_url

                if title:
                    metadata["title"] = title

                documents.append(
                    Document(
                        page_content=text,
                        metadata=metadata,
                    )
                )

        if not documents:
            raise ValueError(
                f"No extractable text found in PDF: "
                f"{document_id}"
            )

        return documents

    def chunk_pdf(
        self,
        pdf_bytes,
        document_id,
        source_url=None,
        title=None,
    ):
        """
        擷取 PDF 文字並使用既有 Chunking 流程。

        Returns:
            list[Document]
        """

        self._validate_pdf(
            pdf_bytes,
            document_id,
        )

        page_documents = self._extract_pages(
            pdf_bytes=pdf_bytes,
            document_id=document_id,
            source_url=source_url,
            title=title,
        )

        chunks = (
            self.document_chunking.chunk_documents(
                page_documents
            )
        )

        for index, chunk in enumerate(chunks):
            chunk.metadata["chunk_id"] = (
                f"{document_id}:{index}"
            )

            chunk.metadata["chunk_index"] = index

        return chunks


__all__ = [
    "PaperPDFChunking",
]