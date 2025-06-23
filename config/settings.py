import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Gemini API
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    
    # Qdrant Configuration
    QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
    QDRANT_COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "vectordb")
    
    # Server Configuration
    SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
    SERVER_PORT = int(os.getenv("SERVER_PORT", 8000))
    
    # Embedding Model
    EMBEDDING_MODEL = "bkai-foundation-models/vietnamese-bi-encoder"
    EMBEDDING_DIMENSION = 768

    # MODEL RẺANKER
    MODEL_RERANKER = "BAAI/bge-reranker-v2-m3"

settings = Settings()