#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FastAPI Server cho RAG Chatbot
API endpoint để tương tác với chatbot tư vấn mỹ phẩm
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uvicorn
import logging
from services.rag_service import RAGService

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Khởi tạo FastAPI app
app = FastAPI(
    title="Hasaki RAG Chatbot API",
    description="API cho chatbot tư vấn mỹ phẩm sử dụng RAG (Retrieval-Augmented Generation)",
    version="1.0.0"
)

# Cấu hình CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Khởi tạo RAG Service (global variable)
rag_service = None

class ChatRequest(BaseModel):
    """Model cho request chat"""
    message: str
    session_id: Optional[str] = "default"

class ChatResponse(BaseModel):
    """Model cho response chat"""
    success: bool
    answer: str
    intent: Optional[str] = None
    id_product: Optional[str] = None
    name_product: Optional[str] = None
    error: Optional[str] = None

@app.on_event("startup")
async def startup_event():
    """Khởi tạo RAG Service khi server start"""
    global rag_service
    try:
        logger.info("Đang khởi tạo RAG Service...")
        rag_service = RAGService(use_rerank=True)
        logger.info("RAG Service đã sẵn sàng!")
    except Exception as e:
        logger.error(f"Lỗi khởi tạo RAG Service: {str(e)}")
        raise e

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Hasaki RAG Chatbot API đang hoạt động!",
        "status": "healthy",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Kiểm tra trạng thái hệ thống"""
    global rag_service
    
    if rag_service is None:
        return {
            "status": "unhealthy",
            "message": "RAG Service chưa được khởi tạo"
        }
    
    return {
        "status": "healthy",
        "message": "Tất cả dịch vụ đang hoạt động bình thường",
        "rag_service": "ready"
    }

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Endpoint chính để chat với bot
    
    Args:
        request: ChatRequest chứa message và session_id
        
    Returns:
        ChatResponse với câu trả lời và thông tin liên quan
    """
    global rag_service
    
    if rag_service is None:
        raise HTTPException(
            status_code=503, 
            detail="RAG Service chưa sẵn sàng. Vui lòng thử lại sau."
        )
    
    try:
        user_input = request.message.strip()
        
        if not user_input:
            return ChatResponse(
                success=False,
                answer="Vui lòng nhập câu hỏi của bạn!",
                error="Empty message"
            )
        
        logger.info(f"Nhận câu hỏi: {user_input}")
        
        # Tăng cường query với lịch sử hội thoại
        enhanced_query = rag_service.gemini_service.enhance_query_with_history(user_input)
        
        # Phân tích ý định
        intent = rag_service.gemini_service.build_promt_intent(enhanced_query)
        logger.info(f"Phân loại: {intent}")
        
        # Xử lý theo ý định
        if intent == "SPECIFIC_PRODUCT":
            # Xác định filter cho sản phẩm cụ thể
            filters = rag_service.gemini_service.identify_key_for_filter(enhanced_query)
            logger.info(f"Filters được tạo: {filters}")
            
            # Thử tìm kiếm với filter trước
            result = rag_service.query(enhanced_query, filters=filters, rerank_top_k=5, top_k=20)
            
            # Nếu không tìm thấy kết quả với filter, thử không filter
            if result["success"] and result["answer"] == "Xin lỗi, tôi không tìm thấy thông tin phù hợp để trả lời câu hỏi của bạn.":
                logger.info("Không tìm thấy với filter, thử tìm kiếm không filter...")
                result = rag_service.query(enhanced_query, filters=None, rerank_top_k=5, top_k=20)
            
            if result["success"]:
                # Lưu vào lịch sử hội thoại
                rag_service.gemini_service.append_to_conversation(
                    enhanced_query, 
                    result["answer"], 
                    intent,
                    result.get("id_product"),
                    result.get("name_product")
                )
                
                return ChatResponse(
                    success=True,
                    answer=result["answer"],
                    intent=intent,
                    id_product=result.get("id_product"),
                    name_product=result.get("name_product")
                )
            else:
                rag_service.gemini_service.append_to_conversation(
                    enhanced_query, 
                    result["answer"], 
                    intent
                )
                
                return ChatResponse(
                    success=False,
                    answer=result["answer"],
                    intent=intent,
                    error="No relevant information found"
                )
        
        elif intent == "GENERAL_QUESTION":
            # Xử lý câu hỏi tổng quát
            result = rag_service.query(enhanced_query, rerank_top_k=5, top_k=20, filters=None)
            
            if result["success"]:
                rag_service.gemini_service.append_to_conversation(
                    enhanced_query, 
                    result["answer"], 
                    intent
                )
                
                return ChatResponse(
                    success=True,
                    answer=result["answer"],
                    intent=intent
                )
            else:
                rag_service.gemini_service.append_to_conversation(
                    enhanced_query, 
                    result["answer"], 
                    intent
                )
                
                return ChatResponse(
                    success=False,
                    answer=result["answer"],
                    intent=intent,
                    error="No relevant information found"
                )
        
        else:
            return ChatResponse(
                success=False,
                answer="Xin lỗi, tôi không hiểu câu hỏi của bạn. Vui lòng thử lại!",
                intent=intent,
                error="Unknown intent"
            )
            
    except Exception as e:
        logger.error(f"Lỗi xử lý chat: {str(e)}")
        return ChatResponse(
            success=False,
            answer="Đã xảy ra lỗi trong quá trình xử lý. Vui lòng thử lại!",
            error=str(e)
        )

@app.post("/clear-history")
async def clear_history():
    """Xóa lịch sử hội thoại"""
    global rag_service
    
    if rag_service is None:
        raise HTTPException(
            status_code=503, 
            detail="RAG Service chưa sẵn sàng"
        )
    
    try:
        # Reset conversation history
        rag_service.gemini_service.conversation_history = []
        return {
            "success": True,
            "message": "Đã xóa lịch sử hội thoại"
        }
    except Exception as e:
        logger.error(f"Lỗi xóa lịch sử: {str(e)}")
        return {
            "success": False,
            "message": "Lỗi khi xóa lịch sử hội thoại",
            "error": str(e)
        }

if __name__ == "__main__":
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )