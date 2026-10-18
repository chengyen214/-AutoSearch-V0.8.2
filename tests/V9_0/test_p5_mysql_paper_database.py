"""
tests/V9_0/test_p5_mysql_paper_database.py

AutoSearch V5

P5 MySQL Paper Database Real Test

測試：

1. MySQL Connection
2. Paper Article INSERT
3. Article 欄位驗證
4. document_id 驗證
5. URL Relationship 驗證
6. ispaper 驗證
7. authors 驗證
8. Duplicate document_id
9. Duplicate 不新增第二筆
10. Cleanup
"""

import json
from datetime import datetime

from database.connection import (
    get_connection,
)
from database.paper_article_repository import (
    PaperArticleRepository,
)


TEST_DOCUMENT_ID = (
    "test-v9-p5-mysql-paper-database"
)

TEST_URL = (
    "https://example.com/paper/test-p5"
)

TEST_PDF_URL = (
    "https://example.com/paper/test-p5.pdf"
)


def cleanup_test_data(
    connection,
):
    """清除本次 P5 Real Test 建立的 MySQL 資料。"""

    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            DELETE FROM articles
            WHERE document_id = %s
            """,
            (
                TEST_DOCUMENT_ID,
            ),
        )

        connection.commit()

    finally:
        cursor.close()


def verify_article(
    connection,
    article,
    article_id,
):
    """確認 Article 所有 P5 欄位。"""

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
        assert row[9] == article["status"]
        assert row[10] == article["ispaper"]
        assert row[11] == article["authors"]

        authors = json.loads(
            row[11]
        )

        assert authors == [
            "Author One",
            "Author Two",
        ]

        print(
            "\n[PASS] Article fields verified"
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
            f"  content size: {len(row[7])}"
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


def verify_document_id(
    connection,
    article_id,
):
    """確認 document_id 可以直接找到 Article。"""

    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT
                id,
                document_id
            FROM articles
            WHERE document_id = %s
            """,
            (
                TEST_DOCUMENT_ID,
            ),
        )

        rows = cursor.fetchall()

        assert len(rows) == 1
        assert rows[0][0] == article_id
        assert rows[0][1] == TEST_DOCUMENT_ID

        print(
            "\n[PASS] document_id verification"
        )

        print(
            f"  document_id : {rows[0][1]}"
        )

        print(
            f"  article_id  : {rows[0][0]}"
        )

    finally:
        cursor.close()


def verify_url(
    connection,
    article_id,
):
    """確認 Article URL 為 Paper Landing Page URL。"""

    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT
                id,
                url
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
        assert row[1] == TEST_URL

        print(
            "\n[PASS] URL relationship verification"
        )

        print(
            f"  article_id : {row[0]}"
        )

        print(
            f"  url        : {row[1]}"
        )

    finally:
        cursor.close()


def verify_duplicate_count(
    connection,
):
    """確認相同 document_id 只有一筆。"""

    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM articles
            WHERE document_id = %s
            """,
            (
                TEST_DOCUMENT_ID,
            ),
        )

        count = cursor.fetchone()[0]

        assert count == 1

        print(
            "\n[PASS] Duplicate row count verification"
        )

        print(
            f"  document_id count: {count}"
        )

    finally:
        cursor.close()


def verify_cleanup(
    connection,
):
    """確認測試資料已清除。"""

    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM articles
            WHERE document_id = %s
            """,
            (
                TEST_DOCUMENT_ID,
            ),
        )

        count = cursor.fetchone()[0]

        assert count == 0

        print(
            "\n[PASS] Cleanup verification"
        )

        print(
            f"  articles count: {count}"
        )

    finally:
        cursor.close()


def main():
    """執行 P5 MySQL Paper Database Real Test。"""

    print(
        "=" * 60
    )

    print(
        "P5 MySQL Paper Database Real Test"
    )

    print(
        "=" * 60
    )

    connection = get_connection()

    if connection is None:
        raise Exception(
            "MySQL connection failed."
        )

    try:
        print(
            "\n[1] Cleaning old test data..."
        )

        cleanup_test_data(
            connection
        )

        print(
            "[PASS] Old test data cleaned"
        )

        published = datetime(
            2026,
            10,
            7,
            0,
            0,
            0,
        )

        crawl_time = datetime.now().replace(
            microsecond=0
        )

        article = {
            "document_id": TEST_DOCUMENT_ID,
            "keyword": "IC semiconductor",
            "title": (
                "P5 MySQL Paper Database Real Test"
            ),
            "url": TEST_URL,
            "source": "Test Journal",
            "published": published,
            "content": (
                "This is representative "
                "paper abstract content."
            ),
            "crawl_time": crawl_time,
            "status": None,
            "ispaper": 1,
            "authors": json.dumps(
                [
                    "Author One",
                    "Author Two",
                ],
                ensure_ascii=False,
            ),
        }

        print(
            "\n[2] Creating PaperArticleRepository..."
        )

        repository = PaperArticleRepository()

        print(
            "[PASS] Repository created"
        )

        print(
            "\n[3] Saving Paper Article..."
        )

        article_id = (
            repository.save_article(
                article
            )
        )

        assert article_id is not None

        print(
            "[PASS] Article INSERT completed"
        )

        print(
            f"  article_id: {article_id}"
        )

        print(
            "\n[4] Verifying Article fields..."
        )

        verify_article(
            connection,
            article,
            article_id,
        )

        print(
            "\n[5] Verifying document_id..."
        )

        verify_document_id(
            connection,
            article_id,
        )

        print(
            "\n[6] Verifying URL..."
        )

        verify_url(
            connection,
            article_id,
        )

        print(
            "\n[7] Saving duplicate Article..."
        )

        duplicate_article_id = (
            repository.save_article(
                article
            )
        )

        assert duplicate_article_id == (
            article_id
        )

        print(
            "[PASS] Duplicate detection completed"
        )

        print(
            f"  first article_id : {article_id}"
        )

        print(
            f"  second article_id: "
            f"{duplicate_article_id}"
        )

        print(
            "\n[8] Verifying duplicate count..."
        )

        verify_duplicate_count(
            connection
        )

        print(
            "\n[9] Cleaning test data..."
        )

        cleanup_test_data(
            connection
        )

        verify_cleanup(
            connection
        )

        print(
            "\n"
            + "=" * 60
        )

        print(
            "P5 MySQL Paper Database Real Test: PASS"
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
            "P5 MySQL Paper Database Real Test: FAIL"
        )

        print(
            "=" * 60
        )

        print(
            f"\nError: {e}"
        )

        cleanup_test_data(
            connection
        )

        raise

    finally:
        connection.close()


if __name__ == "__main__":
    main()