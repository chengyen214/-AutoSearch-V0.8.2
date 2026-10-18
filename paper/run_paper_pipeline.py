"""
paper/run_paper_pipeline.py

AutoSearch Paper Pipeline

執行流程：

1. OpenAlex 搜尋論文
2. 爬取 Landing Page 與 PDF
3. 解析論文 metadata
4. 後續整合 MySQL articles 與 document_metadata 儲存
"""

from paper.openalex_provider import OpenAlexProvider
from paper.paper_crawler import PaperCrawler
from paper.paper_parser import PaperParser


def run_pipeline(keyword=None):
    provider = OpenAlexProvider(result_count=10)
    crawler = PaperCrawler()
    parser = PaperParser()

    papers = provider.search(keyword=keyword)

    print(f"搜尋完成：{len(papers)} 篇")

    results = []

    for index, paper in enumerate(papers, start=1):
        print(f"[{index}/{len(papers)}] {paper.get('title', paper.get('url', 'Unknown'))}")

        try:
            crawl_result = crawler.crawl(paper)

            if not crawl_result:
                print("爬取失敗")
                continue

            parsed_result = parser.parse(crawl_result)
            article = parser.to_article(parsed_result)

            results.append(article)
            print("解析完成")

        except Exception as exc:
            print(f"處理失敗：{exc}")

    print(f"Pipeline 完成：成功解析 {len(results)} 篇")

    return results


if __name__ == "__main__":
    run_pipeline()