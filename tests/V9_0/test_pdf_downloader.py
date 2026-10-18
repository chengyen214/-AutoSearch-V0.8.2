"""
tests/V9_0/test_pdf_downloader.py

AutoSearch V5

V9_0 PDF Downloader Real Test
"""

from pathlib import Path

from paper.pdf_downloader import (
    download_pdf,
)


PDF_URL = (
    "https://link.springer.com/"
    "content/pdf/10.1007/s00034-026-03814-w.pdf"
)

OUTPUT_DIR = Path(
    "tests/V9_0/output"
)

OUTPUT_FILE = (
    OUTPUT_DIR / "paper.pdf"
)


def main():
    print("=" * 60)
    print("V9_0 PDF Downloader Real Test")
    print("=" * 60)

    print()
    print(f"PDF URL: {PDF_URL}")

    print()
    print("[1] Browser PDF Download")

    result = download_pdf(
        PDF_URL,
        timeout=30,
        headless=True,
    )

    print()
    print(f"Success: {result.success}")
    print(f"Status Code: {result.status_code}")
    print(f"Final URL: {result.final_url}")
    print(f"Content Type: {result.content_type}")
    print(f"Content Size: {result.content_size}")
    print(f"Content Hash: {result.content_hash}")
    print(f"Elapsed Time: {result.elapsed_time:.2f}s")
    print(f"Error: {result.error}")

    if result.content:
        print(
            f"PDF Header: "
            f"{result.content[:8]}"
        )

    if result.success:
        OUTPUT_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        OUTPUT_FILE.write_bytes(
            result.content
        )

        print()
        print("[2] Save PDF")
        print(f"Saved File: {OUTPUT_FILE}")
        print(
            f"Saved Size: "
            f"{OUTPUT_FILE.stat().st_size}"
        )

    print()
    print("=" * 60)

    if result.success:
        print(
            "PDF Downloader Real Test: PASS"
        )
    else:
        print(
            "PDF Downloader Real Test: FAIL"
        )

    print("=" * 60)


if __name__ == "__main__":
    main()