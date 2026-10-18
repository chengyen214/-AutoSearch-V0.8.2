"""
database/paper_article_repository.py

AutoSearch V5

Paper Article Repository

用途：

    負責將 Paper Article 寫入既有 articles Table。

目前功能：

    - Article Persistence
    - Duplicate Detection
    - MySQL INSERT
    - Transaction Commit / Rollback
"""

from database.connection import (
    get_connection,
)

from utils.logger import (
    logger,
)


class PaperArticleRepository:
    """AutoSearch V5 Paper Article Repository。"""

    def __init__(self):
        """建立 Database Connection。"""

        self.connection = get_connection()

        if self.connection is None:
            raise Exception(
                "Database connection failed."
            )

    def save_article(
        self,
        article,
    ):
        """儲存 Paper Article，重複 document_id 時略過 INSERT。"""

        if not article:
            raise ValueError(
                "Article cannot be empty."
            )

        document_id = article.get(
            "document_id"
        )

        if not document_id:
            raise ValueError(
                "Article document_id cannot be empty."
            )

        url = article.get(
            "url"
        )

        if not url:
            raise ValueError(
                "Article URL cannot be empty."
            )

        if article.get(
            "ispaper"
        ) != 1:
            raise ValueError(
                "Paper Article ispaper must be 1."
            )

        existing_article_id = (
            self._get_existing_article_id(
                document_id
            )
        )

        if existing_article_id is not None:
            logger.info(
                "Duplicate Paper Article skipped: "
                f"id={existing_article_id}, "
                f"document_id={document_id}"
            )

            return existing_article_id

        cursor = self.connection.cursor()

        sql = """
            INSERT INTO articles (
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
            )
            VALUES (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )
        """

        values = (
            article.get("document_id"),
            article.get("keyword"),
            article.get("title"),
            article.get("url"),
            article.get("source"),
            article.get("published"),
            article.get("content"),
            article.get("crawl_time"),
            article.get("status"),
            article.get("ispaper"),
            article.get("authors"),
        )

        try:
            cursor.execute(
                sql,
                values,
            )

            self.connection.commit()

            article_id = cursor.lastrowid

            logger.info(
                "Paper Article saved: "
                f"id={article_id}, "
                f"document_id={document_id}, "
                f"url={url}"
            )

            return article_id

        except Exception as e:
            self.connection.rollback()

            logger.exception(
                f"Failed to save Paper Article: {e}"
            )

            raise

        finally:
            cursor.close()

    def _get_existing_article_id(
        self,
        document_id,
    ):
        """依 document_id 查詢既有 Article ID。"""

        cursor = self.connection.cursor()

        try:
            cursor.execute(
                """
                SELECT id
                FROM articles
                WHERE document_id = %s
                LIMIT 1
                """,
                (
                    document_id,
                ),
            )

            row = cursor.fetchone()

            if row is None:
                return None

            return row[0]

        finally:
            cursor.close()


__all__ = [
    "PaperArticleRepository",
]