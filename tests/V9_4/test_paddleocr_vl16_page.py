
"""
tests/V9_4/test_paddleocr_vl16_page.py

AutoSearch V9

PaddleOCR-VL-1.6 Single Page OCR Test
"""

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
DOCUMENT_ID = "openalex:W7221469030"
PAGE_NUMBER = 14
RENDER_SCALE = 2.5
MAX_NEW_TOKENS = 2048
CPU_THREADS = 8

OUTPUT_PATH = Path(
    r"D:\AI_Models\cardioneural_soc_page14_retry.txt"
)

OCR_PROMPT = (
    "Transcribe all visible text on this PDF page. "
    "This page contains a technical figure and its caption. "
    "Pay special attention to figure captions, labels, "
    "annotations, technical terms, and text near the bottom "
    "of the page. Preserve the original reading order. "
    "Do not summarize, translate, or invent text. "
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

    pdf_bytes = gridfs.get(file_info["_id"]).read()

    if not pdf_bytes:
        raise ValueError("Retrieved PDF is empty.")

    print(f"GridFS file ID: {file_info['_id']}")
    print(f"PDF size: {len(pdf_bytes):,} bytes")

    return pdf_bytes


def main():
    if not MODEL_PATH.is_dir():
        raise FileNotFoundError(
            f"Model directory not found: {MODEL_PATH}"
        )

    device = "cuda" if torch.cuda.is_available() else "cpu"

    if device == "cpu":
        torch.set_num_threads(CPU_THREADS)

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

        if not 1 <= PAGE_NUMBER <= total_pages:
            raise ValueError(
                f"Page {PAGE_NUMBER} is outside the PDF range "
                f"of 1-{total_pages}."
            )

        page = pdf[PAGE_NUMBER - 1]

        print(f"Page: {PAGE_NUMBER}/{total_pages}")
        print("Native PDF text:")
        print(page.get_text())

        pixmap = page.get_pixmap(
            matrix=pymupdf.Matrix(
                RENDER_SCALE,
                RENDER_SCALE,
            ),
            alpha=False,
        )

        image = Image.frombytes(
            "RGB",
            (pixmap.width, pixmap.height),
            pixmap.samples,
        )

        print(
            f"Image size: {image.width} x {image.height}"
        )

        dtype = (
            torch.float16
            if device == "cuda"
            else torch.float32
        )

        print("Loading processor...", flush=True)

        processor = AutoProcessor.from_pretrained(
            str(MODEL_PATH),
            trust_remote_code=False,
            local_files_only=True,
        )

        print("Loading model...", flush=True)
        load_start = perf_counter()

        model = AutoModelForImageTextToText.from_pretrained(
            str(MODEL_PATH),
            trust_remote_code=False,
            local_files_only=True,
            dtype=dtype,
            low_cpu_mem_usage=True,
        ).to(device).eval()

        print(
            f"Model loading time: "
            f"{perf_counter() - load_start:.2f}s"
        )

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

        print("Running single-page OCR...", flush=True)
        start = perf_counter()

        with torch.inference_mode():
            outputs = model.generate(
                **inputs,
                max_new_tokens=MAX_NEW_TOKENS,
                do_sample=False,
                use_cache=True,
            )

        if device == "cuda":
            torch.cuda.synchronize()

        elapsed = perf_counter() - start

        result = processor.decode(
            outputs[0, input_length:],
            skip_special_tokens=True,
        ).strip()

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_PATH.write_text(
        result + "\n",
        encoding="utf-8",
    )

    print("\n===== PAGE 14 RETRY RESULT =====")
    print(result)
    print(f"\nCharacters: {len(result)}")
    print(f"Elapsed: {elapsed:.2f}s")
    print(f"Saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
