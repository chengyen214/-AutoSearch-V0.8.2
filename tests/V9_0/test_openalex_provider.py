"""
tests/V9_0/test_openalex_provider.py

AutoSearch V5

V9_0 OpenAlex Provider Test

測試：

1. OpenAlex 真實 API
2. Default Keyword
3. Paper Search
4. Landing Page URL
5. PDF URL
6. Final Result Count
7. Final Paper URLs
"""

from paper.openalex_provider import (
    OpenAlexProvider
)


def main():
    provider = OpenAlexProvider()

    print("=" * 60)
    print("V9_0 OpenAlex Provider Test")
    print("=" * 60)

    print("\n[1] Default Keyword Test")

    results = provider.search()

    print("Keyword: IC semiconductor")
    print(f"Results: {len(results)}")

    if not results:
        raise AssertionError(
            "OpenAlex returned no results."
        )

    print("\n[2] Final Paper URLs")

    for index, result in enumerate(
        results,
        start=1,
    ):
        url = result.get("url")

        print(
            f"{index}. {url}"
        )

        if not url:
            raise AssertionError(
                f"Paper {index} has no URL."
            )

    print("\n[3] Result Validation")

    valid_urls = sum(
        1
        for result in results
        if result.get("url")
    )

    valid_pdf_urls = sum(
        1
        for result in results
        if result.get("pdf_url")
    )

    print(
        f"Valid Landing Pages: "
        f"{valid_urls}/{len(results)}"
    )

    print(
        f"Valid PDF URLs: "
        f"{valid_pdf_urls}/{len(results)}"
    )

    if len(results) > 10:
        raise AssertionError(
            "OpenAlex returned more than 10 results."
        )

    if valid_urls != len(results):
        raise AssertionError(
            "Some OpenAlex results are missing URLs."
        )

    print("\nOpenAlex Provider Test: PASS")


if __name__ == "__main__":
    main()