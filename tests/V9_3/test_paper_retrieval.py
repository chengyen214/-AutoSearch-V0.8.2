from unittest.mock import Mock

import pytest

from rag.paper_retrieval import PaperRetrieval


@pytest.fixture
def retrieval():
    embedder = Mock()
    embedder.embed_chunk.return_value = [0.1] * 1024

    collection = Mock()
    collection.query.return_value = {
        "ids": [["openalex:W1:0"]],
        "documents": [["Paper chunk content"]],
        "metadatas": [[{
            "document_id": "openalex:W1",
            "chunk_id": "openalex:W1:0",
            "chunk_index": 0,
            "page_number": 1,
        }]],
        "distances": [[0.12]],
    }

    storage = Mock()
    storage.get_collection.return_value = collection
    storage.get_collection_name.return_value = (
        "autosearch_papers_qwen3"
    )

    return PaperRetrieval(
        embedder=embedder,
        storage=storage,
    )


def test_retrieve_returns_results(retrieval):
    result = retrieval.retrieve(
        query="What is semiconductor packaging?",
        top_k=5,
    )

    assert result["total_results"] == 1
    assert result["results"][0]["chunk_id"] == (
        "openalex:W1:0"
    )
    assert result["results"][0]["distance"] == 0.12


def test_retrieve_passes_document_filter(retrieval):
    retrieval.retrieve(
        query="semiconductor packaging",
        document_id="openalex:W1",
    )

    collection = retrieval.storage.get_collection.return_value
    kwargs = collection.query.call_args.kwargs

    assert kwargs["where"] == {
        "document_id": "openalex:W1"
    }


def test_retrieve_passes_multiple_filters(retrieval):
    retrieval.retrieve(
        query="semiconductor packaging",
        document_id="openalex:W1",
        source_type="paper_pdf",
        page_number=1,
    )

    collection = retrieval.storage.get_collection.return_value
    kwargs = collection.query.call_args.kwargs

    assert kwargs["where"] == {
        "$and": [
            {"document_id": "openalex:W1"},
            {"source_type": "paper_pdf"},
            {"page_number": 1},
        ]
    }


def test_retrieve_empty_results(retrieval):
    collection = retrieval.storage.get_collection.return_value
    collection.query.return_value = {
        "ids": [[]],
        "documents": [[]],
        "metadatas": [[]],
        "distances": [[]],
    }

    result = retrieval.retrieve(
        query="unknown topic",
    )

    assert result["total_results"] == 0
    assert result["results"] == []


def test_retrieve_rejects_empty_query(retrieval):
    with pytest.raises(ValueError):
        retrieval.retrieve("  ")


def test_retrieve_rejects_invalid_top_k(retrieval):
    with pytest.raises(ValueError):
        retrieval.retrieve(
            query="semiconductor",
            top_k=0,
        )


def test_retrieve_rejects_conflicting_document_filters(
    retrieval,
):
    with pytest.raises(ValueError):
        retrieval.retrieve(
            query="semiconductor",
            document_id="openalex:W1",
            document_ids=["openalex:W2"],
        )