"""
tests/V8_0/test_crawl_service_robots_integration.py

AutoSearch V6

CrawlService Robots Real Website Integration Test
"""

from services.crawl_service import (
    CrawlService,
)


ALLOWED_URL = (
    "https://www.digitimes.com.tw/"
    "research/report/?cnlid=3&v=20260922-293&n=1"
)

DISALLOWED_URL = (
    "https://www.digitimes.com.tw/"
    "tech/webad/"
)


def test_crawl_allowed_real_website():
    """
    真實網站允許 URL 應該正常執行 CrawlService。
    """

    service = CrawlService(
        save_raw_html=False,
    )

    result = service.crawl(
        ALLOWED_URL
    )

    print(
        f"\nURL: {ALLOWED_URL}"
    )

    print(
        f"Success: {result.success}"
    )

    print(
        f"Error: {result.error}"
    )

    assert result.success is True

    assert result.error is None


def test_crawl_disallowed_real_website():
    """
    真實網站禁止 URL 應該被 robots.txt 阻擋。
    """

    service = CrawlService(
        save_raw_html=False,
    )

    result = service.crawl(
        DISALLOWED_URL
    )

    print(
        f"\nURL: {DISALLOWED_URL}"
    )

    print(
        f"Success: {result.success}"
    )

    print(
        f"Error: {result.error}"
    )

    assert result.success is False

    assert result.error == (
        "Crawl blocked by robots.txt"
    )