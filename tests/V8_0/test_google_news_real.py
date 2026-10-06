"""
tests/V8_0/test_google_news_real.py

Google News Real RSS Test

用途：

    直接測試 V4 Google News Search Engine。

測試：

    IC semiconductor when:7d
    IC semiconductor when:1m
    IC semiconductor when:6m
"""

from search.search_engine import search as google_news_search


KEYWORD = "IC semiconductor"

TIME_RANGES = [
    "when:7d",
    "when:1m",
    "when:6m",
]


def test_real_google_news_time_ranges():
    results_by_range = {}

    for time_range in TIME_RANGES:
        search_keyword = (
            f"{KEYWORD} {time_range}"
        )

        print()
        print("=" * 60)
        print(
            f"Real Google News: {search_keyword}"
        )
        print("=" * 60)

        results = google_news_search(
            search_keyword,
            max_results=45,
        )

        assert isinstance(
            results,
            list,
        )

        results_by_range[time_range] = results

        print(
            f"取得結果：{len(results)}"
        )

        for index, result in enumerate(
            results,
            start=1,
        ):
            print(
                f"{index}. {result.url}"
            )

        assert len(results) <= 45

    print()
    print("=" * 60)
    print("Google News Real Search Summary")
    print("=" * 60)

    for time_range in TIME_RANGES:
        print(
            f"{time_range}: "
            f"{len(results_by_range[time_range])}"
        )