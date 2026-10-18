
"""
tests/V9_3/test_paper_generation_real.py

AutoSearch V9
P5.5 Paper Generation Real Test
"""

from pprint import pprint

from rag.paper_generation import PaperGeneration


def test_paper_generation_real():
    document_id = "openalex:W7221558939"
    query = (
        "What surface engineering strategies improve "
        "g-C3N4-based nanocatalysts for photocatalytic "
        "cancer therapy, and what are their limitations?"
    )

    generation = PaperGeneration()

    result = generation.generate(
        query=query,
        top_k=5,
        document_id=document_id,
    )

    print("\n=== Paper Generation Real Test ===")
    print(f"Document ID: {document_id}")
    print(f"Query: {query}")
    print(f"Status: {result['status']}")

    print("\n=== Answer ===")
    print(result["answer_text"])

    print("\n=== Source References ===")
    pprint(result["source_references"])

    print("\n=== Retrieval Result ===")
    pprint(result["retrieval"])

    print("\n=== Context Summary ===")
    context = result["context"]
    print(f"Context length: {len(context.get('context', ''))}")
    print(f"Chunk count: {len(context.get('chunks', []))}")

    assert result["status"] == "DONE", (
        "Generation did not complete. "
        "Check whether document 226 has indexed chunks "
        "and whether the LLM service is available. "
        f"Status: {result['status']}"
    )

    assert result["answer_text"].strip(), (
        "Generated answer is empty."
    )

    assert result["context"]["chunks"], (
        "No retrieved chunks were returned."
    )

    assert result["source_references"], (
        "No source references were returned."
    )
