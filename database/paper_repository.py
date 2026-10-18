"""
database/paper_repository.py

AutoSearch V5

Paper Repository

用途：

    負責 Paper 的 Database Persistence。

目前功能：

    - 取得已儲存 Paper URL
    - Database Connection Lifecycle
"""

from database.connection import (
    get_connection
)

from utils.logger import (
    logger
)


class PaperRepository:
    """AutoSearch V5 Paper Repository。"""

    def __init__(
        self
    ):
        """建立 Database Connection。"""

        self.connection = get_connection()

        if self.connection is None:
            raise Exception(
                "Database connection failed."
            )

    def get_existing_urls(
        self
    ):
        """取得已儲存 Paper 的 URL。"""

        cursor = self.connection.cursor()

        sql = """
            SELECT url
            FROM articles
            WHERE url IS NOT NULL
              AND url != ''
        """

        try:
            cursor.execute(
                sql
            )

            rows = cursor.fetchall()

            urls = [
                row[0]
                for row in rows
                if row[0]
            ]

            logger.info(
                "Existing Paper URLs loaded: "
                f"count={len(urls)}"
            )

            return urls

        except Exception as e:
            logger.exception(
                f"Failed to load existing Paper URLs: {e}"
            )

            return []

        finally:
            cursor.close()


__all__ = [
    "PaperRepository",
]