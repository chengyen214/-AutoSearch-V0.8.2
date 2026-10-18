"""
rag/paper_embedding.py

AutoSearch V9

P2 Paper Chunk -> Embedding

功能：

    1. 載入 Qwen3-Embedding-0.6B
    2. 將 Paper Chunk 轉換為 Embedding
    3. 支援單筆與批次 Embedding
    4. 驗證輸入文字
    5. 驗證 Embedding 維度與數值
    6. 執行 L2 正規化
    7. 回傳 Embedding Vector

不負責：

    1. PDF 文字擷取
    2. Chunking
    3. ChromaDB
    4. LLM
"""

import math

import numpy as np
from sentence_transformers import SentenceTransformer
from tqdm import tqdm


MODEL_NAME = "Qwen/Qwen3-Embedding-0.6B"
EMBEDDING_DIMENSION = 1024
DEFAULT_BATCH_SIZE = 8


class PaperEmbedding:
    """Paper Chunk Embedding。"""

    def __init__(
        self,
        model_name=MODEL_NAME,
        device=None,
    ):
        model_kwargs = {}

        if device is not None:
            model_kwargs["device"] = device

        self.model = SentenceTransformer(
            model_name,
            **model_kwargs,
        )

        self.embedding_dimension = (
            self.model.get_embedding_dimension()
        )

        if self.embedding_dimension != EMBEDDING_DIMENSION:
            raise ValueError(
                "Unexpected embedding dimension: "
                f"{self.embedding_dimension}. "
                f"Expected: {EMBEDDING_DIMENSION}."
            )

    def _validate_text(self, text):
        if not isinstance(text, str):
            raise TypeError(
                "Chunk text must be a string."
            )

        if not text.strip():
            raise ValueError(
                "Chunk text cannot be empty."
            )

    def _normalize_embedding(self, embedding):
        embedding = np.asarray(
            embedding,
            dtype=np.float32,
        )

        if embedding.ndim != 1:
            raise ValueError(
                "Embedding must be a one-dimensional vector."
            )

        if len(embedding) != self.embedding_dimension:
            raise ValueError(
                "Incorrect embedding dimension: "
                f"{len(embedding)}."
            )

        if not np.isfinite(embedding).all():
            raise ValueError(
                "Embedding contains non-finite values."
            )

        norm = float(np.linalg.norm(embedding))

        if not math.isfinite(norm) or norm <= 0:
            raise ValueError(
                f"Invalid embedding norm: {norm}."
            )

        embedding = embedding / norm

        if not np.isfinite(embedding).all():
            raise ValueError(
                "Normalized embedding contains non-finite values."
            )

        return embedding.tolist()

    def embed_chunk(self, text):
        """
        將單一 Chunk 轉換為 Embedding。

        Args:
            text: 單一 Chunk 的文字內容。

        Returns:
            list[float]: L2 正規化後的 Embedding Vector。
        """

        self._validate_text(text)

        embedding = self.model.encode(
            text,
            normalize_embeddings=False,
            convert_to_numpy=True,
            show_progress_bar=False,
        )

        return self._normalize_embedding(embedding)

    def embed_chunks(
        self,
        texts,
        batch_size=DEFAULT_BATCH_SIZE,
        show_progress_bar=True,
    ):
        """
        批次將多個 Chunk 轉換為 Embedding。

        Args:
            texts: Chunk 文字列表。
            batch_size: 每批送入模型的文字數量。
            show_progress_bar: 是否顯示進度條。

        Returns:
            list[list[float]]: L2 正規化後的 Embedding Vectors。
        """

        if not isinstance(texts, (list, tuple)):
            raise TypeError(
                "texts must be a list or tuple."
            )

        if not texts:
            return []

        if (
            not isinstance(batch_size, int)
            or isinstance(batch_size, bool)
            or batch_size < 1
        ):
            raise ValueError(
                "batch_size must be a positive integer."
            )

        for text in texts:
            self._validate_text(text)

        embeddings = self.model.encode(
            list(texts),
            batch_size=batch_size,
            normalize_embeddings=False,
            convert_to_numpy=True,
            show_progress_bar=False,
        )

        embeddings = np.asarray(
            embeddings,
            dtype=np.float32,
        )

        if embeddings.ndim != 2:
            raise ValueError(
                "Batch embeddings must be a two-dimensional array."
            )

        if embeddings.shape[0] != len(texts):
            raise ValueError(
                "Embedding count does not match input text count."
            )

        if embeddings.shape[1] != self.embedding_dimension:
            raise ValueError(
                "Incorrect embedding dimension: "
                f"{embeddings.shape[1]}."
            )

        if not np.isfinite(embeddings).all():
            raise ValueError(
                "Embeddings contain non-finite values."
            )

        vectors = []

        iterator = enumerate(embeddings, start=1)

        if show_progress_bar:
            iterator = tqdm(
                iterator,
                total=len(embeddings),
                desc="Embedding",
                unit="chunk",
                dynamic_ncols=True,
            )

        for _, embedding in iterator:
            vectors.append(
                self._normalize_embedding(embedding)
            )

        return vectors


__all__ = [
    "PaperEmbedding",
]