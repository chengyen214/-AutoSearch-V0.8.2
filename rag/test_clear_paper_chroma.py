"""
tests/V9_3/test_clear_paper_chroma.py

AutoSearch V9

清除 Paper ChromaDB 索引資料。
"""

from rag.paper_chroma_storage import PaperChromaStorage


def main():
    storage = PaperChromaStorage()

    collection = storage.get_collection()
    before = collection.count()

    print(f"清理前 Paper Chunks：{before}")

    if before == 0:
        print("Paper ChromaDB 已經是空的。")
        return

    collection.delete(where={"source_type": "paper_pdf"})

    after = collection.count()

    print(f"清理後 Paper Chunks：{after}")

    if after == 0:
        print("Paper ChromaDB 清理完成。")
    else:
        print("警告：仍有資料未清除。")


if __name__ == "__main__":
    main()