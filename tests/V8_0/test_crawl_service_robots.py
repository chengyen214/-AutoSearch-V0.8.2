"""
tests/V8_0/test_crawl_service_robots.py

AutoSearch V6

CrawlService Robots Permission Test
"""

from services.crawl_service import (
    CrawlService,
)


class FakeRobotsCacheRepository:
    """
    Fake Robots Cache Repository。
    """

    def __init__(
        self,
        allowed=True,
    ):
        self.allowed = allowed
        self.checked_urls = []

    def check(
        self,
        url,
    ):
        self.checked_urls.append(
            url
        )

        return self.allowed


class FakeDownloader:
    """
    Fake Downloader。
    """

    def __init__(self):
        self.called_urls = []

    def __call__(
        self,
        url,
    ):
        self.called_urls.append(
            url
        )

        return (
            "<html>"
            "<body>"
            "Test"
            "</body>"
            "</html>"
        )


class FakeResourceDownloader:
    """
    Fake Resource Downloader。
    """

    def __call__(
        self,
        html,
        resolved_url,
    ):
        return {
            "css": [],
            "images": [],
        }


def test_crawl_allowed_by_robots():
    """
    Robots 允許時，應該正常執行 Downloader。
    """

    robots_repository = (
        FakeRobotsCacheRepository(
            allowed=True
        )
    )

    downloader = FakeDownloader()

    service = CrawlService(
        downloader=downloader,
        url_resolver=lambda url: url,
        resource_downloader=(
            FakeResourceDownloader()
        ),
        raw_html_repository=None,
        robots_cache_repository=(
            robots_repository
        ),
        save_raw_html=False,
    )

    url = (
        "https://example.com/"
    )

    result = service.crawl(
        url
    )

    assert result.success is True

    assert (
        robots_repository.checked_urls
        == [url]
    )

    assert (
        downloader.called_urls
        == [url]
    )


def test_crawl_blocked_by_robots():
    """
    Robots 禁止時，不應該執行 Downloader。
    """

    robots_repository = (
        FakeRobotsCacheRepository(
            allowed=False
        )
    )

    downloader = FakeDownloader()

    service = CrawlService(
        downloader=downloader,
        url_resolver=lambda url: url,
        resource_downloader=(
            FakeResourceDownloader()
        ),
        raw_html_repository=None,
        robots_cache_repository=(
            robots_repository
        ),
        save_raw_html=False,
    )

    url = (
        "https://example.com/"
    )

    result = service.crawl(
        url
    )

    assert result.success is False

    assert result.error == (
        "Crawl blocked by robots.txt"
    )

    assert (
        robots_repository.checked_urls
        == [url]
    )

    assert (
        downloader.called_urls
        == []
    )


class FailingRobotsCacheRepository:
    """
    Fake Robots Repository。
    """

    def check(
        self,
        url,
    ):
        raise RuntimeError(
            "robots check failed"
        )


def test_crawl_robots_check_error():
    """
    Robots Check 發生錯誤時，不應該執行 Downloader。
    """

    robots_repository = (
        FailingRobotsCacheRepository()
    )

    downloader = FakeDownloader()

    service = CrawlService(
        downloader=downloader,
        url_resolver=lambda url: url,
        resource_downloader=(
            FakeResourceDownloader()
        ),
        raw_html_repository=None,
        robots_cache_repository=(
            robots_repository
        ),
        save_raw_html=False,
    )

    url = (
        "https://example.com/"
    )

    result = service.crawl(
        url
    )

    assert result.success is False

    assert result.error == (
        "robots check failed"
    )

    assert (
        downloader.called_urls
        == []
    )