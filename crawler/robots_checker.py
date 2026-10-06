"""
crawler/robots_checker.py

AutoSearch V6

Robots.txt Checker

用途：

    檢查網站 robots.txt 是否允許爬取指定 URL。

負責：

    - 建立 robots.txt URL
    - 下載 robots.txt
    - 解析 robots.txt
    - 判斷指定 URL 是否允許爬蟲

不負責：

    - MySQL
    - robots_cache
    - CrawlService
    - 實際網頁下載
"""

from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser


DEFAULT_USER_AGENT = "*"
ROBOTS_PATH = "/robots.txt"
TIMEOUT = 10


def get_base_url(url):
    """
    取得網站 Base URL。
    """

    parsed = urlparse(url)

    if not parsed.scheme or not parsed.netloc:
        raise ValueError(
            "Invalid URL"
        )

    return (
        f"{parsed.scheme}://{parsed.netloc}"
    )


def get_robots_url(url):
    """
    建立網站 robots.txt URL。
    """

    return (
        f"{get_base_url(url)}{ROBOTS_PATH}"
    )


def get_robots_content(
    url,
    user_agent=DEFAULT_USER_AGENT,
    timeout=TIMEOUT
):
    """
    取得 robots.txt 內容。
    """

    robots_url = get_robots_url(
        url
    )

    request = Request(
        robots_url,
        headers={
            "User-Agent": user_agent
        }
    )

    with urlopen(
        request,
        timeout=timeout
    ) as response:

        return response.read().decode(
            "utf-8",
            errors="ignore"
        )


def check_robots(
    url,
    user_agent=DEFAULT_USER_AGENT,
    timeout=TIMEOUT
):
    """
    取得 robots.txt 並判斷指定 URL 是否允許爬取。
    """

    robots_url = get_robots_url(
        url
    )

    try:

        content = get_robots_content(
            url,
            user_agent=user_agent,
            timeout=timeout
        )

    except Exception:

        return False

    parser = RobotFileParser()

    parser.set_url(
        robots_url
    )

    parser.parse(
        content.splitlines()
    )

    return parser.can_fetch(
        user_agent,
        url
    )


__all__ = [
    "get_base_url",
    "get_robots_url",
    "get_robots_content",
    "check_robots"
]