#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FastAPI Server cho RAG Chatbot với Unified Service
API endpoint sử dụng luồng xử lý mới với thông tin chi tiết
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import uvicorn
import logging
import time
from contextlib import asynccontextmanager
from services.unified_rag_service import UnifiedRAGService

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global service
rag_service = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler thay thế cho on_event"""
    global rag_service
    
    # Startup
    try:
        logger.info("Đang khởi tạo Unified RAG Service...")
        rag_service = UnifiedRAGService(use_rerank=True)
        logger.info("Unified RAG Service đã sẵn sàng!")
    except Exception as e:
        logger.error(f"Lỗi khởi tạo RAG Service: {str(e)}")
        raise e
    
    yield
    
    # Shutdown
    logger.info("Đang dừng RAG Service...")


# Khởi tạo FastAPI app với lifespan
app = FastAPI(
    title="Hasaki RAG Chatbot API",
    description="API cho chatbot tư vấn mỹ phẩm với luồng xử lý mới",
    version="5.1.0",
    lifespan=lifespan
)

# Cấu hình CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    """Model cho request chat"""
    message: str
    session_id: Optional[str] = "default"
    show_details: Optional[bool] = True  # Hiển thị thông tin chi tiết


class ChatResponse(BaseModel):
    """Model cho response chat với thông tin chi tiết"""
    success: bool
    answer: str
    enhanced_query: Optional[str] = None
    sub_queries: Optional[List[str]] = None
    query_count: Optional[int] = None
    route: Optional[str] = None
    documents_found: Optional[int] = None
    id_product: Optional[str] = None
    name_product: Optional[str] = None
    processing_time: Optional[float] = None
    memory_stats: Optional[Dict[str, Any]] = None
    
    # Thông tin chi tiết về query transform và chunks
    query_transform_info: Optional[Dict[str, Any]] = None
    chunks_info: Optional[List[Dict[str, Any]]] = None
    context_info: Optional[Dict[str, Any]] = None
    
    error: Optional[str] = None


class MemoryResponse(BaseModel):
    """Model cho memory response"""
    success: bool
    summary: Optional[str] = None
    stats: Optional[Dict[str, Any]] = None
    message: Optional[str] = None


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Hasaki RAG Chatbot API đang hoạt động!",
        "status": "healthy",
        "version": "5.1.0",
        "features": [
            "Unified LLM Processing",
            "Query Processing & Routing",
            "Multi-Query Support", 
            "Advanced Search & Rerank",
            "Intelligent Response Generation",
            "Memory Management",
            "Detailed Query Transform Info",
            "Chunks Analysis"
        ]
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
    
    try:
        memory_stats = rag_service.get_memory_stats()
        return {
            "status": "healthy",
            "message": "Tất cả dịch vụ đang hoạt động bình thường",
            "rag_service": "ready",
            "unified": "enabled",
            "memory_stats": memory_stats
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"Lỗi kiểm tra health: {str(e)}"
        }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Endpoint chính để chat với bot - bao gồm thông tin chi tiết
    
    Args:
        request: ChatRequest chứa message, session_id và show_details
        
    Returns:
        ChatResponse với câu trả lời và thông tin chi tiết
    """
    global rag_service
    
    if rag_service is None:
        raise HTTPException(
            status_code=503, 
            detail="RAG Service chưa sẵn sàng. Vui lòng thử lại sau."
        )
    
    start_time = time.time()
    
    try:
        user_input = request.message.strip()
        
        if not user_input:
            return ChatResponse(
                success=False,
                answer="Vui lòng nhập câu hỏi của bạn!",
                error="Empty message"
            )
        
        logger.info(f"Nhận câu hỏi: {user_input}")
        
        # Xử lý với unified service và lấy thông tin chi tiết
        result = rag_service.process_complete_query_with_details(user_input, show_details=request.show_details)
        
        # Tính thời gian xử lý
        processing_time = time.time() - start_time
        
        if result.get("success"):
            return ChatResponse(
                success=True,
                answer=result["answer"],
                enhanced_query=result.get("enhanced_query"),
                sub_queries=result.get("sub_queries"),
                query_count=result.get("query_count"),
                route=result.get("route"),
                documents_found=result.get("documents_found"),
                id_product=result.get("id_product"),
                name_product=result.get("name_product"),
                processing_time=processing_time,
                memory_stats=result.get("memory_stats"),
                query_transform_info=result.get("query_transform_info"),
                chunks_info=result.get("chunks_info"),
                context_info=result.get("context_info")
            )
        else:
            return ChatResponse(
                success=False,
                answer=result["answer"],
                error=result.get("error"),
                processing_time=processing_time
            )
            
    except Exception as e:
        logger.error(f"Lỗi xử lý chat: {str(e)}")
        return ChatResponse(
            success=False,
            answer="Đã xảy ra lỗi trong quá trình xử lý. Vui lòng thử lại!",
            error=str(e),
            processing_time=time.time() - start_time
        )


@app.get("/memory/summary", response_model=MemoryResponse)
async def get_conversation_summary():
    """Lấy tóm tắt cuộc hội thoại"""
    global rag_service
    
    if rag_service is None:
        raise HTTPException(
            status_code=503, 
            detail="RAG Service chưa sẵn sàng"
        )
    
    try:
        summary = rag_service.get_conversation_summary()
        stats = rag_service.get_memory_stats()
        
        return MemoryResponse(
            success=True,
            summary=summary,
            stats=stats
        )
    except Exception as e:
        logger.error(f"Lỗi lấy tóm tắt: {str(e)}")
        return MemoryResponse(
            success=False,
            message=f"Lỗi khi lấy tóm tắt cu���c hội thoại: {str(e)}"
        )


@app.get("/memory/stats", response_model=MemoryResponse)
async def get_memory_stats():
    """Lấy thống kê memory"""
    global rag_service
    
    if rag_service is None:
        raise HTTPException(
            status_code=503, 
            detail="RAG Service chưa sẵn sàng"
        )
    
    try:
        stats = rag_service.get_memory_stats()
        
        return MemoryResponse(
            success=True,
            stats=stats,
            message="Thống kê memory được lấy thành công"
        )
    except Exception as e:
        logger.error(f"Lỗi lấy thống kê: {str(e)}")
        return MemoryResponse(
            success=False,
            message=f"Lỗi khi lấy thống kê memory: {str(e)}"
        )


@app.post("/memory/clear")
async def clear_memory():
    """Xóa lịch sử hội thoại"""
    global rag_service
    
    if rag_service is None:
        raise HTTPException(
            status_code=503, 
            detail="RAG Service chưa sẵn sàng"
        )
    
    try:
        rag_service.clear_memory()
        return {
            "success": True,
            "message": "Đã xóa lịch sử hội thoại và memory"
        }
    except Exception as e:
        logger.error(f"Lỗi xóa memory: {str(e)}")
        return {
            "success": False,
            "message": "Lỗi khi xóa lịch sử hội thoại",
            "error": str(e)
        }


@app.get("/test")
async def test_endpoint():
    """Test endpoint để kiểm tra API"""
    return {
        "message": "API test successful",
        "timestamp": time.time(),
        "rag_service_status": "ready" if rag_service else "not_initialized"
    }


if __name__ == "__main__":
    uvicorn.run(
        "api_modular:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
        log_level="info"
    )