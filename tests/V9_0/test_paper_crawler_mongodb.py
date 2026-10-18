"""
tests/V9_0/test_paper_crawler_mongodb.py

AutoSearch V5

Paper Crawler MongoDB Integration Real Test

測試：

1. PaperCrawler Landing Page Crawl
2. PaperCrawler PDF Download
3. MongoDB raw_html Persistence
4. MongoDB GridFS Persistence
5. CSS / Images Persistence
6. PDF Binary Verification
7. GridFS Chunk URL Verification
8. Test Data Cleanup
"""

from gridfs import GridFS

from database.mongo_connection import (
    get_mongo_database,
)
from paper.paper_crawler import (
    PaperCrawler,
)


TEST_DOCUMENT_ID = "test-v9-paper-crawler-document"

TEST_PAPER = {
    "document_id": TEST_DOCUMENT_ID,
    "title": "Paper Crawler MongoDB Integration Test",
    "url": "https://link.springer.com/article/10.1007/s00034-026-03814-w",
    "pdf_url": (
        "https://link.springer.com/content/pdf/"
        "10.1007/s00034-026-03814-w.pdf"
    ),
}


def cleanup_test_data():
    """清除本次 Real Test 建立的 MongoDB 測試資料。"""

    database = get_mongo_database()

    database["raw_html"].delete_many(
        {
            "document_id": TEST_DOCUMENT_ID,
        }
    )

    fs = GridFS(
        database
    )

    files = database["fs.files"].find(
        {
            "metadata.document_id": TEST_DOCUMENT_ID,
        }
    )

    for file_document in files:
        fs.delete(
            file_document["_id"]
        )


def verify_raw_html(
    database,
):
    """確認 Paper Landing Page 已儲存至 raw_html。"""

    document = database["raw_html"].find_one(
        {
            "document_id": TEST_DOCUMENT_ID,
        }
    )

    assert document is not None

    assert document["document_id"] == (
        TEST_DOCUMENT_ID
    )

    assert document["url"] == (
        TEST_PAPER["url"]
    )

    assert document.get(
        "html"
    )

    assert document.get(
        "content_hash"
    )

    assert document.get(
        "created_at"
    )

    assert document.get(
        "updated_at"
    )

    resources = document.get(
        "resources",
        {},
    )

    assert "css" in resources
    assert "images" in resources

    print(
        "\n[PASS] MongoDB raw_html"
    )

    print(
        f"  document_id  : {document['document_id']}"
    )

    print(
        f"  url          : {document['url']}"
    )

    print(
        f"  html size    : {len(document['html'])}"
    )

    print(
        f"  content_hash : {document['content_hash']}"
    )

    print(
        f"  CSS count    : {len(resources['css'])}"
    )

    print(
        f"  Image count  : {len(resources['images'])}"
    )


def verify_gridfs(
    database,
    expected_pdf,
):
    """確認 PDF 已儲存至 GridFS 並可讀回。"""

    files = list(
        database["fs.files"].find(
            {
                "metadata.document_id":
                    TEST_DOCUMENT_ID,
            }
        )
    )

    assert len(files) == 1

    file_document = files[0]

    fs = GridFS(
        database
    )

    grid_file = fs.get(
        file_document["_id"]
    )

    stored_pdf = grid_file.read()

    assert stored_pdf == expected_pdf

    assert grid_file is not None

    assert (
        grid_file.filename
        == "paper.pdf"
    )

    metadata = grid_file.metadata

    assert metadata is not None

    assert metadata["document_id"] == (
        TEST_DOCUMENT_ID
    )

    assert metadata["url"] == (
        TEST_PAPER["url"]
    )

    assert metadata["pdf_url"] == (
        TEST_PAPER["pdf_url"]
    )

    assert metadata["content_hash"]

    assert metadata["file_size"] == (
        len(expected_pdf)
    )

    chunks = list(
        database["fs.chunks"].find(
            {
                "files_id":
                    file_document["_id"],
            }
        )
    )

    assert len(chunks) >= 1

    for chunk in chunks:
        assert chunk["files_id"] == (
            file_document["_id"]
        )

        assert chunk["url"] == (
            TEST_PAPER["url"]
        )

        assert "n" in chunk
        assert "data" in chunk

    print(
        "\n[PASS] MongoDB GridFS"
    )

    print(
        f"  file_id      : {file_document['_id']}"
    )

    print(
        f"  filename     : {file_document['filename']}"
    )

    print(
        f"  PDF size     : {len(stored_pdf)}"
    )

    print(
        f"  document_id  : {metadata['document_id']}"
    )

    print(
        f"  url          : {metadata['url']}"
    )

    print(
        f"  pdf_url      : {metadata['pdf_url']}"
    )

    print(
        f"  content_hash : {metadata['content_hash']}"
    )

    print(
        f"  chunk count  : {len(chunks)}"
    )

    print(
        f"  chunk url    : {chunks[0]['url']}"
    )


def main():
    """執行 PaperCrawler MongoDB Integration Real Test。"""

    print(
        "=" * 60
    )

    print(
        "PaperCrawler MongoDB Integration Real Test"
    )

    print(
        "=" * 60
    )

    database = get_mongo_database()

    try:
        print(
            "\n[1] MongoDB Connection"
        )

        print(
            f"Database : {database.name}"
        )

        print(
            "\n[2] Cleaning old test data..."
        )

        cleanup_test_data()

        print(
            "[PASS] Old test data cleaned"
        )

        print(
            "\n[3] Running PaperCrawler..."
        )

        crawler = PaperCrawler()

        result = crawler.crawl(
            TEST_PAPER
        )

        assert result is not None

        assert result.get(
            "html"
        )

        assert result.get(
            "content_hash"
        )

        assert result.get(
            "pdf"
        )

        print(
            "[PASS] PaperCrawler completed"
        )

        print(
            f"  Landing URL : {result['url']}"
        )

        print(
            f"  Resolved URL: {result['resolved_url']}"
        )

        print(
            f"  HTML size   : {len(result['html'])}"
        )

        print(
            f"  PDF URL     : {result['pdf_url']}"
        )

        print(
            f"  PDF size    : "
            f"{result['pdf']['file_size']}"
        )

        print(
            "\n[4] Verifying raw_html..."
        )

        verify_raw_html(
            database
        )

        print(
            "\n[5] Verifying GridFS..."
        )

        verify_gridfs(
            database,
            result["pdf"]["content"],
        )

        print(
            "\n[6] Cleaning test data..."
        )

        cleanup_test_data()

        print(
            "[PASS] Test data cleaned"
        )

        remaining_raw_html = database[
            "raw_html"
        ].count_documents(
            {
                "document_id":
                    TEST_DOCUMENT_ID,
            }
        )

        remaining_gridfs = database[
            "fs.files"
        ].count_documents(
            {
                "metadata.document_id":
                    TEST_DOCUMENT_ID,
            }
        )

        remaining_chunks = database[
            "fs.chunks"
        ].count_documents(
            {
                "url": TEST_PAPER["url"],
            }
        )

        assert remaining_raw_html == 0
        assert remaining_gridfs == 0
        assert remaining_chunks == 0

        print(
            "[PASS] Cleanup verified"
        )

        print(
            "\n"
            + "=" * 60
        )

        print(
            "PaperCrawler MongoDB Integration Real Test: PASS"
        )

        print(
            "=" * 60
        )

    except Exception as e:
        print(
            "\n"
            + "=" * 60
        )

        print(
            "PaperCrawler MongoDB Integration Real Test: FAIL"
        )

        print(
            "=" * 60
        )

        print(
            f"\nError: {e}"
        )

        cleanup_test_data()

        raise


if __name__ == "__main__":
    main()