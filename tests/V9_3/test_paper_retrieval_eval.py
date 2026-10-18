"""
tests/V9_3/test_paper_retrieval_eval.py

AutoSearch V9

P5.4 Paper Retrieval Evaluation

用途：
    評估 Paper RAG 的檢索結果與 Context Assembly。

評估項目：
    1. Top-K Retrieval
    2. Precision@K / Recall@K
    3. Mean Reciprocal Rank (MRR)
    4. Context Assembly
    5. Duplicate Chunks
    6. Context Truncation
    7. Source Traceability

注意：
    relevant_chunks 尚未完成標註時，
    不計算 Precision、Recall 與 MRR。
"""

import json
import math
import unittest
from pathlib import Path

from rag.paper_retrieval import PaperRetrieval
from rag.paper_context_assembler import PaperContextAssembler


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "paper_retrieval_eval.json"
)

TOP_K = 5


def load_evaluation_dataset():
    """載入 Retrieval Evaluation Dataset。"""
    with FIXTURE_PATH.open("r", encoding="utf-8") as file:
        dataset = json.load(file)

    if not isinstance(dataset, dict):
        raise ValueError("Evaluation dataset must be a JSON object.")

    queries = dataset.get("queries")

    if not isinstance(queries, list) or not queries:
        raise ValueError("Dataset must contain a non-empty queries list.")

    query_ids = set()

    for item in queries:
        if not isinstance(item, dict):
            raise ValueError("Each evaluation query must be an object.")

        query_id = item.get("id")
        query = item.get("query")
        expected_document_ids = item.get("expected_document_ids")
        relevant_chunks = item.get("relevant_chunks")

        if not isinstance(query_id, str) or not query_id.strip():
            raise ValueError("Each query must have a non-empty id.")

        if query_id in query_ids:
            raise ValueError(f"Duplicate query id: {query_id}")

        query_ids.add(query_id)

        if not isinstance(query, str) or not query.strip():
            raise ValueError(f"{query_id}: query must be a non-empty string.")

        if not isinstance(expected_document_ids, list):
            raise ValueError(
                f"{query_id}: expected_document_ids must be a list."
            )

        if not isinstance(relevant_chunks, list):
            raise ValueError(
                f"{query_id}: relevant_chunks must be a list."
            )

    return dataset


def calculate_retrieval_metrics(results, relevant_chunks, top_k):
    """
    計算 Chunk 層級的 Precision@K、Recall@K 與 Reciprocal Rank。

    relevance：
        0 = 不相關
        1 = 部分相關
        2 = 高度相關

    只有 relevance > 0 才視為相關 Chunk。
    """
    if not relevant_chunks:
        return {
            "metrics_available": False,
            "reason": "relevant_chunks has not been annotated.",
            "precision_at_k": None,
            "recall_at_k": None,
            "reciprocal_rank": None,
        }

    relevant_ids = set()
    relevance_by_id = {}

    for item in relevant_chunks:
        if not isinstance(item, dict):
            raise ValueError("Each relevant_chunks entry must be an object.")

        chunk_id = item.get("chunk_id")
        relevance = item.get("relevance")

        if not isinstance(chunk_id, str) or not chunk_id:
            raise ValueError("Each relevant chunk must have a chunk_id.")

        if (
            isinstance(relevance, bool)
            or not isinstance(relevance, int)
            or relevance not in (0, 1, 2)
        ):
            raise ValueError(
                f"Invalid relevance for chunk {chunk_id}; expected 0, 1, or 2."
            )

        relevance_by_id[chunk_id] = relevance

        if relevance > 0:
            relevant_ids.add(chunk_id)

    retrieved = results[:top_k]
    retrieved_ids = [
        item.get("chunk_id")
        for item in retrieved
        if item.get("chunk_id")
    ]

    hit_count = sum(
        1 for chunk_id in retrieved_ids
        if chunk_id in relevant_ids
    )

    precision = hit_count / top_k

    recall = (
        hit_count / len(relevant_ids)
        if relevant_ids
        else None
    )

    reciprocal_rank = 0.0

    for rank, chunk_id in enumerate(retrieved_ids, start=1):
        if chunk_id in relevant_ids:
            reciprocal_rank = 1.0 / rank
            break

    return {
        "metrics_available": True,
        "precision_at_k": precision,
        "recall_at_k": recall,
        "reciprocal_rank": reciprocal_rank,
        "relevant_chunk_count": len(relevant_ids),
        "retrieved_relevant_count": hit_count,
        "relevance_by_id": relevance_by_id,
    }


def calculate_document_hit(results, expected_document_ids):
    """檢查 Top-K 是否命中預期文件。"""
    if not expected_document_ids:
        return None

    expected = set(expected_document_ids)

    return any(
        item.get("metadata", {}).get("document_id") in expected
        for item in results
    )


def evaluate_query(
    retrieval,
    assembler,
    query_item,
    top_k=TOP_K,
    max_context_chars=None,
):
    """執行單一 Query 的 Retrieval 與 Context Assembly 評估。"""
    query = query_item["query"]

    retrieval_result = retrieval.retrieve(
        query=query,
        top_k=top_k,
    )

    results = retrieval_result.get("results", [])

    metrics = calculate_retrieval_metrics(
        results=results,
        relevant_chunks=query_item["relevant_chunks"],
        top_k=top_k,
    )

    expected_document_hit = calculate_document_hit(
        results=results,
        expected_document_ids=query_item["expected_document_ids"],
    )

    if max_context_chars is None:
        context_result = assembler.assemble(retrieval_result)
    else:
        context_result = assembler.assemble(
            retrieval_result,
            max_context_chars=max_context_chars,
        )

    context_chunks = context_result.get("chunks", [])

    source_traceability = all(
        isinstance(item.get("chunk_id"), str)
        and isinstance(item.get("metadata"), dict)
        and isinstance(item["metadata"].get("document_id"), str)
        for item in context_chunks
    )

    return {
        "id": query_item["id"],
        "query": query,
        "retrieval": {
            "top_k": top_k,
            "total_results": len(results),
            "results": results,
            "expected_document_hit": expected_document_hit,
            "metrics": metrics,
        },
        "context": {
            "total_chars": context_result.get("total_chars"),
            "max_context_chars": context_result.get("max_context_chars"),
            "total_chunks": context_result.get("total_chunks"),
            "input_chunks": context_result.get("input_chunks"),
            "duplicates_removed": context_result.get("duplicates_removed"),
            "truncated": context_result.get("truncated"),
            "source_traceability": source_traceability,
            "chunks": context_chunks,
        },
    }


def build_summary(query_results):
    """彙整可計算的評估指標。"""
    document_hits = [
        item["retrieval"]["expected_document_hit"]
        for item in query_results
        if item["retrieval"]["expected_document_hit"] is not None
    ]

    metric_results = [
        item["retrieval"]["metrics"]
        for item in query_results
        if item["retrieval"]["metrics"]["metrics_available"]
    ]

    precision_values = [
        item["precision_at_k"]
        for item in metric_results
        if item["precision_at_k"] is not None
    ]

    recall_values = [
        item["recall_at_k"]
        for item in metric_results
        if item["recall_at_k"] is not None
    ]

    reciprocal_ranks = [
        item["reciprocal_rank"]
        for item in metric_results
        if item["reciprocal_rank"] is not None
    ]

    context_results = [item["context"] for item in query_results]

    def average(values):
        return sum(values) / len(values) if values else None

    return {
        "query_count": len(query_results),
        "document_hit_rate": average(
            [float(value) for value in document_hits]
        ),
        "precision_at_k": average(precision_values),
        "recall_at_k": average(recall_values),
        "mrr": average(reciprocal_ranks),
        "annotated_query_count": len(metric_results),
        "unannotated_query_count": (
            len(query_results) - len(metric_results)
        ),
        "context_truncated_count": sum(
            item.get("truncated") is True
            for item in context_results
        ),
        "context_duplicate_chunks_removed": sum(
            item.get("duplicates_removed") or 0
            for item in context_results
        ),
        "context_source_traceability_pass_count": sum(
            item.get("source_traceability") is True
            for item in context_results
        ),
    }


class TestPaperRetrievalEvaluation(unittest.TestCase):
    """Paper RAG P5.4 評估測試。"""

    @classmethod
    def setUpClass(cls):
        cls.dataset = load_evaluation_dataset()
        cls.retrieval = PaperRetrieval()
        cls.assembler = PaperContextAssembler()

    def test_evaluation_dataset(self):
        """驗證評估資料集結構。"""
        self.assertEqual(len(self.dataset["queries"]), 10)

        for item in self.dataset["queries"]:
            self.assertTrue(item["id"])
            self.assertTrue(item["query"])
            self.assertIsInstance(item["expected_document_ids"], list)
            self.assertIsInstance(item["relevant_chunks"], list)

    def test_retrieval_and_context_assembly(self):
        """執行所有 Query 的真實 Retrieval 與 Context Assembly。"""
        query_results = []

        for item in self.dataset["queries"]:
            with self.subTest(query_id=item["id"]):
                result = evaluate_query(
                    retrieval=self.retrieval,
                    assembler=self.assembler,
                    query_item=item,
                    top_k=TOP_K,
                )

                self.assertEqual(result["id"], item["id"])
                self.assertIsInstance(
                    result["retrieval"]["results"],
                    list,
                )
                self.assertIsInstance(
                    result["context"]["source_traceability"],
                    bool,
                )

                query_results.append(result)

        summary = build_summary(query_results)

        output = {
            "dataset": str(FIXTURE_PATH),
            "collection_name": self.dataset.get("collection_name"),
            "evaluation_settings": {
                "top_k": TOP_K,
            },
            "summary": summary,
            "results": query_results,
        }

        output_path = (
            Path(__file__).parent
            / "fixtures"
            / "paper_retrieval_eval_results.json"
        )

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with output_path.open("w", encoding="utf-8") as file:
            json.dump(
                output,
                file,
                ensure_ascii=False,
                indent=2,
            )

        print("\nPaper Retrieval Evaluation")
        print("=" * 50)
        print(f"Queries: {summary['query_count']}")
        print(f"Document Hit Rate: {summary['document_hit_rate']}")
        print(f"Precision@{TOP_K}: {summary['precision_at_k']}")
        print(f"Recall@{TOP_K}: {summary['recall_at_k']}")
        print(f"MRR: {summary['mrr']}")
        print(f"Annotated queries: {summary['annotated_query_count']}")
        print(f"Unannotated queries: {summary['unannotated_query_count']}")
        print(
            "Context truncated:",
            summary["context_truncated_count"],
        )
        print(
            "Duplicate chunks removed:",
            summary["context_duplicate_chunks_removed"],
        )
        print(
            "Source traceability passed:",
            summary["context_source_traceability_pass_count"],
            "/",
            summary["query_count"],
        )
        print(f"Results saved to: {output_path}")

        self.assertEqual(len(query_results), len(self.dataset["queries"]))


if __name__ == "__main__":
    unittest.main()