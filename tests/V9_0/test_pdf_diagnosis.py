"""
tests/V9_0/test_pdf_diagnosis.py

AutoSearch V5

V9_0 PDF Download Diagnosis
"""

from playwright.sync_api import (
    sync_playwright,
)


PDF_URL = (
    "https://link.springer.com/"
    "content/pdf/10.1007/s00034-026-03814-w.pdf"
)


def main():
    print("=" * 60)
    print("V9_0 PDF Download Diagnosis")
    print("=" * 60)

    print()
    print(f"PDF URL: {PDF_URL}")

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=False,
        )

        context = browser.new_context(
            accept_downloads=True,
        )

        page = context.new_page()

        def on_request(request):
            if ".pdf" in request.url.lower():
                print()
                print("[REQUEST]")
                print(f"URL: {request.url}")
                print(f"Method: {request.method}")
                print(f"Resource Type: {request.resource_type}")

        def on_response(response):
            if ".pdf" in response.url.lower():
                print()
                print("[RESPONSE]")
                print(f"URL: {response.url}")
                print(f"Status: {response.status}")
                print(
                    "Content-Type: "
                    f"{response.headers.get('content-type', '')}"
                )
                print(
                    "Content-Disposition: "
                    f"{response.headers.get('content-disposition', '')}"
                )
                print(
                    "Content-Length: "
                    f"{response.headers.get('content-length', '')}"
                )

        def on_request_failed(request):
            if ".pdf" in request.url.lower():
                print()
                print("[REQUEST FAILED]")
                print(f"URL: {request.url}")
                print(f"Failure: {request.failure}")

        def on_download(download):
            print()
            print("[DOWNLOAD EVENT]")
            print(f"URL: {download.url}")
            print(
                "Suggested Filename: "
                f"{download.suggested_filename}"
            )

            try:
                path = download.path()
                print(f"Download Path: {path}")
            except Exception as e:
                print(f"Download Path Error: {e}")

        page.on(
            "request",
            on_request,
        )

        page.on(
            "response",
            on_response,
        )

        page.on(
            "requestfailed",
            on_request_failed,
        )

        page.on(
            "download",
            on_download,
        )

        print()
        print("[1] Browser Navigation")

        try:
            page.goto(
                PDF_URL,
                timeout=30000,
                wait_until="commit",
            )
        except Exception as e:
            print()
            print("[GOTO ERROR]")
            print(type(e).__name__)
            print(str(e))

        print()
        print("[2] Browser State")
        print(f"Page URL: {page.url}")

        print()
        print("[3] Waiting")

        page.wait_for_timeout(
            5000
        )

        print()
        print("[4] Final Browser State")
        print(f"Page URL: {page.url}")

        context.close()
        browser.close()

    print()
    print("=" * 60)
    print("PDF Download Diagnosis Complete")
    print("=" * 60)


if __name__ == "__main__":
    main()