"""
tests/V8_0/test_google_news_provider_time_fallback.py

AutoSearch V5

Google News Provider Time Fallback Test
"""

from models.search_result import (
    SearchResult,
)

from search.google_news_provider import (
    GoogleNewsProvider,
)


def create_search_result(
    url,
    title,
):
    """
    建立測試用 SearchResult。
    """

    return SearchResult(
        title=title,
        url=url,
        source="Google News",
    )


def test_ic_semiconductor_time_fallback(
    monkeypatch,
):
    """
    驗證 IC semiconductor 依序使用 7d、1m、6m。
    """

    calls = []

    primary_results = [
        create_search_result(
            f"https://example.com/7d/{index}",
            f"7d-{index}",
        )
        for index in range(6)
    ]

    one_month_results = [
        create_search_result(
            f"https://example.com/1m/{index}",
            f"1m-{index}",
        )
        for index in range(10)
    ]

    six_month_results = [
        create_search_result(
            f"https://example.com/6m/{index}",
            f"6m-{index}",
        )
        for index in range(29)
    ]

    def mock_google_news_search(
        search_keyword,
        max_results,
    ):
        calls.append(
            (
                search_keyword,
                max_results,
            )
        )

        if len(calls) == 1:
            return primary_results

        if len(calls) == 2:
            return one_month_results

        return six_month_results

    monkeypatch.setattr(
        "search.google_news_provider.google_news_search",
        mock_google_news_search,
    )

    monkeypatch.setattr(
        "services.url_source_grouping_service.URLSourceGroupingService.fetch_crawler_urls",
        lambda self: [],
    )

    provider = GoogleNewsProvider()

    results = provider.search(
        "IC semiconductor"
    )

    assert calls == [
        (
            "IC semiconductor when:7d",
            45,
        ),
        (
            "IC semiconductor when:1m",
            39,
        ),
        (
            "IC semiconductor when:6m",
            29,
        ),
    ]

    assert len(results) == 10

    primary_urls = {
        item.url
        for item in primary_results
    }

    result_urls = {
        item.url
        for item in results
    }

    assert primary_urls.issubset(
        result_urls
    )

    assert len(
        primary_urls.intersection(
            result_urls
        )
    ) == 6


def test_ic_semiconductor_randomly_fills_remaining_results(
    monkeypatch,
):
    """
    驗證 7d 結果優先，其餘結果隨機補足 10 筆。
    """

    primary_results = [
        create_search_result(
            f"https://example.com/7d/{index}",
            f"7d-{index}",
        )
        for index in range(4)
    ]

    extended_results = [
        create_search_result(
            f"https://example.com/extended/{index}",
            f"extended-{index}",
        )
        for index in range(41)
    ]

    calls = []

    def mock_google_news_search(
        search_keyword,
        max_results,
    ):
        calls.append(
            (
                search_keyword,
                max_results,
            )
        )

        if len(calls) == 1:
            return primary_results

        if len(calls) == 2:
            return extended_results[:20]

        return extended_results[20:]

    monkeypatch.setattr(
        "search.google_news_provider.google_news_search",
        mock_google_news_search,
    )

    monkeypatch.setattr(
        "services.url_source_grouping_service.URLSourceGroupingService.fetch_crawler_urls",
        lambda self: [],
    )

    sampled_items = []

    def mock_random_sample(
        population,
        k,
    ):
        sampled_items.append(
            (
                population,
                k,
            )
        )

        return population[:k]

    monkeypatch.setattr(
        "search.google_news_provider.random.sample",
        mock_random_sample,
    )

    provider = GoogleNewsProvider()

    results = provider.search(
        "IC semiconductor"
    )

    assert len(results) == 10

    assert len(
        sampled_items
    ) == 1

    population, sample_size = (
        sampled_items[0]
    )

    assert len(population) == 41

    assert sample_size == 6

    primary_urls = {
        item.url
        for item in primary_results
    }

    result_urls = {
        item.url
        for item in results
    }

    assert primary_urls.issubset(
        result_urls
    )

    assert len(
        primary_urls.intersection(
            result_urls
        )
    ) == 4

    assert len(
        result_urls
        - primary_urls
    ) == 6