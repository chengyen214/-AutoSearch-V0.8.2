
"""
paper/paper_ocr_pipeline.py

AutoSearch V9

Paper PDF OCR Pipeline
"""

import argparse
import re
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

import pymupdf
import torch
from gridfs import GridFS
from PIL import Image
from transformers import (
    AutoModelForImageTextToText,
    AutoProcessor,
)

from database.mongo_connection import get_mongo_database


MODEL_PATH = Path(r"D:\AI_Models\PaddleOCR-VL-1.6")
OUTPUT_ROOT = Path(r"D:\AI_Models\paper_ocr")

COLLECTION_NAME = "paper_ocr_results"
OCR_MODEL_NAME = "PaddleOCR-VL-1.6"

RENDER_SCALE = 1.5
RETRY_RENDER_SCALE = 2.5

MAX_NEW_TOKENS = 4096
CPU_THREADS = 8
MIN_OUTPUT_CHARS = 80

OCR_PROMPT = (
    "Transcribe all visible text on this PDF page as completely "
    "and accurately as possible. Include the title, headings, "
    "paragraphs, captions, figure labels, table contents, "
    "footnotes, references, page numbers, mathematical formulas, "
    "symbols, and text inside diagrams. "
    "Preserve the original reading order and paragraph structure. "
    "Do not summarize, translate, explain, or invent text. "
    "Do not omit short words, punctuation, numbers, or text near "
    "the edges of the page. Return only the transcription."
)


def utc_now():
    return datetime.now(timezone.utc)


def get_database():
    database = get_mongo_database()
    database[COLLECTION_NAME].create_index(
        [("document_id", 1)],
        unique=True,
        name="uq_paper_ocr_document_id",
    )
    return database


def get_pdf_candidates(database, document_id=None):
    """取得 GridFS 中每篇論文最新的 PDF。"""

    query = {
        "metadata.document_id": {"$exists": True, "$ne": None},
        "length": {"$gt": 0},
        "contentType": "application/pdf",
    }

    if document_id:
        query["metadata.document_id"] = document_id

    latest = {}

    cursor = database["fs.files"].find(query).sort(
        [("uploadDate", -1), ("_id", -1)]
    )

    for item in cursor:
        doc_id = item.get("metadata", {}).get("document_id")

        if doc_id and doc_id not in latest:
            latest[doc_id] = {
                "document_id": doc_id,
                "pdf_file_id": item["_id"],
                "pdf_length": item.get("length", 0),
                "upload_date": item.get("uploadDate"),
                "filename": item.get("filename"),
            }

    return list(latest.values())


def safe_directory_name(document_id):
    name = re.sub(
        r'[<>:"/\\|?*\x00-\x1f]',
        "_",
        str(document_id),
    )
    return name[:180] or "unknown_document"


def render_page(page, scale):
    pixmap = page.get_pixmap(
        matrix=pymupdf.Matrix(scale, scale),
        alpha=False,
    )
    return Image.frombytes(
        "RGB",
        (pixmap.width, pixmap.height),
        pixmap.samples,
    )


def clean_ocr_text(text):
    return re.sub(r"<\|LOC_\d+\|>", "", text).strip()


def run_ocr(model, processor, image, device):
    """執行單頁 OCR，回傳文字及生成狀態。"""

    messages = [{
        "role": "user",
        "content": [
            {"type": "image", "image": image},
            {"type": "text", "text": OCR_PROMPT},
        ],
    }]

    inputs = processor.apply_chat_template(
        messages,
        add_generation_prompt=True,
        tokenize=True,
        return_dict=True,
        return_tensors="pt",
    ).to(device)

    input_length = inputs["input_ids"].shape[-1]

    with torch.inference_mode():
        outputs = model.generate(
            **inputs,
            max_new_tokens=MAX_NEW_TOKENS,
            do_sample=False,
            use_cache=True,
        )

    if device == "cuda":
        torch.cuda.synchronize()

    generated_ids = outputs[0, input_length:]
    generated_tokens = generated_ids.numel()

    eos_token_id = model.generation_config.eos_token_id

    if isinstance(eos_token_id, int):
        eos_ids = {eos_token_id}
    elif eos_token_id:
        eos_ids = set(eos_token_id)
    else:
        eos_ids = set()

    ended_with_eos = (
        generated_tokens > 0
        and generated_ids[-1].item() in eos_ids
    )

    raw_text = processor.decode(
        generated_ids,
        skip_special_tokens=True,
    )

    text = clean_ocr_text(raw_text)

    return {
        "raw_text": raw_text,
        "text": text,
        "tokens": generated_tokens,
        "ended_with_eos": ended_with_eos,
        "token_limit_reached": (
            generated_tokens >= MAX_NEW_TOKENS
        ),
    }


def get_quality_issues(result):
    """只根據 OCR 自身的輸出狀態檢查品質。"""

    issues = []

    if len(result["text"]) < MIN_OUTPUT_CHARS:
        issues.append("OCR output is unusually short")

    if result["token_limit_reached"]:
        issues.append("Generation reached the token limit")

    if not result["ended_with_eos"]:
        issues.append("Generation did not end with EOS")

    if not result["text"].strip():
        issues.append("OCR output is empty")

    return issues


def choose_result(first, retry):
    """依生成狀態選擇 OCR 結果，不比較原生 PDF 文字。"""

    first_status = (
        not first["token_limit_reached"],
        first["ended_with_eos"],
        bool(first["text"].strip()),
        len(first["text"]),
    )
    retry_status = (
        not retry["token_limit_reached"],
        retry["ended_with_eos"],
        bool(retry["text"].strip()),
        len(retry["text"]),
    )

    return retry if retry_status > first_status else first


def build_page_result(page_number, result):
    return {
        "page": page_number,
        "raw_text": result["raw_text"],
        "text": result["text"],
        "ocr_characters": len(result["text"]),
        "generated_tokens": result["tokens"],
        "ended_with_eos": result["ended_with_eos"],
        "token_limit_reached": result["token_limit_reached"],
        "review_reasons": get_quality_issues(result),
        "updated_at": utc_now(),
    }


def save_local_results(document_id, page_results, review_items):
    """保存每篇論文的 OCR 文字與檢查報告。"""

    output_dir = OUTPUT_ROOT / safe_directory_name(document_id)
    output_dir.mkdir(parents=True, exist_ok=True)

    page_results = sorted(
        page_results,
        key=lambda item: item["page"],
    )

    raw_sections = []
    clean_sections = []

    for item in page_results:
        raw_sections.append(
            f"===== PAGE {item['page']} =====\n"
            f"{item.get('raw_text', '').strip()}"
        )
        clean_sections.append(
            f"===== PAGE {item['page']} =====\n"
            f"{item.get('text', '').strip()}"
        )

    (output_dir / "ocr_raw.txt").write_text(
        "\n\n".join(raw_sections) + "\n",
        encoding="utf-8",
    )

    (output_dir / "ocr.txt").write_text(
        "\n\n".join(clean_sections) + "\n",
        encoding="utf-8",
    )

    review_lines = [
        "AutoSearch V9 - OCR Review Report",
        f"Document ID: {document_id}",
        "",
    ]

    if review_items:
        for item in review_items:
            review_lines.append(
                f"Page {item['page']}: {item['reason']}"
            )
    else:
        review_lines.append(
            "No pages triggered warning checks."
        )

    (output_dir / "ocr_review.txt").write_text(
        "\n".join(review_lines) + "\n",
        encoding="utf-8",
    )


def process_pdf(
    database,
    gridfs,
    candidate,
    model,
    processor,
    device,
    force=False,
):
    collection = database[COLLECTION_NAME]
    document_id = candidate["document_id"]
    pdf_file_id = candidate["pdf_file_id"]

    existing = collection.find_one({
        "document_id": document_id,
    }) or {}

    same_pdf = (
        str(existing.get("pdf_file_id")) == str(pdf_file_id)
    )

    if (
        existing.get("status") == "DONE"
        and same_pdf
        and existing.get("processed_pages", 0)
        == existing.get("total_pages", -1)
        and existing.get("total_pages", 0) > 0
        and existing.get("ocr_text", "").strip()
        and not force
    ):
        print(f"SKIP completed: {document_id}")
        return "SKIPPED"

    page_results = []

    if same_pdf and not force:
        page_results = existing.get("page_results", [])

    completed_pages = {
        item["page"]: item
        for item in page_results
        if item.get("page")
        and item.get("text") is not None
    }

    collection.update_one(
        {"document_id": document_id},
        {
            "$set": {
                "document_id": document_id,
                "pdf_file_id": pdf_file_id,
                "pdf_length": candidate["pdf_length"],
                "filename": candidate.get("filename"),
                "ocr_model": OCR_MODEL_NAME,
                "status": "PROCESSING",
                "started_at": utc_now(),
                "updated_at": utc_now(),
                "error": None,
            },
            "$setOnInsert": {
                "created_at": utc_now(),
            },
        },
        upsert=True,
    )

    try:
        pdf_bytes = gridfs.get(pdf_file_id).read()

        if not pdf_bytes:
            raise ValueError("Retrieved PDF is empty.")

        with pymupdf.open(
            stream=pdf_bytes,
            filetype="pdf",
        ) as pdf:
            total_pages = len(pdf)

            if total_pages == 0:
                raise ValueError("PDF contains no pages.")

            if (
                existing.get("total_pages") is not None
                and existing["total_pages"] != total_pages
            ):
                completed_pages = {}

            collection.update_one(
                {"document_id": document_id},
                {"$set": {
                    "total_pages": total_pages,
                    "updated_at": utc_now(),
                }},
            )

            for page_index, page in enumerate(pdf, start=1):
                if page_index in completed_pages:
                    print(
                        f"Resume page {page_index}/{total_pages}"
                    )
                    continue

                page_start = perf_counter()

                print(
                    f"\n[{document_id}] "
                    f"Page {page_index}/{total_pages}",
                    flush=True,
                )

                image = render_page(page, RENDER_SCALE)
                result = run_ocr(
                    model,
                    processor,
                    image,
                    device,
                )

                issues = get_quality_issues(result)

                if issues:
                    print(
                        "Retry: " + "; ".join(issues),
                        flush=True,
                    )

                    retry_image = render_page(
                        page,
                        RETRY_RENDER_SCALE,
                    )

                    retry_result = run_ocr(
                        model,
                        processor,
                        retry_image,
                        device,
                    )

                    result = choose_result(
                        result,
                        retry_result,
                    )

                completed_pages[page_index] = build_page_result(
                    page_index,
                    result,
                )

                ordered_results = sorted(
                    completed_pages.values(),
                    key=lambda item: item["page"],
                )

                review_items = [
                    {
                        "page": item["page"],
                        "reason": "; ".join(
                            item["review_reasons"]
                        ),
                    }
                    for item in ordered_results
                    if item.get("review_reasons")
                ]

                save_local_results(
                    document_id,
                    ordered_results,
                    review_items,
                )

                ocr_text = "\n\n".join(
                    f"===== PAGE {item['page']} =====\n"
                    f"{item.get('text', '').strip()}"
                    for item in ordered_results
                )

                ocr_raw_text = "\n\n".join(
                    f"===== PAGE {item['page']} =====\n"
                    f"{item.get('raw_text', '').strip()}"
                    for item in ordered_results
                )

                # 每頁完成後更新 MongoDB，支援中斷續跑。
                collection.update_one(
                    {"document_id": document_id},
                    {"$set": {
                        "page_results": ordered_results,
                        "processed_pages": len(ordered_results),
                        "ocr_text": ocr_text,
                        "ocr_raw_text": ocr_raw_text,
                        "review_items": review_items,
                        "updated_at": utc_now(),
                    }},
                )

                print(
                    f"Characters: {len(result['text'])}; "
                    f"elapsed: {perf_counter() - page_start:.2f}s",
                    flush=True,
                )

        ordered_results = sorted(
            completed_pages.values(),
            key=lambda item: item["page"],
        )

        review_items = [
            {
                "page": item["page"],
                "reason": "; ".join(item["review_reasons"]),
            }
            for item in ordered_results
            if item.get("review_reasons")
        ]

        all_pages_complete = (
            len(ordered_results) == total_pages
            and {
                item["page"] for item in ordered_results
            } == set(range(1, total_pages + 1))
        )

        all_pages_have_text = all(
            item.get("text", "").strip()
            for item in ordered_results
        )

        final_status = (
            "DONE"
            if all_pages_complete and all_pages_have_text
            else "FAILED"
        )

        collection.update_one(
            {"document_id": document_id},
            {"$set": {
                "status": final_status,
                "total_pages": total_pages,
                "processed_pages": len(ordered_results),
                "page_results": ordered_results,
                "ocr_text": "\n\n".join(
                    f"===== PAGE {item['page']} =====\n"
                    f"{item.get('text', '').strip()}"
                    for item in ordered_results
                ),
                "ocr_raw_text": "\n\n".join(
                    f"===== PAGE {item['page']} =====\n"
                    f"{item.get('raw_text', '').strip()}"
                    for item in ordered_results
                ),
                "review_items": review_items,
                "finished_at": utc_now(),
                "updated_at": utc_now(),
                "error": (
                    None
                    if final_status == "DONE"
                    else "Some pages are missing or have empty OCR output"
                ),
            }},
        )

        print(
            f"{final_status}: {document_id} "
            f"({len(ordered_results)}/{total_pages} pages)",
            flush=True,
        )

        return final_status

    except Exception as exc:
        collection.update_one(
            {"document_id": document_id},
            {"$set": {
                "status": "FAILED",
                "error": f"{type(exc).__name__}: {exc}",
                "updated_at": utc_now(),
            }},
        )

        print(
            f"FAILED: {document_id}: "
            f"{type(exc).__name__}: {exc}",
            flush=True,
        )

        return "FAILED"


def main():
    parser = argparse.ArgumentParser(
        description="AutoSearch V9 Paper OCR Pipeline"
    )
    parser.add_argument(
        "--document-id",
        help="Only process the specified document_id.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Reprocess completed OCR results.",
    )
    args = parser.parse_args()

    if not MODEL_PATH.is_dir():
        raise FileNotFoundError(
            f"Model directory not found: {MODEL_PATH}"
        )

    database = get_database()
    gridfs = GridFS(database)

    candidates = get_pdf_candidates(
        database,
        document_id=args.document_id,
    )

    if not candidates:
        print("No matching PDF files found in GridFS.")
        return

    device = "cuda" if torch.cuda.is_available() else "cpu"

    if device == "cpu":
        torch.set_num_threads(CPU_THREADS)
        dtype = torch.float32
    else:
        dtype = (
            torch.bfloat16
            if torch.cuda.is_bf16_supported()
            else torch.float16
        )

    print(f"PyTorch: {torch.__version__}")
    print(f"Device: {device}")

    if device == "cuda":
        print(f"GPU: {torch.cuda.get_device_name(0)}")

    print(f"PDF candidates: {len(candidates)}")
    print(f"MongoDB collection: {COLLECTION_NAME}")

    print("Loading OCR processor...")
    processor = AutoProcessor.from_pretrained(
        str(MODEL_PATH),
        local_files_only=True,
    )

    print("Loading OCR model...")
    model = AutoModelForImageTextToText.from_pretrained(
        str(MODEL_PATH),
        torch_dtype=dtype,
        local_files_only=True,
    ).to(device).eval()

    summary = {
        "DONE": 0,
        "FAILED": 0,
        "SKIPPED": 0,
    }

    for candidate in candidates:
        status = process_pdf(
            database=database,
            gridfs=gridfs,
            candidate=candidate,
            model=model,
            processor=processor,
            device=device,
            force=args.force,
        )
        summary[status] = summary.get(status, 0) + 1

    print("\n===== PAPER OCR SUMMARY =====")
    print(f"Candidates: {len(candidates)}")
    print(f"Completed: {summary['DONE']}")
    print(f"Failed: {summary['FAILED']}")
    print(f"Skipped: {summary['SKIPPED']}")
    print(f"Local output: {OUTPUT_ROOT}")


if __name__ == "__main__":
    main()
