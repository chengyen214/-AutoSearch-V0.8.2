"""
rag/paper_pipeline.py

AutoSearch V9

Paper RAG Pipeline

功能：

    1. 執行 PDF Chunking
    2. 批次產生 Chunk Embeddings
    3. 比對 Paper ChromaDB 是否已有索引
    4. 跳過已存在索引的論文
    5. 儲存新的 Paper Chunks

不負責：

    1. MySQL 論文清單查詢
    2. MongoDB GridFS PDF 查詢
    3. Web RAG 索引
"""

from tqdm import tqdm

from rag.paper_pdf_chunking import PaperPDFChunking
from rag.paper_embedding import PaperEmbedding
from rag.paper_chroma_storage import PaperChromaStorage


EMBEDDING_BATCH_SIZE = 8


class PaperPipeline:
    """Paper RAG 索引流程。"""

    def __init__(
        self,
        chunker=None,
        embedder=None,
        storage=None,
    ):
        self.chunker = (
            chunker
            if chunker is not None
            else PaperPDFChunking()
        )

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

    def is_indexed(self, document_id):
        """判斷論文是否已有 Chunk 索引。"""

        return (
            self.storage.count_document_chunks(
                document_id
            ) > 0
        )

    def index_pdf(
        self,
        pdf_bytes,
        document_id,
        source_url=None,
        title=None,
    ):
        """處理單篇 PDF 並寫入 ChromaDB。"""

        if not isinstance(pdf_bytes, bytes) or not pdf_bytes:
            raise ValueError(
                "pdf_bytes must be non-empty bytes."
            )

        if (
            not isinstance(document_id, str)
            or not document_id.strip()
        ):
            raise ValueError(
                "document_id cannot be empty."
            )

        document_id = document_id.strip()

        existing_count = (
            self.storage.count_document_chunks(
                document_id
            )
        )

        if existing_count > 0:
            return {
                "document_id": document_id,
                "status": "SKIPPED",
                "reason": "Already indexed in ChromaDB.",
                "indexed_count": existing_count,
            }

        chunks = self.chunker.chunk_pdf(
            pdf_bytes=pdf_bytes,
            document_id=document_id,
            source_url=source_url,
            title=title,
        )

        if not chunks:
            return {
                "document_id": document_id,
                "status": "EMPTY",
                "chunk_count": 0,
                "indexed_count": 0,
            }

        total_chunks = len(chunks)

        print(
            f"Chunk 切分完成：{total_chunks} chunks"
        )

        texts = []

        for chunk in chunks:
            text = chunk.page_content

            if not isinstance(text, str) or not text.strip():
                raise ValueError(
                    "Chunk text cannot be empty."
                )

            texts.append(text)

        embeddings = []

        embed_chunks_method = getattr(
            type(self.embedder),
            "embed_chunks",
            None,
        )

        with tqdm(
            total=total_chunks,
            desc="Embedding",
            unit="chunk",
            dynamic_ncols=True,
        ) as progress:
            for start in range(
                0,
                total_chunks,
                EMBEDDING_BATCH_SIZE,
            ):
                batch_texts = texts[
                    start:start + EMBEDDING_BATCH_SIZE
                ]

                if callable(embed_chunks_method):
                    batch_embeddings = (
                        self.embedder.embed_chunks(
                            batch_texts,
                            batch_size=EMBEDDING_BATCH_SIZE,
                            show_progress_bar=False,
                        )
                    )

                    if len(batch_embeddings) != len(batch_texts):
                        raise ValueError(
                            "Embedding count does not match "
                            "batch text count."
                        )
                else:
                    batch_embeddings = [
                        self.embedder.embed_chunk(text)
                        for text in batch_texts
                    ]

                embeddings.extend(batch_embeddings)
                progress.update(len(batch_texts))

        if len(embeddings) != total_chunks:
            raise ValueError(
                "Embedding count does not match chunk count."
            )

        storage_chunks = []

        for chunk, embedding in zip(chunks, embeddings):
            metadata = dict(chunk.metadata)
            metadata["document_id"] = document_id

            if not metadata.get("chunk_id"):
                raise ValueError(
                    "Chunk metadata requires chunk_id."
                )

            storage_chunks.append({
                "text": chunk.page_content,
                "embedding": embedding,
                "metadata": metadata,
            })

        indexed_ids = self.storage.upsert_chunks(
            storage_chunks
        )

        indexed_count = len(indexed_ids)

        print(
            f"ChromaDB 寫入完成：{indexed_count} chunks"
        )

        return {
            "document_id": document_id,
            "status": "DONE",
            "chunk_count": total_chunks,
            "indexed_count": indexed_count,
            "collection_name": (
                self.storage.get_collection_name()
            ),
        }

    def process_pending_papers(self, papers):
        """批次處理尚未建立 ChromaDB 索引的論文。"""

        if not isinstance(papers, (list, tuple)):
            raise TypeError(
                "papers must be a list or tuple."
            )

        results = {
            "total": len(papers),
            "done": 0,
            "skipped": 0,
            "empty": 0,
            "failed": 0,
            "items": [],
        }

        for paper in papers:
            if not isinstance(paper, dict):
                results["failed"] += 1
                results["items"].append({
                    "status": "FAILED",
                    "error": "Paper must be a dictionary.",
                })
                continue

            document_id = paper.get("document_id")

            try:
                result = self.index_pdf(
                    pdf_bytes=paper.get("pdf_bytes"),
                    document_id=document_id,
                    source_url=paper.get("source_url"),
                    title=paper.get("title"),
                )

                status = result["status"]

                if status == "DONE":
                    results["done"] += 1
                elif status == "SKIPPED":
                    results["skipped"] += 1
                elif status == "EMPTY":
                    results["empty"] += 1

                results["items"].append(result)

            except Exception as exc:
                results["failed"] += 1
                results["items"].append({
                    "document_id": document_id,
                    "status": "FAILED",
                    "error": str(exc),
                })

        return results


__all__ = [
    "PaperPipeline",
]