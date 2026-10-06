"""
search/search_engine.py

AutoSearch V4

Google News RSS Search

功能：
    - Google News RSS 搜尋
    - Google News URL 解碼
    - URL 去重
    - 搜尋數量限制
    - RSS 資料解析
    - SearchResult 統一回傳

不負責：
    - Article 建立
    - HTML Download
    - Parser
    - Archive
    - AI Analysis
    - Database Storage
"""

from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed,
)

from datetime import datetime, timedelta
from urllib.parse import quote
import re

import feedparser

from googlenewsdecoder import gnewsdecoder

from models.search_result import SearchResult


DEFAULT_USER_AGENT = "*"


def resolve_google_news_url(url):
    """
    將 Google News URL 解碼成原始新聞 URL。
    """

    if not url:
        return url

    try:
        result = gnewsdecoder(url)

        if isinstance(
            result,
            dict,
        ) and result.get("status"):
            decoded_url = result.get(
                "decoded_url"
            )

            if decoded_url:
                return decoded_url

        return url

    except Exception as e:
        print(
            "Google News URL 解碼失敗:",
            e,
        )
        return url


def resolve_google_news_urls(
    urls,
    max_workers=10,
):
    """
    並行解碼多個 Google News URL。
    """

    if not urls:
        return {}

    valid_urls = []

    for url in urls:

        if not url:
            continue

        url = str(
            url
        ).strip()

        if not url:
            continue

        if url in valid_urls:
            continue

        valid_urls.append(
            url
        )

    if not valid_urls:
        return {}

    try:
        max_workers = int(
            max_workers
        )

    except (
        TypeError,
        ValueError,
    ):
        max_workers = 10

    max_workers = max(
        1,
        min(
            max_workers,
            len(valid_urls),
        ),
    )

    decoded_urls = {}

    with ThreadPoolExecutor(
        max_workers=max_workers
    ) as executor:

        future_map = {
            executor.submit(
                resolve_google_news_url,
                url,
            ): url
            for url in valid_urls
        }

        for future in as_completed(
            future_map
        ):
            source_url = future_map[
                future
            ]

            try:
                decoded_url = future.result()

            except Exception:
                decoded_url = source_url

            if not decoded_url:
                decoded_url = source_url

            decoded_urls[
                source_url
            ] = str(
                decoded_url
            ).strip()

    return decoded_urls


def _build_google_news_query(keyword):
    """
    將 when:7d、when:1m、when:6m 轉換成 Google News 時間查詢。
    """

    match = re.search(
        r"\bwhen:(\d+)([dwm])\b",
        keyword,
        re.IGNORECASE,
    )

    if not match:
        return keyword

    value = int(match.group(1))
    unit = match.group(2).lower()

    if value <= 0:
        return keyword

    if unit == "d":
        delta = timedelta(days=value)

    elif unit == "w":
        delta = timedelta(weeks=value)

    elif unit == "m":
        delta = timedelta(days=value * 30)

    else:
        return keyword

    after_date = (
        datetime.now() - delta
    ).strftime("%Y-%m-%d")

    query = re.sub(
        r"\s+when:\d+[dwm]\b",
        "",
        keyword,
        flags=re.IGNORECASE,
    ).strip()

    if not query:
        return f"after:{after_date}"

    return f"{query} after:{after_date}"


def search(
    keyword,
    max_results=10,
    resolve_urls=True,
):
    """
    執行 Google News RSS 搜尋並回傳 SearchResult。
    """

    if keyword is None:
        keyword = ""

    if not isinstance(
        keyword,
        str,
    ):
        keyword = str(
            keyword
        )

    keyword = keyword.strip()

    if not keyword:
        return []

    try:
        max_results = int(
            max_results
        )

    except (
        TypeError,
        ValueError,
    ):
        max_results = 10

    if max_results <= 0:
        return []

    print()
    print("=" * 50)
    print(
        f"開始搜尋：{keyword}"
    )
    print("=" * 50)

    search_query = _build_google_news_query(
        keyword
    )

    keyword_encode = quote(
        search_query
    )

    rss_url = (
        "https://news.google.com/rss/search?"
        f"q={keyword_encode}"
        "&hl=zh-TW"
        "&gl=TW"
        "&ceid=TW:zh-Hant"
    )

    try:
        feed = feedparser.parse(
            rss_url
        )

    except Exception as e:
        print(
            "Google News RSS 搜尋失敗:",
            e,
        )
        return []

    if getattr(
        feed,
        "bozo",
        False,
    ):
        exception = getattr(
            feed,
            "bozo_exception",
            None,
        )

        if exception:
            print(
                "Google News RSS 解析警告:",
                exception,
            )

    results = []
    url_set = set()

    total_candidates = min(
        len(feed.entries),
        max_results,
    )

    if total_candidates > 0:
        print(
            f"Candidate {max_results}: "
            f"[{'░' * 20}] "
            f"0% "
            f"(0/{total_candidates})",
            end="",
            flush=True,
        )

    for index, item in enumerate(
        feed.entries,
        start=1,
    ):
        if len(results) >= max_results:
            break

        if total_candidates > 0:
            percentage = int(
                index / total_candidates * 100
            )

            filled = int(
                index / total_candidates * 20
            )

            bar = (
                "█" * filled
                + "░" * (20 - filled)
            )

            print(
                f"\rCandidate {max_results}: "
                f"[{bar}] "
                f"{percentage}% "
                f"({index}/{total_candidates})",
                end="",
                flush=True,
            )

        title = item.get(
            "title",
            "",
        )

        url = item.get(
            "link",
            "",
        )

        if not url:
            continue

        published = item.get(
            "published",
            None,
        )

        source = ""

        item_source = getattr(
            item,
            "source",
            None,
        )

        if item_source:
            try:
                source = item_source.get(
                    "title",
                    "",
                )

            except (
                AttributeError,
                TypeError,
            ):
                source = ""

        if resolve_urls:
            url = resolve_google_news_url(
                url
            )

        if url in url_set:
            continue

        url_set.add(url)

        result = SearchResult(
            keyword=keyword,
            title=title,
            url=url,
            source=source,
            published=published,
            search_source="google_news",
            rank=len(results) + 1,
        )

        results.append(
            result
        )

    if total_candidates > 0:
        print()

    print(
        f"搜尋完成：{keyword}"
    )

    print(
        f"取得文章：{len(results)}"
    )

    return results


__all__ = [
    "resolve_google_news_url",
    "resolve_google_news_urls",
    "search",
]