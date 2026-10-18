
"""
rag/paper_chroma_storage.py

AutoSearch V9

P3 Paper ChromaDB Storage

功能：

    1. 建立獨立的 Paper ChromaDB Client
    2. 建立或取得 Paper Collection
    3. 儲存 Paper Chunk、Embedding 與 Metadata
    4. 支援單筆與多筆 Upsert
    5. 查詢 Chunk 與 Document 索引
    6. 取得 Collection 索引數量

不負責：

    1. PDF 下載與解析
    2. Chunking
    3. Embedding 生成
    4. MongoDB PDF 儲存
    5. Web RAG 索引
"""

import math
from pathlib import Path

from rag.chroma.client import ChromaDBClient
from rag.chroma.collection import ChromaCollection


PAPER_CHROMA_PERSIST_DIRECTORY = (
    Path(__file__).resolve().parent.parent
    / "chroma_db"
    / "papers"
)

PAPER_CHROMA_COLLECTION_NAME = (
    "autosearch_papers_qwen3"
)

PAPER_CHROMA_DISTANCE_METRIC = "cosine"

PAPER_EMBEDDING_DIMENSION = 1024

PAPER_METADATA_FIELDS = (
    "document_id",
    "chunk_id",
    "chunk_index",
    "page_number",
    "title",
    "source_type",
    "source",
)


class PaperChromaStorage:
    """Paper 專用 ChromaDB Storage。"""

    def __init__(
        self,
        persist_directory=None,
        collection_name=PAPER_CHROMA_COLLECTION_NAME,
        distance_metric=PAPER_CHROMA_DISTANCE_METRIC,
    ):
        self.persist_directory = str(
            persist_directory
            if persist_directory is not None
            else PAPER_CHROMA_PERSIST_DIRECTORY
        )

        self.collection_name = str(
            collection_name
        ).strip()

        self.distance_metric = str(
            distance_metric
        ).strip().lower()

        if not self.collection_name:
            raise ValueError(
                "Collection name cannot be empty."
            )

        if self.distance_metric not in {
            "cosine",
            "l2",
            "ip",
        }:
            raise ValueError(
                f"Unsupported distance metric: "
                f"{self.distance_metric}."
            )

        Path(self.persist_directory).mkdir(
            parents=True,
            exist_ok=True,
        )

        self.chroma_client = ChromaDBClient(
            persist_directory=self.persist_directory
        )

        self.chroma_collection = ChromaCollection(
            chroma_client=self.chroma_client,
            collection_name=self.collection_name,
            distance_metric=self.distance_metric,
        )

        self.collection = (
            self.chroma_collection.get_collection()
        )

    @staticmethod
    def _validate_embedding(embedding):
        """驗證 Embedding 維度與數值。"""

        if not isinstance(embedding, (list, tuple)):
            raise TypeError(
                "Embedding must be a list or tuple."
            )

        if len(embedding) != PAPER_EMBEDDING_DIMENSION:
            raise ValueError(
                "Incorrect embedding dimension: "
                f"{len(embedding)}. "
                f"Expected: {PAPER_EMBEDDING_DIMENSION}."
            )

        vector = []

        for value in embedding:
            if isinstance(value, bool):
                raise TypeError(
                    "Embedding values must be numeric."
                )

            try:
                number = float(value)
            except (TypeError, ValueError) as exc:
                raise TypeError(
                    "Embedding values must be numeric."
                ) from exc

            if not math.isfinite(number):
                raise ValueError(
                    "Embedding contains non-finite values."
                )

            vector.append(number)

        return vector

    @staticmethod
    def _validate_metadata(metadata):
        """驗證並轉換 Paper Metadata。"""

        if not isinstance(metadata, dict):
            raise TypeError(
                "Metadata must be a dictionary."
            )

        result = {}

        for field in PAPER_METADATA_FIELDS:
            value = metadata.get(field)

            if value is None:
                continue

            if isinstance(value, bool):
                result[field] = value
            elif isinstance(value, (str, int, float)):
                if isinstance(value, float) and not math.isfinite(value):
                    raise ValueError(
                        f"Metadata field '{field}' "
                        "contains a non-finite value."
                    )

                result[field] = value
            else:
                raise TypeError(
                    f"Metadata field '{field}' "
                    "must be a scalar value."
                )

        document_id = result.get("document_id")
        chunk_id = result.get("chunk_id")
        chunk_index = result.get("chunk_index")

        if not isinstance(document_id, str) or not document_id.strip():
            raise ValueError(
                "Metadata requires a non-empty document_id."
            )

        if not isinstance(chunk_id, str) or not chunk_id.strip():
            raise ValueError(
                "Metadata requires a non-empty chunk_id."
            )

        if (
            isinstance(chunk_index, bool)
            or not isinstance(chunk_index, int)
            or chunk_index < 0
        ):
            raise ValueError(
                "Metadata requires a non-negative integer chunk_index."
            )

        return result

    @staticmethod
    def _validate_text(text):
        """驗證 Chunk 文字。"""

        if not isinstance(text, str):
            raise TypeError(
                "Chunk text must be a string."
            )

        if not text.strip():
            raise ValueError(
                "Chunk text cannot be empty."
            )

        return text

    def upsert_chunk(
        self,
        text,
        embedding,
        metadata,
    ):
        """
        儲存或更新單一 Paper Chunk。

        Args:
            text: Chunk 文字。
            embedding: 1024 維 Embedding Vector。
            metadata: Paper Chunk Metadata。

        Returns:
            str: ChromaDB Record ID。
        """

        text = self._validate_text(text)
        embedding = self._validate_embedding(
            embedding
        )
        metadata = self._validate_metadata(
            metadata
        )

        record_id = metadata["chunk_id"]

        self.collection.upsert(
            ids=[record_id],
            documents=[text],
            embeddings=[embedding],
            metadatas=[metadata],
        )

        return record_id

    def upsert_chunks(
        self,
        chunks,
    ):
        """
        批次儲存 Paper Chunks。

        Args:
            chunks: dict 列表，每筆包含：
                text
                embedding
                metadata

        Returns:
            list[str]: 成功送出 Upsert 的 Record IDs。
        """

        if not isinstance(chunks, (list, tuple)):
            raise TypeError(
                "Chunks must be a list or tuple."
            )

        if not chunks:
            return []

        ids = []
        documents = []
        embeddings = []
        metadatas = []
        seen_ids = set()

        for index, chunk in enumerate(chunks):
            if not isinstance(chunk, dict):
                raise TypeError(
                    f"Chunk at index {index} must be a dictionary."
                )

            text = self._validate_text(
                chunk.get("text")
            )

            embedding = self._validate_embedding(
                chunk.get("embedding")
            )

            metadata = self._validate_metadata(
                chunk.get("metadata")
            )

            record_id = metadata["chunk_id"]

            if record_id in seen_ids:
                raise ValueError(
                    f"Duplicate chunk_id in batch: {record_id}."
                )

            seen_ids.add(record_id)
            ids.append(record_id)
            documents.append(text)
            embeddings.append(embedding)
            metadatas.append(metadata)

        self.collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )

        return ids

    def get_chunk(
        self,
        chunk_id,
        include_embeddings=False,
    ):
        """依 Chunk ID 取得單筆資料。"""

        if not isinstance(chunk_id, str) or not chunk_id.strip():
            raise ValueError(
                "chunk_id cannot be empty."
            )

        include = [
            "documents",
            "metadatas",
        ]

        if include_embeddings:
            include.append("embeddings")

        return self.collection.get(
            ids=[chunk_id],
            include=include,
        )

    def get_document_chunks(
        self,
        document_id,
        include_embeddings=False,
    ):
        """取得指定 Document 的全部 Chunk。"""

        if not isinstance(document_id, str) or not document_id.strip():
            raise ValueError(
                "document_id cannot be empty."
            )

        include = [
            "documents",
            "metadatas",
        ]

        if include_embeddings:
            include.append("embeddings")

        return self.collection.get(
            where={
                "document_id": document_id,
            },
            include=include,
        )

    def count_document_chunks(
        self,
        document_id,
    ):
        """取得指定 Document 的 Chunk 數量。"""

        result = self.get_document_chunks(
            document_id=document_id,
        )

        return len(result.get("ids", []))

    def count(self):
        """取得 Collection 的總記錄數。"""

        return self.collection.count()

    def get_collection(self):
        """取得目前 Paper Collection。"""

        return self.collection

    def get_collection_name(self):
        """取得 Collection 名稱。"""

        return self.collection_name

    def get_persist_directory(self):
        """取得 Persistent Directory。"""

        return self.persist_directory


__all__ = [
    "PaperChromaStorage",
    "PAPER_CHROMA_PERSIST_DIRECTORY",
    "PAPER_CHROMA_COLLECTION_NAME",
    "PAPER_CHROMA_DISTANCE_METRIC",
]
