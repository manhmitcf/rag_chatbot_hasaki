#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Streamlit App cho RAG Chatbot
Giao diện web đơn giản để tương tác với chatbot tư vấn mỹ phẩm
"""

import streamlit as st
import requests
import json
from typing import Dict, Any
import time

# Cấu hình trang
st.set_page_config(
    page_title="Hasaki RAG Chatbot",
    page_icon="🌸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# URL của API (có thể thay đổi nếu cần)
API_BASE_URL = "http://localhost:8000"

def check_api_health() -> bool:
    """Kiểm tra trạng thái API"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def send_message(message: str) -> Dict[str, Any]:
    """Gửi tin nhắn đến API"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/chat",
            json={"message": message},
            timeout=60
        )
        return response.json()
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "answer": "⏰ Timeout: Phản hồi quá lâu, vui lòng thử lại!",
            "error": "timeout"
        }
    except Exception as e:
        return {
            "success": False,
            "answer": f"❌ Lỗi kết nối: {str(e)}",
            "error": str(e)
        }

def clear_history() -> bool:
    """Xóa lịch sử hội thoại"""
    try:
        response = requests.post(f"{API_BASE_URL}/clear-history", timeout=10)
        return response.json().get("success", False)
    except:
        return False

def main():
    """Hàm chính của ứng dụng Streamlit"""
    
    # Header
    st.title("🌸 Hasaki RAG Chatbot")
    st.markdown("### 💄 Chatbot tư vấn mỹ phẩm thông minh")
    
    # Sidebar
    with st.sidebar:
        st.header("🔧 Cài đặt")
        
        # Kiểm tra trạng thái API
        api_status = check_api_health()
        if api_status:
            st.success("✅ API đang hoạt động")
        else:
            st.error("❌ API không khả dụng")
            st.warning("Vui lòng khởi động API server trước khi sử dụng!")
            st.code("python api.py", language="bash")
        
        st.divider()
        
        # Nút xóa lịch sử
        if st.button("🗑️ Xóa lịch sử hội thoại", type="secondary"):
            if clear_history():
                st.success("Đã xóa lịch sử hội thoại!")
                st.session_state.messages = []
                st.rerun()
            else:
                st.error("Lỗi khi xóa lịch sử!")
        
        st.divider()
        
        # Hướng dẫn sử dụng
        st.header("📋 Hướng dẫn")
        st.markdown("""
        **🔍 Các loại câu hỏi:**
        
        1️⃣ **Sản phẩm cụ thể:**
        - "Thông tin về kem chống nắng Anessa"
        - "Giá của sản phẩm ID: 12345"
        
        2️⃣ **Câu hỏi tổng quát:**
        - "Có những loại sữa rửa mặt nào?"
        - "Tư vấn kem dưỡng ẩm cho da khô"
        
        3️⃣ **Chào hỏi:**
        - "Xin chào"
        - "Cảm ơn bạn"
        """)
    
    # Khởi tạo session state cho messages
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Hiển thị lịch sử chat
    chat_container = st.container()
    
    with chat_container:
        # Hiển thị tin nhắn chào mừng nếu chưa có tin nhắn nào
        if not st.session_state.messages:
            with st.chat_message("assistant"):
                st.markdown("""
                👋 **Xin chào! Tôi là chatbot tư vấn mỹ phẩm của Hasaki.**
                
                🌟 Tôi có thể giúp bạn:
                - 💄 Tìm hiểu về sản phẩm mỹ phẩm
                - 🧴 Tư vấn chăm sóc da
                - 💅 Gợi ý sản phẩm phù hợp
                
                Hãy đặt câu hỏi để bắt đầu nhé! 😊
                """)
        
        # Hiển thị các tin nhắn trong lịch sử
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                
                # Hiển thị thông tin bổ sung nếu có
                if message["role"] == "assistant" and "metadata" in message:
                    metadata = message["metadata"]
                    if metadata.get("intent"):
                        st.caption(f"🎯 Phân loại: {metadata['intent']}")
                    if metadata.get("id_product"):
                        st.caption(f"🆔 ID sản phẩm: {metadata['id_product']}")
                    if metadata.get("name_product"):
                        st.caption(f"📦 Tên sản phẩm: {metadata['name_product']}")
    
    # Input cho tin nhắn mới
    if prompt := st.chat_input("Nhập câu hỏi của bạn..."):
        if not api_status:
            st.error("❌ API không khả dụng. Vui lòng khởi động API server!")
            return
        
        # Thêm tin nhắn của user vào lịch sử
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Hiển thị tin nhắn của user
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Hiển thị tin nhắn đang xử lý
        with st.chat_message("assistant"):
            with st.spinner("🤖 Đang suy nghĩ..."):
                # Gửi tin nhắn đến API
                response = send_message(prompt)
            
            # Hiển thị phản hồi
            if response.get("success"):
                st.markdown(response["answer"])
                
                # Hiển thị thông tin metadata
                metadata = {}
                if response.get("intent"):
                    st.caption(f"🎯 Phân loại: {response['intent']}")
                    metadata["intent"] = response["intent"]
                if response.get("id_product"):
                    st.caption(f"🆔 ID sản phẩm: {response['id_product']}")
                    metadata["id_product"] = response["id_product"]
                if response.get("name_product"):
                    st.caption(f"📦 Tên sản phẩm: {response['name_product']}")
                    metadata["name_product"] = response["name_product"]
                
                # Thêm vào lịch sử
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