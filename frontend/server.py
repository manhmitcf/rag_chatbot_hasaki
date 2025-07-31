#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Simple HTTP Server để serve frontend
"""

import http.server
import socketserver
import os
import webbrowser
from pathlib import Path

# Configuration
PORT = 3000
DIRECTORY = Path(__file__).parent

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    
    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

def main():
    """Start the frontend server"""
    
    # Change to frontend directory
    os.chdir(DIRECTORY)
    
    # Create server
    with socketserver.TCPServer(("", PORT), CustomHTTPRequestHandler) as httpd:
        print("=" * 60)
        print("HASAKI BEAUTY AI CHATBOT FRONTEND")
        print("=" * 60)
        print(f"🚀 Server đang chạy tại: http://localhost:{PORT}")
        print(f"📁 Serving files từ: {DIRECTORY}")
        print("=" * 60)
        print("📋 Hướng dẫn:")
        print("1. Đảm bảo backend API đang chạy (port 8002)")
        print("2. Mở trình duyệt và truy cập URL trên")
        print("3. Nhấn Ctrl+C để dừng server")
        print("=" * 60)
        
        # Auto open browser
        try:
            webbrowser.open(f'http://localhost:{PORT}')
            print("✅ Đã mở trình duyệt tự động")
        except:
            print("⚠️  Không thể mở trình duyệt tự động")
        
        print("\n🎉 Frontend sẵn sàng! Nhấn Ctrl+C để dừng...\n")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n👋 Đang dừng server...")
            print("Cảm ơn bạn đã sử dụng Hasaki Beauty AI!")

if __name__ == "__main__":
    main()