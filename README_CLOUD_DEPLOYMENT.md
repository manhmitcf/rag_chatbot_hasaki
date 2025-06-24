# 🌸 Hasaki RAG Chatbot - Cloud Deployment Guide

Hướng dẫn chi tiết để deploy RAG Chatbot lên Google Colab và Kaggle với Ngrok tunnel.

## 📋 Tổng quan

Dự án bao gồm:
- **`api_colab.py`** - FastAPI server tối ưu cho cloud
- **`streamlit_colab.py`** - Streamlit app kết nối với API cloud
- **`Hasaki_RAG_Chatbot_Colab.ipynb`** - Jupyter notebook cho Colab
- **`kaggle_deploy.py`** - Script tự động cho Kaggle

## 🚀 Deployment trên Google Colab

### Cách 1: Sử dụng Jupyter Notebook (Khuyến nghị)

1. **Upload notebook lên Colab:**
   - Mở [Google Colab](https://colab.research.google.com/)
   - Upload file `Hasaki_RAG_Chatbot_Colab.ipynb`
   - Chọn GPU runtime (Runtime → Change runtime type → GPU)

2. **Chuẩn bị API Keys:**
   - Lấy Gemini API Key từ [Google AI Studio](https://makersuite.google.com/app/apikey)
   - (Tùy chọn) Lấy Ngrok Auth Token từ [Ngrok Dashboard](https://dashboard.ngrok.com/get-started/your-authtoken)

3. **Thiết lập Colab Secrets:**
   - Click vào 🔑 icon bên trái Colab
   - Thêm secrets:
     - `GEMINI_API_KEY`: Your Gemini API key
     - `NGROK_AUTH_TOKEN`: Your Ngrok token (optional)

4. **Upload Project Files:**
   - Tạo folder `rag_chatbot_hasaki` trong Colab
   - Upload tất cả files: `services/`, `config/`, `data/`, `api_colab.py`

5. **Chạy Notebook:**
   - Chạy từng cell theo thứ tự
   - Copy Ngrok URL từ output cuối cùng

### Cách 2: Sử dụng Script Python

```python
# Trong Colab cell
!git clone <your-repo-url>  # hoặc upload files
%cd rag_chatbot_hasaki

# Cài đặt dependencies
!pip install fastapi uvicorn pyngrok python-dotenv
!pip install google-generativeai sentence-transformers transformers torch
!pip install qdrant-client accelerate tokenizers safetensors

# Thiết lập API keys
import os
os.environ['GEMINI_API_KEY'] = 'your-api-key'
os.environ['NGROK_AUTH_TOKEN'] = 'your-ngrok-token'  # optional

# Chạy API server
!python api_colab.py --port 8000
```

## 🔬 Deployment trên Kaggle

### Cách 1: Sử dụng Kaggle Notebook

1. **Tạo Kaggle Dataset:**
   - Upload project files lên Kaggle Dataset
   - Include: `services/`, `config/`, `data/`, `api_colab.py`

2. **Tạo Kaggle Notebook:**
   - Tạo notebook mới
   - Add dataset vừa tạo
   - Enable Internet access

3. **Chạy Deployment Script:**
```python
# Copy kaggle_deploy.py content vào cell
exec(open('/kaggle/input/your-dataset/kaggle_deploy.py').read())
```

### Cách 2: Manual Setup

```python
# Cài đặt dependencies
!pip install fastapi uvicorn pyngrok python-dotenv google-generativeai

# Copy files
!cp -r /kaggle/input/your-dataset/* /kaggle/working/

# Thiết lập environment
import os
os.environ['GEMINI_API_KEY'] = 'your-api-key'

# Chạy server
!python api_colab.py
```

## 🌐 Sử dụng Streamlit App

### Local Streamlit với Cloud API

1. **Cài đặt Streamlit:**
```bash
pip install streamlit requests
```

2. **Chạy Streamlit App:**
```bash
streamlit run streamlit_colab.py
```

3. **Kết nối với API:**
   - Paste Ngrok URL vào Streamlit interface
   - Test connection
   - Bắt đầu chat!

### Deploy Streamlit lên Cloud

#### Streamlit Cloud:
1. Push code lên GitHub
2. Connect với [Streamlit Cloud](https://streamlit.io/cloud)
3. Deploy từ repository

#### Hugging Face Spaces:
1. Tạo Space mới trên [Hugging Face](https://huggingface.co/spaces)
2. Upload `streamlit_colab.py` và `requirements.txt`
3. Configure secrets cho API URL

## 🔧 Cấu hình và Tùy chỉnh

### Environment Variables

```bash
# Required
GEMINI_API_KEY=your_gemini_api_key

# Optional
NGROK_AUTH_TOKEN=your_ngrok_token
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION_NAME=hasaki_products
```

### API Endpoints

- **Health Check**: `GET /health`
- **System Info**: `GET /system-info`
- **Chat**: `POST /chat`
- **Clear History**: `POST /clear-history`
- **Setup Ngrok**: `POST /setup-ngrok`

### Streamlit Features

- 🔍 Auto-detect Ngrok URLs
- ✅ Real-time API status checking
- 📊 Display metadata (intent, processing time, etc.)
- 🗑️ Clear conversation history
- ⚙️ Adjustable parameters (top_k, rerank_top_k, timeout)

## 🛠️ Troubleshooting

### Common Issues

#### 1. API không khởi động được
```bash
# Kiểm tra dependencies
pip list | grep fastapi

# Kiểm tra port
netstat -tulpn | grep :8000

# Kiểm tra logs
python api_colab.py --port 8000
```

#### 2. Ngrok tunnel thất bại
```bash
# Cài đặt pyngrok
pip install pyngrok

# Thiết lập auth token
from pyngrok import ngrok
ngrok.set_auth_token("your-token")
```

#### 3. RAG Service không khởi tạo được
- Kiểm tra API keys trong `.env`
- Đảm bảo có đủ RAM/GPU
- Kiểm tra kết nối internet

#### 4. Streamlit không kết nối được API
- Kiểm tra URL có đúng format không
- Test API health endpoint trước
- Kiểm tra CORS settings

### Performance Tips

1. **Sử dụng GPU** trên Colab/Kaggle
2. **Cache models** để tránh reload
3. **Optimize timeout** settings
4. **Monitor memory usage**

## 📊 Monitoring và Logs

### API Monitoring
```python
# Check system info
import requests
response = requests.get(f"{api_url}/system-info")
print(response.json())
```

### Streamlit Monitoring
- Sidebar hiển thị API status
- Real-time connection testing
- Processing time tracking

## 🔒 Security Notes

1. **Không commit API keys** vào code
2. **Sử dụng environment variables** hoặc secrets
3. **Ngrok URLs là public** - cẩn thận với sensitive data
4. **Rotate API keys** định kỳ

## 📱 Mobile Access

Ngrok URLs có thể truy cập từ mobile:
- Copy URL từ deployment output
- Mở trên mobile browser
- Sử dụng `/docs` endpoint để test

## 🤝 Collaboration

### Chia sẻ API:
1. Share Ngrok URL với team
2. Provide API documentation
3. Set up monitoring dashboard

### Multiple Environments:
- Development: Local
- Staging: Colab
- Production: Dedicated server

## 📈 Scaling

### Horizontal Scaling:
- Deploy multiple instances
- Use load balancer
- Implement session management

### Vertical Scaling:
- Upgrade Colab to Pro
- Use high-memory Kaggle kernels
- Optimize model loading

---

## 🎯 Quick Start Checklist

- [ ] Lấy Gemini API Key
- [ ] (Optional) Lấy Ngrok Auth Token
- [ ] Upload project files lên Colab/Kaggle
- [ ] Chạy deployment script/notebook
- [ ] Copy Ngrok URL
- [ ] Test API endpoints
- [ ] Chạy Streamlit app
- [ ] Paste URL vào Streamlit
- [ ] Bắt đầu chat!

## 🆘 Support

Nếu gặp vấn đề:
1. Kiểm tra logs trong Colab/Kaggle output
2. Test từng component riêng lẻ
3. Verify API keys và permissions
4. Check network connectivity

---

**🌸 Happy Deploying with Hasaki RAG Chatbot! 🌸**

**Phát triển bởi**: Hasaki RAG Team  
**Phiên bản**: 2.0.0 - Cloud Edition