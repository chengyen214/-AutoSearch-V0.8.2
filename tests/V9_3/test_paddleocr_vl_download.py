from huggingface_hub import snapshot_download

snapshot_download(
    repo_id="PaddlePaddle/PaddleOCR-VL-1.6",
    local_dir="D:/AI_Models/PaddleOCR-VL-1.6",
)

print("Model download completed.")