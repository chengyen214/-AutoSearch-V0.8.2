
"""
rag/chroma/ai_keyword_filter.py

AutoSearch RAG

用途：

    檢查 Chroma Chunk：

        page_content
        metadata["ai_keywords"]

    建立：

        metadata["matched_ai_keywords"]

    規則：

        ai_keywords
            = Article-level AI keywords

        matched_ai_keywords
            = 本 Chunk page_content
              實際出現的 keywords

    不修改：
        ai_keywords
        其他 metadata
"""

import json
import re


AI_KEYWORDS_FIELD = "ai_keywords"
MATCHED_AI_KEYWORDS_FIELD = "matched_ai_keywords"


def _keyword_exists(
    page_content,
    keyword,
):
    """
    判斷 keyword 是否存在於 page_content。
    """

    if not page_content:
        return False

    if not keyword:
        return False

    text = str(
        page_content
    )

    keyword = str(
        keyword
    ).strip()

    if not keyword:
        return False

    if re.fullmatch(
        r"[A-Za-z0-9][A-Za-z0-9 ._+/-]*",
        keyword,
    ):
        pattern = (
            r"(?<![A-Za-z0-9])"
            + re.escape(keyword)
            + r"(?![A-Za-z0-9])"
        )

        return (
            re.search(
                pattern,
                text,
                flags=re.IGNORECASE,
            )
            is not None
        )

    return (
        keyword.casefold()
        in text.casefold()
    )


def _load_keywords(
    value,
):
    """
    將 ai_keywords 轉成 list[str]。
    """

    if value is None:
        return []

    if isinstance(
        value,
        str,
    ):
        value = value.strip()

        if not value:
            return []

        try:
            value = json.loads(
                value
            )

        except (
            json.JSONDecodeError,
            TypeError,
        ):
            return []

    if isinstance(
        value,
        (list, tuple),
    ):
        keywords = []

        for keyword in value:
            if keyword is None:
                continue

            keyword = str(
                keyword
            ).strip()

            if keyword:
                keywords.append(
                    keyword
                )

        return keywords

    return []


def filter_ai_keywords(
    page_content,
    metadata,
):
    """
    建立 Chunk-level matched_ai_keywords。

    保留：

        ai_keywords

    新增：

        matched_ai_keywords

    不修改原始 metadata。
    """

    if metadata is None:
        return {}

    filtered_metadata = dict(
        metadata
    )

    keywords = _load_keywords(
        metadata.get(
            AI_KEYWORDS_FIELD
        )
    )

    matched_keywords = [
        keyword
        for keyword in keywords
        if _keyword_exists(
            page_content,
            keyword,
        )
    ]

    filtered_metadata[
        MATCHED_AI_KEYWORDS_FIELD
    ] = json.dumps(
        matched_keywords,
        ensure_ascii=False,
    )

    return filtered_metadata


def filter_document_metadata(
    page_content,
    metadata,
):
    """
    Chroma Chunk Metadata Filter。

    目前只處理：

        matched_ai_keywords

    其他 metadata 原樣保留。
    """

    return filter_ai_keywords(
        page_content,
        metadata,
    )


__all__ = [
    "AI_KEYWORDS_FIELD",
    "MATCHED_AI_KEYWORDS_FIELD",
    "filter_ai_keywords",
    "filter_document_metadata",
]