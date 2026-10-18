
"""
rag/reset_paddleocr_collection.py

AutoSearch V9

PaddleOCR ChromaDB Collection Reset

用途：
    清除 PaddleOCR 專用 Collection 的所有 Chunk。
    保留 Collection 與其他資料不變。
"""

from rag.paper_chroma_storage import PaperChromaStorage


PADDLEOCR_COLLECTION_NAME = (
    "autosearch_papers_paddleocr_vl16"
)


def main():
    storage = PaperChromaStorage(
        collection_name=PADDLEOCR_COLLECTION_NAME
    )

    collection = storage.get_collection()
    before_count = collection.count()

    print("===== PaddleOCR Collection Reset =====")
    print(f"Collection: {storage.get_collection_name()}")
    print(f"Chunks before reset: {before_count}")

    if before_count == 0:
        print("Collection is already empty.")
        return

    confirmation = input(
        "輸入 RESET 確認清空此 Collection："
    )

    if confirmation != "RESET":
        print("Cancelled. No data was deleted.")
        return

    result = collection.get(
        include=[]
    )
    chunk_ids = result.get("ids", [])

    if chunk_ids:
        collection.delete(ids=chunk_ids)

    after_count = collection.count()

    print(f"Chunks after reset: {after_count}")

    if after_count != 0:
        raise RuntimeError(
            "Reset verification failed: collection is not empty."
        )

    print("PaddleOCR Collection reset successfully.")


if __name__ == "__main__":
    main()
