# colab_api.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import logging

# Giả lập RAGService đơn giản cho demo
class DummyRAGService:
    def __init__(self):
        self.conversation_history = []

    def gemini_service(self):
        return self

    def enhance_query_with_history(self, msg):
        return msg

    def build_promt_intent(self, msg):
        return "GENERAL_QUESTION" if "gì" in msg else "SPECIFIC_PRODUCT"

    def identify_key_for_filter(self, msg):
        return {"brand": "hasaki"}

    def query(self, msg, filters=None, rerank_top_k=5, top_k=20):
        return {
            "success": True,
            "answer": f"Câu trả lời cho: {msg}",
            "id_product": "123",
            "name_product": "Kem dưỡng Hasaki"
        }

    def append_to_conversation(self, q, a, i, pid=None, pname=None):
        self.conversation_history.append((q, a, i))


# Cấu hình FastAPI và logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Colab RAG Chatbot")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

rag_service = DummyRAGService()

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default"

class ChatResponse(BaseModel):
    success: bool
    answer: str
    intent: Optional[str] = None
    id_product: Optional[str] = None
    name_product: Optional[str] = None
    error: Optional[str] = None

@app.get("/")
async def root():
    return {"message": "🌐 Colab RAG API đang hoạt động!"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        msg = request.message.strip()
        if not msg:
            return ChatResponse(success=False, answer="Vui lòng nhập câu hỏi!", error="Empty message")
        
        query = rag_service.enhance_query_with_history(msg)
        intent = rag_service.build_promt_intent(query)
        filters = rag_service.identify_key_for_filter(query) if intent == "SPECIFIC_PRODUCT" else None
        result = rag_service.query(query, filters=filters)

        rag_service.append_to_conversation(query, result["answer"], intent)

        return ChatResponse(
            success=True,
            answer=result["answer"],
            intent=intent,
            id_product=result.get("id_product"),
            name_product=result.get("name_product")
        )
    except Exception as e:
        return ChatResponse(success=False, answer="Lỗi hệ thống", error=str(e))

@app.post("/clear-history")
async def clear_history():
    rag_service.conversation_history = []
    return {"success": True, "message": "Lịch sử đã được xóa"}