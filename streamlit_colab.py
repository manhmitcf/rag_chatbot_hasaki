#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Streamlit App cho RAG Chatbot - Phiên bản Colab/Cloud
Giao diện web tối ưu để kết nối với API đã deploy trên Colab/Kaggle
"""

import streamlit as st
import requests
import json
import time
from typing import Dict, Any, Optional
import re
from urllib.parse import urlparse

# Cấu hình trang
st.set_page_config(
    page_title="🌸 Hasaki RAG Chatbot - Cloud Edition",
    page_icon="🌸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS tùy chỉnh
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem;
        background: linear-gradient(90deg, #ff6b6b, #feca57);
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    
    .status-success {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 0.75rem;
        border-radius: 0.375rem;
        margin: 1rem 0;
    }
    
    .status-error {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 0.75rem;
        border-radius: 0.375rem;
        margin: 1rem 0;
    }
    
    .chat-message {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 10px;
    }
    
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
    
    .bot-message {
        background-color: #f3e5f5;
        border-left: 4px solid #9c27b0;
    }
</style>
""", unsafe_allow_html=True)

def validate_url(url: str) -> bool:
    """Kiểm tra URL hợp lệ"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def extract_ngrok_url(text: str) -> Optional[str]:
    """Trích xuất Ngrok URL từ text"""
    # Pattern cho Ngrok URL
    pattern = r'https://[a-zA-Z0-9-]+\.ngrok-free\.app|https://[a-zA-Z0-9-]+\.ngrok\.io'
    matches = re.findall(pattern, text)
    return matches[0] if matches else None

def test_api_connection(api_url: str, timeout: int = 10) -> Dict[str, Any]:
    """Test kết nối API"""
    try:
        # Thêm /health nếu chưa có
        if not api_url.endswith('/health'):
            test_url = f"{api_url.rstrip('/')}/health"
        else:
            test_url = api_url
            
        response = requests.get(test_url, timeout=timeout)
        
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "status": data.get("status", "unknown"),
                "rag_ready": data.get("rag_service_ready", False),
                "response_time": response.elapsed.total_seconds(),
                "data": data
            }
        else:
            return {
                "success": False,
                "error": f"HTTP {response.status_code}",
                "response_time": response.elapsed.total_seconds()
            }
            
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": "Timeout - API không phản hồi trong thời gian cho phép"
        }
    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "error": "Không thể kết nối đến API"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Lỗi: {str(e)}"
        }

def send_chat_message(api_url: str, message: str, **kwargs) -> Dict[str, Any]:
    """Gửi tin nhắn chat đến API"""
    try:
        chat_url = f"{api_url.rstrip('/')}/chat"
        
        payload = {
            "message": message,
            "session_id": kwargs.get("session_id", "streamlit_session"),
            "use_rerank": kwargs.get("use_rerank", True),
            "top_k": kwargs.get("top_k", 20),
            "rerank_top_k": kwargs.get("rerank_top_k", 5)
        }
        
        response = requests.post(
            chat_url,
            json=payload,
            timeout=kwargs.get("timeout", 60)
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "success": False,
                "answer": f"Lỗi API: HTTP {response.status_code}",
                "error": f"HTTP {response.status_code}"
            }
            
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "answer": "⏰ Timeout: API phản hồi quá lâu, vui lòng thử lại!",
            "error": "timeout"
        }
    except Exception as e:
        return {
            "success": False,
            "answer": f"❌ Lỗi kết nối: {str(e)}",
            "error": str(e)
        }

def clear_api_history(api_url: str) -> bool:
    """Xóa lịch sử hội thoại trên API"""
    try:
        clear_url = f"{api_url.rstrip('/')}/clear-history"
        response = requests.post(clear_url, timeout=10)
        return response.status_code == 200 and response.json().get("success", False)
    except:
        return False

def get_system_info(api_url: str) -> Optional[Dict[str, Any]]:
    """Lấy thông tin hệ thống từ API"""
    try:
        info_url = f"{api_url.rstrip('/')}/system-info"
        response = requests.get(info_url, timeout=10)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None

def main():
    """Hàm chính của ứng dụng"""
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🌸 Hasaki RAG Chatbot - Cloud Edition</h1>
        <p>💄 Chatbot tư vấn mỹ phẩm thông minh - Kết nối với API Cloud</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar - Cấu hình API
    with st.sidebar:
        st.header("🔧 Cấu hình API")
        
        # Input API URL
        api_url = st.text_input(
            "🌐 API URL",
            placeholder="https://your-ngrok-url.ngrok-free.app",
            help="Nhập URL của API đã deploy (Ngrok, Colab, Kaggle, etc.)"
        )
        
        # Auto-extract Ngrok URL
        st.markdown("**💡 Mẹo:** Paste toàn bộ output từ Colab/Kaggle, tôi sẽ tự động tìm Ngrok URL!")
        
        ngrok_text = st.text_area(
            "📋 Paste Colab/Kaggle Output",
            placeholder="Paste toàn bộ output từ cell chạy API...",
            height=100
        )
        
        if ngrok_text and not api_url:
            extracted_url = extract_ngrok_url(ngrok_text)
            if extracted_url:
                st.success(f"✅ Tìm thấy URL: {extracted_url}")
                if st.button("📌 Sử dụng URL này"):
                    st.session_state.api_url = extracted_url
                    st.rerun()
        
        # Sử dụng URL từ session state nếu có
        if 'api_url' in st.session_state and not api_url:
            api_url = st.session_state.api_url
            st.text_input("🌐 API URL", value=api_url, key="api_url_display")
        
        st.divider()
        
        # Test kết nối
        if api_url:
            if st.button("🔍 Test Kết Nối", type="primary"):
                with st.spinner("Đang kiểm tra kết nối..."):
                    result = test_api_connection(api_url)
                
                if result["success"]:
                    st.markdown(f"""
                    <div class="status-success">
                        ✅ <strong>Kết nối thành công!</strong><br>
                        📊 Status: {result.get('status', 'unknown')}<br>
                        🤖 RAG Ready: {'✅' if result.get('rag_ready') else '⏳'}<br>
                        ⚡ Response Time: {result.get('response_time', 0):.2f}s
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Lưu API URL hợp lệ
                    st.session_state.verified_api_url = api_url
                    
                else:
                    st.markdown(f"""
                    <div class="status-error">
                        ❌ <strong>Kết nối thất bại!</strong><br>
                        🔍 Lỗi: {result.get('error', 'Unknown error')}
                    </div>
                    """, unsafe_allow_html=True)
        
        st.divider()
        
        # Cài đặt chat
        st.header("⚙️ Cài đặt Chat")
        
        use_rerank = st.checkbox("🔄 Sử dụng Rerank", value=True)
        top_k = st.slider("📊 Top K", min_value=5, max_value=50, value=20)
        rerank_top_k = st.slider("🎯 Rerank Top K", min_value=3, max_value=15, value=5)
        timeout = st.slider("⏱️ Timeout (giây)", min_value=10, max_value=120, value=60)
        
        st.divider()
        
        # Nút xóa lịch sử
        if st.button("🗑️ Xóa Lịch Sử", type="secondary"):
            if 'verified_api_url' in st.session_state:
                if clear_api_history(st.session_state.verified_api_url):
                    st.success("✅ Đã xóa lịch sử trên API!")
                    st.session_state.messages = []
                    st.rerun()
                else:
                    st.error("❌ Lỗi khi xóa lịch sử!")
            else:
                st.warning("⚠️ Chưa có API URL hợp lệ!")
        
        st.divider()
        
        # Thông tin hệ thống
        if 'verified_api_url' in st.session_state:
            if st.button("📊 Thông Tin Hệ Thống"):
                system_info = get_system_info(st.session_state.verified_api_url)
                if system_info:
                    st.json(system_info)
        
        st.divider()
        
        # Hướng dẫn
        st.header("📋 Hướng Dẫn")
        st.markdown("""
        **🚀 Cách sử dụng:**
        
        1️⃣ **Deploy API trên Colab/Kaggle:**
        ```python
        !pip install fastapi uvicorn pyngrok
        !python api_colab.py
        ```
        
        2️⃣ **Copy Ngrok URL** từ output
        
        3️⃣ **Paste URL** vào ô "API URL" ở trên
        
        4️⃣ **Test kết nối** và bắt đầu chat!
        
        **🔍 Các loại câu hỏi:**
        - "Thông tin về kem chống nắng Anessa"
        - "Tư vấn kem dưỡng ẩm cho da khô"
        - "Có những loại sữa rửa mặt nào?"
        """)
    
    # Main chat interface
    if 'verified_api_url' not in st.session_state:
        st.warning("⚠️ Vui lòng cấu hình và test API URL trước khi chat!")
        st.info("👈 Sử dụng sidebar để cấu hình API")
        return
    
    # Khởi tạo session state cho messages
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Container cho chat
    chat_container = st.container()
    
    with chat_container:
        # Tin nhắn chào mừng
        if not st.session_state.messages:
            with st.chat_message("assistant"):
                st.markdown("""
                👋 **Xin chào! Tôi là chatbot tư vấn mỹ phẩm của Hasaki.**
                
                🌟 **Tôi có thể giúp bạn:**
                - 💄 Tìm hiểu về sản phẩm mỹ phẩm
                - 🧴 Tư vấn chăm sóc da
                - 💅 Gợi ý sản phẩm phù hợp
                
                **🔗 Đang kết nối với API:** `{}`
                
                Hãy đặt câu hỏi để bắt đầu nhé! 😊
                """.format(st.session_state.verified_api_url))
        
        # Hiển thị lịch sử chat
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                
                # Hiển thị metadata cho assistant
                if message["role"] == "assistant" and "metadata" in message:
                    metadata = message["metadata"]
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if metadata.get("intent"):
                            st.caption(f"🎯 **Intent:** {metadata['intent']}")
                    
                    with col2:
                        if metadata.get("processing_time"):
                            st.caption(f"⚡ **Time:** {metadata['processing_time']:.2f}s")
                    
                    with col3:
                        if metadata.get("id_product"):
                            st.caption(f"🆔 **ID:** {metadata['id_product']}")
                    
                    if metadata.get("name_product"):
                        st.caption(f"📦 **Sản phẩm:** {metadata['name_product']}")
    
    # Input cho tin nhắn mới
    if prompt := st.chat_input("Nhập câu hỏi của bạn..."):
        # Thêm tin nhắn user
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Hiển thị tin nhắn user
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Xử lý và hiển thị phản hồi
        with st.chat_message("assistant"):
            with st.spinner("🤖 Đang suy nghĩ..."):
                response = send_chat_message(
                    st.session_state.verified_api_url,
                    prompt,
                    use_rerank=use_rerank,
                    top_k=top_k,
                    rerank_top_k=rerank_top_k,
                    timeout=timeout
                )
            
            # Hiển thị câu trả lời
            if response.get("success"):
                st.markdown(response["answer"])
                
                # Hiển thị metadata
                metadata = {}
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if response.get("intent"):
                        st.caption(f"🎯 **Intent:** {response['intent']}")
                        metadata["intent"] = response["intent"]
                
                with col2:
                    if response.get("processing_time"):
                        st.caption(f"⚡ **Time:** {response['processing_time']:.2f}s")
                        metadata["processing_time"] = response["processing_time"]
                
                with col3:
                    if response.get("id_product"):
                        st.caption(f"🆔 **ID:** {response['id_product']}")
                        metadata["id_product"] = response["id_product"]
                
                if response.get("name_product"):
                    st.caption(f"📦 **Sản phẩm:** {response['name_product']}")
                    metadata["name_product"] = response["name_product"]
                
                # Lưu vào lịch sử
                message_data = {
                    "role": "assistant",
                    "content": response["answer"]
                }
                if metadata:
                    message_data["metadata"] = metadata
                
                st.session_state.messages.append(message_data)
                
            else:
                st.error(response["answer"])
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response["answer"]
                })

if __name__ == "__main__":
    main()