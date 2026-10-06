"""
tests/V8_0/test_google_news_provider_real.py

AutoSearch V5

Real Test

驗證：

    Google News 最終 10
    +
    Google Search 最終 10
    =
    Provider 最終 20

同時確認：

    Google Search 不包含 Google News 結果。
"""

from search.google_news_provider import GoogleNewsProvider


KEYWORD = "IC semiconductor"

EXPECTED_NEWS = 10
EXPECTED_GOOGLE = 10
EXPECTED_TOTAL = 20


def test_real_google_news_provider():
    provider = GoogleNewsProvider()

    results = provider.search(
        KEYWORD,
        max_results=10,
    )

    print()
    print("=" * 60)
    print("Google News + Google Search Real Test")
    print("=" * 60)

    print(f"Keyword: {KEYWORD}")
    print(f"Provider Results: {len(results)}")

    news_results = [
        result
        for result in results
        if result.search_source == "google_news"
    ]

    google_results = [
        result
        for result in results
        if result.search_source == "google_search"
    ]

    print()
    print(f"Google News: {len(news_results)}")
    print(f"Google Search: {len(google_results)}")
    print(f"Total: {len(results)}")

    assert len(news_results) == EXPECTED_NEWS, (
        f"Google News 預期 {EXPECTED_NEWS} 筆，"
        f"實際 {len(news_results)} 筆"
    )

    assert len(google_results) == EXPECTED_GOOGLE, (
        f"Google Search 預期 {EXPECTED_GOOGLE} 筆，"
        f"實際 {len(google_results)} 筆"
    )

    assert len(results) == EXPECTED_TOTAL, (
        f"Provider 預期 {EXPECTED_TOTAL} 筆，"
        f"實際 {len(results)} 筆"
    )

    news_urls = {
        result.url
        for result in news_results
        if result.url
    }

    google_urls = {
        result.url
        for result in google_results
        if result.url
    }

    overlap = news_urls & google_urls

    print()
    print("Google News Results:")
    for index, result in enumerate(
        news_results,
        start=1,
    ):
        print(
            f"{index}. {result.url}"
        )

    print()
    print("Google Search Results:")
    for index, result in enumerate(
        google_results,
        start=1,
    ):
        print(
            f"{index}. {result.url}"
        )

    print()
    print("=" * 60)
    print("URL Exclusion Check")
    print("=" * 60)

    print(
        f"Google News URLs: {len(news_urls)}"
    )

    print(
        f"Google Search URLs: {len(google_urls)}"
    )

    print(
        f"Overlap: {len(overlap)}"
    )

    assert not overlap, (
        "Google Search 出現 Google News 已存在的 URL："
        f"{sorted(overlap)}"
    )

    print()
    print("PASSED")