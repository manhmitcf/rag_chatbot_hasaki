#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script khởi động toàn bộ hệ thống: Backend + Frontend
"""

import subprocess
import time
import sys
import signal
import os
import webbrowser
from pathlib import Path


def run_backend():
    """Chạy backend API"""
    print("🚀 Đang khởi động Backend API (Port 8002)...")
    
    process = subprocess.Popen([
        sys.executable, "api_modular.py"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    return process


def run_frontend():
    """Chạy frontend server"""
    print("🌐 Đang khởi động Frontend Server (Port 3000)...")
    
    frontend_path = Path(__file__).parent / "frontend" / "server.py"
    
    process = subprocess.Popen([
        sys.executable, str(frontend_path)
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    return process


def check_backend_health():
    """Kiểm tra backend có sẵn sàng không"""
    import requests
    
    for i in range(10):  # Thử 10 lần
        try:
            response = requests.get("http://localhost:8002/health", timeout=2)
            if response.status_code == 200:
                return True
        except:
            pass
        time.sleep(1)
    
    return False


def main():
    """Chạy toàn bộ hệ thống"""
    processes = []
    
    try:
        print("=" * 70)
        print("🌸 HASAKI BEAUTY AI CHATBOT - FULL SYSTEM STARTUP")
        print("=" * 70)
        print("Khởi động hệ thống chatbot mỹ phẩm hoàn chỉnh...")
        print("=" * 70)
        
        # 1. Backend API
        backend_process = run_backend()
        processes.append(("Backend API", backend_process))
        
        # Đợi backend khởi động
        print("⏳ Đang đợi backend khởi động...")
        time.sleep(8)
        
        # Kiểm tra backend health
        if check_backend_health():
            print("✅ Backend API đã sẵn sàng!")
        else:
            print("❌ Backend API không phản hồi. Vui lòng kiểm tra lại.")
            return
        
        # 2. Frontend Server
        frontend_process = run_frontend()
        processes.append(("Frontend Server", frontend_process))
        time.sleep(3)
        
        print("\n" + "=" * 70)
        print("🎉 HỆ THỐNG ĐÃ KHỞI ĐỘNG THÀNH CÔNG!")
        print("=" * 70)
        print("🔧 Backend API: http://localhost:8002")
        print("📚 API Documentation: http://localhost:8002/docs")
        print("🌐 Frontend Chatbot: http://localhost:3000")
        print("=" * 70)
        print("🎯 Tính năng:")
        print("• 🤖 AI tư vấn mỹ phẩm thông minh")
        print("• 🔍 Tìm kiếm sản phẩm nâng cao")
        print("• 💬 Giao diện chat hiện đại")
        print("• 📱 Responsive design")
        print("• ⚡ Xử lý nhanh với reranking")
        print("=" * 70)
        
        # Mở trình duyệt
        try:
            time.sleep(2)
            webbrowser.open('http://localhost:3000')
            print("🌐 Đã mở chatbot trong trình duyệt!")
        except:
            print("⚠️  Vui lòng mở trình duyệt và truy cập: http://localhost:3000")
        
        print("\n💡 Nhấn Ctrl+C để dừng toàn bộ hệ thống...\n")
        
        # Đợi cho đến khi người dùng dừng
        while True:
            time.sleep(1)
            
            # Kiểm tra xem có process nào bị crash không
            for name, process in processes:
                if process.poll() is not None:
                    print(f"\n⚠️  {name} đã dừng b���t ngờ!")
                    return_code = process.poll()
                    stdout, stderr = process.communicate()
                    print(f"Return code: {return_code}")
                    if stderr:
                        print(f"Error: {stderr.decode()}")
                    break
                    
    except KeyboardInterrupt:
        print("\n\n" + "=" * 50)
        print("🛑 ĐANG DỪNG HỆ THỐNG...")
        print("=" * 50)
        
        # Dừng tất cả processes
        for name, process in processes:
            if process.poll() is None:  # Process vẫn đang chạy
                print(f"🔄 Đang dừng {name}...")
                process.terminate()
                
                # Đợi process dừng, nếu không thì kill
                try:
                    process.wait(timeout=5)
                    print(f"✅ {name} đã dừng")
                except subprocess.TimeoutExpired:
                    print(f"⚡ Force killing {name}...")
                    process.kill()
                    process.wait()
                    print(f"✅ {name} đã bị force kill")
        
        print("\n🎉 Hệ thống đã được dừng hoàn toàn.")
        print("👋 Cảm ơn bạn đã sử dụng Hasaki Beauty AI Chatbot!")
        
    except Exception as e:
        print(f"\n❌ Lỗi: {str(e)}")
        
        # Dừng tất cả processes nếu có lỗi
        for name, process in processes:
            if process.poll() is None:
                process.terminate()
                process.wait()


if __name__ == "__main__":
    main()