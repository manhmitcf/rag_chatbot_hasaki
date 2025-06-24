#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Kaggle Deployment Script cho Hasaki RAG Chatbot
Script tự động để deploy API lên Kaggle Notebooks
"""

import os
import sys
import subprocess
import time
import threading
from pathlib import Path

def detect_environment():
    """Phát hiện môi trường chạy"""
    if 'KAGGLE_KERNEL_RUN_TYPE' in os.environ:
        return "Kaggle"
    elif 'COLAB_GPU' in os.environ:
        return "Google Colab"
    else:
        return "Local"

def install_dependencies():
    """Cài đặt các dependencies cần thiết"""
    print("📦 Installing dependencies...")
    
    packages = [
        "fastapi",
        "uvicorn",
        "pyngrok",
        "python-dotenv",
        "google-generativeai",
        "sentence-transformers",
        "transformers",
        "torch",
        "qdrant-client",
        "accelerate",
        "tokenizers",
        "safetensors",
        "psutil",
        "requests",
        "tqdm",
        "numpy"
    ]
    
    for package in packages:
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", package], 
                         check=True, capture_output=True)
            print(f"✅ {package}")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {package}: {e}")
            return False
    
    print("✅ All dependencies installed!")
    return True

def setup_environment():
    """Thiết lập môi trường"""
    print("🔧 Setting up environment...")
    
    # Tạo thư mục làm việc
    work_dir = Path("/kaggle/working/rag_chatbot")
    work_dir.mkdir(exist_ok=True)
    
    # Copy files nếu cần
    current_dir = Path.cwd()
    
    # Các file cần thiết
    required_files = [
        "api_colab.py",
        "services/",
        "config/",
        "data/",
        ".env"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not (current_dir / file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print("⚠️ Missing required files:")
        for file in missing_files:
            print(f"   - {file}")
        print("\n💡 Please upload the following to Kaggle dataset:")
        print("   1. Create a new dataset")
        print("   2. Upload your project files")
        print("   3. Add dataset to this notebook")
        return False
    
    print("✅ Environment setup complete!")
    return True

def create_env_file():
    """Tạo file .env với cấu hình"""
    print("📝 Creating .env file...")
    
    # Lấy API keys từ Kaggle secrets hoặc input
    gemini_key = os.environ.get('GEMINI_API_KEY')
    if not gemini_key:
        gemini_key = input("🔑 Enter Gemini API Key: ")
    
    ngrok_token = os.environ.get('NGROK_AUTH_TOKEN', '')
    if not ngrok_token:
        ngrok_token = input("🌐 Enter Ngrok Auth Token (optional): ")
    
    env_content = f"""# API Keys
GEMINI_API_KEY={gemini_key}

# Qdrant Configuration
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=
QDRANT_COLLECTION_NAME=hasaki_products

# Model Configuration
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
RERANK_MODEL=BAAI/bge-reranker-base

# Generation Configuration
GEMINI_MODEL=gemini-1.5-flash
MAX_TOKENS=2048
TEMPERATURE=0.7
"""
    
    with open(".env", "w", encoding="utf-8") as f:
        f.write(env_content)
    
    # Set environment variables
    os.environ['GEMINI_API_KEY'] = gemini_key
    if ngrok_token:
        os.environ['NGROK_AUTH_TOKEN'] = ngrok_token
    
    print("✅ Environment file created!")
    return True

def start_api_server(port=8000, use_ngrok=True):
    """Khởi động API server"""
    print(f"🚀 Starting API server on port {port}...")
    
    # Tạo command
    cmd = [sys.executable, "api_colab.py", "--port", str(port)]
    
    if not use_ngrok:
        cmd.append("--no-ngrok")
    
    if os.environ.get('NGROK_AUTH_TOKEN'):
        cmd.extend(["--ngrok-token", os.environ['NGROK_AUTH_TOKEN']])
    
    # Chạy server
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # Monitor output
        ngrok_url = None
        for line in process.stdout:
            print(line.strip())
            
            # Extract Ngrok URL
            if "ngrok.io" in line or "ngrok-free.app" in line:
                import re
                urls = re.findall(r'https://[a-zA-Z0-9-]+\.(?:ngrok\.io|ngrok-free\.app)', line)
                if urls:
                    ngrok_url = urls[0]
            
            # Stop monitoring after server starts
            if "Uvicorn running" in line:
                break
        
        return process, ngrok_url
        
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        return None, None

def test_api(base_url="http://localhost:8000"):
    """Test API endpoints"""
    print(f"🧪 Testing API at {base_url}...")
    
    import requests
    
    try:
        # Test health
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health: {data.get('status')}")
            print(f"🤖 RAG Service: {'Ready' if data.get('rag_service_ready') else 'Initializing'}")
        
        # Test system info
        response = requests.get(f"{base_url}/system-info", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"🖥️ Environment: {data.get('environment')}")
            if data.get('ngrok_url'):
                print(f"🌐 Public URL: {data['ngrok_url']}")
                return data['ngrok_url']
        
        return True
        
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

def main():
    """Main deployment function"""
    print("🌸 Hasaki RAG Chatbot - Kaggle Deployment")
    print("=" * 50)
    print(f"🖥️ Environment: {detect_environment()}")
    
    # Step 1: Install dependencies
    if not install_dependencies():
        print("❌ Failed to install dependencies")
        return False
    
    # Step 2: Setup environment
    if not setup_environment():
        print("❌ Failed to setup environment")
        return False
    
    # Step 3: Create .env file
    if not create_env_file():
        print("❌ Failed to create environment file")
        return False
    
    # Step 4: Start API server
    print("\n🚀 Starting API server...")
    process, ngrok_url = start_api_server()
    
    if not process:
        print("❌ Failed to start API server")
        return False
    
    # Step 5: Wait for server to initialize
    print("⏳ Waiting for server to initialize...")
    time.sleep(15)
    
    # Step 6: Test API
    test_url = ngrok_url if ngrok_url else "http://localhost:8000"
    result = test_api(test_url)
    
    if result:
        print("\n🎉 Deployment successful!")
        print("=" * 50)
        
        if isinstance(result, str):  # Ngrok URL
            print(f"🌐 Public URL: {result}")
            print(f"📚 API Docs: {result}/docs")
            print(f"🏥 Health Check: {result}/health")
        else:
            print(f"🔗 Local URL: http://localhost:8000")
            print(f"📚 API Docs: http://localhost:8000/docs")
        
        print("\n📱 For Streamlit:")
        print("1. Copy the URL above")
        print("2. Paste into Streamlit app")
        print("3. Start chatting!")
        
        print("\n💡 Keep this notebook running to maintain the API")
        
        # Keep process running
        try:
            process.wait()
        except KeyboardInterrupt:
            print("\n👋 Shutting down...")
            process.terminate()
    
    else:
        print("❌ Deployment failed!")
        return False

if __name__ == "__main__":
    main()