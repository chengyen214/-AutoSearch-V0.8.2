
"""
tests/V9_5/test_paddleocr_paper_generation.py

AutoSearch V9

P5.5 PaddleOCR-VL-1.6 Real LLM Generation Test
"""

from rag.paddleocr_paper_generation import PaddleOCRPaperGeneration


DOCUMENT_ID = "openalex:W7221558939"

QUERY = "What are the main contributions of this paper?"

TOP_K = 5


def main():
    generator = PaddleOCRPaperGeneration()

    print("===== PaddleOCR Paper LLM Generation Test =====")
    print(f"Document ID: {DOCUMENT_ID}")
    print(f"Query: {QUERY}")
    print(f"Top-K: {TOP_K}")

    result = generator.generate(
        query=QUERY,
        top_k=TOP_K,
        document_id=DOCUMENT_ID,
    )

    print("\n===== Generation Result =====")
    print(f"Status: {result['status']}")
    print(f"Query: {result['query']}")

    print("\n===== Retrieved Chunks =====")
    retrieval = result["retrieval"]

    print(f"Collection: {retrieval['collection_name']}")
    print(f"Total Results: {retrieval['total_results']}")

    for index, chunk in enumerate(
        retrieval["results"],
        start=1,
    ):
        metadata = chunk["metadata"]

        print(f"\n[Chunk {index}]")
        print(f"Chunk ID: {chunk['chunk_id']}")
        print(f"Document ID: {metadata.get('document_id')}")
        print(f"Chunk Index: {metadata.get('chunk_index')}")
        print(f"Page Number: {metadata.get('page_number')}")
        print(f"Distance: {chunk['distance']:.6f}")
        print(f"Text: {chunk['text'][:500]}")

    print("\n===== Generated Answer =====")
    print(result["answer_text"])

    print("\n===== Source References =====")

    for reference in result["source_references"]:
        print(reference)

    print("\n===== Context Statistics =====")
    context = result["context"]

    print(f"Total Chunks: {context['total_chunks']}")
    print(f"Total Characters: {context['total_chars']}")
    print(f"Context Truncated: {context['truncated']}")

    if result["status"] != "DONE":
        raise RuntimeError(
            f"Generation did not complete: {result['status']}"
        )

    if not result["answer_text"].strip():
        raise AssertionError("Generated answer is empty.")

    print("\nPASS: PaddleOCR LLM Generation completed.")


if __name__ == "__main__":
    main()
