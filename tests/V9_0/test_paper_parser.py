"""
tests/V9_0/test_paper_parser.py

AutoSearch V5

Paper Parser Real Test

測試：

1. PaperCrawler Real Crawl
2. PaperParser Real Parse
3. Title Extraction
4. Author Extraction
5. Abstract Extraction
6. Published Extraction
7. Source Extraction
8. Content Extraction
9. PDF Text Fallback
10. Article Mapping
11. MongoDB Test Data Cleanup
"""

import json

from gridfs import GridFS

from database.mongo_connection import (
    get_mongo_database,
)
from paper.paper_crawler import (
    PaperCrawler,
)
from paper.paper_parser import (
    PaperParser,
)


TEST_DOCUMENT_ID = "test-v9-paper-parser"

TEST_PAPER = {
    "document_id": TEST_DOCUMENT_ID,
    "keyword": "IC semiconductor",
    "title": "Paper Parser Real Test",
    "url": (
        "https://link.springer.com/article/"
        "10.1007/s00034-026-03814-w"
    ),
    "pdf_url": (
        "https://link.springer.com/content/pdf/"
        "10.1007/s00034-026-03814-w.pdf"
    ),
}


def cleanup_test_data():
    """清除本次 Real Test 建立的 MongoDB 測試資料。"""

    database = get_mongo_database()

    database["raw_html"].delete_many(
        {
            "document_id": TEST_DOCUMENT_ID,
        }
    )

    fs = GridFS(
        database
    )

    files = database["fs.files"].find(
        {
            "metadata.document_id":
                TEST_DOCUMENT_ID,
        }
    )

    for file_document in files:
        fs.delete(
            file_document["_id"]
        )


def print_text_result(
    name,
    value,
):
    """Print parsed text result。"""

    print(
        f"\n{name}:"
    )

    if not value:
        print(
            "  [EMPTY]"
        )
        return

    print(
        f"  Type : {type(value).__name__}"
    )

    print(
        f"  Size : {len(value)}"
    )

    preview = str(
        value
    ).replace(
        "\n",
        " ",
    )

    print(
        f"  Preview: {preview[:500]}"
    )


def verify_result_structure(
    result,
):
    """確認 Parser Result 基本結構。"""

    expected_keys = {
        "document_id",
        "keyword",
        "title",
        "authors",
        "abstract",
        "published",
        "source",
        "content",
        "url",
        "resolved_url",
        "pdf_url",
    }

    actual_keys = set(
        result.keys()
    )

    assert (
        actual_keys
        == expected_keys
    )

    print(
        "\n[PASS] Parser result structure"
    )

    print(
        f"  Keys: {sorted(actual_keys)}"
    )


def verify_basic_fields(
    result,
):
    """確認 Paper 基本欄位。"""

    assert result["document_id"] == (
        TEST_DOCUMENT_ID
    )

    assert result["keyword"] == (
        TEST_PAPER.get("keyword")
    )

    assert result["url"] == (
        TEST_PAPER["url"]
    )

    assert result["resolved_url"]

    assert result["pdf_url"] == (
        TEST_PAPER["pdf_url"]
    )

    print(
        "\n[PASS] Basic Paper fields"
    )

    print(
        f"  document_id  : {result['document_id']}"
    )

    print(
        f"  keyword      : {result['keyword']}"
    )

    print(
        f"  url          : {result['url']}"
    )

    print(
        f"  resolved_url : {result['resolved_url']}"
    )

    print(
        f"  pdf_url      : {result['pdf_url']}"
    )


def verify_title(
    result,
):
    """確認 Title 已成功解析。"""

    assert result["title"]

    assert isinstance(
        result["title"],
        str,
    )

    assert len(
        result["title"].strip()
    ) > 0

    print_text_result(
        "Title",
        result["title"],
    )

    print(
        "[PASS] Title extraction"
    )


def verify_authors(
    result,
):
    """確認 Authors 解析結果。"""

    authors = result["authors"]

    assert isinstance(
        authors,
        list,
    )

    print(
        "\nAuthors:"
    )

    print(
        f"  Type : {type(authors).__name__}"
    )

    print(
        f"  Count: {len(authors)}"
    )

    for index, author in enumerate(
        authors,
        start=1,
    ):
        print(
            f"  {index}. {author}"
        )

    print(
        "[PASS] Author extraction"
    )


def verify_abstract(
    result,
):
    """確認 Abstract 解析結果。"""

    abstract = result["abstract"]

    assert isinstance(
        abstract,
        str,
    )

    print_text_result(
        "Abstract",
        abstract,
    )

    if abstract:
        print(
            "[PASS] Abstract extraction"
        )
    else:
        print(
            "[WARN] Abstract not found"
        )


def verify_published(
    result,
):
    """確認 Published 解析結果。"""

    published = result["published"]

    print(
        "\nPublished:"
    )

    print(
        f"  Type : {type(published).__name__}"
    )

    print(
        f"  Value: {published}"
    )

    if published:
        print(
            "[PASS] Published extraction"
        )
    else:
        print(
            "[WARN] Published date not found"
        )


def verify_source(
    result,
):
    """確認 Source 解析結果。"""

    source = result["source"]

    assert isinstance(
        source,
        str,
    )

    print_text_result(
        "Source",
        source,
    )

    if source:
        print(
            "[PASS] Source extraction"
        )
    else:
        print(
            "[WARN] Source not found"
        )


def verify_content(
    result,
):
    """確認代表性 Content。"""

    content = result["content"]

    assert isinstance(
        content,
        str,
    )

    print_text_result(
        "Content",
        content,
    )

    if content:
        print(
            "[PASS] Content extraction"
        )
    else:
        print(
            "[WARN] Content is empty"
        )


def verify_content_relation(
    result,
):
    """確認 Content 與 Abstract 的關係。"""

    abstract = (
        result["abstract"]
        or ""
    )

    content = (
        result["content"]
        or ""
    )

    if abstract:
        assert content == abstract

        print(
            "\n[PASS] Content uses Landing Page Abstract"
        )

        return

    assert content

    print(
        "\n[PASS] Content fallback is available"
    )


def verify_pdf_input(
    crawl_result,
):
    """確認 Parser 使用的 PDF binary 已存在。"""

    pdf = crawl_result.get(
        "pdf"
    )

    assert pdf is not None

    content = pdf.get(
        "content",
        b"",
    )

    assert content

    assert isinstance(
        content,
        bytes,
    )

    assert content.startswith(
        b"%PDF-"
    )

    print(
        "\n[PASS] PDF binary available to Parser"
    )

    print(
        f"  PDF size: {len(content)}"
    )


def verify_article_mapping(
    parsed_result,
):
    """確認 Paper Parser Result 可正確映射至既有 Article 欄位。"""

    article = PaperParser.to_article(
        parsed_result
    )

    assert isinstance(
        article,
        dict,
    )

    expected_keys = {
        "document_id",
        "keyword",
        "title",
        "url",
        "source",
        "published",
        "content",
        "crawl_time",
        "status",
        "ispaper",
        "authors",
    }

    actual_keys = set(
        article.keys()
    )

    assert (
        actual_keys
        == expected_keys
    )

    assert article["document_id"] == (
        parsed_result["document_id"]
    )

    assert article["keyword"] == (
        parsed_result.get("keyword")
    )

    assert article["title"] == (
        parsed_result["title"]
    )

    assert article["url"] == (
        parsed_result["url"]
    )

    assert article["source"] == (
        parsed_result["source"]
    )

    assert article["published"] == (
        parsed_result["published"]
    )

    assert article["content"] == (
        parsed_result["content"]
    )

    assert article["crawl_time"] is not None

    assert article["status"] is None

    assert article["ispaper"] == 1

    if parsed_result.get("authors"):
        mapped_authors = json.loads(
            article["authors"]
        )

        assert mapped_authors == (
            parsed_result["authors"]
        )

    else:
        assert article["authors"] is None

    print(
        "\n[PASS] Article Mapping"
    )

    print(
        f"  document_id : {article['document_id']}"
    )

    print(
        f"  keyword     : {article['keyword']}"
    )

    print(
        f"  title       : {article['title']}"
    )

    print(
        f"  url         : {article['url']}"
    )

    print(
        f"  source      : {article['source']}"
    )

    print(
        f"  published   : {article['published']}"
    )

    print(
        f"  content size: {len(article['content'])}"
    )

    print(
        f"  crawl_time  : {article['crawl_time']}"
    )

    print(
        f"  status      : {article['status']}"
    )

    print(
        f"  ispaper     : {article['ispaper']}"
    )

    print(
        f"  authors     : {article['authors']}"
    )


def verify_mongodb_cleanup(
    database,
):
    """確認測試資料已清除。"""

    raw_html_count = database[
        "raw_html"
    ].count_documents(
        {
            "document_id":
                TEST_DOCUMENT_ID,
        }
    )

    gridfs_count = database[
        "fs.files"
    ].count_documents(
        {
            "metadata.document_id":
                TEST_DOCUMENT_ID,
        }
    )

    assert raw_html_count == 0
    assert gridfs_count == 0

    print(
        "[PASS] MongoDB cleanup verified"
    )

    print(
        f"  raw_html : {raw_html_count}"
    )

    print(
        f"  fs.files : {gridfs_count}"
    )


def main():
    """執行 Paper Parser Real Test。"""

    print(
        "=" * 60
    )

    print(
        "Paper Parser Real Test"
    )

    print(
        "=" * 60
    )

    database = get_mongo_database()

    try:
        print(
            "\n[1] Cleaning old test data..."
        )

        cleanup_test_data()

        print(
            "[PASS] Old test data cleaned"
        )

        print(
            "\n[2] Running PaperCrawler..."
        )

        crawler = PaperCrawler()

        crawl_result = crawler.crawl(
            TEST_PAPER
        )

        assert crawl_result is not None

        assert crawl_result.get(
            "html"
        )

        print(
            "[PASS] PaperCrawler completed"
        )

        print(
            f"  HTML size: "
            f"{len(crawl_result['html'])}"
        )

        print(
            f"  PDF size : "
            f"{crawl_result['pdf']['file_size']}"
        )

        print(
            "\n[3] Verifying PDF input..."
        )

        verify_pdf_input(
            crawl_result
        )

        print(
            "\n[4] Creating PaperParser..."
        )

        parser = PaperParser()

        print(
            "[PASS] PaperParser created"
        )

        print(
            "\n[5] Running PaperParser..."
        )

        result = parser.parse(
            crawl_result
        )

        assert result is not None

        print(
            "[PASS] PaperParser completed"
        )

        print(
            "\n[6] Verifying result structure..."
        )

        verify_result_structure(
            result
        )

        print(
            "\n[7] Verifying basic fields..."
        )

        verify_basic_fields(
            result
        )

        print(
            "\n[8] Verifying title..."
        )

        verify_title(
            result
        )

        print(
            "\n[9] Verifying authors..."
        )

        verify_authors(
            result
        )

        print(
            "\n[10] Verifying abstract..."
        )

        verify_abstract(
            result
        )

        print(
            "\n[11] Verifying published..."
        )

        verify_published(
            result
        )

        print(
            "\n[12] Verifying source..."
        )

        verify_source(
            result
        )

        print(
            "\n[13] Verifying content..."
        )

        verify_content(
            result
        )

        print(
            "\n[14] Verifying content source..."
        )

        verify_content_relation(
            result
        )

        print(
            "\n[15] Verifying Article Mapping..."
        )

        verify_article_mapping(
            result
        )

        print(
            "\n[16] Cleaning test data..."
        )

        cleanup_test_data()

        verify_mongodb_cleanup(
            database
        )

        print(
            "\n"
            + "=" * 60
        )

        print(
            "Paper Parser Real Test: PASS"
        )

        print(
            "=" * 60
        )

    except Exception as e:
        print(
            "\n"
            + "=" * 60
        )

        print(
            "Paper Parser Real Test: FAIL"
        )

        print(
            "=" * 60
        )

        print(
            f"\nError: {e}"
        )

        cleanup_test_data()

        raise


if __name__ == "__main__":
    main()