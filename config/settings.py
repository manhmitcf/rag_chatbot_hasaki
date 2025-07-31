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
    EMBEDDING_BATCH_SIZE = 32

    # MODEL RERANKER
    MODEL_RERANKER = "BAAI/bge-reranker-v2-m3"
    
    # Search Configuration
    SEMANTIC_SEARCH_LIMIT = int(os.getenv("SEMANTIC_SEARCH_LIMIT", 50))
    RERANK_TOP_K = int(os.getenv("RERANK_TOP_K", 20))
    CONTEXT_TOP_K = int(os.getenv("CONTEXT_TOP_K", 8))
    
    # RAG Configuration
    CONVERSATION_MEMORY_K = int(os.getenv("CONVERSATION_MEMORY_K", 3))
    LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", 20))
    LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", 0.1))

settings = Settings()

# Export constants for backward compatibility
EMBEDDING_BATCH_SIZE = settings.EMBEDDING_BATCH_SIZE