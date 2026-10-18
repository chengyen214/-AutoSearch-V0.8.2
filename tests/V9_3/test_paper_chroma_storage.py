"""
tests/V9_3/test_paper_chroma_storage.py

AutoSearch V9

P3 Paper ChromaDB Storage Test

測試：

    1. Storage 初始化
    2. Chunk 寫入
    3. Chunk 查詢
    4. Metadata 驗證
    5. 重複 Upsert
    6. Document Chunk 查詢
    7. Collection 計數
    8. 無效輸入驗證

使用獨立暫存目錄，不修改正式 Paper Collection。
"""

import gc
import tempfile
import unittest

from rag.paper_chroma_storage import PaperChromaStorage


class TestPaperChromaStorage(unittest.TestCase):
    """Paper ChromaDB Storage 測試。"""

    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()

        self.storage = PaperChromaStorage(
            persist_directory=self.temp_directory.name,
            collection_name="test_papers",
        )

        self.document_id = "openalex:test_storage_001"

        self.metadata = {
            "document_id": self.document_id,
            "chunk_id": f"{self.document_id}:0",
            "chunk_index": 0,
            "page_number": 1,
            "title": "Paper Storage Test",
            "source_type": "paper_pdf",
        }

        self.embedding = [0.0] * 1024
        self.embedding[0] = 1.0

        self.text = "Paper ChromaDB storage test."

    def tearDown(self):
        temp_directory = self.temp_directory.name

        try:
            storage = getattr(self, "storage", None)

            if storage is not None:
                collection = getattr(
                    storage,
                    "collection",
                    None,
                )

                chroma_collection = getattr(
                    storage,
                    "chroma_collection",
                    None,
                )

                chroma_client_wrapper = getattr(
                    storage,
                    "chroma_client",
                    None,
                )

                if collection is not None:
                    del storage.collection

                if chroma_collection is not None:
                    chroma_collection.collection = None
                    chroma_collection.client = None
                    chroma_collection.chroma_client = None

                if chroma_client_wrapper is not None:
                    chroma_client = getattr(
                        chroma_client_wrapper,
                        "client",
                        None,
                    )

                    close = getattr(
                        chroma_client,
                        "close",
                        None,
                    )

                    if callable(close):
                        close()

                    chroma_client_wrapper.client = None

                self.storage = None

            gc.collect()

        finally:
            self.temp_directory.cleanup()

    def test_initialization(self):
        self.assertEqual(
            self.storage.get_collection_name(),
            "test_papers",
        )

        self.assertEqual(
            self.storage.count(),
            0,
        )

    def test_upsert_and_get_chunk(self):
        record_id = self.storage.upsert_chunk(
            self.text,
            self.embedding,
            self.metadata,
        )

        self.assertEqual(
            record_id,
            self.metadata["chunk_id"],
        )

        result = self.storage.get_chunk(record_id)

        self.assertEqual(
            result["ids"],
            [record_id],
        )

        self.assertEqual(
            result["documents"][0],
            self.text,
        )

        self.assertEqual(
            result["metadatas"][0]["document_id"],
            self.document_id,
        )

        self.assertEqual(
            result["metadatas"][0]["chunk_index"],
            0,
        )

    def test_upsert_updates_existing_chunk(self):
        self.storage.upsert_chunk(
            self.text,
            self.embedding,
            self.metadata,
        )

        updated_text = "Updated Paper Chunk."

        self.storage.upsert_chunk(
            updated_text,
            self.embedding,
            self.metadata,
        )

        result = self.storage.get_chunk(
            self.metadata["chunk_id"]
        )

        self.assertEqual(
            result["documents"][0],
            updated_text,
        )

        self.assertEqual(
            self.storage.count(),
            1,
        )

    def test_get_document_chunks(self):
        second_metadata = {
            **self.metadata,
            "chunk_id": f"{self.document_id}:1",
            "chunk_index": 1,
            "page_number": 2,
        }

        self.storage.upsert_chunks([
            {
                "text": "First chunk.",
                "embedding": self.embedding,
                "metadata": self.metadata,
            },
            {
                "text": "Second chunk.",
                "embedding": self.embedding,
                "metadata": second_metadata,
            },
        ])

        result = self.storage.get_document_chunks(
            self.document_id
        )

        self.assertEqual(
            len(result["ids"]),
            2,
        )

        self.assertEqual(
            self.storage.count_document_chunks(
                self.document_id
            ),
            2,
        )

    def test_upsert_chunks_rejects_duplicate_ids(self):
        chunk = {
            "text": self.text,
            "embedding": self.embedding,
            "metadata": self.metadata,
        }

        with self.assertRaises(ValueError):
            self.storage.upsert_chunks([
                chunk,
                chunk,
            ])

        self.assertEqual(
            self.storage.count(),
            0,
        )

    def test_rejects_invalid_embedding_dimension(self):
        with self.assertRaises(ValueError):
            self.storage.upsert_chunk(
                self.text,
                [0.0] * 10,
                self.metadata,
            )

    def test_rejects_non_finite_embedding(self):
        embedding = self.embedding.copy()
        embedding[0] = float("nan")

        with self.assertRaises(ValueError):
            self.storage.upsert_chunk(
                self.text,
                embedding,
                self.metadata,
            )

    def test_rejects_empty_text(self):
        with self.assertRaises(ValueError):
            self.storage.upsert_chunk(
                "   ",
                self.embedding,
                self.metadata,
            )

    def test_rejects_missing_chunk_id(self):
        metadata = self.metadata.copy()
        metadata.pop("chunk_id")

        with self.assertRaises(ValueError):
            self.storage.upsert_chunk(
                self.text,
                self.embedding,
                metadata,
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)