"""
tests/V9_0/test_paper_pipeline.py

AutoSearch V5

Paper Pipeline Real Test

測試：

1. OpenAlex Search → 10 Papers
2. Select first Paper only
3. PaperCrawler Real Crawl
4. MongoDB raw_html Persistence
5. MongoDB GridFS Persistence
6. PaperParser Real Parse
7. Article Mapping
8. Keyword Propagation
9. Test Data Cleanup
"""

from gridfs import GridFS

from database.mongo_connection import (
    get_mongo_database,
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


TEST_KEYWORD = "IC semiconductor"
EXPECTED_RESULT_COUNT = 10


def cleanup_test_data(
    database,
    document_id,
):
    """清除本次 Real Test 建立的 MongoDB 測試資料。"""

    if not document_id:
        return

    database["raw_html"].delete_many(
        {
            "document_id": document_id,
        }
    )

    fs = GridFS(
        database
    )

    files = database["fs.files"].find(
        {
            "metadata.document_id": document_id,
        }
    )

    for file_document in files:
        fs.delete(
            file_document["_id"]
        )


def verify_openalex_results(
    papers,
):
    """確認 OpenAlex 實際回傳 10 筆 Paper。"""

    assert isinstance(
        papers,
        list,
    )

    assert len(papers) == (
        EXPECTED_RESULT_COUNT
    )

    for paper in papers:
        assert isinstance(
            paper,
            dict,
        )

        assert paper.get(
            "document_id"
        )

        assert paper.get(
            "keyword"
        ) == TEST_KEYWORD

        assert paper.get(
            "title"
        )

        assert paper.get(
            "url"
        )

    print(
        "\n[PASS] OpenAlex Search"
    )

    print(
        f"  Results : {len(papers)}"
    )

    for index, paper in enumerate(
        papers,
        start=1,
    ):
        print(
            f"  {index}. "
            f"{paper['title']}"
        )

        print(
            f"     document_id : "
            f"{paper['document_id']}"
        )

        print(
            f"     keyword     : "
            f"{paper['keyword']}"
        )

        print(
            f"     url         : "
            f"{paper['url']}"
        )

        print(
            f"     pdf_url     : "
            f"{paper.get('pdf_url')}"
        )


def verify_crawl_result(
    crawl_result,
    paper,
):
    """確認 PaperCrawler 結果。"""

    assert crawl_result is not None

    assert crawl_result["document_id"] == (
        paper["document_id"]
    )

    assert crawl_result["keyword"] == (
        paper["keyword"]
    )

    assert crawl_result["title"] == (
        paper["title"]
    )

    assert crawl_result["url"] == (
        paper["url"]
    )

    assert crawl_result["resolved_url"]

    assert crawl_result["html"]

    assert crawl_result["content_hash"]

    assert crawl_result["resources"]

    assert crawl_result["pdf_url"] == (
        paper.get("pdf_url")
    )

    print(
        "\n[PASS] PaperCrawler"
    )

    print(
        f"  document_id  : "
        f"{crawl_result['document_id']}"
    )

    print(
        f"  keyword      : "
        f"{crawl_result['keyword']}"
    )

    print(
        f"  title        : "
        f"{crawl_result['title']}"
    )

    print(
        f"  url          : "
        f"{crawl_result['url']}"
    )

    print(
        f"  resolved_url : "
        f"{crawl_result['resolved_url']}"
    )

    print(
        f"  HTML size    : "
        f"{len(crawl_result['html'])}"
    )

    print(
        f"  CSS count    : "
        f"{len(crawl_result['resources'].get('css', []))}"
    )

    print(
        f"  Image count  : "
        f"{len(crawl_result['resources'].get('images', []))}"
    )

    pdf = crawl_result.get(
        "pdf"
    )

    if pdf:
        print(
            f"  PDF size     : "
            f"{pdf['file_size']}"
        )
    else:
        print(
            "  PDF          : None"
        )


def verify_mongodb(
    database,
    crawl_result,
):
    """確認 PaperCrawler 已寫入 MongoDB。"""

    document_id = crawl_result[
        "document_id"
    ]

    raw_html = database[
        "raw_html"
    ].find_one(
        {
            "document_id": document_id,
        }
    )

    assert raw_html is not None

    assert raw_html["url"] == (
        crawl_result["url"]
    )

    assert raw_html["resolved_url"] == (
        crawl_result["resolved_url"]
    )

    assert raw_html["html"] == (
        crawl_result["html"]
    )

    assert raw_html["content_hash"] == (
        crawl_result["content_hash"]
    )

    assert raw_html["resources"] == (
        crawl_result["resources"]
    )

    resources = raw_html[
        "resources"
    ]

    assert "css" in resources
    assert "images" in resources

    print(
        "\n[PASS] MongoDB raw_html"
    )

    print(
        f"  document_id : "
        f"{raw_html['document_id']}"
    )

    print(
        f"  url         : "
        f"{raw_html['url']}"
    )

    print(
        f"  CSS count   : "
        f"{len(resources['css'])}"
    )

    print(
        f"  Image count : "
        f"{len(resources['images'])}"
    )

    pdf = crawl_result.get(
        "pdf"
    )

    if not pdf:
        print(
            "\n[WARN] PDF not available"
        )
        return

    files = list(
        database["fs.files"].find(
            {
                "metadata.document_id":
                    document_id,
            }
        )
    )

    assert len(files) == 1

    file_document = files[0]

    fs = GridFS(
        database
    )

    grid_file = fs.get(
        file_document["_id"]
    )

    stored_pdf = grid_file.read()

    assert stored_pdf == (
        pdf["content"]
    )

    metadata = grid_file.metadata

    assert metadata["document_id"] == (
        document_id
    )

    assert metadata["url"] == (
        crawl_result["url"]
    )

    assert metadata["pdf_url"] == (
        crawl_result["pdf_url"]
    )

    chunks = list(
        database["fs.chunks"].find(
            {
                "files_id":
                    file_document["_id"],
            }
        )
    )

    assert chunks

    for chunk in chunks:
        assert chunk["url"] == (
            crawl_result["url"]
        )

    print(
        "\n[PASS] MongoDB GridFS"
    )

    print(
        f"  file_id      : "
        f"{file_document['_id']}"
    )

    print(
        f"  PDF size     : "
        f"{len(stored_pdf)}"
    )

    print(
        f"  document_id  : "
        f"{metadata['document_id']}"
    )

    print(
        f"  url          : "
        f"{metadata['url']}"
    )

    print(
        f"  pdf_url      : "
        f"{metadata['pdf_url']}"
    )

    print(
        f"  chunk count  : "
        f"{len(chunks)}"
    )

    print(
        f"  chunk url    : "
        f"{chunks[0]['url']}"
    )


def verify_parser(
    parser,
    crawl_result,
):
    """確認 PaperParser 實際解析結果。"""

    parsed_result = parser.parse(
        crawl_result
    )

    assert parsed_result is not None

    assert parsed_result["document_id"] == (
        crawl_result["document_id"]
    )

    assert parsed_result["keyword"] == (
        TEST_KEYWORD
    )

    assert parsed_result["title"]

    assert parsed_result["authors"] is not None

    assert parsed_result["abstract"] is not None

    assert parsed_result["published"] is not None

    assert parsed_result["source"]

    assert parsed_result["content"]

    assert parsed_result["url"] == (
        crawl_result["url"]
    )

    assert parsed_result["resolved_url"] == (
        crawl_result["resolved_url"]
    )

    assert parsed_result["pdf_url"] == (
        crawl_result["pdf_url"]
    )

    print(
        "\n[PASS] PaperParser"
    )

    print(
        f"  document_id : "
        f"{parsed_result['document_id']}"
    )

    print(
        f"  keyword     : "
        f"{parsed_result['keyword']}"
    )

    print(
        f"  title       : "
        f"{parsed_result['title']}"
    )

    print(
        f"  authors     : "
        f"{len(parsed_result['authors'])}"
    )

    print(
        f"  abstract    : "
        f"{len(parsed_result['abstract'])}"
    )

    print(
        f"  published   : "
        f"{parsed_result['published']}"
    )

    print(
        f"  source      : "
        f"{parsed_result['source']}"
    )

    print(
        f"  content     : "
        f"{len(parsed_result['content'])}"
    )

    return parsed_result


def verify_article_mapping(
    parser,
    parsed_result,
):
    """確認 Parser Result → Article Mapping。"""

    article = parser.to_article(
        parsed_result
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
    }

    assert set(
        article.keys()
    ) == expected_keys

    assert article["document_id"] == (
        parsed_result["document_id"]
    )

    assert article["keyword"] == (
        TEST_KEYWORD
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

    print(
        "\n[PASS] Article Mapping"
    )

    print(
        f"  document_id : "
        f"{article['document_id']}"
    )

    print(
        f"  keyword     : "
        f"{article['keyword']}"
    )

    print(
        f"  title       : "
        f"{article['title']}"
    )

    print(
        f"  url         : "
        f"{article['url']}"
    )

    print(
        f"  source      : "
        f"{article['source']}"
    )

    print(
        f"  published   : "
        f"{article['published']}"
    )

    print(
        f"  content size: "
        f"{len(article['content'])}"
    )

    print(
        f"  crawl_time  : "
        f"{article['crawl_time']}"
    )


def verify_cleanup(
    database,
    document_id,
):
    """確認測試資料已清除。"""

    raw_html_count = database[
        "raw_html"
    ].count_documents(
        {
            "document_id":
                document_id,
        }
    )

    gridfs_count = database[
        "fs.files"
    ].count_documents(
        {
            "metadata.document_id":
                document_id,
        }
    )

    assert raw_html_count == 0
    assert gridfs_count == 0

    print(
        "[PASS] Cleanup verified"
    )

    print(
        f"  raw_html : {raw_html_count}"
    )

    print(
        f"  fs.files : {gridfs_count}"
    )


def main():
    """執行 Paper Pipeline Real Test。"""

    print(
        "=" * 60
    )

    print(
        "Paper Pipeline Real Test"
    )

    print(
        "=" * 60
    )

    database = get_mongo_database()

    document_id = None

    try:
        print(
            "\n[1] OpenAlex Search..."
        )

        provider = OpenAlexProvider(
            result_count=EXPECTED_RESULT_COUNT
        )

        papers = provider.search(
            keyword=TEST_KEYWORD
        )

        verify_openalex_results(
            papers
        )

        paper = papers[0]

        document_id = paper[
            "document_id"
        ]

        print(
            "\n[2] Selecting first Paper only..."
        )

        print(
            f"  document_id : "
            f"{paper['document_id']}"
        )

        print(
            f"  keyword     : "
            f"{paper['keyword']}"
        )

        print(
            f"  title       : "
            f"{paper['title']}"
        )

        print(
            f"  url         : "
            f"{paper['url']}"
        )

        print(
            f"  pdf_url     : "
            f"{paper.get('pdf_url')}"
        )

        print(
            "\n[3] Cleaning old test data..."
        )

        cleanup_test_data(
            database,
            document_id,
        )

        print(
            "[PASS] Old test data cleaned"
        )

        print(
            "\n[4] Running PaperCrawler..."
        )

        crawler = PaperCrawler()

        crawl_result = crawler.crawl(
            paper
        )

        verify_crawl_result(
            crawl_result,
            paper,
        )

        print(
            "\n[5] Verifying MongoDB..."
        )

        verify_mongodb(
            database,
            crawl_result,
        )

        print(
            "\n[6] Running PaperParser..."
        )

        parser = PaperParser()

        parsed_result = verify_parser(
            parser,
            crawl_result,
        )

        print(
            "\n[7] Verifying Article Mapping..."
        )

        verify_article_mapping(
            parser,
            parsed_result,
        )

        print(
            "\n[8] Cleaning test data..."
        )

        cleanup_test_data(
            database,
            document_id,
        )

        verify_cleanup(
            database,
            document_id,
        )

        print(
            "\n"
            + "=" * 60
        )

        print(
            "Paper Pipeline Real Test: PASS"
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
            "Paper Pipeline Real Test: FAIL"
        )

        print(
            "=" * 60
        )

        print(
            f"\nError: {e}"
        )

        if document_id:
            cleanup_test_data(
                database,
                document_id,
            )

        raise


if __name__ == "__main__":
    main()