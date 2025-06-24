#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FastAPI Server cho RAG Chatbot - Phiên bản Colab/Kaggle
API endpoint tối ưu cho deployment trên Google Colab hoặc Kaggle với Ngrok
"""

import os
import sys
import asyncio
import threading
import time
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import uvicorn
import logging

# Import cho Ngrok
try:
    from pyngrok import ngrok
    NGROK_AVAILABLE = True
except ImportError:
    NGROK_AVAILABLE = False
    print("⚠️ pyngrok không có sẵn. Cài đặt với: pip install pyngrok")

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Khởi tạo FastAPI app
app = FastAPI(
    title="🌸 Hasaki RAG Chatbot API - Colab Edition",
    description="API cho chatbot tư vấn mỹ phẩm - Tối ưu cho Google Colab/Kaggle",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Cấu hình CORS rộng rãi cho cloud deployment
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
rag_service = None
ngrok_tunnel = None
public_url = None

class ChatRequest(BaseModel):
    """Model cho request chat"""
    message: str
    session_id: Optional[str] = "default"
    use_rerank: Optional[bool] = True
    top_k: Optional[int] = 20
    rerank_top_k: Optional[int] = 5

class ChatResponse(BaseModel):
    """Model cho response chat"""
    success: bool
    answer: str
    intent: Optional[str] = None
    id_product: Optional[str] = None
    name_product: Optional[str] = None
    processing_time: Optional[float] = None
    error: Optional[str] = None

class SystemInfo(BaseModel):
    """Model cho thông tin hệ thống"""
    status: str
    rag_service_ready: bool
    ngrok_url: Optional[str] = None
    local_url: str
    environment: str
    python_version: str
    memory_usage: Optional[Dict[str, Any]] = None

def detect_environment():
    """Phát hiện môi trường chạy"""
    if 'COLAB_GPU' in os.environ:
        return "Google Colab"
    elif 'KAGGLE_KERNEL_RUN_TYPE' in os.environ:
        return "Kaggle"
    elif 'JUPYTER_SERVER_ROOT' in os.environ:
        return "Jupyter"
    else:
        return "Local"

def get_memory_usage():
    """Lấy thông tin sử dụng memory"""
    try:
        import psutil
        memory = psutil.virtual_memory()
        return {
            "total_gb": round(memory.total / (1024**3), 2),
            "available_gb": round(memory.available / (1024**3), 2),
            "used_gb": round(memory.used / (1024**3), 2),
            "percent": memory.percent
        }
    except ImportError:
        return None

def setup_ngrok(port: int = 8000, auth_token: str = None):
    """Thiết lập Ngrok tunnel"""
    global ngrok_tunnel, public_url
    
    if not NGROK_AVAILABLE:
        logger.warning("Ngrok không có sẵn")
        return None
    
    try:
        # Thiết lập auth token nếu có
        if auth_token:
            ngrok.set_auth_token(auth_token)
        
        # Tạo tunnel
        ngrok_tunnel = ngrok.connect(port, "http")
        public_url = ngrok_tunnel.public_url
        
        logger.info(f"🌐 Ngrok tunnel đã được tạo: {public_url}")
        return public_url
        
    except Exception as e:
        logger.error(f"❌ Lỗi tạo Ngrok tunnel: {str(e)}")
        return None

def initialize_rag_service():
    """Khởi tạo RAG Service với error handling tốt hơn"""
    global rag_service
    
    try:
        logger.info("🚀 Đang khởi tạo RAG Service...")
        
        # Import RAG Service (có thể cần điều chỉnh path)
        try:
            from services.rag_service import RAGService
        except ImportError:
            logger.error("❌ Không thể import RAGService. Kiểm tra đường dẫn.")
            return False
        
        # Khởi tạo với timeout
        rag_service = RAGService(use_rerank=True)
        logger.info("✅ RAG Service đã sẵn sàng!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Lỗi khởi tạo RAG Service: {str(e)}")
        rag_service = None
        return False

@app.on_event("startup")
async def startup_event():
    """Khởi tạo khi server start"""
    logger.info("🌸 Khởi động Hasaki RAG Chatbot API - Colab Edition")
    logger.info(f"🖥️ Môi trường: {detect_environment()}")
    
    # Khởi tạo RAG Service trong background
    def init_rag():
        initialize_rag_service()
    
    # Chạy trong thread riêng để không block startup
    threading.Thread(target=init_rag, daemon=True).start()

@app.on_event("shutdown")
async def shutdown_event():
    """Dọn dẹp khi server shutdown"""
    global ngrok_tunnel
    
    if ngrok_tunnel:
        try:
            ngrok.disconnect(ngrok_tunnel.public_url)
            logger.info("🔌 Đã ngắt kết nối Ngrok tunnel")
        except:
            pass

@app.get("/", response_model=Dict[str, Any])
async def root():
    """Root endpoint với thông tin cơ bản"""
    return {
        "message": "🌸 Hasaki RAG Chatbot API - Colab Edition",
        "status": "running",
        "version": "2.0.0",
        "environment": detect_environment(),
        "endpoints": {
            "chat": "/chat",
            "health": "/health",
            "system_info": "/system-info",
            "setup_ngrok": "/setup-ngrok",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    """Kiểm tra trạng thái chi tiết"""
    global rag_service, public_url
    
    return {
        "status": "healthy" if rag_service else "initializing",
        "rag_service_ready": rag_service is not None,
        "ngrok_url": public_url,
        "environment": detect_environment(),
        "timestamp": time.time()
    }

@app.get("/system-info", response_model=SystemInfo)
async def get_system_info():
    """Lấy thông tin hệ thống chi tiết"""
    global rag_service, public_url
    
    return SystemInfo(
        status="ready" if rag_service else "initializing",
        rag_service_ready=rag_service is not None,
        ngrok_url=public_url,
        local_url="http://localhost:8000",
        environment=detect_environment(),
        python_version=sys.version,
        memory_usage=get_memory_usage()
    )

@app.post("/setup-ngrok")
async def setup_ngrok_endpoint(auth_token: Optional[str] = None):
    """Endpoint để thiết lập Ngrok tunnel"""
    if not NGROK_AVAILABLE:
        raise HTTPException(
            status_code=400,
            detail="pyngrok không có sẵn. Cài đặt với: pip install pyngrok"
        )
    
    url = setup_ngrok(8000, auth_token)
    
    if url:
        return {
            "success": True,
            "ngrok_url": url,
            "message": "Ngrok tunnel đã được tạo thành công"
        }
    else:
        raise HTTPException(
            status_code=500,
            detail="Không thể tạo Ngrok tunnel"
        )

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Endpoint chính để chat với bot - Phiên bản tối ưu
    """
    global rag_service
    
    start_time = time.time()
    
    # Kiểm tra RAG service
    if rag_service is None:
        # Thử khởi tạo lại nếu chưa có
        if not initialize_rag_service():
            raise HTTPException(
                status_code=503,
                detail="RAG Service chưa sẵn sàng. Vui lòng đợi hoặc kiểm tra logs."
            )
    
    try:
        user_input = request.message.strip()
        
        if not user_input:
            return ChatResponse(
                success=False,
                answer="Vui lòng nhập câu hỏi của bạn!",
                processing_time=time.time() - start_time,
                error="Empty message"
            )
        
        logger.info(f"📝 Nhận câu hỏi: {user_input}")
        
        # Tăng cường query với lịch sử hội thoại
        enhanced_query = rag_service.gemini_service.enhance_query_with_history(user_input)
        
        # Phân tích ý định
        intent = rag_service.gemini_service.build_promt_intent(enhanced_query)
        logger.info(f"🎯 Phân loại: {intent}")
        
        # Xử lý theo ý định
        if intent == "SPECIFIC_PRODUCT":
            # Xác định filter cho sản phẩm cụ thể
            filters = rag_service.gemini_service.identify_key_for_filter(enhanced_query)
            logger.info(f"🔍 Filters: {filters}")
            
            # Thử tìm kiếm với filter trước
            result = rag_service.query(
                enhanced_query, 
                filters=filters, 
                rerank_top_k=request.rerank_top_k, 
                top_k=request.top_k
            )
            
            # Fallback nếu không tìm thấy
            if (result["success"] and 
                result["answer"] == "Xin lỗi, tôi không tìm thấy thông tin phù hợp để trả lời câu hỏi của bạn."):
                logger.info("⚠️ Fallback: Tìm kiếm không filter...")
                result = rag_service.query(
                    enhanced_query, 
                    filters=None, 
                    rerank_top_k=request.rerank_top_k, 
                    top_k=request.top_k
                )
            
            # Lưu lịch sử
            rag_service.gemini_service.append_to_conversation(
                enhanced_query, 
                result["answer"], 
                intent,
                result.get("id_product"),
                result.get("name_product")
            )
            
            return ChatResponse(
                success=result["success"],
                answer=result["answer"],
                intent=intent,
                id_product=result.get("id_product"),
                name_product=result.get("name_product"),
                processing_time=time.time() - start_time
            )
        
        elif intent == "GENERAL_QUESTION":
            # Xử lý câu hỏi tổng quát
            result = rag_service.query(
                enhanced_query, 
                rerank_top_k=request.rerank_top_k, 
                top_k=request.top_k, 
                filters=None
            )
            
            # Lưu lịch sử
            rag_service.gemini_service.append_to_conversation(
                enhanced_query, 
                result["answer"], 
                intent
            )
            
            return ChatResponse(
                success=result["success"],
                answer=result["answer"],
                intent=intent,
                processing_time=time.time() - start_time
            )
        
        else:
            return ChatResponse(
                success=False,
                answer="Xin lỗi, tôi không hiểu câu hỏi của bạn. Vui lòng thử lại!",
                intent=intent,
                processing_time=time.time() - start_time,
                error="Unknown intent"
            )
            
    except Exception as e:
        logger.error(f"❌ Lỗi xử lý chat: {str(e)}")
        return ChatResponse(
            success=False,
            answer="Đã xảy ra lỗi trong quá trình xử lý. Vui lòng thử lại!",
            processing_time=time.time() - start_time,
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
        rag_service.gemini_service.conversation_history = []
        return {
            "success": True,
            "message": "Đã xóa lịch sử hội thoại",
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"❌ Lỗi xóa lịch sử: {str(e)}")
        return {
            "success": False,
            "message": "Lỗi khi xóa lịch sử hội thoại",
            "error": str(e)
        }

@app.get("/conversation-history")
async def get_conversation_history():
    """Lấy lịch sử hội thoại"""
    global rag_service
    
    if rag_service is None:
        raise HTTPException(
            status_code=503,
            detail="RAG Service chưa sẵn sàng"
        )
    
    try:
        history = getattr(rag_service.gemini_service, 'conversation_history', [])
        return {
            "success": True,
            "history": history,
            "count": len(history)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def run_server(port: int = 8000, setup_ngrok_tunnel: bool = True, ngrok_auth_token: str = None):
    """
    Chạy server với các tùy chọn
    
    Args:
        port: Port để chạy server
        setup_ngrok_tunnel: Có tạo Ngrok tunnel không
        ngrok_auth_token: Auth token cho Ngrok
    """
    
    print("🌸 Hasaki RAG Chatbot API - Colab Edition")
    print("=" * 50)
    print(f"🖥️ Môi trường: {detect_environment()}")
    print(f"🐍 Python: {sys.version}")
    
    # Thiết lập Ngrok nếu cần
    if setup_ngrok_tunnel and NGROK_AVAILABLE:
        ngrok_url = setup_ngrok(port, ngrok_auth_token)
        if ngrok_url:
            print(f"🌐 Ngrok URL: {ngrok_url}")
        else:
            print("⚠️ Không thể tạo Ngrok tunnel")
    elif setup_ngrok_tunnel and not NGROK_AVAILABLE:
        print("⚠️ pyngrok không có sẵn. Cài đặt với: pip install pyngrok")
    
    print(f"🔗 Local URL: http://localhost:{port}")
    print(f"📚 API Docs: http://localhost:{port}/docs")
    print("🚀 Đang khởi động server...")
    
    # Chạy server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=True
    )

if __name__ == "__main__":
    # Cấu hình cho Colab/Kaggle
    import argparse
    
    parser = argparse.ArgumentParser(description="Hasaki RAG Chatbot API - Colab Edition")
    parser.add_argument("--port", type=int, default=8000, help="Port để chạy server")
    parser.add_argument("--no-ngrok", action="store_true", help="Không sử dụng Ngrok")
    parser.add_argument("--ngrok-token", type=str, help="Ngrok auth token")
    
    args = parser.parse_args()
    
    run_server(
        port=args.port,
        setup_ngrok_tunnel=not args.no_ngrok,
        ngrok_auth_token=args.ngrok_token
    )