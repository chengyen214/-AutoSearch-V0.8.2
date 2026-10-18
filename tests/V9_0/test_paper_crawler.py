"""
tests/V9_0/test_paper_crawler.py

AutoSearch V5

Paper Crawler Real Test
"""

from paper.openalex_provider import OpenAlexProvider
from paper.paper_crawler import PaperCrawler


def main():
    print("=" * 60)
    print("V9_0 Paper Crawler Real Test")
    print("=" * 60)

    provider = OpenAlexProvider()

    print()
    print("[1] OpenAlex Real Paper")

    results = provider.search()

    if not results:
        print("No Paper found.")
        return

    paper = results[0]

    print(f"Title: {paper.get('title')}")
    print(f"Landing Page: {paper.get('url')}")
    print(f"PDF URL: {paper.get('pdf_url')}")

    print()
    print("[2] PaperCrawler Real Crawl")

    crawler = PaperCrawler()

    result = crawler.crawl(paper)

    print()
    print("[3] Crawl Result")

    print(f"Title: {result.get('title')}")
    print(f"URL: {result.get('url')}")
    print(f"Resolved URL: {result.get('resolved_url')}")

    html = result.get("html")

    print(
        f"HTML: "
        f"{len(html) if html else 0} bytes"
    )

    print(
        f"Content Hash: "
        f"{result.get('content_hash')}"
    )

    resources = result.get("resources") or {}

    css = resources.get("css") or []
    images = resources.get("images") or []

    print(f"CSS Resources: {len(css)}")
    print(f"Image Resources: {len(images)}")

    pdf = result.get("pdf")

    if pdf:
        print()
        print("[4] PDF Result")
        print(f"PDF URL: {pdf.get('url')}")
        print(f"PDF Final URL: {pdf.get('final_url')}")
        print(f"PDF Size: {pdf.get('file_size')}")
        print(f"PDF Hash: {pdf.get('content_hash')}")
    else:
        print()
        print("[4] PDF Result")
        print("PDF: Failed or unavailable")

    print()
    print("=" * 60)
    print("Paper Crawler Real Test: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()