"""
services/paper_service.py

AutoSearch V5

Paper Service

用途：

    控制 Paper Search 到 Paper Article Persistence 的流程。

目前功能：

    1. OpenAlex Search
    2. Paper Crawl
    3. Paper Parse
    4. Article Mapping
    5. Article Persistence
    6. 依序處理 Paper
"""

from database.paper_article_repository import (
    PaperArticleRepository,
)

from paper.openalex_provider import (
    OpenAlexProvider,
)

from paper.paper_crawler import (
    PaperCrawler,
)

from paper.paper_parser import (
    PaperParser,
)


class PaperService:
    """AutoSearch V5 Paper Service。"""

    def __init__(
        self,
        provider=None,
        crawler=None,
        parser=None,
        article_repository=None,
    ):
        """建立 Paper Service。"""

        self.provider = (
            provider
            or OpenAlexProvider()
        )

        self.crawler = (
            crawler
            or PaperCrawler()
        )

        self.parser = (
            parser
            or PaperParser()
        )

        self.article_repository = (
            article_repository
            or PaperArticleRepository()
        )

    def run(
        self,
        keyword=None,
        per_page=None,
    ):
        """執行 Paper Search、Crawl、Parse、Mapping 與 Persistence。"""

        search_kwargs = {}

        if keyword is not None:
            search_kwargs["keyword"] = keyword

        if per_page is not None:
            search_kwargs["per_page"] = per_page

        papers = self.provider.search(
            **search_kwargs
        )

        results = []

        for index, paper in enumerate(
            papers,
            start=1,
        ):
            print(
                f"\nProcessing Paper "
                f"{index}/{len(papers)}"
            )

            crawl_result = self.crawler.crawl(
                paper
            )

            parsed_result = self.parser.parse(
                crawl_result
            )

            article = self.parser.to_article(
                parsed_result
            )

            article_id = (
                self.article_repository.save_article(
                    article
                )
            )

            results.append(
                {
                    "paper": paper,
                    "crawl_result": crawl_result,
                    "parsed_result": parsed_result,
                    "article": article,
                    "article_id": article_id,
                }
            )

        return results


__all__ = [
    "PaperService",
]