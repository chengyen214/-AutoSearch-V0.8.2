"""
tests/V9_0/test_paper_crawler_result_structure.py

AutoSearch V5

Paper Crawler Result Structure Real Test

測試：

1. PaperCrawler Real Crawl
2. Crawl Result Top-Level Structure
3. Resources Structure
4. PDF Result Structure
5. MongoDB Test Data Cleanup
"""

from gridfs import GridFS

from database.mongo_connection import (
    get_mongo_database,
)
from paper.paper_crawler import (
    PaperCrawler,
)


TEST_DOCUMENT_ID = "test-v9-paper-crawler-result-structure"

TEST_PAPER = {
    "document_id": TEST_DOCUMENT_ID,
    "title": "Paper Crawler Result Structure Test",
    "url": "https://link.springer.com/article/10.1007/s00034-026-03814-w",
    "pdf_url": (
        "https://link.springer.com/content/pdf/"
        "10.1007/s00034-026-03814-w.pdf"
    ),
}


EXPECTED_TOP_LEVEL_KEYS = {
    "document_id",
    "title",
    "url",
    "resolved_url",
    "html",
    "content_hash",
    "resources",
    "pdf_url",
    "pdf",
}

EXPECTED_PDF_KEYS = {
    "url",
    "final_url",
    "content",
    "content_hash",
    "mime_type",
    "file_size",
}

EXPECTED_RESOURCE_KEYS = {
    "css",
    "images",
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
            "metadata.document_id":
                TEST_DOCUMENT_ID,
        }
    )

    for file_document in files:
        fs.delete(
            file_document["_id"]
        )


def print_value_type(
    name,
    value,
):
    """Print field name and value type。"""

    print(
        f"  {name:<15}: {type(value).__name__}"
    )


def verify_top_level_structure(
    result,
):
    """確認 Crawl Result 頂層資料結構。"""

    assert isinstance(
        result,
        dict,
    )

    actual_keys = set(
        result.keys()
    )

    assert (
        actual_keys
        == EXPECTED_TOP_LEVEL_KEYS
    )

    print(
        "\n[PASS] Crawl Result top-level structure"
    )

    print(
        f"  Keys           : {sorted(actual_keys)}"
    )

    for key in sorted(
        actual_keys
    ):
        print_value_type(
            key,
            result[key],
        )


def verify_paper_fields(
    result,
):
    """確認 Paper 基本欄位。"""

    assert result["document_id"] == (
        TEST_DOCUMENT_ID
    )

    assert result["title"] == (
        TEST_PAPER["title"]
    )

    assert result["url"] == (
        TEST_PAPER["url"]
    )

    assert result["pdf_url"] == (
        TEST_PAPER["pdf_url"]
    )

    assert result["resolved_url"]

    assert result["html"]

    assert isinstance(
        result["html"],
        str,
    )

    assert result["content_hash"]

    assert isinstance(
        result["content_hash"],
        str,
    )

    print(
        "\n[PASS] Paper fields"
    )

    print(
        f"  document_id  : {result['document_id']}"
    )

    print(
        f"  title        : {result['title']}"
    )

    print(
        f"  url          : {result['url']}"
    )

    print(
        f"  resolved_url : {result['resolved_url']}"
    )

    print(
        f"  html size    : {len(result['html'])}"
    )

    print(
        f"  content_hash : {result['content_hash']}"
    )

    print(
        f"  pdf_url      : {result['pdf_url']}"
    )


def verify_resources_structure(
    result,
):
    """確認 CSS / Images 資料結構。"""

    resources = result["resources"]

    assert isinstance(
        resources,
        dict,
    )

    actual_keys = set(
        resources.keys()
    )

    assert (
        EXPECTED_RESOURCE_KEYS
        <= actual_keys
    )

    css = resources["css"]
    images = resources["images"]

    assert isinstance(
        css,
        list,
    )

    assert isinstance(
        images,
        list,
    )

    print(
        "\n[PASS] Resources structure"
    )

    print(
        f"  resources type : {type(resources).__name__}"
    )

    print(
        f"  resource keys  : {sorted(actual_keys)}"
    )

    print(
        f"  CSS count      : {len(css)}"
    )

    print(
        f"  Image count    : {len(images)}"
    )

    if css:
        print(
            "\n  CSS item structure:"
        )

        print(
            f"    type : {type(css[0]).__name__}"
        )

        if isinstance(
            css[0],
            dict,
        ):
            print(
                f"    keys : {sorted(css[0].keys())}"
            )

    if images:
        print(
            "\n  Image item structure:"
        )

        print(
            f"    type : {type(images[0]).__name__}"
        )

        if isinstance(
            images[0],
            dict,
        ):
            print(
                f"    keys : {sorted(images[0].keys())}"
            )


def verify_pdf_structure(
    result,
):
    """確認 PDF Crawl Result 結構。"""

    pdf = result["pdf"]

    assert pdf is not None

    assert isinstance(
        pdf,
        dict,
    )

    actual_keys = set(
        pdf.keys()
    )

    assert (
        actual_keys
        == EXPECTED_PDF_KEYS
    )

    assert pdf["url"] == (
        TEST_PAPER["pdf_url"]
    )

    assert pdf["final_url"]

    assert isinstance(
        pdf["content"],
        bytes,
    )

    assert pdf["content"].startswith(
        b"%PDF-"
    )

    assert pdf["content_hash"]

    assert isinstance(
        pdf["content_hash"],
        str,
    )

    assert pdf["mime_type"] == (
        "application/pdf"
    )

    assert pdf["file_size"] == (
        len(pdf["content"])
    )

    print(
        "\n[PASS] PDF result structure"
    )

    print(
        f"  Keys          : {sorted(actual_keys)}"
    )

    print(
        f"  url           : {pdf['url']}"
    )

    print(
        f"  final_url     : {pdf['final_url']}"
    )

    print(
        f"  content type  : {type(pdf['content']).__name__}"
    )

    print(
        f"  content size  : {len(pdf['content'])}"
    )

    print(
        f"  content_hash  : {pdf['content_hash']}"
    )

    print(
        f"  mime_type     : {pdf['mime_type']}"
    )

    print(
        f"  file_size     : {pdf['file_size']}"
    )


def verify_mongodb_cleanup(
    database,
):
    """確認測試資料已清除。"""

    raw_html_count = database[
        "raw_html"
    ].count_documents(
        {
            "document_id":
                TEST_DOCUMENT_ID,
        }
    )

    gridfs_count = database[
        "fs.files"
    ].count_documents(
        {
            "metadata.document_id":
                TEST_DOCUMENT_ID,
        }
    )

    assert raw_html_count == 0
    assert gridfs_count == 0

    print(
        "[PASS] MongoDB cleanup verified"
    )

    print(
        f"  raw_html : {raw_html_count}"
    )

    print(
        f"  fs.files : {gridfs_count}"
    )


def main():
    """執行 PaperCrawler Result Structure Real Test。"""

    print(
        "=" * 60
    )

    print(
        "PaperCrawler Result Structure Real Test"
    )

    print(
        "=" * 60
    )

    database = get_mongo_database()

    try:
        print(
            "\n[1] Cleaning old test data..."
        )

        cleanup_test_data()

        print(
            "[PASS] Old test data cleaned"
        )

        print(
            "\n[2] Running PaperCrawler..."
        )

        crawler = PaperCrawler()

        result = crawler.crawl(
            TEST_PAPER
        )

        assert result is not None

        print(
            "[PASS] PaperCrawler completed"
        )

        print(
            "\n[3] Verifying top-level structure..."
        )

        verify_top_level_structure(
            result
        )

        print(
            "\n[4] Verifying Paper fields..."
        )

        verify_paper_fields(
            result
        )

        print(
            "\n[5] Verifying resources..."
        )

        verify_resources_structure(
            result
        )

        print(
            "\n[6] Verifying PDF result..."
        )

        verify_pdf_structure(
            result
        )

        print(
            "\n[7] Cleaning test data..."
        )

        cleanup_test_data()

        verify_mongodb_cleanup(
            database
        )

        print(
            "\n"
            + "=" * 60
        )

        print(
            "PaperCrawler Result Structure Real Test: PASS"
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
            "PaperCrawler Result Structure Real Test: FAIL"
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