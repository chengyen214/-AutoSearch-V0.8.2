"""
tests/V9_3/test_paper_pipeline.py

AutoSearch V9

Paper Pipeline Tests
"""

import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from rag.paper_pipeline import PaperPipeline


class TestPaperPipeline(unittest.TestCase):

    def setUp(self):
        self.chunker = Mock()
        self.embedder = Mock()
        self.storage = Mock()

        self.pipeline = PaperPipeline(
            chunker=self.chunker,
            embedder=self.embedder,
            storage=self.storage,
        )

    def make_chunk(self, index=0):
        return SimpleNamespace(
            page_content=f"Paper chunk {index}",
            metadata={
                "document_id": "openalex:test001",
                "chunk_id": f"openalex:test001:{index}",
                "chunk_index": index,
                "page_number": 1,
                "title": "Test Paper",
                "source_type": "paper_pdf",
            },
        )

    def test_index_new_paper(self):
        """新論文應完成 Chunk、Embedding 與寫入。"""

        self.storage.count_document_chunks.return_value = 0

        self.chunker.chunk_pdf.return_value = [
            self.make_chunk(0),
            self.make_chunk(1),
        ]

        self.embedder.embed_chunk.return_value = [
            0.1
        ] * 1024

        self.storage.upsert_chunks.return_value = [
            "openalex:test001:0",
            "openalex:test001:1",
        ]

        result = self.pipeline.index_pdf(
            pdf_bytes=b"%PDF-test",
            document_id="openalex:test001",
            source_url="https://example.com/paper",
            title="Test Paper",
        )

        self.assertEqual(result["status"], "DONE")
        self.assertEqual(result["chunk_count"], 2)
        self.assertEqual(result["indexed_count"], 2)

        self.chunker.chunk_pdf.assert_called_once()
        self.assertEqual(
            self.embedder.embed_chunk.call_count,
            2,
        )
        self.storage.upsert_chunks.assert_called_once()

    def test_skip_existing_paper(self):
        """已有索引的論文應跳過。"""

        self.storage.count_document_chunks.return_value = 3

        result = self.pipeline.index_pdf(
            pdf_bytes=b"%PDF-test",
            document_id="openalex:test001",
        )

        self.assertEqual(result["status"], "SKIPPED")
        self.assertEqual(result["indexed_count"], 3)

        self.chunker.chunk_pdf.assert_not_called()
        self.embedder.embed_chunk.assert_not_called()
        self.storage.upsert_chunks.assert_not_called()

    def test_empty_chunks(self):
        """沒有 Chunk 時應回傳 EMPTY。"""

        self.storage.count_document_chunks.return_value = 0
        self.chunker.chunk_pdf.return_value = []

        result = self.pipeline.index_pdf(
            pdf_bytes=b"%PDF-test",
            document_id="openalex:test002",
        )

        self.assertEqual(result["status"], "EMPTY")
        self.assertEqual(result["indexed_count"], 0)

        self.embedder.embed_chunk.assert_not_called()
        self.storage.upsert_chunks.assert_not_called()

    def test_batch_continues_after_failure(self):
        """單篇失敗不應中斷後續論文。"""

        self.storage.count_document_chunks.side_effect = [
            RuntimeError("Simulated storage failure"),
            0,
        ]

        self.chunker.chunk_pdf.return_value = [
            self.make_chunk(0),
        ]

        self.embedder.embed_chunk.return_value = [
            0.1
        ] * 1024

        self.storage.upsert_chunks.return_value = [
            "openalex:test002:0",
        ]

        result = self.pipeline.process_pending_papers([
            {
                "document_id": "openalex:test001",
                "pdf_bytes": b"%PDF-test-1",
            },
            {
                "document_id": "openalex:test002",
                "pdf_bytes": b"%PDF-test-2",
            },
        ])

        self.assertEqual(result["total"], 2)
        self.assertEqual(result["failed"], 1)
        self.assertEqual(result["done"], 1)
        self.assertEqual(
            result["items"][0]["status"],
            "FAILED",
        )
        self.assertEqual(
            result["items"][1]["status"],
            "DONE",
        )

    def test_invalid_pdf_bytes(self):
        """無效 PDF 輸入應被拒絕。"""

        with self.assertRaises(ValueError):
            self.pipeline.index_pdf(
                pdf_bytes=b"",
                document_id="openalex:test003",
            )


if __name__ == "__main__":
    unittest.main()