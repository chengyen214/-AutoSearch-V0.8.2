"""
rag/paper_query_filter.py

AutoSearch V9

Paper Query Filter

用途：

    將 Paper RAG 查詢條件轉換為 ChromaDB Metadata Filter。

支援：

    1. 單一 document_id
    2. 多個 document_ids
    3. source_type
    4. page_number

不負責：

    1. Embedding
    2. 向量搜尋
    3. ChromaDB 資料存取
    4. Web RAG 查詢
"""


class PaperQueryFilter:
    """建立 Paper RAG 的 ChromaDB Metadata Filter。"""

    @staticmethod
    def _validate_string(value, field_name):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(
                f"{field_name} must be a non-empty string."
            )

    @staticmethod
    def _validate_page_number(page_number):
        if (
            isinstance(page_number, bool)
            or not isinstance(page_number, int)
            or page_number < 1
        ):
            raise ValueError(
                "page_number must be a positive integer."
            )

    @classmethod
    def build(
        cls,
        document_id=None,
        document_ids=None,
        source_type=None,
        page_number=None,
    ):
        """
        建立 ChromaDB where Filter。

        Args:
            document_id: 單一論文 ID。
            document_ids: 多個論文 ID。
            source_type: 文件來源類型。
            page_number: PDF 頁碼，從 1 開始。

        Returns:
            dict | None: ChromaDB where Filter。
                         沒有條件時回傳 None。
        """

        if document_id is not None and document_ids is not None:
            raise ValueError(
                "Specify either document_id or document_ids, not both."
            )

        conditions = []

        if document_id is not None:
            cls._validate_string(
                document_id,
                "document_id",
            )
            conditions.append({
                "document_id": document_id,
            })

        if document_ids is not None:
            if (
                not isinstance(document_ids, (list, tuple))
                or not document_ids
            ):
                raise ValueError(
                    "document_ids must be a non-empty list or tuple."
                )

            for value in document_ids:
                cls._validate_string(
                    value,
                    "document_ids item",
                )

            conditions.append({
                "document_id": {
                    "$in": list(dict.fromkeys(document_ids)),
                },
            })

        if source_type is not None:
            cls._validate_string(
                source_type,
                "source_type",
            )
            conditions.append({
                "source_type": source_type,
            })

        if page_number is not None:
            cls._validate_page_number(page_number)
            conditions.append({
                "page_number": page_number,
            })

        if not conditions:
            return None

        if len(conditions) == 1:
            return conditions[0]

        return {
            "$and": conditions,
        }


__all__ = [
    "PaperQueryFilter",
]