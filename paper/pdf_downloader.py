"""
paper/pdf_downloader.py

AutoSearch V5

PDF Downloader

功能：

1. Browser Context PDF Download
2. PDF Content Validation
3. PDF Content Hash
4. PDF Metadata
"""

import hashlib
import time

from dataclasses import dataclass

from playwright.sync_api import (
    sync_playwright,
    TimeoutError as PlaywrightTimeoutError,
)


DEFAULT_TIMEOUT = 30


@dataclass
class PDFDownloadResult:
    """PDF Download Result。"""

    success: bool
    url: str
    final_url: str
    content: bytes
    status_code: int
    content_type: str
    content_size: int
    content_hash: str
    elapsed_time: float
    error: str


class PDFDownloader:
    """AutoSearch V5 PDF Downloader。"""

    def __init__(
        self,
        timeout=DEFAULT_TIMEOUT,
        headless=True,
    ):
        self.timeout = timeout
        self.headless = headless

    def download(
        self,
        url,
    ):
        """使用 Browser Context Request 下載 PDF。"""

        if not url:
            return self._build_result(
                url="",
                error="PDF URL cannot be empty.",
            )

        started = time.time()

        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(
                    headless=self.headless,
                )

                context = browser.new_context()

                try:
                    response = context.request.get(
                        url,
                        timeout=self.timeout * 1000,
                        fail_on_status_code=False,
                    )

                    status_code = response.status

                    final_url = response.url

                    content_type = (
                        response.headers.get(
                            "content-type",
                            "",
                        )
                    )

                    content = response.body()

                    if not content.startswith(
                        b"%PDF-"
                    ):
                        return self._build_result(
                            url=url,
                            final_url=final_url,
                            content=content,
                            status_code=status_code,
                            content_type=content_type,
                            elapsed_time=(
                                time.time()
                                - started
                            ),
                            error=(
                                "Response content "
                                "is not a valid PDF."
                            ),
                        )

                    content_hash = (
                        hashlib.sha256(
                            content
                        ).hexdigest()
                    )

                    return PDFDownloadResult(
                        success=True,
                        url=url,
                        final_url=final_url,
                        content=content,
                        status_code=status_code,
                        content_type=(
                            content_type
                            or "application/pdf"
                        ),
                        content_size=len(content),
                        content_hash=content_hash,
                        elapsed_time=(
                            time.time()
                            - started
                        ),
                        error="",
                    )

                finally:
                    context.close()
                    browser.close()

        except PlaywrightTimeoutError:
            return self._build_result(
                url=url,
                elapsed_time=(
                    time.time()
                    - started
                ),
                error="PDF download timeout.",
            )

        except Exception as e:
            return self._build_result(
                url=url,
                elapsed_time=(
                    time.time()
                    - started
                ),
                error=str(e),
            )

    def _build_result(
        self,
        url,
        final_url="",
        content=b"",
        status_code=0,
        content_type="",
        elapsed_time=0,
        error="",
    ):
        """建立 PDF Download Result。"""

        return PDFDownloadResult(
            success=False,
            url=url,
            final_url=final_url or url,
            content=content or b"",
            status_code=status_code,
            content_type=content_type,
            content_size=len(content or b""),
            content_hash="",
            elapsed_time=elapsed_time,
            error=error,
        )


def download_pdf(
    url,
    timeout=DEFAULT_TIMEOUT,
    headless=True,
):
    """下載 PDF。"""

    downloader = PDFDownloader(
        timeout=timeout,
        headless=headless,
    )

    return downloader.download(
        url
    )


__all__ = [
    "PDFDownloadResult",
    "PDFDownloader",
    "download_pdf",
]