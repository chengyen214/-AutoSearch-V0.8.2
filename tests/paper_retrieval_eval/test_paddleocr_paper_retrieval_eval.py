"""
P5.4 PaddleOCR Paper Retrieval Evaluation

Load a question set, retrieve PaddleOCR paper chunks,
and save the results for manual relevance annotation.
"""

import json
from pathlib import Path

import pytest

from rag.paddleocr_paper_retrieval import PaddleOCRPaperRetrieval


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

QUESTION_FILE = "questions5.json"
ANSWER_FILE = "answer5_paddleocr.json"

TOP_K = 5


@pytest.fixture(scope="module")
def retrieval():
    return PaddleOCRPaperRetrieval()


def load_questions():
    question_path = DATA_DIR / QUESTION_FILE

    if not question_path.exists():
        pytest.fail(f"Question file not found: {question_path}")

    with question_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data.get("questions"), list):
        pytest.fail("Question file must contain a 'questions' list.")

    if not data["questions"]:
        pytest.fail("Question list is empty.")

    if not data.get("document_id"):
        pytest.fail("Question file must contain 'document_id'.")

    return data


def run_retrieval(retrieval, question_data):
    document_id = question_data["document_id"]
    evaluation_results = []

    for item in question_data["questions"]:
        question_id = item["id"]
        question = item["question"]

        print(f"\n[{question_id}] {question}")

        result = retrieval.retrieve(
            query=question,
            top_k=TOP_K,
            document_id=document_id,
        )

        chunks = []

        for rank, chunk in enumerate(result.get("results", []), start=1):
            chunks.append({
                "rank": rank,
                "chunk_id": chunk.get("chunk_id"),
                "text": chunk.get("text", ""),
                "metadata": chunk.get("metadata", {}),
                "distance": chunk.get("distance"),
                "relevance": None,
                "relevance_notes": ""
            })

        evaluation_results.append({
            "question_id": question_id,
            "question": question,
            "retrieval_query": result.get("query", question),
            "collection_name": result.get("collection_name"),
            "total_results": result.get("total_results", len(chunks)),
            "top_k": TOP_K,
            "chunks": chunks
        })

        print(f"Retrieved chunks: {len(chunks)}")

    return evaluation_results


def test_paddleocr_paper_retrieval_eval(retrieval):
    question_data = load_questions()

    evaluation_results = run_retrieval(
        retrieval=retrieval,
        question_data=question_data,
    )

    output = {
        "document_id": question_data["document_id"],
        "paper_title": question_data.get("paper_title", ""),
        "round": question_data.get("round"),
        "question_file": QUESTION_FILE,
        "top_k": TOP_K,
        "retrieval_method": "paddleocr_vl_1_6",
        "collection_name": retrieval.storage.get_collection_name(),
        "evaluation_method": "manual_chunk_relevance",
        "relevance_scale": {
            "2": "Directly relevant: the chunk contains information that answers the question.",
            "1": "Partially relevant: the chunk contains useful but incomplete or indirect information.",
            "0": "Not relevant: the chunk does not provide useful information for answering the question."
        },
        "results": evaluation_results
    }

    output_path = DATA_DIR / ANSWER_FILE
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(output, file, ensure_ascii=False, indent=2)

    print(f"\nEvaluation output saved: {output_path}")
    print(f"Questions: {len(evaluation_results)}")
    print(f"Top-K: {TOP_K}")

    assert len(evaluation_results) == len(question_data["questions"])
    assert output_path.exists()