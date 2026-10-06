"""
database/robots_cache_repository.py

AutoSearch V6

Robots Cache Repository

用途：

    Robots.txt Crawl Permission Cache

負責：

    - robots_cache 查詢
    - robots_cache 新增
    - 依 base_url 取得 Robots.txt
    - 依指定 URL 判斷 Crawl Permission

Table:

    robots_cache
"""

from datetime import datetime
from urllib.robotparser import RobotFileParser

from database.connection import get_connection
from crawler.robots_checker import (
    get_base_url,
    get_robots_url,
    get_robots_content,
)


class RobotsCacheRepository:
    """
    Robots Cache Repository

    負責操作：

        robots_cache

    主要用途：

        Robots.txt Crawl Permission Cache
    """

    def get_by_base_url(
        self,
        base_url
    ):
        """
        依 Base URL 取得 Robots Cache。
        """

        conn = get_connection()

        cursor = conn.cursor(
            dictionary=True
        )

        try:

            cursor.execute(
                """
                SELECT *
                FROM robots_cache
                WHERE base_url=%s
                LIMIT 1
                """,
                (
                    base_url,
                )
            )

            return cursor.fetchone()

        finally:

            cursor.close()
            conn.close()

    def insert(
        self,
        base_url,
        robots_url,
        robots_content,
        checked_at
    ):
        """
        新增 Robots Cache。
        """

        conn = get_connection()

        cursor = conn.cursor()

        try:

            cursor.execute(
                """
                INSERT INTO robots_cache
                (
                    base_url,
                    robots_url,
                    robots_content,
                    allowed,
                    checked_at
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    base_url,
                    robots_url,
                    robots_content,
                    True,
                    checked_at
                )
            )

            conn.commit()

            return cursor.lastrowid

        except Exception:

            conn.rollback()

            raise

        finally:

            cursor.close()
            conn.close()

    def check(
        self,
        url
    ):
        """
        取得指定 URL 的 Robots Crawl Permission。
        """

        base_url = get_base_url(
            url
        )

        cached = self.get_by_base_url(
            base_url
        )

        if cached is not None:

            parser = RobotFileParser()

            parser.set_url(
                cached["robots_url"]
            )

            parser.parse(
                cached["robots_content"].splitlines()
            )

            return parser.can_fetch(
                "*",
                url
            )

        robots_url = get_robots_url(
            url
        )

        try:

            robots_content = get_robots_content(
                url
            )

        except Exception:

            return False

        parser = RobotFileParser()

        parser.set_url(
            robots_url
        )

        parser.parse(
            robots_content.splitlines()
        )

        allowed = parser.can_fetch(
            "*",
            url
        )

        self.insert(
            base_url=base_url,
            robots_url=robots_url,
            robots_content=robots_content,
            checked_at=datetime.now()
        )

        return allowed


__all__ = [
    "RobotsCacheRepository"
]