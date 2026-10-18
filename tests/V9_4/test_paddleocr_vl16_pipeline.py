"""
tests/V9_4/test_paddleocr_vl16_pipeline.py

AutoSearch V9

PaddleOCR-VL-1.6 Official Pipeline Test
"""

from pathlib import Path

import torch
from paddleocr import PaddleOCRVL


INPUT_PATH = Path(r"D:\AI_Models\test_page.png")
OUTPUT_PATH = Path(r"D:\AI_Models\paddleocr_vl16_pipeline_result")

def main():
    if not INPUT_PATH.is_file():
        raise FileNotFoundError(f"Test image not found: {INPUT_PATH}")

    OUTPUT_PATH.mkdir(parents=True, exist_ok=True)

    pipeline = PaddleOCRVL(
        pipeline_version="v1.6",
    )

    results = pipeline.predict(input=str(INPUT_PATH))

    for index, result in enumerate(results, start=1):
        print(f"Saving result {index}...")
        result.save_to_json(save_path=str(OUTPUT_PATH))
        result.save_to_markdown(save_path=str(OUTPUT_PATH))
        result.print()

    print(f"Results saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()