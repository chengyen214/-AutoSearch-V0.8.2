"""
paper/paper_parser.py

AutoSearch V5

Paper Parser

功能：

1. Landing Page HTML Parsing
2. Paper Metadata Extraction
3. Title Extraction
4. Author Extraction
5. Abstract Extraction
6. Published Date Extraction
7. Source Extraction
8. Content Extraction
9. PDF Text Extraction
10. PDF Abstract / Summary Fallback
11. Article Mapping
"""

import json
import re
from datetime import datetime

from bs4 import BeautifulSoup


class PaperParser:
    """AutoSearch V5 Paper Parser。"""

    def parse(
        self,
        crawl_result,
    ):
        """Parse Paper Crawl Result。"""

        if not crawl_result:
            raise ValueError(
                "Crawl result cannot be empty."
            )

        html = crawl_result.get(
            "html",
            "",
        )

        if not html:
            raise ValueError(
                "Paper HTML cannot be empty."
            )

        soup = BeautifulSoup(
            html,
            "html.parser",
        )

        title = self._extract_title(
            soup,
            crawl_result,
        )

        authors = self._extract_authors(
            soup
        )

        abstract = self._extract_abstract(
            soup
        )

        published = self._extract_published(
            soup
        )

        source = self._extract_source(
            soup,
            crawl_result,
        )

        content = self._extract_content(
            soup,
            abstract,
            crawl_result.get(
                "pdf"
            ),
        )

        return {
            "document_id": crawl_result.get(
                "document_id"
            ),
            "keyword": crawl_result.get(
                "keyword"
            ),
            "title": title,
            "authors": authors,
            "abstract": abstract,
            "published": published,
            "source": source,
            "content": content,
            "url": crawl_result.get(
                "url"
            ),
            "resolved_url": crawl_result.get(
                "resolved_url"
            ),
            "pdf_url": crawl_result.get(
                "pdf_url"
            ),
        }

    @staticmethod
    def to_article(
        parsed_result,
        crawl_time=None,
        status=None,
    ):
        """Map Paper Parser Result to existing Article fields。"""

        if not parsed_result:
            raise ValueError(
                "Parsed result cannot be empty."
            )

        url = parsed_result.get(
            "url"
        )

        if not url:
            raise ValueError(
                "Article URL cannot be empty."
            )

        if crawl_time is None:
            crawl_time = datetime.now().replace(
                microsecond=0
            )
        else:
            crawl_time = crawl_time.replace(
                microsecond=0
            )

        if status is None:
            status = "Success"

        authors = parsed_result.get(
            "authors"
        )

        authors_text = None

        if authors:
            authors_text = json.dumps(
                authors,
                ensure_ascii=False,
            )

        return {
            "document_id": parsed_result.get(
                "document_id"
            ),
            "keyword": parsed_result.get(
                "keyword"
            ),
            "title": parsed_result.get(
                "title"
            ),
            "url": url,
            "source": parsed_result.get(
                "source"
            ),
            "published": parsed_result.get(
                "published"
            ),
            "content": parsed_result.get(
                "content"
            ),
            "crawl_time": crawl_time,
            "status": status,
            "ispaper": 1,
            "authors": authors_text,
        }

    @staticmethod
    def _extract_title(
        soup,
        crawl_result,
    ):
        """Extract Paper title。"""

        meta_selectors = [
            {
                "attrs": {
                    "name": "citation_title",
                },
            },
            {
                "attrs": {
                    "name": "dc.title",
                },
            },
            {
                "attrs": {
                    "property": "og:title",
                },
            },
        ]

        for selector in meta_selectors:
            tag = soup.find(
                "meta",
                attrs=selector["attrs"],
            )

            if tag and tag.get("content"):
                value = tag["content"].strip()

                if value:
                    return value

        json_ld_title = soup.find(
            "meta",
            attrs={
                "itemprop": "name",
            },
        )

        if (
            json_ld_title
            and json_ld_title.get("content")
        ):
            value = json_ld_title["content"].strip()

            if value:
                return value

        for selector in [
            "h1",
            "h1.article-title",
            "h1.c-article-title",
            "[class*='title']",
        ]:
            tag = soup.select_one(
                selector
            )

            if tag:
                value = tag.get_text(
                    " ",
                    strip=True,
                )

                if value:
                    return value

        title = soup.title

        if title:
            value = title.get_text(
                " ",
                strip=True,
            )

            if value:
                return value

        return crawl_result.get(
            "title"
        )

    @staticmethod
    def _extract_authors(
        soup,
    ):
        """Extract Paper authors。"""

        authors = []

        meta_selectors = [
            {
                "name": "citation_author",
            },
            {
                "name": "author",
            },
            {
                "name": "dc.creator",
            },
        ]

        for attrs in meta_selectors:
            tags = soup.find_all(
                "meta",
                attrs=attrs,
            )

            for tag in tags:
                value = tag.get(
                    "content",
                    "",
                ).strip()

                if value and value not in authors:
                    authors.append(
                        value
                    )

            if authors:
                return authors

        author_selectors = [
            "[rel='author']",
            "[itemprop='author']",
            "[class*='author']",
            "[class*='Author']",
        ]

        for selector in author_selectors:
            tags = soup.select(
                selector
            )

            for tag in tags:
                value = tag.get_text(
                    " ",
                    strip=True,
                )

                value = PaperParser._clean_text(
                    value
                )

                if (
                    value
                    and len(value) <= 200
                    and value not in authors
                ):
                    authors.append(
                        value
                    )

            if authors:
                break

        return authors

    @staticmethod
    def _extract_abstract(
        soup,
    ):
        """Extract Paper abstract。"""

        meta_selectors = [
            {
                "name": "citation_abstract",
            },
            {
                "name": "dc.description",
            },
            {
                "property": "og:description",
            },
        ]

        for attrs in meta_selectors:
            tag = soup.find(
                "meta",
                attrs=attrs,
            )

            if tag and tag.get("content"):
                value = PaperParser._clean_text(
                    tag["content"]
                )

                if value:
                    return value

        selectors = [
            "[class*='abstract']",
            "[id*='abstract']",
            "[class*='Abstract']",
            "[id*='Abstract']",
            "section.abstract",
            "section#abstract",
        ]

        for selector in selectors:
            tags = soup.select(
                selector
            )

            for tag in tags:
                value = PaperParser._extract_block_text(
                    tag
                )

                if len(value) >= 80:
                    return value

        headings = soup.find_all(
            [
                "h2",
                "h3",
                "h4",
            ]
        )

        for heading in headings:
            heading_text = heading.get_text(
                " ",
                strip=True,
            ).lower()

            if "abstract" not in heading_text:
                continue

            block = heading.find_next(
                [
                    "p",
                    "div",
                    "section",
                ]
            )

            if block:
                value = PaperParser._extract_block_text(
                    block
                )

                if len(value) >= 80:
                    return value

        return ""

    @staticmethod
    def _extract_published(
        soup,
    ):
        """Extract Paper publication date。"""

        meta_names = [
            "citation_publication_date",
            "citation_date",
            "dc.date",
            "date",
            "pub-date",
        ]

        for name in meta_names:
            tag = soup.find(
                "meta",
                attrs={
                    "name": name,
                },
            )

            if not tag:
                tag = soup.find(
                    "meta",
                    attrs={
                        "property": name,
                    },
                )

            if tag and tag.get("content"):
                value = (
                    tag["content"]
                    .strip()
                )

                parsed = PaperParser._parse_date(
                    value
                )

                if parsed:
                    return parsed

        time_tag = soup.find(
            "time",
            attrs={
                "datetime": True,
            },
        )

        if time_tag:
            parsed = PaperParser._parse_date(
                time_tag.get(
                    "datetime"
                )
            )

            if parsed:
                return parsed

        text = soup.get_text(
            " ",
            strip=True,
        )

        patterns = [
            r"\b(20\d{2}-\d{2}-\d{2})\b",
            r"\b(20\d{2}/\d{2}/\d{2})\b",
            r"\b(\d{1,2}\s+\w+\s+20\d{2})\b",
            r"\b(\w+\s+\d{1,2},\s+20\d{2})\b",
        ]

        for pattern in patterns:
            match = re.search(
                pattern,
                text,
            )

            if match:
                parsed = PaperParser._parse_date(
                    match.group(1)
                )

                if parsed:
                    return parsed

        return None

    @staticmethod
    def _extract_source(
        soup,
        crawl_result,
    ):
        """Extract Paper source。"""

        meta_selectors = [
            {
                "name": "citation_journal_title",
            },
            {
                "name": "citation_conference_title",
            },
            {
                "name": "citation_publisher",
            },
            {
                "name": "dc.publisher",
            },
        ]

        for attrs in meta_selectors:
            tag = soup.find(
                "meta",
                attrs=attrs,
            )

            if tag and tag.get("content"):
                value = PaperParser._clean_text(
                    tag["content"]
                )

                if value:
                    return value

        selectors = [
            "[itemprop='isPartOf']",
            "[itemprop='publisher']",
            "[class*='journal']",
            "[class*='Journal']",
            "[class*='publisher']",
            "[class*='Publisher']",
        ]

        for selector in selectors:
            tag = soup.select_one(
                selector
            )

            if tag:
                value = PaperParser._clean_text(
                    tag.get_text(
                        " ",
                        strip=True,
                    )
                )

                if value:
                    return value

        url = (
            crawl_result.get(
                "resolved_url"
            )
            or crawl_result.get(
                "url"
            )
        )

        if url:
            try:
                from urllib.parse import urlparse

                hostname = (
                    urlparse(
                        url
                    ).hostname
                    or ""
                )

                if hostname:
                    return hostname

            except Exception:
                pass

        return ""

    def _extract_content(
        self,
        soup,
        abstract,
        pdf,
    ):
        """Extract representative Paper content。"""

        if abstract:
            return abstract

        main_text = self._extract_main_text(
            soup
        )

        if main_text:
            return main_text

        pdf_text = self._extract_pdf_text(
            pdf
        )

        if pdf_text:
            return self._extract_pdf_summary(
                pdf_text
            )

        return ""

    @staticmethod
    def _extract_main_text(
        soup,
    ):
        """Find the main text block from Landing Page。"""

        for tag in soup.find_all(
            [
                "script",
                "style",
                "nav",
                "header",
                "footer",
                "aside",
                "form",
            ]
        ):
            tag.decompose()

        candidates = []

        selectors = [
            "main",
            "article",
            "[role='main']",
            "[class*='article-body']",
            "[class*='articleBody']",
            "[class*='fulltext']",
            "[class*='full-text']",
            "[class*='main-content']",
            "[class*='content']",
        ]

        for selector in selectors:
            for tag in soup.select(
                selector
            ):
                text = PaperParser._extract_block_text(
                    tag
                )

                if len(text) >= 200:
                    candidates.append(
                        text
                    )

        if not candidates:
            for tag in soup.find_all(
                [
                    "section",
                    "div",
                ]
            ):
                text = PaperParser._extract_block_text(
                    tag
                )

                if len(text) >= 200:
                    candidates.append(
                        text
                    )

        if not candidates:
            return ""

        candidates.sort(
            key=len,
            reverse=True,
        )

        for candidate in candidates:
            lowered = candidate.lower()

            if (
                "references" in lowered
                and len(candidate) > 5000
            ):
                continue

            if (
                "related articles" in lowered
                and len(candidate) > 3000
            ):
                continue

            if (
                "cookie" in lowered
                and len(candidate) > 2000
            ):
                continue

            return candidate

        return candidates[0]

    @staticmethod
    def _extract_pdf_text(
        pdf,
    ):
        """Extract text from PDF binary。"""

        if not pdf:
            return ""

        content = pdf.get(
            "content",
            b"",
        )

        if not content:
            return ""

        try:
            import fitz

            document = fitz.open(
                stream=content,
                filetype="pdf",
            )

            pages = []

            for page in document:
                text = page.get_text(
                    "text"
                )

                if text:
                    pages.append(
                        text
                    )

            document.close()

            return PaperParser._clean_text(
                "\n".join(
                    pages
                )
            )

        except Exception:
            return ""

    @staticmethod
    def _extract_pdf_summary(
        text,
    ):
        """Extract Abstract / Summary from PDF text。"""

        if not text:
            return ""

        patterns = [
            r"\babstract\b",
            r"\bsummary\b",
            r"\bexecutive summary\b",
        ]

        lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]

        for index, line in enumerate(
            lines
        ):
            lowered = line.lower()

            if not any(
                re.fullmatch(
                    pattern,
                    lowered,
                )
                for pattern in patterns
            ):
                continue

            collected = []

            for next_line in lines[
                index + 1:
            ]:
                lowered_next = (
                    next_line.lower()
                )

                if (
                    lowered_next
                    in {
                        "introduction",
                        "keywords",
                        "key words",
                        "1 introduction",
                        "1. introduction",
                    }
                ):
                    break

                collected.append(
                    next_line
                )

                if len(
                    " ".join(
                        collected
                    )
                ) >= 3000:
                    break

            value = PaperParser._clean_text(
                " ".join(
                    collected
                )
            )

            if len(value) >= 80:
                return value

        return ""

    @staticmethod
    def _extract_block_text(
        tag,
    ):
        """Extract readable text from HTML block。"""

        text = tag.get_text(
            " ",
            strip=True,
        )

        return PaperParser._clean_text(
            text
        )

    @staticmethod
    def _clean_text(
        text,
    ):
        """Clean extracted text。"""

        if not text:
            return ""

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text.strip()

    @staticmethod
    def _parse_date(
        value,
    ):
        """Parse supported date formats。"""

        if not value:
            return None

        value = value.strip()

        formats = [
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%d %B %Y",
            "%d %b %Y",
            "%B %d, %Y",
            "%b %d, %Y",
            "%Y-%m",
            "%Y",
        ]

        for date_format in formats:
            try:
                parsed = datetime.strptime(
                    value,
                    date_format,
                )

                return parsed

            except ValueError:
                continue

        iso_value = value.replace(
            "Z",
            "+00:00",
        )

        try:
            return datetime.fromisoformat(
                iso_value
            )

        except ValueError:
            return None


__all__ = [
    "PaperParser",
]