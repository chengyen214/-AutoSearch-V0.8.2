"""
tests/V9_0/test_paper_article_repository.py

AutoSearch V5

Paper Article Repository Real Test

測試：

1. MySQL Connection
2. Paper Article INSERT
3. Duplicate Detection
4. Duplicate Article ID Verification
5. Article Row Count Verification
6. Article Field Verification
7. Cleanup
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
    "test-v9-paper-article-repository"
)


def cleanup_test_data(
    connection,
):
    """清除本次 Real Test 建立的 MySQL 測試資料。"""

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


def verify_saved_article(
    connection,
    article_id,
):
    """確認 Article 已寫入 articles。"""

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
        assert row[1] == TEST_DOCUMENT_ID
        assert row[2] == "IC semiconductor"
        assert row[3] == "Paper Article Repository Real Test"
        assert row[4] == (
            "https://example.com/paper/test"
        )
        assert row[5] == "Test Journal"
        assert row[6] == datetime(
            2026,
            10,
            7,
        )
        assert row[7] == (
            "This is representative paper abstract content."
        )
        assert row[8] is not None
        assert row[9] is None
        assert row[10] == 1

        authors = json.loads(
            row[11]
        )

        assert authors == [
            "Author One",
            "Author Two",
        ]

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
            f"  ispaper     : {row[10]}"
        )

        print(
            f"  authors     : {row[11]}"
        )

    finally:
        cursor.close()


def verify_row_count(
    connection,
):
    """確認相同 document_id 只有一筆 Article。"""

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
            "\n[PASS] Duplicate row count verified"
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
            "\n[PASS] MySQL cleanup verified"
        )

        print(
            f"  articles count: {count}"
        )

    finally:
        cursor.close()


def main():
    """執行 Paper Article Repository Duplicate Real Test。"""

    print(
        "=" * 60
    )

    print(
        "Paper Article Repository Duplicate Real Test"
    )

    print(
        "=" * 60
    )

    connection = get_connection()

    if connection is None:
        raise Exception(
            "Database connection failed."
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

        article = {
            "document_id": TEST_DOCUMENT_ID,
            "keyword": "IC semiconductor",
            "title": (
                "Paper Article Repository Real Test"
            ),
            "url": (
                "https://example.com/paper/test"
            ),
            "source": "Test Journal",
            "published": datetime(
                2026,
                10,
                7,
            ),
            "content": (
                "This is representative "
                "paper abstract content."
            ),
            "crawl_time": datetime.now(),
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
            "\n[3] Saving first Article..."
        )

        first_article_id = (
            repository.save_article(
                article
            )
        )

        assert first_article_id is not None

        print(
            "[PASS] First Article INSERT completed"
        )

        print(
            f"  article_id: {first_article_id}"
        )

        print(
            "\n[4] Saving duplicate Article..."
        )

        second_article_id = (
            repository.save_article(
                article
            )
        )

        assert second_article_id == (
            first_article_id
        )

        print(
            "[PASS] Duplicate detection completed"
        )

        print(
            f"  existing article_id: "
            f"{second_article_id}"
        )

        print(
            "\n[5] Verifying duplicate row count..."
        )

        verify_row_count(
            connection
        )

        print(
            "\n[6] Verifying Article fields..."
        )

        verify_saved_article(
            connection,
            first_article_id,
        )

        print(
            "\n[7] Cleaning test data..."
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
            "Paper Article Repository Duplicate Real Test: PASS"
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
            "Paper Article Repository Duplicate Real Test: FAIL"
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