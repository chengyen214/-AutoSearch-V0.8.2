"""
database/paper_mongo_repository.py

AutoSearch V5

Paper MongoDB Repository

用途：

    負責 Paper 的 MongoDB Persistence。

目前功能：

    - 儲存 Paper Landing Page HTML
    - 儲存 Paper PDF 至 MongoDB GridFS
    - 使用既有 raw_html Collection
    - 沿用既有 raw_html 資料結構
"""

from datetime import datetime, timezone

from gridfs import GridFS

from database.mongo_connection import (
    get_mongo_collection,
    get_mongo_database,
)

from utils.logger import (
    logger,
)

RAW_HTML_COLLECTION = "raw_html"


class PaperMongoRepository:
    """AutoSearch V5 Paper MongoDB Repository。"""

    def __init__(self):
        """建立 MongoDB Collection 與 GridFS。"""
        self.collection = get_mongo_collection(
            RAW_HTML_COLLECTION
        )
        self.database = get_mongo_database()
        self.gridfs = GridFS(
            self.database
        )

    def save_raw_html(
        self,
        crawl_result,
    ):
        """儲存 Paper Landing Page HTML。"""

        if not crawl_result:
            raise ValueError(
                "Crawl result cannot be empty."
            )

        url = crawl_result.get("url")

        if not url:
            raise ValueError(
                "Paper URL cannot be empty."
            )

        now = datetime.now(
            timezone.utc
        )

        document = {
            "article_id": None,
            "document_id": crawl_result.get(
                "document_id"
            ),
            "title": crawl_result.get(
                "title"
            ),
            "keyword": crawl_result.get(
                "keyword"
            ),
            "url": url,
            "resolved_url": crawl_result.get(
                "resolved_url"
            ),
            "pdf_url": crawl_result.get(
                "pdf_url"
            ),
            "html": crawl_result.get(
                "html",
                "",
            ),
            "content_hash": crawl_result.get(
                "content_hash"
            ),
            "resources": crawl_result.get(
                "resources",
                {
                    "css": [],
                    "images": [],
                },
            ),
            "created_at": now,
            "updated_at": now,
        }

        result = self.collection.insert_one(
            document
        )

        logger.info(
            "Paper raw HTML saved: "
            f"document_id={document.get('document_id')}, "
            f"url={url}, "
            f"_id={result.inserted_id}"
        )

        return result.inserted_id

    def save_pdf(
        self,
        document_id,
        url,
        pdf_result,
    ):
        """儲存 Paper PDF 至 MongoDB GridFS。"""

        if not pdf_result:
            raise ValueError(
                "PDF result cannot be empty."
            )

        content = pdf_result.get(
            "content",
            b"",
        )

        if not content:
            raise ValueError(
                "PDF content cannot be empty."
            )

        if not document_id:
            raise ValueError(
                "Document ID cannot be empty."
            )

        if not url:
            raise ValueError(
                "Paper URL cannot be empty."
            )

        pdf_url = pdf_result.get(
            "url"
        )

        if not pdf_url:
            raise ValueError(
                "PDF URL cannot be empty."
            )

        now = datetime.now(
            timezone.utc
        )

        file_id = self.gridfs.put(
            content,
            filename=pdf_result.get(
                "filename",
                "paper.pdf",
            ),
            content_type=pdf_result.get(
                "mime_type",
                "application/pdf",
            ),
            metadata={
                "document_id": document_id,
                "url": url,
                "pdf_url": pdf_url,
                "final_url": pdf_result.get(
                    "final_url"
                ),
                "content_hash": pdf_result.get(
                    "content_hash"
                ),
                "mime_type": pdf_result.get(
                    "mime_type",
                    "application/pdf",
                ),
                "file_size": pdf_result.get(
                    "file_size",
                    len(content),
                ),
                "created_at": now,
            },
        )

        self.database["fs.chunks"].update_many(
            {
                "files_id": file_id,
            },
            {
                "$set": {
                    "url": url,
                },
            },
        )

        logger.info(
            "Paper PDF saved to GridFS: "
            f"document_id={document_id}, "
            f"url={url}, "
            f"pdf_url={pdf_url}, "
            f"file_id={file_id}"
        )

        return file_id


__all__ = [
    "PaperMongoRepository",
]