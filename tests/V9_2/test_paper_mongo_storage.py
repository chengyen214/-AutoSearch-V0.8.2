
"""
tests/V9_0/test_paper_mongo_storage.py

驗證 Paper Pipeline 的 MongoDB HTML 與 GridFS PDF 儲存結果。
"""

from database.paper_mongo_repository import PaperMongoRepository


def main():
    repository = PaperMongoRepository()
    collection = repository.collection
    database = repository.database
    gridfs_collection = database["fs.files"]

    documents = list(
        collection.find(
            {"document_id": {"$regex": "^openalex:"}},
            {
                "_id": 1,
                "document_id": 1,
                "url": 1,
                "resolved_url": 1,
                "html": 1,
                "resources": 1,
                "created_at": 1,
            },
        ).sort("created_at", -1).limit(10)
    )

    print("\nMongoDB Paper Storage Test")
    print("=" * 60)
    print(f"檢查 HTML 文件數：{len(documents)}")

    if not documents:
        print("FAIL：找不到 OpenAlex 論文 HTML 文件")
        return

    html_pass = 0
    resource_pass = 0
    pdf_pass = 0

    for index, document in enumerate(documents, start=1):
        document_id = document.get("document_id")
        html = document.get("html")
        resources = document.get("resources") or {}

        html_ok = isinstance(html, str) and bool(html.strip())
        resource_ok = (
            isinstance(resources.get("css", []), list)
            and isinstance(resources.get("images", []), list)
        )

        pdf = gridfs_collection.find_one(
            {"metadata.document_id": document_id},
            {"_id": 1, "length": 1, "filename": 1, "metadata": 1},
        )

        pdf_ok = pdf is not None

        html_pass += html_ok
        resource_pass += resource_ok
        pdf_pass += pdf_ok

        print(f"\n[{index}] {document.get('url')}")
        print(f"  document_id : {document_id}")
        print(f"  HTML         : {'PASS' if html_ok else 'FAIL'}")
        print(f"  CSS entries  : {len(resources.get('css', []))}")
        print(f"  Image entries: {len(resources.get('images', []))}")
        print(f"  Resources    : {'PASS' if resource_ok else 'FAIL'}")
        print(f"  PDF in GridFS: {'PASS' if pdf_ok else 'NOT FOUND'}")

        if pdf:
            print(f"  PDF filename : {pdf.get('filename')}")
            print(f"  PDF size     : {pdf.get('length')} bytes")

    print("\n" + "=" * 60)
    print(f"HTML 非空：{html_pass}/{len(documents)}")
    print(f"Resources 格式：{resource_pass}/{len(documents)}")
    print(f"GridFS PDF：{pdf_pass}/{len(documents)}")
    print("注意：沒有 PDF 的論文不一定代表儲存失敗，可能是來源沒有提供或下載失敗。")


if __name__ == "__main__":
    main()
