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
    - 委派 robots.txt 權限檢查
"""

from database.connection import get_connection


class RobotsCacheRepository:
    """
    Robots Cache Repository。

    負責 robots_cache 的 SQL 操作。
    Robots.txt 檢查流程由 crawler.robots_checker 統一協調。
    """

    def get_by_base_url(self, base_url):
        """依 Base URL 取得 Robots Cache。"""

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            cursor.execute(
                """
                SELECT *
                FROM robots_cache
                WHERE base_url = %s
                LIMIT 1
                """,
                (base_url,),
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
        rule_group,
        checked_at,
    ):
        """新增 Robots Cache。"""

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
                    rule_group,
                    checked_at
                )
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    base_url,
                    robots_url,
                    robots_content,
                    rule_group,
                    checked_at,
                ),
            )

            conn.commit()
            return cursor.lastrowid

        except Exception:
            conn.rollback()
            raise

        finally:
            cursor.close()
            conn.close()

    def check(self, url):
        """
        委派至 robots_checker 的單一入口。

        不在 module import 階段匯入，
        避免 Circular Import。
        """

        from crawler.robots_checker import check_robots

        return check_robots(url)


__all__ = [
    "RobotsCacheRepository",
]