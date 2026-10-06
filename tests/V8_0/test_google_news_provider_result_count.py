"""
tests/V8_0/test_google_news_provider_result_count.py

AutoSearch V5

Google News Provider Result Count Test
"""

from search.google_news_provider import (
    GoogleNewsProvider,
)


KEYWORD = "半導體"


def test_google_news_candidate_and_final_count():
    """
    確認 Google News Candidate 與 Provider 最終結果數量。
    """

    provider = GoogleNewsProvider()

    final_results = (
        provider.search(
            KEYWORD,
            max_results=10,
        )
    )

    print(
        f"\nCandidate Limit: "
        f"{provider.candidate_results}"
    )

    print(
        f"Provider Final Count: "
        f"{len(final_results)}"
    )

    assert isinstance(
        final_results,
        list,
    )

    assert (
        provider.candidate_results
        == 45
    )

    assert (
        len(final_results)
        <= provider.max_results
    )

    assert (
        len(final_results)
        <= 10
    )