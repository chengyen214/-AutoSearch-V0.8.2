
"""
rag/paddleocr_paper_pipeline.py

AutoSearch V9

PaddleOCR-VL-1.6 Paper RAG Pipeline

功能：

    1. 從 MongoDB paper_ocr_results 讀取 OCR 結果
    2. 自動找出尚未建立 ChromaDB 索引的論文
    3. 依頁碼排序並執行 Chunking
    4. 保留 Chunk 頁碼 Metadata
    5. 跳過已建立索引的論文
    6. 僅對尚未索引的論文產生 Embedding
    7. 儲存至獨立的 PaddleOCR ChromaDB Collection
    8. 顯示 Embedding 進度與批次處理統計
"""

from tqdm import tqdm
from langchain_core.documents import Document

from database.mongo_connection import get_mongo_database
from rag.chunking.document_chunking import DocumentChunking
from rag.paper_embedding import PaperEmbedding
from rag.paper_chroma_storage import PaperChromaStorage


EMBEDDING_BATCH_SIZE = 8

MONGO_COLLECTION_NAME = "paper_ocr_results"

PADDLEOCR_COLLECTION_NAME = (
    "autosearch_papers_paddleocr_vl16"
)

OCR_SOURCE = "mongodb:paper_ocr_results"


class PaddleOCRPaperPipeline:
    """從 MongoDB OCR 結果建立 Paper RAG 索引。"""

    def __init__(
        self,
        chunker=None,
        embedder=None,
        storage=None,
        database=None,
    ):
        self.database = (
            database
            if database is not None
            else get_mongo_database()
        )

        self.mongo_collection = self.database[
            MONGO_COLLECTION_NAME
        ]

        self.chunker = (
            chunker
            if chunker is not None
            else DocumentChunking()
        )

        self.embedder = (
            embedder
            if embedder is not None
            else PaperEmbedding()
        )

        self.storage = (
            storage
            if storage is not None
            else PaperChromaStorage(
                collection_name=PADDLEOCR_COLLECTION_NAME
            )
        )

    def load_documents(
        self,
        document_id,
        metadata=None,
    ):
        """從 MongoDB 載入逐頁 OCR 文字。"""

        if (
            not isinstance(document_id, str)
            or not document_id.strip()
        ):
            raise ValueError(
                "document_id cannot be empty."
            )

        if metadata is not None and not isinstance(metadata, dict):
            raise TypeError(
                "metadata must be a dictionary."
            )

        document_id = document_id.strip()

        ocr_record = self.mongo_collection.find_one({
            "document_id": document_id,
        })

        if ocr_record is None:
            raise FileNotFoundError(
                "MongoDB OCR result not found: "
                f"document_id={document_id}"
            )

        if ocr_record.get("status") != "DONE":
            raise ValueError(
                "OCR result is not complete: "
                f"document_id={document_id}, "
                f"status={ocr_record.get('status')}"
            )

        page_results = ocr_record.get("page_results")

        if not isinstance(page_results, list) or not page_results:
            raise ValueError(
                "MongoDB OCR result has no page_results: "
                f"document_id={document_id}"
            )

        total_pages = ocr_record.get("total_pages", 0)

        if (
            not isinstance(total_pages, int)
            or isinstance(total_pages, bool)
            or total_pages <= 0
        ):
            raise ValueError(
                f"Invalid total_pages: {total_pages}"
            )

        if len(page_results) != total_pages:
            raise ValueError(
                "OCR page count mismatch: "
                f"expected={total_pages}, "
                f"actual={len(page_results)}"
            )

        sorted_pages = sorted(
            page_results,
            key=lambda item: item.get("page", 0),
        )

        actual_page_numbers = [
            item.get("page")
            for item in sorted_pages
        ]

        expected_page_numbers = list(
            range(1, total_pages + 1)
        )

        if actual_page_numbers != expected_page_numbers:
            raise ValueError(
                "OCR page numbers are missing or invalid: "
                f"document_id={document_id}"
            )

        document_metadata = dict(metadata or {})

        document_metadata.update({
            "document_id": document_id,
            "source_type": "paddleocr_vl_1_6",
            "source": OCR_SOURCE,
        })

        documents = []

        for page_item in sorted_pages:
            page_number = page_item["page"]
            page_text = page_item.get("text", "")

            if (
                not isinstance(page_text, str)
                or not page_text.strip()
            ):
                raise ValueError(
                    "OCR page contains empty text: "
                    f"document_id={document_id}, "
                    f"page={page_number}"
                )

            page_metadata = dict(document_metadata)
            page_metadata["page_number"] = page_number

            documents.append(
                Document(
                    page_content=page_text.strip(),
                    metadata=page_metadata,
                )
            )

        return documents

    @staticmethod
    def _build_chunk_metadata(
        chunk,
        document_id,
        chunk_index,
    ):
        """建立符合 PaperChromaStorage 格式的 Metadata。"""

        metadata = dict(chunk.metadata)

        metadata.update({
            "document_id": document_id,
            "chunk_id": (
                f"paddleocr_vl_1_6:"
                f"{document_id}:{chunk_index}"
            ),
            "chunk_index": chunk_index,
            "source_type": "paddleocr_vl_1_6",
            "source": OCR_SOURCE,
        })

        return metadata

    def is_indexed(self, document_id):
        """檢查 ChromaDB 是否已有該篇論文的 Chunk。"""

        collection = self.storage.get_collection()

        result = collection.get(
            where={"document_id": document_id},
            include=["metadatas"],
            limit=1,
        )

        return bool(result.get("ids"))

    def _get_existing_chunks(self, chunk_ids):
        """批次查詢指定 Chunk ID 的既有文字。"""

        if not chunk_ids:
            return {}

        collection = self.storage.get_collection()

        result = collection.get(
            ids=chunk_ids,
            include=["documents"],
        )

        return {
            chunk_id: text
            for chunk_id, text in zip(
                result.get("ids", []),
                result.get("documents", []),
            )
        }

    def _remove_stale_chunks(
        self,
        document_id,
        expected_ids,
    ):
        """移除本篇論文已不再使用的舊 Chunk ID。"""

        collection = self.storage.get_collection()

        result = collection.get(
            where={"document_id": document_id},
            include=["metadatas"],
        )

        stale_ids = [
            chunk_id
            for chunk_id in result.get("ids", [])
            if chunk_id not in expected_ids
        ]

        if stale_ids:
            collection.delete(ids=stale_ids)

            print(
                f"[{document_id}] 清除舊索引："
                f"{len(stale_ids)} chunks"
            )

        return len(stale_ids)

    def index_ocr_text(
        self,
        document_id,
        metadata=None,
        batch_size=EMBEDDING_BATCH_SIZE,
    ):
        """從 MongoDB OCR 文字建立 ChromaDB 索引。"""

        if (
            not isinstance(batch_size, int)
            or isinstance(batch_size, bool)
            or batch_size <= 0
        ):
            raise ValueError(
                "batch_size must be a positive integer."
            )

        if (
            not isinstance(document_id, str)
            or not document_id.strip()
        ):
            raise ValueError(
                "document_id cannot be empty."
            )

        document_id = document_id.strip()

        paper_title = (metadata or {}).get(
            "title",
            document_id,
        )

        print("\n===== PaddleOCR Paper RAG =====")
        print(f"Document ID: {document_id}")
        print(f"Title: {paper_title}")
        print(f"MongoDB Collection: {MONGO_COLLECTION_NAME}")
        print(
            f"ChromaDB Collection: "
            f"{self.storage.get_collection_name()}"
        )

        documents = self.load_documents(
            document_id=document_id,
            metadata=metadata,
        )

        print(
            f"\n[{document_id}] MongoDB 載入完成："
            f"{len(documents)} pages"
        )

        chunk_records = []

        for page_document in documents:
            page_number = page_document.metadata["page_number"]

            print(
                f"[{document_id}] "
                f"Chunking page {page_number}/{len(documents)}",
                flush=True,
            )

            page_chunks = self.chunker.chunk(page_document)

            for chunk in page_chunks:
                if (
                    not isinstance(chunk.page_content, str)
                    or not chunk.page_content.strip()
                ):
                    raise ValueError(
                        f"Page {page_number} contains an empty chunk."
                    )

                chunk_records.append({
                    "text": chunk.page_content,
                    "metadata": self._build_chunk_metadata(
                        chunk=chunk,
                        document_id=document_id,
                        chunk_index=len(chunk_records),
                    ),
                })

        print(
            f"[{document_id}] Chunking 完成："
            f"{len(chunk_records)} chunks"
        )

        if not chunk_records:
            print(f"[{document_id}] 沒有可索引的 Chunk。")

            return {
                "document_id": document_id,
                "title": paper_title,
                "status": "EMPTY",
                "chunk_count": 0,
                "existing_count": 0,
                "embedded_count": 0,
                "indexed_count": 0,
                "collection_name": (
                    self.storage.get_collection_name()
                ),
            }

        chunk_ids = [
            record["metadata"]["chunk_id"]
            for record in chunk_records
        ]

        print(f"[{document_id}] 比對 ChromaDB 既有索引...")

        existing_chunks = self._get_existing_chunks(
            chunk_ids
        )

        pending_records = [
            record
            for record in chunk_records
            if existing_chunks.get(
                record["metadata"]["chunk_id"]
            ) != record["text"]
        ]

        unchanged_count = (
            len(chunk_records) - len(pending_records)
        )

        print(
            f"[{document_id}] 內容相同、跳過："
            f"{unchanged_count} chunks"
        )
        print(
            f"[{document_id}] 需要重新索引："
            f"{len(pending_records)} chunks"
        )

        if not pending_records:
            removed_count = self._remove_stale_chunks(
                document_id=document_id,
                expected_ids=set(chunk_ids),
            )

            print(
                f"[{document_id}] 所有 Chunk 均已存在，"
                "不需要重新產生 Embedding。"
            )

            return {
                "document_id": document_id,
                "title": paper_title,
                "status": "SKIPPED",
                "chunk_count": len(chunk_records),
                "existing_count": unchanged_count,
                "embedded_count": 0,
                "indexed_count": 0,
                "removed_count": removed_count,
                "collection_name": (
                    self.storage.get_collection_name()
                ),
            }

        embeddings = []

        progress_description = (
            f"Embedding [{document_id}] {paper_title}"
        )

        print(f"\n[{document_id}] 開始產生 Embedding...")

        with tqdm(
            total=len(pending_records),
            desc=progress_description,
            unit="chunk",
            dynamic_ncols=True,
        ) as progress:
            for start in range(
                0,
                len(pending_records),
                batch_size,
            ):
                batch_records = pending_records[
                    start:start + batch_size
                ]

                batch_texts = [
                    record["text"]
                    for record in batch_records
                ]

                batch_embeddings = self.embedder.embed_chunks(
                    batch_texts,
                    batch_size=batch_size,
                    show_progress_bar=False,
                )

                if len(batch_embeddings) != len(batch_texts):
                    raise ValueError(
                        "Embedding count does not match "
                        "batch text count."
                    )

                embeddings.extend(batch_embeddings)
                progress.update(len(batch_texts))

        if len(embeddings) != len(pending_records):
            raise ValueError(
                "Embedding count does not match pending chunks."
            )

        print(
            f"\n[{document_id}] Embedding 完成："
            f"{len(embeddings)} chunks"
        )

        storage_chunks = []

        for record, embedding in zip(
            pending_records,
            embeddings,
        ):
            storage_chunks.append({
                "text": record["text"],
                "embedding": embedding,
                "metadata": record["metadata"],
            })

        print(
            f"[{document_id}] 開始寫入 ChromaDB，"
            f"共 {len(storage_chunks)} chunks..."
        )

        indexed_ids = self.storage.upsert_chunks(
            storage_chunks
        )

        indexed_count = len(indexed_ids)

        print(
            f"[{document_id}] ChromaDB 寫入完成："
            f"{indexed_count} chunks"
        )

        removed_count = self._remove_stale_chunks(
            document_id=document_id,
            expected_ids=set(chunk_ids),
        )

        return {
            "document_id": document_id,
            "title": paper_title,
            "status": "DONE",
            "chunk_count": len(chunk_records),
            "existing_count": unchanged_count,
            "embedded_count": len(pending_records),
            "indexed_count": indexed_count,
            "removed_count": removed_count,
            "collection_name": (
                self.storage.get_collection_name()
            ),
        }

    def process_unindexed_papers(self):
        """只處理尚未出現在 ChromaDB 的論文。"""

        papers = list(
            self.mongo_collection.find(
                {"status": "DONE"},
                {
                    "_id": 0,
                    "document_id": 1,
                    "total_pages": 1,
                    "processed_pages": 1,
                    "page_results": 1,
                },
            ).sort("document_id", 1)
        )

        results = {
            "total": len(papers),
            "done": 0,
            "skipped": 0,
            "failed": 0,
            "empty": 0,
            "items": [],
        }

        print("\n===== PaddleOCR Batch RAG =====")
        print(f"MongoDB OCR completed: {len(papers)}")
        print(
            f"ChromaDB Collection: "
            f"{self.storage.get_collection_name()}"
        )

        for index, paper in enumerate(papers, start=1):
            document_id = paper.get("document_id")

            print(
                f"\n===== Paper {index}/{len(papers)} ====="
            )
            print(f"Document ID: {document_id}")

            if not document_id:
                results["failed"] += 1
                results["items"].append({
                    "document_id": None,
                    "status": "FAILED",
                    "error": "Missing document_id.",
                })
                print("FAILED: Missing document_id.")
                continue

            try:
                if self.is_indexed(document_id):
                    results["skipped"] += 1
                    results["items"].append({
                        "document_id": document_id,
                        "status": "SKIPPED",
                        "reason": "Paper already has indexed chunks.",
                    })
                    print("SKIPPED: Paper already indexed.")
                    continue

                result = self.index_ocr_text(
                    document_id=document_id,
                    metadata={
                        "title": document_id,
                    },
                )

                status = result["status"]

                if status == "DONE":
                    results["done"] += 1
                elif status == "EMPTY":
                    results["empty"] += 1
                elif status == "SKIPPED":
                    results["skipped"] += 1
                else:
                    results["failed"] += 1

                results["items"].append(result)

            except Exception as exc:
                results["failed"] += 1
                results["items"].append({
                    "document_id": document_id,
                    "status": "FAILED",
                    "error": str(exc),
                })

                print(
                    f"[{document_id}] FAILED: "
                    f"{type(exc).__name__}: {exc}",
                    flush=True,
                )

        print("\n===== PaddleOCR Batch Result =====")
        print(f"MongoDB OCR completed: {results['total']}")
        print(f"Newly indexed: {results['done']}")
        print(f"Skipped: {results['skipped']}")
        print(f"Empty: {results['empty']}")
        print(f"Failed: {results['failed']}")

        return results


def main():
    pipeline = PaddleOCRPaperPipeline()
    pipeline.process_unindexed_papers()


if __name__ == "__main__":
    main()


__all__ = [
    "PaddleOCRPaperPipeline",
]
