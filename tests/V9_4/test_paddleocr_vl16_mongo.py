
"""
tests/V9_4/test_paddleocr_vl16_mongo.py

AutoSearch V9

PaddleOCR-VL-1.6 Full PDF OCR
"""

import re
import unicodedata
from difflib import SequenceMatcher
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

RAW_OUTPUT_PATH = Path(
    r"D:\AI_Models\cardioneural_soc_ocr_raw.txt"
)
OUTPUT_PATH = Path(
    r"D:\AI_Models\cardioneural_soc_ocr.txt"
)
REVIEW_PATH = Path(
    r"D:\AI_Models\cardioneural_soc_ocr_review.txt"
)

DOCUMENT_ID = "openalex:W7221469030"

RENDER_SCALE = 1.5
RETRY_RENDER_SCALE = 2.5

MAX_NEW_TOKENS = 2048
CPU_THREADS = 8

MIN_OUTPUT_CHARS = 80
MIN_NATIVE_COMPARE_CHARS = 80
MIN_NATIVE_TEXT_CHARS = 200
MIN_NATIVE_TEXT_RATIO = 0.45
OCR_SIMILARITY_THRESHOLD = 0.80

OCR_PROMPT = (
    "Transcribe all visible text on this PDF page as completely "
    "and accurately as possible. Include the title, headings, "
    "paragraphs, captions, figure labels, table contents, "
    "footnotes, references, page numbers, mathematical formulas, "
    "symbols, and text inside diagrams. "
    "Preserve the original reading order and paragraph structure. "
    "Do not summarize, translate, explain, or invent text. "
    "Do not omit short words, punctuation, numbers, or text near "
    "the edges of the page. "
    "Return only the transcription."
)


def get_pdf_bytes(document_id):
    """從 MongoDB GridFS 取得論文 PDF。"""

    database = get_mongo_database()
    gridfs = GridFS(database)

    file_info = database["fs.files"].find_one(
        {
            "metadata.document_id": document_id,
            "contentType": "application/pdf",
        },
        sort=[("uploadDate", -1)],
    )

    if file_info is None:
        file_info = database["fs.files"].find_one(
            {"metadata.document_id": document_id},
            sort=[("uploadDate", -1)],
        )

    if file_info is None:
        raise FileNotFoundError(
            f"No GridFS PDF found for document_id={document_id}"
        )

    pdf_file = gridfs.get(file_info["_id"])
    pdf_bytes = pdf_file.read()

    if not pdf_bytes:
        raise ValueError("Retrieved PDF is empty.")

    print(f"GridFS file ID: {file_info['_id']}")
    print(f"PDF size: {len(pdf_bytes):,} bytes")

    return pdf_bytes


def render_page(page, scale):
    """將 PDF 頁面轉成 OCR 使用的 RGB 圖片。"""

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
    """只移除模型 LOC 標記，不過濾一般文字。"""

    return re.sub(r"<\|LOC_\d+\|>", "", text).strip()


def normalize_for_comparison(text):
    """只建立比較用文字，不修改實際 OCR 輸出。"""

    text = unicodedata.normalize("NFKC", text).casefold()

    return "".join(
        char
        for char in text
        if char.isalnum()
    )


def compare_native_and_ocr(native_text, ocr_text):
    """比較 PDF 原生文字與 OCR 文字的字元序列相似度。"""

    native = normalize_for_comparison(native_text)
    ocr = normalize_for_comparison(ocr_text)

    if len(native) < MIN_NATIVE_COMPARE_CHARS:
        return {
            "comparable": False,
            "similarity": None,
            "reason": "Native PDF text is insufficient",
        }

    if not ocr:
        return {
            "comparable": True,
            "similarity": 0.0,
            "reason": "OCR output is empty",
        }

    similarity = SequenceMatcher(
        None,
        native,
        ocr,
        autojunk=False,
    ).ratio()

    return {
        "comparable": True,
        "similarity": similarity,
        "reason": (
            "Similar"
            if similarity >= OCR_SIMILARITY_THRESHOLD
            else "Text differs from native PDF text"
        ),
    }


def run_ocr(model, processor, image, device):
    """辨識單頁並回傳文字及生成狀態。"""

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": image},
                {"type": "text", "text": OCR_PROMPT},
            ],
        }
    ]

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


def get_native_text(page):
    """取得 PDF 原生文字層。"""

    return page.get_text("text").strip()


def get_quality_issues(result, native_text):
    """回傳需要重試或人工檢查的原因。"""

    issues = []

    if len(result["text"]) < MIN_OUTPUT_CHARS:
        issues.append("OCR output is unusually short")

    if result["token_limit_reached"]:
        issues.append("Generation reached the token limit")

    if not result["ended_with_eos"]:
        issues.append("Generation did not end with EOS")

    native_length = len(
        normalize_for_comparison(native_text)
    )
    ocr_length = len(
        normalize_for_comparison(result["text"])
    )

    if (
        native_length >= MIN_NATIVE_TEXT_CHARS
        and ocr_length < native_length * MIN_NATIVE_TEXT_RATIO
    ):
        issues.append(
            "OCR output is much shorter than native PDF text"
        )

    comparison = compare_native_and_ocr(
        native_text,
        result["text"],
    )

    if comparison["comparable"]:
        if (
            comparison["similarity"]
            < OCR_SIMILARITY_THRESHOLD
        ):
            issues.append(
                "Native/OCR similarity is low: "
                f"{comparison['similarity']:.1%}"
            )

    return issues, comparison


def choose_result(first, retry, native_text):
    """依原生文字相似度選擇結果；不可比較時使用輔助指標。"""

    first_cmp = compare_native_and_ocr(
        native_text,
        first["text"],
    )
    retry_cmp = compare_native_and_ocr(
        native_text,
        retry["text"],
    )

    if first_cmp["comparable"] and retry_cmp["comparable"]:
        first_score = first_cmp["similarity"]
        retry_score = retry_cmp["similarity"]

        print(
            f"Initial similarity: {first_score:.1%}"
        )
        print(
            f"Retry similarity: {retry_score:.1%}"
        )

        if retry_score > first_score:
            return retry

        if first_score > retry_score:
            return first

        # 相似度相同時，優先選擇未達生成上限且正常結束的結果。
        first_status = (
            not first["token_limit_reached"],
            first["ended_with_eos"],
        )
        retry_status = (
            not retry["token_limit_reached"],
            retry["ended_with_eos"],
        )

        if retry_status > first_status:
            return retry

        return first

    # 原生文字不可用時，不能用相似度決定哪份 OCR 正確。
    # 只用生成狀態與文字長度作為保守的輔助判斷。
    first_status = (
        not first["token_limit_reached"],
        first["ended_with_eos"],
    )
    retry_status = (
        not retry["token_limit_reached"],
        retry["ended_with_eos"],
    )

    if retry_status > first_status:
        return retry

    if first_status > retry_status:
        return first

    if len(retry["text"]) > len(first["text"]):
        return retry

    return first


def save_results(page_results, review_items):
    """儲存已完成頁面與檢查報告。"""

    RAW_OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    raw_sections = []
    clean_sections = []

    for item in page_results:
        page_number = item["page"]

        raw_sections.append(
            f"===== PAGE {page_number} =====\n"
            f"{item['raw_text'].strip()}"
        )
        clean_sections.append(
            f"===== PAGE {page_number} =====\n"
            f"{item['text'].strip()}"
        )

    RAW_OUTPUT_PATH.write_text(
        "\n\n".join(raw_sections) + "\n",
        encoding="utf-8",
    )

    OUTPUT_PATH.write_text(
        "\n\n".join(clean_sections) + "\n",
        encoding="utf-8",
    )

    review_lines = [
        "AutoSearch V9 - OCR Review Report",
        f"Document ID: {DOCUMENT_ID}",
        "",
    ]

    if review_items:
        for item in review_items:
            review_lines.append(
                f"Page {item['page']}: {item['reason']}"
            )
    else:
        review_lines.append(
            "No pages triggered the configured warning checks."
        )

    REVIEW_PATH.write_text(
        "\n".join(review_lines) + "\n",
        encoding="utf-8",
    )


def main():
    if not MODEL_PATH.is_dir():
        raise FileNotFoundError(
            f"Model directory not found: {MODEL_PATH}"
        )

    device = "cuda" if torch.cuda.is_available() else "cpu"

    if device == "cpu":
        torch.set_num_threads(CPU_THREADS)

    if device == "cuda":
        dtype = (
            torch.bfloat16
            if torch.cuda.is_bf16_supported()
            else torch.float16
        )
    else:
        dtype = torch.float32

    print(f"PyTorch: {torch.__version__}")
    print(f"Device: {device}")

    if device == "cuda":
        print(f"GPU: {torch.cuda.get_device_name(0)}")

    pdf_bytes = get_pdf_bytes(DOCUMENT_ID)

    with pymupdf.open(
        stream=pdf_bytes,
        filetype="pdf",
    ) as pdf:
        total_pages = len(pdf)

        if total_pages == 0:
            raise ValueError("PDF contains no pages.")

        print(f"PDF pages: {total_pages}")

        processor = AutoProcessor.from_pretrained(
            str(MODEL_PATH),
            local_files_only=True,
        )

        model = AutoModelForImageTextToText.from_pretrained(
            str(MODEL_PATH),
            torch_dtype=dtype,
            local_files_only=True,
        ).to(device).eval()

        page_results = []
        review_items = []
        total_start = perf_counter()

        for page_index, page in enumerate(pdf, start=1):
            page_start = perf_counter()

            print(
                f"\n===== PAGE {page_index}/{total_pages} =====",
                flush=True,
            )

            native_text = get_native_text(page)

            print(
                f"Native PDF text: {len(native_text)} characters"
            )

            image = render_page(page, RENDER_SCALE)

            result = run_ocr(
                model,
                processor,
                image,
                device,
            )

            issues, comparison = get_quality_issues(
                result,
                native_text,
            )

            if comparison["comparable"]:
                print(
                    "Initial native/OCR similarity: "
                    f"{comparison['similarity']:.1%}"
                )
            else:
                print(
                    "Native/OCR comparison skipped: "
                    f"{comparison['reason']}"
                )

            if issues:
                print(
                    "Retry required: " + "; ".join(issues),
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
                    native_text,
                )

                final_issues, final_comparison = (
                    get_quality_issues(
                        result,
                        native_text,
                    )
                )

                if final_issues:
                    review_items.append(
                        {
                            "page": page_index,
                            "reason": "; ".join(final_issues),
                        }
                    )
                elif not final_comparison["comparable"]:
                    review_items.append(
                        {
                            "page": page_index,
                            "reason": (
                                "Native text unavailable; "
                                "OCR completeness cannot be verified "
                                "by direct text comparison"
                            ),
                        }
                    )
            elif not comparison["comparable"]:
                review_items.append(
                    {
                        "page": page_index,
                        "reason": (
                            "Native text unavailable; "
                            "OCR completeness cannot be verified "
                            "by direct text comparison"
                        ),
                    }
                )

            if not result["text"]:
                review_items.append(
                    {
                        "page": page_index,
                        "reason": "OCR output is empty",
                    }
                )

            page_results.append(
                {
                    "page": page_index,
                    "raw_text": result["raw_text"],
                    "text": result["text"],
                }
            )

            save_results(page_results, review_items)

            print(
                f"Final characters: {len(result['text'])}"
            )
            print(f"Generated tokens: {result['tokens']}")
            print(f"Ended with EOS: {result['ended_with_eos']}")
            print(
                f"Page elapsed: "
                f"{perf_counter() - page_start:.2f}s"
            )
            print("Page saved.", flush=True)

        total_elapsed = perf_counter() - total_start

    print("\n===== OCR SUMMARY =====")
    print(
        f"Pages processed: {len(page_results)}/{total_pages}"
    )
    print(
        "Total OCR characters: "
        f"{sum(len(item['text']) for item in page_results):,}"
    )
    print(f"Pages requiring review: {len(review_items)}")
    print(f"Total elapsed: {total_elapsed:.2f}s")
    print(f"Raw OCR: {RAW_OUTPUT_PATH}")
    print(f"Clean OCR: {OUTPUT_PATH}")
    print(f"Review report: {REVIEW_PATH}")


if __name__ == "__main__":
    main()
