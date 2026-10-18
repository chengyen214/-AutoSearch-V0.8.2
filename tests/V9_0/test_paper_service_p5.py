"""
tests/V9_0/test_paper_service_p5.py

AutoSearch V5

PaperService P5 Real Test

測試：

1. OpenAlex Real Search
2. 只處理 1 篇 Paper
3. PaperService Real Pipeline
4. Article Mapping
5. MySQL articles Persistence
6. status = Success
7. ispaper = 1
8. authors
9. MongoDB / MySQL Cleanup
"""

import json

from gridfs import GridFS

from database.connection import (
    get_connection,
)

from database.mongo_connection import (
    get_mongo_database,
)

from paper.openalex_provider import (
    OpenAlexProvider,
)

from services.paper_service import (
    PaperService,
)


def cleanup_mongodb(
    database,
    document_id,
):
    """清除本次 Real Test 建立的 MongoDB 資料。"""

    database["raw_html"].delete_many(
        {
            "document_id": document_id,
        }
    )

    fs = GridFS(
        database
    )

    files = database["fs.files"].find(
        {
            "metadata.document_id":
                document_id,
        }
    )

    for file_document in files:
        fs.delete(
            file_document["_id"]
        )


def cleanup_mysql(
    connection,
    document_id,
):
    """清除本次 Real Test 建立的 MySQL Article。"""

    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            DELETE FROM articles
            WHERE document_id = %s
            """,
            (
                document_id,
            ),
        )

        connection.commit()

    finally:
        cursor.close()


def verify_mysql_article(
    connection,
    article,
    article_id,
):
    """確認 PaperService 已將 Article 寫入 articles。"""

    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT
                id,
                document_id,
                keyword,
                title,
                url,
                source,
                published,
                content,
                crawl_time,
                status,
                ispaper,
                authors
            FROM articles
            WHERE id = %s
            """,
            (
                article_id,
            ),
        )

        row = cursor.fetchone()

        assert row is not None

        assert row[0] == article_id
        assert row[1] == article["document_id"]
        assert row[2] == article["keyword"]
        assert row[3] == article["title"]
        assert row[4] == article["url"]
        assert row[5] == article["source"]
        assert row[6] == article["published"]
        assert row[7] == article["content"]
        assert row[8] == article["crawl_time"]
        assert row[9] == "Success"
        assert row[10] == 1
        assert row[11] == article["authors"]

        authors = json.loads(
            row[11]
        )

        assert isinstance(
            authors,
            list,
        )

        assert authors

        print(
            "\n[PASS] MySQL Article verification"
        )

        print(
            f"  id          : {row[0]}"
        )

        print(
            f"  document_id : {row[1]}"
        )

        print(
            f"  keyword     : {row[2]}"
        )

        print(
            f"  title       : {row[3]}"
        )

        print(
            f"  url         : {row[4]}"
        )

        print(
            f"  source      : {row[5]}"
        )

        print(
            f"  published   : {row[6]}"
        )

        print(
            f"  content size: {len(row[7] or '')}"
        )

        print(
            f"  crawl_time  : {row[8]}"
        )

        print(
            f"  status      : {row[9]}"
        )

        print(
            f"  ispaper     : {row[10]}"
        )

        print(
            f"  authors     : {row[11]}"
        )

    finally:
        cursor.close()


def verify_mysql_count(
    connection,
    document_id,
):
    """確認該 Paper 只有一筆 Article。"""

    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM articles
            WHERE document_id = %s
            """,
            (
                document_id,
            ),
        )

        count = cursor.fetchone()[0]

        assert count == 1

        print(
            "\n[PASS] MySQL Article count verification"
        )

        print(
            f"  document_id count: {count}"
        )

    finally:
        cursor.close()


def verify_mongodb_storage(
    database,
    document_id,
    url,
):
    """確認 PaperService 執行後 MongoDB 已建立資料。"""

    raw_html = database[
        "raw_html"
    ].find_one(
        {
            "document_id": document_id,
            "url": url,
        }
    )

    assert raw_html is not None

    assert raw_html.get(
        "html"
    )

    assert raw_html.get(
        "content_hash"
    )

    resources = raw_html.get(
        "resources",
        {},
    )

    assert isinstance(
        resources.get(
            "css",
            [],
        ),
        list,
    )

    assert isinstance(
        resources.get(
            "images",
            [],
        ),
        list,
    )

    fs_file = database[
        "fs.files"
    ].find_one(
        {
            "metadata.document_id":
                document_id,
            "metadata.url":
                url,
        }
    )

    assert fs_file is not None

    metadata = fs_file.get(
        "metadata",
        {},
    )

    assert metadata.get(
        "document_id"
    ) == document_id

    assert metadata.get(
        "url"
    ) == url

    chunks = database[
        "fs.chunks"
    ].count_documents(
        {
            "files_id":
                fs_file["_id"],
        }
    )

    assert chunks > 0

    print(
        "\n[PASS] MongoDB storage verification"
    )

    print(
        f"  HTML size     : "
        f"{len(raw_html['html'])}"
    )

    print(
        f"  CSS count     : "
        f"{len(resources.get('css', []))}"
    )

    print(
        f"  Image count   : "
        f"{len(resources.get('images', []))}"
    )

    print(
        f"  GridFS chunks : {chunks}"
    )


def verify_cleanup(
    database,
    connection,
    document_id,
):
    """確認 MongoDB 與 MySQL 測試資料已清除。"""

    raw_html_count = database[
        "raw_html"
    ].count_documents(
        {
            "document_id": document_id,
        }
    )

    gridfs_count = database[
        "fs.files"
    ].count_documents(
        {
            "metadata.document_id":
                document_id,
        }
    )

    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM articles
            WHERE document_id = %s
            """,
            (
                document_id,
            ),
        )

        article_count = cursor.fetchone()[0]

    finally:
        cursor.close()

    assert raw_html_count == 0
    assert gridfs_count == 0
    assert article_count == 0

    print(
        "\n[PASS] Cleanup verification"
    )

    print(
        f"  raw_html : {raw_html_count}"
    )

    print(
        f"  fs.files : {gridfs_count}"
    )

    print(
        f"  articles : {article_count}"
    )


def main():
    """執行 PaperService → P5 → articles Real Test。"""

    print(
        "=" * 60
    )

    print(
        "PaperService P5 Real Test"
    )

    print(
        "=" * 60
    )

    connection = get_connection()

    if connection is None:
        raise Exception(
            "MySQL connection failed."
        )

    database = get_mongo_database()

    document_id = None

    try:
        print(
            "\n[1] Creating OpenAlexProvider..."
        )

        provider = OpenAlexProvider(
            result_count=1
        )

        print(
            "[PASS] OpenAlexProvider created"
        )

        print(
            "\n[2] Running OpenAlex Real Search..."
        )

        papers = provider.search(
            keyword="IC semiconductor"
        )

        assert len(papers) == 1

        paper = papers[0]

        document_id = paper.get(
            "document_id"
        )

        assert document_id

        assert paper.get(
            "url"
        )

        print(
            "[PASS] OpenAlex returned 1 Paper"
        )

        print(
            f"  document_id : {paper['document_id']}"
        )

        print(
            f"  title       : {paper.get('title')}"
        )

        print(
            f"  url         : {paper['url']}"
        )

        print(
            f"  pdf_url     : {paper.get('pdf_url')}"
        )

        print(
            "\n[3] Cleaning old test data..."
        )

        cleanup_mongodb(
            database,
            document_id,
        )

        cleanup_mysql(
            connection,
            document_id,
        )

        print(
            "[PASS] Old test data cleaned"
        )

        print(
            "\n[4] Creating PaperService..."
        )

        service = PaperService(
            provider=provider
        )

        print(
            "[PASS] PaperService created"
        )

        print(
            "\n[5] Running PaperService..."
        )

        results = service.run(
            keyword="IC semiconductor"
        )

        assert len(results) == 1

        result = results[0]

        article = result.get(
            "article"
        )

        article_id = result.get(
            "article_id"
        )

        assert article is not None
        assert article_id is not None

        assert (
            article["document_id"]
            == document_id
        )

        assert (
            article["keyword"]
            == "IC semiconductor"
        )

        assert (
            article["status"]
            == "Success"
        )

        assert (
            article["ispaper"]
            == 1
        )

        assert article["url"]

        assert article["title"]

        assert article["content"]

        print(
            "[PASS] PaperService completed"
        )

        print(
            f"  article_id  : {article_id}"
        )

        print(
            f"  document_id : {article['document_id']}"
        )

        print(
            f"  title       : {article['title']}"
        )

        print(
            f"  url         : {article['url']}"
        )

        print(
            f"  status      : {article['status']}"
        )

        print(
            f"  ispaper     : {article['ispaper']}"
        )

        print(
            f"  authors     : {article['authors']}"
        )

        print(
            "\n[6] Verifying MySQL articles..."
        )

        verify_mysql_article(
            connection,
            article,
            article_id,
        )

        verify_mysql_count(
            connection,
            document_id,
        )

        print(
            "\n[7] Verifying MongoDB..."
        )

        verify_mongodb_storage(
            database,
            document_id,
            article["url"],
        )

        print(
            "\n[8] Cleaning test data..."
        )

        cleanup_mongodb(
            database,
            document_id,
        )

        cleanup_mysql(
            connection,
            document_id,
        )

        verify_cleanup(
            database,
            connection,
            document_id,
        )

        print(
            "\n"
            + "=" * 60
        )

        print(
            "PaperService P5 Real Test: PASS"
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
            "PaperService P5 Real Test: FAIL"
        )

        print(
            "=" * 60
        )

        print(
            f"\nError: {e}"
        )

        if document_id:
            cleanup_mongodb(
                database,
                document_id,
            )

            cleanup_mysql(
                connection,
                document_id,
            )

        raise

    finally:
        connection.close()


if __name__ == "__main__":
    main()