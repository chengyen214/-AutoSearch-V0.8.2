"""
tests/V9_1/test_rag_context_metadata.py

AutoSearch V7

RAG-6 Context Metadata Test
"""

from rag.context.context_builder import (
    ContextBuilder,
)

from rag.retriever.retrieval_result import (
    RetrievalResult,
)


def create_retrieval_result():
    return RetrievalResult(
        chunk="台積電於 2026 年 9 月 28 日發布重要消息。",
        distance=0.1,
        similarity=0.9,
        document_id="doc-001",
        chunk_index=0,
        metadata={
            "title": "DIGITIMES Test Article",
            "url": "https://example.com/article",
            "source": "DIGITIMES",
            "crawl_time": "2026-09-28T08:30:00+00:00",
            "ai_summary": "台積電相關重要消息。",
            "ai_category": "semiconductor",
            "ai_keywords": '["TSMC", "AI", "semiconductor"]',
            "ai_importance": 5,
            "ai_confidence": 0.95,
        },
    )


def test_context_preserves_metadata():
    builder = ContextBuilder()

    result = builder.build(
        [create_retrieval_result()]
    )

    assert result["count"] == 1
    assert len(result["entries"]) == 1

    entry = result["entries"][0]

    assert entry["metadata"]["title"] == (
        "DIGITIMES Test Article"
    )

    assert entry["metadata"]["url"] == (
        "https://example.com/article"
    )

    assert entry["metadata"]["crawl_time"] == (
        "2026-09-28T08:30:00+00:00"
    )

    assert entry["metadata"]["ai_summary"] == (
        "台積電相關重要消息。"
    )


def test_context_metadata_handler_receives_full_metadata():
    builder = ContextBuilder()

    result = builder.build(
        [create_retrieval_result()]
    )

    entry = result["entries"][0]

    assert entry["source_metadata"]["title"] == (
        "DIGITIMES Test Article"
    )

    assert entry["source_metadata"]["url"] == (
        "https://example.com/article"
    )

    assert entry["source_metadata"]["crawl_time"] == (
        "2026-09-28T08:30:00+00:00"
    )

    assert entry["ai_metadata"]["ai_summary"] == (
        "台積電相關重要消息。"
    )

    assert entry["ai_metadata"]["ai_category"] == (
        "semiconductor"
    )


def test_context_text_contains_crawl_time():
    builder = ContextBuilder()

    result = builder.build(
        [create_retrieval_result()]
    )

    context_text = result["context_text"]

    assert (
        "Crawl Time: 2026-09-28T08:30:00+00:00"
        in context_text
    )