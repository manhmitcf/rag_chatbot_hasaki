import os
import torch
from dotenv import load_dotenv

load_dotenv()

# MongoDB Configuration
MONGODB_USERNAME = os.getenv("MONGODB_USERNAME")
MONGODB_PASSWORD = os.getenv("MONGODB_PASSWORD")
MONGODB_HOST = os.getenv("MONGODB_HOST")
MONGODB_PORT = int(os.getenv("MONGODB_PORT", 27017))
MONGODB_AUTH_SOURCE = os.getenv("MONGODB_AUTH_SOURCE", "admin")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION")

# MongoDB URI (chỉ tạo nếu có đủ thông tin)
MONGODB_URI = None
if MONGODB_USERNAME and MONGODB_PASSWORD and MONGODB_HOST:
    MONGODB_URI = (
        f"mongodb://{MONGODB_USERNAME}:{MONGODB_PASSWORD}"
        f"@{MONGODB_HOST}:{MONGODB_PORT}/?authSource={MONGODB_AUTH_SOURCE}"
    )

# Qdrant Configuration
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
QDRANT_COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "vectordb")

# Embedding Model Configuration
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "bkai-foundation-models/vietnamese-bi-encoder")
EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", 768))

# GPU Configuration
USE_GPU = os.getenv("USE_GPU", "auto").lower()  # auto, true, false
GPU_DEVICE_ID = int(os.getenv("GPU_DEVICE_ID", 0))

# Auto-detect GPU availability
def get_device():
    """Tự động phát hiện và trả về device tốt nhất"""
    if USE_GPU == "false":
        return "cpu"
    elif USE_GPU == "true":
        if torch.cuda.is_available():
            return f"cuda:{GPU_DEVICE_ID}"
        else:
            print("GPU được yêu cầu nhưng không khả dụng, sử dụng CPU")
            return "cpu"
    else:  # auto
        if torch.cuda.is_available():
            device = f"cuda:{GPU_DEVICE_ID}"
            print(f"Phát hiện GPU: {torch.cuda.get_device_name(GPU_DEVICE_ID)}")
            return device
        else:
            print("Không phát hiện GPU, sử dụng CPU")
            return "cpu"

DEVICE = get_device()

# Text Splitter Configuration
DEFAULT_CHUNK_SIZE = int(os.getenv("DEFAULT_CHUNK_SIZE", 500))
DEFAULT_OVERLAP = int(os.getenv("DEFAULT_OVERLAP", 100))
MARKDOWN_CHUNK_SIZE = int(os.getenv("MARKDOWN_CHUNK_SIZE", 800))
MARKDOWN_OVERLAP = int(os.getenv("MARKDOWN_OVERLAP", 150))

# Processing Configuration
MAX_PRODUCTS_LIMIT = int(os.getenv("MAX_PRODUCTS_LIMIT", 50))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", 100))
UPLOAD_BATCH_SIZE = int(os.getenv("UPLOAD_BATCH_SIZE", 50))

# GPU-specific batch sizes
if DEVICE.startswith("cuda"):
    # Tăng batch size khi sử dụng GPU
    EMBEDDING_BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", 64))
    RERANK_BATCH_SIZE = int(os.getenv("RERANK_BATCH_SIZE", 32))
else:
    # Batch size nhỏ hơn cho CPU
    EMBEDDING_BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", 16))
    RERANK_BATCH_SIZE = int(os.getenv("RERANK_BATCH_SIZE", 8))