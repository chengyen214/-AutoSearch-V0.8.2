"""
tests/V9_0/test_paper_end_to_end.py

AutoSearch V5

Paper End-to-End Real Test

測試：

1. OpenAlex Real Search
2. 取得 1 篇 Paper
3. PaperService End-to-End
4. PaperCrawler
5. MongoDB raw_html
6. MongoDB GridFS
7. PaperParser
8. Article Mapping
9. MySQL articles
10. MongoDB / MySQL Relationship
11. Test Data Cleanup
"""

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


class FixedPaperProvider:
    """固定使用 OpenAlex 第一次取得的 Paper。"""

    def __init__(
        self,
        paper,
    ):
        self.paper = paper

    def search(
        self,
        **kwargs,
    ):
        """回傳固定的單一 Paper。"""

        return [
            self.paper.copy()
        ]


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


def verify_paper_service_result(
    result,
    paper,
):
    """確認 PaperService End-to-End Result。"""

    assert result is not None

    crawl_result = result.get(
        "crawl_result"
    )

    parsed_result = result.get(
        "parsed_result"
    )

    article = result.get(
        "article"
    )

    article_id = result.get(
        "article_id"
    )

    assert crawl_result is not None
    assert parsed_result is not None
    assert article is not None
    assert article_id is not None

    assert (
        article["document_id"]
        == paper["document_id"]
    )

    assert (
        article["keyword"]
        == paper["keyword"]
    )

    assert article["url"] == (
        paper["url"]
    )

    assert article["title"]

    assert article["content"]

    assert article["status"] == (
        "Success"
    )

    assert article["ispaper"] == 1

    assert article["authors"]

    assert crawl_result.get(
        "html"
    )

    assert crawl_result.get(
        "content_hash"
    )

    assert crawl_result.get(
        "resources"
    )

    assert crawl_result.get(
        "pdf"
    )

    assert parsed_result.get(
        "title"
    )

    assert parsed_result.get(
        "authors"
    )

    assert parsed_result.get(
        "abstract"
    )

    print(
        "\n[PASS] PaperService result verification"
    )

    print(
        f"  article_id  : {article_id}"
    )

    print(
        f"  document_id : {article['document_id']}"
    )

    print(
        f"  keyword     : {article['keyword']}"
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


def verify_mongodb(
    database,
    paper,
):
    """確認 Paper Landing Page 與 PDF 已存入 MongoDB。"""

    document_id = paper[
        "document_id"
    ]

    url = paper[
        "url"
    ]

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
        "document_id"
    ) == document_id

    assert raw_html.get(
        "url"
    ) == url

    assert raw_html.get(
        "resolved_url"
    )

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

    css = resources.get(
        "css",
        [],
    )

    images = resources.get(
        "images",
        [],
    )

    assert isinstance(
        css,
        list,
    )

    assert isinstance(
        images,
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

    assert metadata.get(
        "pdf_url"
    )

    assert metadata.get(
        "content_hash"
    )

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
        "\n[PASS] MongoDB verification"
    )

    print(
        f"  raw_html    : 1"
    )

    print(
        f"  HTML size   : "
        f"{len(raw_html['html'])}"
    )

    print(
        f"  CSS count   : {len(css)}"
    )

    print(
        f"  Image count : {len(images)}"
    )

    print(
        f"  fs.files    : 1"
    )

    print(
        f"  GridFS chunks: {chunks}"
    )


def verify_mysql(
    connection,
    article,
    article_id,
):
    """確認 Paper Article 已存入 MySQL articles。"""

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

        print(
            "\n[PASS] MySQL verification"
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
    """確認同一 document_id 只有一筆 Article。"""

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
            "\n[PASS] MySQL document_id count"
        )

        print(
            f"  count: {count}"
        )

    finally:
        cursor.close()


def verify_relationship(
    database,
    connection,
    paper,
    article,
):
    """確認 MongoDB 與 MySQL 使用相同 Paper identity。"""

    document_id = paper[
        "document_id"
    ]

    url = paper[
        "url"
    ]

    assert article[
        "document_id"
    ] == document_id

    assert article[
        "url"
    ] == url

    raw_html = database[
        "raw_html"
    ].find_one(
        {
            "document_id": document_id,
            "url": url,
        }
    )

    assert raw_html is not None

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

    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT
                document_id,
                url
            FROM articles
            WHERE document_id = %s
            """,
            (
                document_id,
            ),
        )

        row = cursor.fetchone()

        assert row is not None

        assert row[0] == document_id
        assert row[1] == url

    finally:
        cursor.close()

    print(
        "\n[PASS] Paper identity relationship verification"
    )

    print(
        f"  document_id : {document_id}"
    )

    print(
        f"  url         : {url}"
    )


def verify_cleanup(
    database,
    connection,
    document_id,
):
    """確認所有 End-to-End 測試資料已清除。"""

    raw_html_count = database[
        "raw_html"
    ].count_documents(
        {
            "document_id":
                document_id,
        }
    )

    fs_file_count = database[
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
    assert fs_file_count == 0
    assert article_count == 0

    print(
        "\n[PASS] Cleanup verification"
    )

    print(
        f"  raw_html : {raw_html_count}"
    )

    print(
        f"  fs.files : {fs_file_count}"
    )

    print(
        f"  articles : {article_count}"
    )


def main():
    """執行 Paper End-to-End Real Test。"""

    print(
        "=" * 60
    )

    print(
        "Paper End-to-End Real Test"
    )

    print(
        "=" * 60
    )

    mysql_connection = get_connection()

    if mysql_connection is None:
        raise Exception(
            "MySQL connection failed."
        )

    mongo_database = get_mongo_database()

    document_id = None

    try:
        print(
            "\n[1] Running OpenAlex Real Search..."
        )

        openalex_provider = OpenAlexProvider(
            result_count=1
        )

        papers = openalex_provider.search(
            keyword="IC semiconductor"
        )

        assert len(papers) == 1

        paper = papers[0]

        document_id = paper.get(
            "document_id"
        )

        assert document_id

        assert paper.get(
            "keyword"
        )

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
            f"  keyword     : {paper['keyword']}"
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
            "\n[2] Cleaning old test data..."
        )

        cleanup_mongodb(
            mongo_database,
            document_id,
        )

        cleanup_mysql(
            mysql_connection,
            document_id,
        )

        print(
            "[PASS] Old test data cleaned"
        )

        print(
            "\n[3] Creating PaperService..."
        )

        fixed_provider = FixedPaperProvider(
            paper
        )

        service = PaperService(
            provider=fixed_provider
        )

        print(
            "[PASS] PaperService created"
        )

        print(
            "\n[4] Running complete Paper Pipeline..."
        )

        results = service.run()

        assert len(results) == 1

        result = results[0]

        print(
            "[PASS] PaperService completed"
        )

        print(
            "\n[5] Verifying PaperService result..."
        )

        verify_paper_service_result(
            result,
            paper,
        )

        article = result[
            "article"
        ]

        article_id = result[
            "article_id"
        ]

        print(
            "\n[6] Verifying MongoDB..."
        )

        verify_mongodb(
            mongo_database,
            paper,
        )

        print(
            "\n[7] Verifying MySQL..."
        )

        verify_mysql(
            mysql_connection,
            article,
            article_id,
        )

        verify_mysql_count(
            mysql_connection,
            document_id,
        )

        print(
            "\n[8] Verifying MongoDB / MySQL relationship..."
        )

        verify_relationship(
            mongo_database,
            mysql_connection,
            paper,
            article,
        )

        print(
            "\n[9] Cleaning test data..."
        )

        cleanup_mongodb(
            mongo_database,
            document_id,
        )

        cleanup_mysql(
            mysql_connection,
            document_id,
        )

        verify_cleanup(
            mongo_database,
            mysql_connection,
            document_id,
        )

        print(
            "\n"
            + "=" * 60
        )

        print(
            "Paper End-to-End Real Test: PASS"
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
            "Paper End-to-End Real Test: FAIL"
        )

        print(
            "=" * 60
        )

        print(
            f"\nError: {e}"
        )

        if document_id:
            cleanup_mongodb(
                mongo_database,
                document_id,
            )

            cleanup_mysql(
                mysql_connection,
                document_id,
            )

        raise

    finally:
        mysql_connection.close()


if __name__ == "__main__":
    main()