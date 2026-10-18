"""
rag/paddleocr_text_loader.py

AutoSearch V9

PaddleOCR-VL-1.6 OCR Text Loader

用途：
    讀取 PaddleOCR-VL-1.6 已完成的 OCR 文字結果，
    提供 Paper Chunking Pipeline 使用。
"""

from pathlib import Path


DEFAULT_OCR_PATH = Path(
    r"D:\AI_Models\cardioneural_soc_ocr.txt"
)


class PaddleOCRTextLoader:
    """讀取 PaddleOCR-VL-1.6 輸出的文字檔。"""

    def __init__(self, file_path=DEFAULT_OCR_PATH):
        self.file_path = Path(file_path)

    def load(self):
        """讀取完整 OCR 文字。"""

        if not self.file_path.is_file():
            raise FileNotFoundError(
                f"OCR text file not found: {self.file_path}"
            )

        text = self.file_path.read_text(
            encoding="utf-8"
        )

        text = text.strip()

        if not text:
            raise ValueError(
                f"OCR text file is empty: {self.file_path}"
            )

        return text

    def get_document(self, document_id, metadata=None):
        """建立供後續 Chunking 使用的文件資料。"""

        text = self.load()

        document_metadata = {
            "document_id": document_id,
            "source_type": "paddleocr_vl_1_6",
            "source_file": self.file_path.name,
        }

        if metadata:
            document_metadata.update(metadata)

        return {
            "document_id": document_id,
            "text": text,
            "metadata": document_metadata,
        }


def main():
    loader = PaddleOCRTextLoader()

    document = loader.get_document(
        document_id="openalex:W7221469030",
        metadata={
            "title": (
                "CardioNeural-SoC: An Indigenous "
                "RISC-V-Based Mixed-Signal System-on-Chip"
            ),
            "doi": "10.21203/rs.3.rs-10838876/v1",
        },
    )

    print("===== PaddleOCR Text Loader =====")
    print(f"Document ID: {document['document_id']}")
    print(f"Source: {document['metadata']['source_type']}")
    print(f"Characters: {len(document['text']):,}")
    print(f"Source file: {document['metadata']['source_file']}")
    print("\n===== Preview =====")
    print(document["text"][:1000])


if __name__ == "__main__":
    main()
