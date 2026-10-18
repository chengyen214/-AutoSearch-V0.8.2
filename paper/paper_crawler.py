"""
paper/paper_crawler.py

AutoSearch V5

Paper Crawler

功能：

1. Landing Page Crawl
2. Redirect / Resolved URL
3. HTML Content Hash
4. CSS Resource Download
5. Image Resource Download
6. PDF Download
7. Crawl Result
8. MongoDB Persistence
"""

from crawler.crawler import (
    DEFAULT_HEADERS,
    download,
    download_resources,
    generate_resource_hash,
    resolve_url,
)
from database.paper_mongo_repository import (
    PaperMongoRepository,
)
from paper.pdf_downloader import (
    download_pdf,
)

DEFAULT_PDF_TIMEOUT = 30


class PaperCrawler:
    """AutoSearch V5 Paper Crawler。"""

    def __init__(
        self,
        timeout=DEFAULT_PDF_TIMEOUT,
    ):
        self.timeout = timeout
        self.mongo_repository = PaperMongoRepository()

    def crawl(
        self,
        paper,
    ):
        """Crawl Paper Landing Page and PDF."""

        url = paper.get("url")

        if not url:
            raise ValueError(
                "Paper URL cannot be empty."
            )

        pdf_url = paper.get("pdf_url")

        html = download(
            url,
            headers=DEFAULT_HEADERS,
        )

        resolved_url = resolve_url(
            url,
            headers=DEFAULT_HEADERS,
        )

        base_url = (
            resolved_url
            or url
        )

        resources = download_resources(
            html,
            base_url,
        )

        content_hash = generate_resource_hash(
            html.encode(
                "utf-8",
                errors="ignore",
            )
        )

        pdf = None

        if pdf_url:
            pdf = self._download_pdf(
                pdf_url,
            )

            if pdf is None:
                raise RuntimeError(
                    f"PDF download failed. "
                    f"document_id={paper.get('document_id')}, "
                    f"pdf_url={pdf_url}"
                )

        crawl_result = {
            "document_id": paper.get(
                "document_id"
            ),
            "keyword": paper.get(
                "keyword"
            ),
            "title": paper.get(
                "title"
            ),
            "url": url,
            "resolved_url": resolved_url,
            "html": html,
            "content_hash": content_hash,
            "resources": resources,
            "pdf_url": pdf_url,
            "pdf": pdf,
        }

        self.mongo_repository.save_raw_html(
            crawl_result
        )

        if pdf is not None:
            self.mongo_repository.save_pdf(
                document_id=crawl_result.get(
                    "document_id"
                ),
                url=crawl_result.get(
                    "url"
                ),
                pdf_result=pdf,
            )

        return crawl_result

    def _download_pdf(
        self,
        pdf_url,
    ):
        """Download Paper PDF。"""

        result = download_pdf(
            pdf_url,
            timeout=self.timeout,
            headless=True,
        )

        if not result.success:
            return None

        if not result.content:
            return None

        return {
            "url": result.url,
            "final_url": result.final_url,
            "content": result.content,
            "content_hash": result.content_hash,
            "mime_type": result.content_type,
            "file_size": result.content_size,
        }


__all__ = [
    "PaperCrawler",
]