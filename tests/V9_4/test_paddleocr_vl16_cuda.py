import torch
from transformers import AutoModelForImageTextToText, AutoProcessor

MODEL_PATH = r"D:\AI_Models\PaddleOCR-VL-1.6"


def main():
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA 不可用，無法執行 GPU 測試。")

    print(f"PyTorch: {torch.__version__}")
    print(f"CUDA: {torch.version.cuda}")
    print(f"GPU: {torch.cuda.get_device_name(0)}")

    print("\nLoading processor...")
    processor = AutoProcessor.from_pretrained(
        MODEL_PATH,
        trust_remote_code=False,
        local_files_only=True,
    )
    print("Processor loaded.")

    print("\nLoading model...")
    model = AutoModelForImageTextToText.from_pretrained(
        MODEL_PATH,
        trust_remote_code=False,
        local_files_only=True,
        dtype=torch.float16,
        low_cpu_mem_usage=True,
    )
    model = model.to("cuda").eval()

    print("\nModel loaded successfully.")
    print(f"Model device: {next(model.parameters()).device}")
    print(f"Model dtype: {next(model.parameters()).dtype}")
    print(
        f"GPU memory allocated: "
        f"{torch.cuda.memory_allocated(0) / 1024**3:.2f} GB"
    )
    print(
        f"GPU memory reserved: "
        f"{torch.cuda.memory_reserved(0) / 1024**3:.2f} GB"
    )


if __name__ == "__main__":
    main()