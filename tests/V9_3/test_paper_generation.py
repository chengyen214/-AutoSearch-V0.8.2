
from unittest.mock import Mock, call

import pytest

from rag.paper_generation import PaperGeneration


@pytest.fixture
def components():
    retrieval = Mock()
    context_assembler = Mock()
    prompt_builder = Mock()
    llm_invoker = Mock()
    answer_generator = Mock()

    pipeline = PaperGeneration(
        retrieval=retrieval,
        context_assembler=context_assembler,
        prompt_builder=prompt_builder,
        llm_invoker=llm_invoker,
        answer_generator=answer_generator,
    )

    retrieval_result = {
        "results": [{"id": "chunk-1"}],
    }

    assembled_context = {
        "context": "論文指出，測試方法能改善檢索品質。",
        "chunks": [
            {
                "metadata": {
                    "document_id": "paper-001",
                    "chunk_index": 3,
                    "title": "RAG Evaluation",
                    "source_url": "https://example.com/paper",
                },
                "text": "測試方法能改善檢索品質。",
            },
            {
                "metadata": {
                    "document_id": "paper-002",
                    "chunk_index": 5,
                    "title": "Retrieval Methods",
                    "url": "https://example.com/second",
                },
                "text": "檢索品質需要使用相關性評估。",
            },
        ],
    }

    retrieval.retrieve.return_value = retrieval_result
    context_assembler.assemble.return_value = assembled_context
    prompt_builder.build.return_value = "test prompt"
    llm_invoker.invoke.return_value = "test LLM response"
    answer_generator.generate.return_value = {
        "answer_text": "檢索品質可透過相關性評估。",
        "source_references": [
            {"source_index": 1, "document_id": "paper-001"},
        ],
    }

    return {
        "pipeline": pipeline,
        "retrieval": retrieval,
        "context_assembler": context_assembler,
        "prompt_builder": prompt_builder,
        "llm_invoker": llm_invoker,
        "answer_generator": answer_generator,
        "retrieval_result": retrieval_result,
        "assembled_context": assembled_context,
    }


def test_generate_success(components):
    c = components

    result = c["pipeline"].generate("如何評估 RAG？")

    assert result["status"] == "DONE"
    assert result["query"] == "如何評估 RAG？"
    assert result["answer_text"] == "檢索品質可透過相關性評估。"
    assert result["source_references"] == [
        {"source_index": 1, "document_id": "paper-001"},
    ]
    assert result["retrieval"] is c["retrieval_result"]
    assert result["context"] is c["assembled_context"]

    c["retrieval"].retrieve.assert_called_once_with(
        query="如何評估 RAG？",
        top_k=5,
        document_id=None,
        document_ids=None,
        source_type=None,
        page_number=None,
    )
    c["context_assembler"].assemble.assert_called_once_with(
        c["retrieval_result"]
    )
    c["llm_invoker"].invoke.assert_called_once_with("test prompt")
    c["answer_generator"].generate.assert_called_once()


def test_generation_context_mapping(components):
    c = components

    result = c["pipeline"].generate("如何評估 RAG？")

    generation_context = c["prompt_builder"].build.call_args.kwargs[
        "context"
    ]

    assert generation_context["count"] == 2
    assert generation_context["entries"] == [
        {
            "source_index": 1,
            "document_id": "paper-001",
            "chunk_index": 3,
            "title": "RAG Evaluation",
            "url": "https://example.com/paper",
            "content": "測試方法能改善檢索品質。",
        },
        {
            "source_index": 2,
            "document_id": "paper-002",
            "chunk_index": 5,
            "title": "Retrieval Methods",
            "url": "https://example.com/second",
            "content": "檢索品質需要使用相關性評估。",
        },
    ]

    assert "[Source 1]" in generation_context["context_text"]
    assert "[Source 2]" in generation_context["context_text"]
    assert "paper-001" in generation_context["context_text"]
    assert "paper-002" in generation_context["context_text"]


def test_no_context_skips_generation(components):
    c = components
    c["context_assembler"].assemble.return_value = {
        "context": "   ",
        "chunks": [],
    }

    result = c["pipeline"].generate("無相關論文的問題")

    assert result["status"] == "NO_CONTEXT"
    assert result["answer_text"] == (
        "目前檢索到的論文內容不足以回答這個問題。"
    )
    assert result["source_references"] == []
    assert result["retrieval"] is c["retrieval_result"]
    assert result["context"]["chunks"] == []

    c["prompt_builder"].build.assert_not_called()
    c["llm_invoker"].invoke.assert_not_called()
    c["answer_generator"].generate.assert_not_called()


@pytest.mark.parametrize("query", ["", "   ", "\n\t"])
def test_empty_query_raises_value_error(components, query):
    with pytest.raises(ValueError, match="query cannot be empty"):
        components["pipeline"].generate(query)

    components["retrieval"].retrieve.assert_not_called()


@pytest.mark.parametrize("query", [None, 123, [], {}])
def test_non_string_query_raises_type_error(components, query):
    with pytest.raises(TypeError, match="query must be a string"):
        components["pipeline"].generate(query)

    components["retrieval"].retrieve.assert_not_called()


def test_query_is_stripped(components):
    c = components

    result = c["pipeline"].generate("  RAG 評估  ")

    assert result["query"] == "RAG 評估"
    assert c["retrieval"].retrieve.call_args.kwargs["query"] == "RAG 評估"


def test_retrieval_filters_are_forwarded(components):
    c = components

    c["pipeline"].generate(
        "RAG 評估",
        top_k=3,
        document_id="paper-001",
        document_ids=["paper-001", "paper-002"],
        source_type="paper",
        page_number=2,
    )

    assert c["retrieval"].retrieve.call_args == call(
        query="RAG 評估",
        top_k=3,
        document_id="paper-001",
        document_ids=["paper-001", "paper-002"],
        source_type="paper",
        page_number=2,
    )


def test_llm_response_is_forwarded_to_answer_generator(components):
    c = components

    c["pipeline"].generate("RAG 評估")

    c["answer_generator"].generate.assert_called_once()
    kwargs = c["answer_generator"].generate.call_args.kwargs

    assert kwargs["llm_response"] == "test LLM response"
    assert kwargs["context"]["count"] == 2


def test_missing_title_and_url_use_empty_strings(components):
    c = components
    c["context_assembler"].assemble.return_value = {
        "context": "測試內容",
        "chunks": [
            {
                "metadata": {
                    "document_id": "paper-003",
                    "chunk_index": 0,
                },
                "text": "測試內容",
            }
        ],
    }

    c["pipeline"].generate("測試問題")

    entries = c["prompt_builder"].build.call_args.kwargs[
        "context"
    ]["entries"]

    assert entries[0]["title"] == ""
    assert entries[0]["url"] == ""
