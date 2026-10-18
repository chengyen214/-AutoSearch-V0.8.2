"""
rag/paper_runner.py

AutoSearch V9

Paper RAG Entry Runner

功能：

    1. 查詢 MongoDB 中既有的 Paper
    2. 跳過已建立索引的 Paper
    3. 從 GridFS 取得尚未索引的 PDF
    4. 呼叫 PaperPipeline 建立 ChromaDB 索引
    5. 顯示處理進度與統計結果
"""

from gridfs import GridFS
from tqdm import tqdm

from database.paper_mongo_repository import PaperMongoRepository
from rag.paper_pipeline import PaperPipeline


def main():
    repository = PaperMongoRepository()
    collection = repository.collection
    database = repository.database
    gridfs = GridFS(database)
    pipeline = PaperPipeline()

    papers = list(
        collection.find(
            {"document_id": {"$regex": "^openalex:"}},
            {
                "_id": 0,
                "document_id": 1,
                "url": 1,
                "title": 1,
            },
        ).sort("created_at", 1)
    )

    total = len(papers)

    results = {
        "total": total,
        "done": 0,
        "skipped": 0,
        "empty": 0,
        "failed": 0,
        "no_pdf": 0,
    }

    print("\nPaper RAG Indexing")
    print("=" * 60)
    print(f"總論文數：{total}")
    print("=" * 60)

    with tqdm(
        papers,
        desc="Paper RAG",
        unit="paper",
        dynamic_ncols=True,
    ) as progress:
        for index, paper in enumerate(progress, start=1):
            document_id = paper.get("document_id")
            prefix = f"[{index}/{total}]"

            progress.set_postfix_str(
                document_id or "Unknown",
                refresh=True,
            )

            try:
                if not document_id:
                    raise ValueError("Missing document_id.")

                if pipeline.is_indexed(document_id):
                    results["skipped"] += 1
                    tqdm.write(
                        f"{prefix} [SKIPPED] {document_id}"
                    )
                    continue

                pdf_file = gridfs.find_one(
                    {"metadata.document_id": document_id}
                )

                if pdf_file is None:
                    results["no_pdf"] += 1
                    tqdm.write(
                        f"{prefix} [NO PDF] {document_id}"
                    )
                    continue

                tqdm.write(
                    f"{prefix} [PROCESSING] {document_id}"
                )

                result = pipeline.index_pdf(
                    pdf_bytes=pdf_file.read(),
                    document_id=document_id,
                    source_url=paper.get("url"),
                    title=paper.get("title"),
                )

                status = result["status"]

                if status == "DONE":
                    results["done"] += 1
                elif status == "SKIPPED":
                    results["skipped"] += 1
                elif status == "EMPTY":
                    results["empty"] += 1
                else:
                    results["failed"] += 1

                chunk_count = result.get(
                    "indexed_count",
                    result.get("chunk_count", 0),
                )

                tqdm.write(
                    f"{prefix} [{status}] {document_id} "
                    f"| chunks={chunk_count}"
                )

            except Exception as exc:
                results["failed"] += 1
                tqdm.write(
                    f"{prefix} [FAILED] {document_id}: {exc}"
                )

    print("\nPaper RAG Indexing Summary")
    print("=" * 60)
    print(f"總論文數：{results['total']}")
    print(f"索引成功：{results['done']}")
    print(f"已存在索引：{results['skipped']}")
    print(f"沒有 PDF：{results['no_pdf']}")
    print(f"沒有可索引內容：{results['empty']}")
    print(f"處理失敗：{results['failed']}")
    print("=" * 60)


if __name__ == "__main__":
    main()