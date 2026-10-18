"""
tests/V6_0/test_robots_cache_repository.py

AutoSearch V6

Robots Cache Repository Integration Test
"""

import unittest

from database.connection import get_connection
from database.robots_cache_repository import RobotsCacheRepository
from crawler.robots_checker import (
    DEFAULT_USER_AGENT,
    get_base_url,
    get_robots_url,
)


TEST_URL = "https://techorange.com/author/industry-update/"


class TestRobotsCacheRepository(unittest.TestCase):

    def setUp(self):
        self.repository = RobotsCacheRepository()
        self.base_url = get_base_url(TEST_URL)

    def get_cache(self):
        return self.repository.get_by_base_url(
            self.base_url
        )

    def test_robots_cache_integration(self):
        print("\n[1] Check initial cache")
        cached_before = self.get_cache()

        print("[2] Check crawl permission")
        allowed_first = self.repository.check(
            TEST_URL
        )

        self.assertIsInstance(
            allowed_first,
            bool
        )

        print(f"    URL: {TEST_URL}")
        print(f"    User-Agent: {DEFAULT_USER_AGENT}")
        print(f"    Allowed: {allowed_first}")

        print("[3] Verify MySQL cache")
        cached_after = self.get_cache()

        self.assertIsNotNone(
            cached_after,
            "robots_cache should contain this website"
        )

        self.assertEqual(
            cached_after["base_url"],
            self.base_url
        )

        self.assertEqual(
            cached_after["robots_url"],
            get_robots_url(TEST_URL)
        )

        self.assertIsNotNone(
            cached_after["robots_content"]
        )

        self.assertTrue(
            cached_after["rule_group"],
            "rule_group should not be empty"
        )

        print(f"    Base URL: {cached_after['base_url']}")
        print(f"    Robots URL: {cached_after['robots_url']}")
        print(f"    Rule Group: {cached_after['rule_group']}")
        print("    Robots content: stored")

        print("[4] Verify cache reuse")
        allowed_second = self.repository.check(
            TEST_URL
        )

        self.assertEqual(
            allowed_first,
            allowed_second,
            "Permission should remain consistent for unchanged rules"
        )

        cached_second = self.get_cache()

        self.assertEqual(
            cached_after["robots_content"],
            cached_second["robots_content"]
        )

        self.assertEqual(
            cached_after["rule_group"],
            cached_second["rule_group"]
        )

        print(f"    First check: {allowed_first}")
        print(f"    Second check: {allowed_second}")
        print("    Cache reuse: PASS")

        print("[5] Verify cache schema")
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            cursor.execute(
                "DESCRIBE robots_cache"
            )
            columns = {
                row["Field"]
                for row in cursor.fetchall()
            }
        finally:
            cursor.close()
            conn.close()

        required_columns = {
            "base_url",
            "robots_url",
            "robots_content",
            "rule_group",
            "checked_at",
        }

        self.assertTrue(
            required_columns.issubset(columns),
            f"Missing columns: {required_columns - columns}"
        )

        self.assertNotIn(
            "allowed",
            columns,
            "The old allowed column should have been removed"
        )

        print("    Schema: PASS")
        print("\nRobots Cache Integration Test: PASS")


if __name__ == "__main__":
    unittest.main(verbosity=2)