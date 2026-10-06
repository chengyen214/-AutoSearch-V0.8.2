"""
tests/V8_0/test_robots_checker.py

AutoSearch V6

Robots Checker Test
"""

from crawler.robots_checker import (
    get_base_url,
    get_robots_url,
    check_robots,
)

from database.robots_cache_repository import (
    RobotsCacheRepository,
)


ALLOWED_URL = (
    "https://www.digitimes.com.tw/"
    "research/report/?cnlid=3&v=20260922-293&n=1"
)

DISALLOWED_URL = (
    "https://www.digitimes.com.tw/"
    "tech/webad/"
)


def test_get_base_url():

    base_url = get_base_url(
        ALLOWED_URL
    )

    assert base_url == (
        "https://www.digitimes.com.tw"
    )


def test_get_robots_url():

    robots_url = get_robots_url(
        ALLOWED_URL
    )

    assert robots_url == (
        "https://www.digitimes.com.tw/robots.txt"
    )


def test_check_robots():

    allowed = check_robots(
        ALLOWED_URL
    )

    print(
        f"\nURL: {ALLOWED_URL}"
    )

    print(
        f"Allowed: {allowed}"
    )

    assert isinstance(
        allowed,
        bool
    )


def test_robots_cache():

    repository = RobotsCacheRepository()

    allowed_url_result = repository.check(
        ALLOWED_URL
    )

    disallowed_url_result = repository.check(
        DISALLOWED_URL
    )

    print(
        f"\nAllowed URL: {ALLOWED_URL}"
    )

    print(
        f"Allowed: {allowed_url_result}"
    )

    print(
        f"\nDisallowed URL: {DISALLOWED_URL}"
    )

    print(
        f"Allowed: {disallowed_url_result}"
    )

    assert allowed_url_result is True

    assert disallowed_url_result is False

    base_url = get_base_url(
        ALLOWED_URL
    )

    result = repository.get_by_base_url(
        base_url
    )

    assert result is not None

    assert result["base_url"] == base_url

    assert result["robots_url"] == (
        "https://www.digitimes.com.tw/robots.txt"
    )

    assert result["robots_content"] is not None

    assert len(
        result["robots_content"]
    ) > 0

    assert result["checked_at"] is not None