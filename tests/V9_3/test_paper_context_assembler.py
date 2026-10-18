import pytest

from rag.paper_context_assembler import (
    PaperContextAssembler,
    DEFAULT_MAX_CONTEXT_CHARS,
)


@pytest.fixture
def retrieval_result():
    return {
        "query": "semiconductor technology",
        "collection_name": "autosearch_papers_qwen3",
        "total_results": 3,
        "results": [
            {
                "chunk_id": "paper-a:2",
                "text": "Third paragraph.",
                "metadata": {
                    "document_id": "paper-a",
                    "chunk_index": 2,
                    "page_number": 2,
                },
                "distance": 0.3,
            },
            {
                "chunk_id": "paper-a:0",
                "text": "First paragraph.",
                "metadata": {
                    "document_id": "paper-a",
                    "chunk_index": 0,
                    "page_number": 1,
                },
                "distance": 0.1,
            },
            {
                "chunk_id": "paper-a:1",
                "text": "Second paragraph.",
                "metadata": {
                    "document_id": "paper-a",
                    "chunk_index": 1,
                    "page_number": 1,
                },
                "distance": 0.2,
            },
        ],
    }


def test_assemble_preserves_document_order(
    retrieval_result,
):
    assembler = PaperContextAssembler()

    result = assembler.assemble(retrieval_result)

    chunk_ids = [
        item["chunk_id"]
        for item in result["chunks"]
    ]

    assert chunk_ids == [
        "paper-a:0",
        "paper-a:1",
        "paper-a:2",
    ]


def test_assemble_removes_duplicate_chunks(
    retrieval_result,
):
    duplicate = dict(
        retrieval_result["results"][0]
    )

    retrieval_result["results"].append(duplicate)

    result = PaperContextAssembler().assemble(
        retrieval_result
    )

    assert result["input_chunks"] == 4
    assert result["total_chunks"] == 3
    assert result["duplicates_removed"] == 1


def test_assemble_respects_context_limit(
    retrieval_result,
):
    max_chars = 100

    result = PaperContextAssembler(
        max_context_chars=max_chars
    ).assemble(retrieval_result)

    assert result["total_chars"] <= max_chars
    assert len(result["context"]) == result["total_chars"]


def test_assemble_preserves_source_metadata(
    retrieval_result,
):
    result = PaperContextAssembler().assemble(
        retrieval_result
    )

    first_chunk = result["chunks"][0]

    assert first_chunk["metadata"]["document_id"] == "paper-a"
    assert first_chunk["metadata"]["chunk_index"] == 0
    assert first_chunk["metadata"]["page_number"] == 1


def test_assemble_empty_results():
    result = PaperContextAssembler().assemble({
        "query": "unknown topic",
        "results": [],
    })

    assert result["context"] == ""
    assert result["total_chars"] == 0
    assert result["total_chunks"] == 0
    assert result["duplicates_removed"] == 0
    assert result["truncated"] is False


def test_assemble_rejects_invalid_limit():
    with pytest.raises(ValueError):
        PaperContextAssembler(
            max_context_chars=0
        )


def test_assemble_rejects_invalid_result():
    with pytest.raises(ValueError):
        PaperContextAssembler().assemble({
            "query": "test",
            "results": "invalid",
        })


def test_assemble_supports_custom_limit(
    retrieval_result,
):
    result = PaperContextAssembler().assemble(
        retrieval_result,
        max_context_chars=80,
    )

    assert result["max_context_chars"] == 80
    assert result["total_chars"] <= 80


def test_default_context_limit():
    assert DEFAULT_MAX_CONTEXT_CHARS == 6000