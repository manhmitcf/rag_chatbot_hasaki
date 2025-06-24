#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script để khởi động cả API server và Streamlit app
"""

import subprocess
import sys
import time
import threading
import os

def run_api_server():
    """Chạy FastAPI server"""
    print("Đang khởi động FastAPI server...")
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "api:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload"
        ], check=True)
    except KeyboardInterrupt:
        print("\nFastAPI server đã dừng")
    except Exception as e:
        print(f"Lỗi chạy FastAPI server: {e}")

def run_streamlit_app():
    """Chạy Streamlit app"""
    print("Đang khởi động Streamlit app...")
    time.sleep(5)  # Đợi API server khởi động
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", 
            "run", "streamlit_app.py", 
            "--server.port", "8501"
        ], check=True)
    except KeyboardInterrupt:
        print("\nStreamlit app đã dừng")
    except Exception as e:
        print(f"Lỗi chạy Streamlit app: {e}")

def main():
    """Chạy cả hai server"""
    print("Hasaki RAG Chatbot - Khởi động servers")
    print("=" * 50)
    
    # Tạo threads cho mỗi server
    api_thread = threading.Thread(target=run_api_server, daemon=True)
    streamlit_thread = threading.Thread(target=run_streamlit_app, daemon=True)
    
    try:
        # Khởi động API server trước
        api_thread.start()
        
        # Khởi động Streamlit app
        streamlit_thread.start()
        
        print("\nCả hai server đã được khởi động!")
        print("FastAPI: http://localhost:8000")
        print("Streamlit: http://localhost:8501")
        print("\n Nhấn Ctrl+C để dừng tất cả servers")
        
        # Đợi các threads
        api_thread.join()
        streamlit_thread.join()
        
    except KeyboardInterrupt:
        print("\n\nĐang dừng tất cả servers...")
        print("Đã dừng thành công!")

if __name__ == "__main__":
    main()