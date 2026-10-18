"""
tests/V9_2/test_paper_pdf_chunking.py

AutoSearch V9.2

Paper PDF Text Extraction and Chunking Test
"""

import re

import fitz

from database.paper_mongo_repository import PaperMongoRepository


CHUNK_SIZE = 1200
CHUNK_OVERLAP = 200
PAPER_LIMIT = 6


def clean_text(text):
    """清理 PDF 擷取出的基本文字格式。"""
    text = text.replace("\x00", "")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def chunk_page_text(text, page_number):
    """將單頁文字切分成 Chunk。"""
    text = clean_text(text)

    if not text:
        return []

    chunks = []
    start = 0

    while start < len(text):
        end = min(start + CHUNK_SIZE, len(text))
        chunk_text = text[start:end].strip()

        if chunk_text:
            chunks.append({
                "text": chunk_text,
                "page_start": page_number,
                "page_end": page_number,
            })

        if end >= len(text):
            break

        start = end - CHUNK_OVERLAP

    return chunks


def extract_pdf(pdf_bytes):
    """擷取 PDF 各頁文字並產生 Chunk。"""
    pages = []
    chunks = []

    with fitz.open(stream=pdf_bytes, filetype="pdf") as pdf:
        page_count = len(pdf)

        for page_index, page in enumerate(pdf, start=1):
            text = clean_text(page.get_text("text"))

            pages.append({
                "page_number": page_index,
                "text": text,
                "char_count": len(text),
            })

            chunks.extend(chunk_page_text(text, page_index))

    return {
        "page_count": page_count,
        "pages": pages,
        "chunks": chunks,
    }


def get_papers(repository):
    """取得最新的六篇不同 OpenAlex 論文。"""
    cursor = repository.collection.find(
        {"document_id": {"$regex": "^openalex:"}},
        {
            "_id": 0,
            "document_id": 1,
            "url": 1,
            "created_at": 1,
        },
    ).sort("created_at", -1)

    papers = []
    seen_ids = set()

    for document in cursor:
        document_id = document.get("document_id")

        if not document_id or document_id in seen_ids:
            continue

        seen_ids.add(document_id)
        papers.append(document)

        if len(papers) >= PAPER_LIMIT:
            break

    return papers


def get_pdf_bytes(repository, document_id):
    """讀取指定論文的最新 GridFS PDF。"""
    files = repository.gridfs.find(
        {"metadata.document_id": document_id}
    ).sort("uploadDate", -1)

    pdf_file = next(iter(files), None)

    if pdf_file is None:
        return None

    return pdf_file.read()


def main():
    repository = PaperMongoRepository()
    papers = get_papers(repository)

    print("\nPaper PDF Text Extraction and Chunking Test")
    print("=" * 65)
    print(f"找到論文數量：{len(papers)}")
    print(f"Chunk Size：{CHUNK_SIZE} 字元")
    print(f"Chunk Overlap：{CHUNK_OVERLAP} 字元")

    if not papers:
        print("FAIL：找不到 OpenAlex 論文 HTML 文件")
        return

    success_count = 0
    failed_count = 0
    total_chunks = 0

    for index, paper in enumerate(papers, start=1):
        document_id = paper["document_id"]
        url = paper.get("url", "")

        print(f"\n[{index}/{len(papers)}] {url}")
        print(f"document_id：{document_id}")

        try:
            pdf_bytes = get_pdf_bytes(repository, document_id)

            if not pdf_bytes:
                raise ValueError("GridFS 找不到 PDF")

            result = extract_pdf(pdf_bytes)
            pages = result["pages"]
            chunks = result["chunks"]

            nonempty_pages = sum(
                bool(page["text"]) for page in pages
            )
            total_chars = sum(
                page["char_count"] for page in pages
            )

            print(f"PDF 大小：{len(pdf_bytes):,} bytes")
            print(f"PDF 頁數：{result['page_count']}")
            print(f"有文字的頁數：{nonempty_pages}")
            print(f"擷取文字量：{total_chars:,} 字元")
            print(f"Chunk 數量：{len(chunks)}")

            if chunks:
                print("第一個 Chunk 預覽：")
                print(chunks[0]["text"][:200])

            if total_chars == 0:
                raise ValueError("PDF 未擷取到文字")

            if not chunks:
                raise ValueError("沒有產生 Chunk")

            success_count += 1
            total_chunks += len(chunks)
            print("結果：PASS")

        except Exception as exc:
            failed_count += 1
            print(f"結果：FAIL，{type(exc).__name__}: {exc}")

    print("\n" + "=" * 65)
    print(f"測試論文數：{len(papers)}")
    print(f"成功：{success_count}")
    print(f"失敗：{failed_count}")
    print(f"Chunk 總數：{total_chunks}")
    print(
        "整體結果："
        + ("PASS" if failed_count == 0 else "部分失敗")
    )


if __name__ == "__main__":
    main()