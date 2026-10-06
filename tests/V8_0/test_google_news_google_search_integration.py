from unittest.mock import patch

from models.search_result import SearchResult

from search.google_news_provider import GoogleNewsProvider


def create_result(keyword, url, search_source):
    return SearchResult(
        keyword=keyword,
        title=url,
        url=url,
        source="example.com",
        published=None,
        search_source=search_source,
        rank=1,
    )


def test_google_news_and_google_search_return_20_distinct_results():
    provider = GoogleNewsProvider()

    news_results = [
        create_result(
            "IC semiconductor when:7d",
            f"https://news-{index}.example.com",
            "google_news",
        )
        for index in range(10)
    ]

    search_7d_results = [
        create_result(
            "IC semiconductor when:7d",
            f"https://search-7d-{index}.example.com",
            "google_search",
        )
        for index in range(10)
    ]

    search_1m_results = [
        create_result(
            "IC semiconductor when:1m",
            f"https://search-1m-{index}.example.com",
            "google_search",
        )
        for index in range(20)
    ]

    search_6m_results = [
        create_result(
            "IC semiconductor when:6m",
            f"https://search-6m-{index}.example.com",
            "google_search",
        )
        for index in range(20)
    ]

    news_calls = []
    search_calls = []

    def mock_news_search(keyword, max_results=None):
        news_calls.append(
            (keyword, max_results)
        )

        if keyword == "IC semiconductor when:7d":
            return news_results

        return []

    def mock_google_search(
        keyword,
        max_results=None,
        url=None,
        exclude_urls=None,
    ):
        search_calls.append(
            {
                "keyword": keyword,
                "max_results": max_results,
                "exclude_urls": set(exclude_urls or []),
            }
        )

        if keyword == "IC semiconductor when:7d":
            return search_7d_results

        if keyword == "IC semiconductor when:1m":
            return search_1m_results

        if keyword == "IC semiconductor when:6m":
            return search_6m_results

        return []

    with patch(
        "search.google_news_provider.google_news_search",
        side_effect=mock_news_search,
    ), patch.object(
        provider.url_source_grouping_service,
        "fetch_crawler_urls",
        return_value=[],
    ), patch.object(
        provider.google_search_provider,
        "search",
        side_effect=mock_google_search,
    ):
        results = provider.search(
            "IC semiconductor"
        )

    assert len(results) == 20

    news_final = results[:10]
    google_search_final = results[10:]

    assert len(news_final) == 10
    assert len(google_search_final) == 10

    news_urls = {
        result.url
        for result in news_final
    }

    google_search_urls = {
        result.url
        for result in google_search_final
    }

    assert len(news_urls) == 10
    assert len(google_search_urls) == 10

    assert news_urls.isdisjoint(
        google_search_urls
    )

    assert len(
        news_urls | google_search_urls
    ) == 20

    assert all(
        result.search_source == "google_news"
        for result in news_final
    )

    assert all(
        result.search_source == "google_search"
        for result in google_search_final
    )

    assert news_calls == [
        (
            "IC semiconductor when:7d",
            45,
        ),
        (
            "IC semiconductor when:1m",
            35,
        ),
        (
            "IC semiconductor when:6m",
            35,
        ),
    ]

    assert search_calls[0]["keyword"] == (
        "IC semiconductor when:7d"
    )

    assert search_calls[0]["max_results"] == 45

    assert search_calls[1]["keyword"] == (
        "IC semiconductor when:1m"
    )

    assert search_calls[1]["max_results"] == 35

    assert search_calls[0]["exclude_urls"] == news_urls
    assert search_calls[1]["exclude_urls"] == news_urls

    assert search_calls[2]["keyword"] == (
        "IC semiconductor when:6m"
    )

    assert search_calls[2]["max_results"] == 15

    assert search_calls[2]["exclude_urls"] == news_urls

    search_7d_urls = {
        result.url
        for result in search_7d_results
    }

    assert search_7d_urls.issubset(
        google_search_urls
    )


def test_google_search_excludes_google_news_results():
    provider = GoogleNewsProvider()

    news_results = [
        create_result(
            "IC semiconductor when:7d",
            f"https://news-{index}.example.com",
            "google_news",
        )
        for index in range(10)
    ]

    search_7d_results = [
        create_result(
            "IC semiconductor when:7d",
            f"https://news-{index}.example.com",
            "google_search",
        )
        for index in range(10)
    ]

    search_7d_results.extend(
        [
            create_result(
                "IC semiconductor when:7d",
                f"https://search-{index}.example.com",
                "google_search",
            )
            for index in range(10)
        ]
    )

    search_calls = []

    def mock_google_search(
        keyword,
        max_results=None,
        url=None,
        exclude_urls=None,
    ):
        exclude_urls = set(
            exclude_urls or []
        )

        search_calls.append(
            {
                "keyword": keyword,
                "exclude_urls": exclude_urls,
            }
        )

        return [
            result
            for result in search_7d_results
            if result.url not in exclude_urls
        ]

    with patch.object(
        provider.url_source_grouping_service,
        "fetch_crawler_urls",
        return_value=[],
    ), patch.object(
        provider,
        "_normalize_results",
        return_value=news_results,
    ), patch.object(
        provider.google_search_provider,
        "search",
        side_effect=mock_google_search,
    ):
        results = provider.search(
            "IC semiconductor"
        )

    assert len(results) == 20

    news_final = results[:10]
    google_search_final = results[10:]

    news_urls = {
        result.url
        for result in news_final
    }

    google_search_urls = {
        result.url
        for result in google_search_final
    }

    assert len(news_final) == 10
    assert len(google_search_final) == 10

    assert news_urls.isdisjoint(
        google_search_urls
    )

    assert len(
        news_urls | google_search_urls
    ) == 20

    assert (
        search_calls[0]["exclude_urls"]
        == news_urls
    )

    assert not any(
        result.url in news_urls
        for result in google_search_final
    )