"""
tests/V9_0/test_paper_mongo_repository.py

AutoSearch V5

Paper MongoDB Repository Real Test

測試：

1. Paper Landing Page HTML → MongoDB raw_html
2. CSS / Images → raw_html.resources
3. Paper PDF → MongoDB GridFS
4. GridFS PDF Binary Read Back
5. GridFS Metadata
6. GridFS Chunk URL
7. Test Data Cleanup
"""

import hashlib

from gridfs import GridFS

from database.mongo_connection import (
    get_mongo_database,
)
from database.paper_mongo_repository import (
    PaperMongoRepository,
)


TEST_DOCUMENT_ID = "test-v9-paper-mongo-document"
TEST_URL = "https://example.com/paper/test"
TEST_RESOLVED_URL = "https://example.com/paper/test-resolved"
TEST_PDF_URL = "https://example.com/paper/test.pdf"

TEST_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Paper MongoDB Repository Test</title>
</head>
<body>
    <h1>Paper MongoDB Repository Test</h1>
</body>
</html>
""".strip()

TEST_PDF = (
    b"%PDF-1.4\n"
    b"% Paper MongoDB Repository Real Test\n"
    b"1 0 obj\n"
    b"<< /Type /Catalog >>\n"
    b"endobj\n"
    b"%%EOF\n"
)

TEST_HTML_HASH = hashlib.sha256(
    TEST_HTML.encode(
        "utf-8"
    )
).hexdigest()

TEST_PDF_HASH = hashlib.sha256(
    TEST_PDF
).hexdigest()


def cleanup_test_data():
    """清除本次 Real Test 建立的 MongoDB 測試資料。"""

    database = get_mongo_database()

    raw_html = database["raw_html"]

    raw_html.delete_many(
        {
            "document_id": TEST_DOCUMENT_ID,
        }
    )

    fs = GridFS(
        database
    )

    for grid_file in database["fs.files"].find(
        {
            "metadata.document_id": TEST_DOCUMENT_ID,
        }
    ):
        fs.delete(
            grid_file["_id"]
        )


def test_save_raw_html(repository):
    """測試 Paper Landing Page HTML 儲存。"""

    resources = {
        "css": [
            {
                "url": "https://example.com/paper/style.css",
                "content": "body { font-family: sans-serif; }",
                "content_hash": "test-css-hash",
            }
        ],
        "images": [
            {
                "url": "https://example.com/paper/image.png",
                "content": b"test-image-content",
                "content_hash": "test-image-hash",
            }
        ],
    }

    crawl_result = {
        "document_id": TEST_DOCUMENT_ID,
        "url": TEST_URL,
        "resolved_url": TEST_RESOLVED_URL,
        "html": TEST_HTML,
        "content_hash": TEST_HTML_HASH,
        "resources": resources,
    }

    inserted_id = repository.save_raw_html(
        crawl_result
    )

    assert inserted_id is not None

    document = repository.collection.find_one(
        {
            "_id": inserted_id,
        }
    )

    assert document is not None
    assert document["article_id"] is None
    assert document["document_id"] == TEST_DOCUMENT_ID
    assert document["url"] == TEST_URL
    assert document["resolved_url"] == TEST_RESOLVED_URL
    assert document["html"] == TEST_HTML
    assert document["content_hash"] == TEST_HTML_HASH

    assert "resources" in document
    assert "css" in document["resources"]
    assert "images" in document["resources"]

    assert len(
        document["resources"]["css"]
    ) == 1

    assert len(
        document["resources"]["images"]
    ) == 1

    assert (
        document["resources"]["css"][0]["url"]
        == "https://example.com/paper/style.css"
    )

    assert (
        document["resources"]["images"][0]["url"]
        == "https://example.com/paper/image.png"
    )

    assert document.get(
        "created_at"
    ) is not None

    assert document.get(
        "updated_at"
    ) is not None

    print(
        "\n[PASS] raw_html saved"
    )

    print(
        f"  _id           : {inserted_id}"
    )

    print(
        f"  document_id   : {document['document_id']}"
    )

    print(
        f"  url           : {document['url']}"
    )

    print(
        f"  resolved_url  : {document['resolved_url']}"
    )

    print(
        f"  html size     : {len(document['html'])}"
    )

    print(
        f"  content_hash  : {document['content_hash']}"
    )

    print(
        f"  CSS count     : "
        f"{len(document['resources']['css'])}"
    )

    print(
        f"  Image count   : "
        f"{len(document['resources']['images'])}"
    )


def test_save_pdf(repository):
    """測試 Paper PDF GridFS 儲存。"""

    pdf_result = {
        "url": TEST_PDF_URL,
        "final_url": TEST_PDF_URL,
        "content": TEST_PDF,
        "content_hash": TEST_PDF_HASH,
        "mime_type": "application/pdf",
        "file_size": len(TEST_PDF),
        "filename": "test-paper.pdf",
    }

    file_id = repository.save_pdf(
        document_id=TEST_DOCUMENT_ID,
        url=TEST_URL,
        pdf_result=pdf_result,
    )

    assert file_id is not None

    database = get_mongo_database()

    fs = GridFS(
        database
    )

    grid_file = fs.get(
        file_id
    )

    assert grid_file is not None

    stored_pdf = grid_file.read()

    assert (
        stored_pdf
        == TEST_PDF
    )

    assert (
        grid_file.filename
        == "test-paper.pdf"
    )

    assert (
        grid_file.content_type
        == "application/pdf"
    )

    metadata = grid_file.metadata

    assert metadata is not None

    assert (
        metadata["document_id"]
        == TEST_DOCUMENT_ID
    )

    assert (
        metadata["url"]
        == TEST_URL
    )

    assert (
        metadata["pdf_url"]
        == TEST_PDF_URL
    )

    assert (
        metadata["final_url"]
        == TEST_PDF_URL
    )

    assert (
        metadata["content_hash"]
        == TEST_PDF_HASH
    )

    assert (
        metadata["mime_type"]
        == "application/pdf"
    )

    assert (
        metadata["file_size"]
        == len(TEST_PDF)
    )

    chunks = list(
        database["fs.chunks"].find(
            {
                "files_id": file_id,
            }
        )
    )

    assert len(chunks) >= 1

    for chunk in chunks:
        assert chunk["files_id"] == file_id
        assert chunk["url"] == TEST_URL
        assert "n" in chunk
        assert "data" in chunk

    print(
        "\n[PASS] PDF saved to GridFS"
    )

    print(
        f"  file_id       : {file_id}"
    )

    print(
        f"  filename      : {grid_file.filename}"
    )

    print(
        f"  content_type  : {grid_file.content_type}"
    )

    print(
        f"  PDF size      : {len(stored_pdf)}"
    )

    print(
        f"  document_id   : {metadata['document_id']}"
    )

    print(
        f"  url           : {metadata['url']}"
    )

    print(
        f"  pdf_url       : {metadata['pdf_url']}"
    )

    print(
        f"  content_hash  : {metadata['content_hash']}"
    )

    print(
        f"  chunk count   : {len(chunks)}"
    )

    print(
        f"  chunk url     : {chunks[0]['url']}"
    )


def test_gridfs_structure():
    """確認 GridFS fs.files 與 fs.chunks 實際存在。"""

    database = get_mongo_database()

    files = list(
        database["fs.files"].find(
            {
                "metadata.document_id":
                    TEST_DOCUMENT_ID,
            }
        )
    )

    assert len(files) >= 1

    file_ids = [
        document["_id"]
        for document in files
    ]

    chunks = list(
        database["fs.chunks"].find(
            {
                "files_id": {
                    "$in": file_ids,
                }
            }
        )
    )

    assert len(chunks) >= 1

    for chunk in chunks:
        assert chunk["files_id"] in file_ids
        assert chunk["url"] == TEST_URL
        assert "n" in chunk
        assert "data" in chunk

    print(
        "\n[PASS] GridFS structure"
    )

    print(
        f"  fs.files count  : {len(files)}"
    )

    print(
        f"  fs.chunks count : {len(chunks)}"
    )

    print(
        f"  chunk url       : {chunks[0]['url']}"
    )


def main():
    """執行 Paper MongoDB Repository Real Test。"""

    print(
        "=" * 60
    )

    print(
        "Paper MongoDB Repository Real Test"
    )

    print(
        "=" * 60
    )

    repository = None

    try:
        print(
            "\n[1] Connecting MongoDB..."
        )

        database = get_mongo_database()

        print(
            f"Database   : {database.name}"
        )

        print(
            "\n[2] Cleaning old test data..."
        )

        cleanup_test_data()

        print(
            "[PASS] Old test data cleaned"
        )

        print(
            "\n[3] Creating Repository..."
        )

        repository = PaperMongoRepository()

        print(
            "[PASS] PaperMongoRepository created"
        )

        print(
            "\n[4] Testing raw_html..."
        )

        test_save_raw_html(
            repository
        )

        print(
            "\n[5] Testing PDF → GridFS..."
        )

        test_save_pdf(
            repository
        )

        print(
            "\n[6] Testing GridFS structure..."
        )

        test_gridfs_structure()

        print(
            "\n[7] Cleaning test data..."
        )

        cleanup_test_data()

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
                "url": TEST_URL,
            }
        )

        assert remaining_raw_html == 0
        assert remaining_gridfs == 0
        assert remaining_chunks == 0

        print(
            "[PASS] Test data cleaned"
        )

        print(
            "[PASS] Cleanup verified"
        )

        print(
            "\n"
            + "=" * 60
        )

        print(
            "Paper MongoDB Repository Real Test: PASS"
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
            "Paper MongoDB Repository Real Test: FAIL"
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