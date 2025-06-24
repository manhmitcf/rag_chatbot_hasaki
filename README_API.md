# 🌸 Hasaki RAG Chatbot - API & Web Interface

Dự án chatbot tư vấn mỹ phẩm sử dụng RAG (Retrieval-Augmented Generation) với FastAPI và Streamlit.

## 🚀 Cài đặt

### 1. Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### 2. Cấu hình môi trường

Đảm bảo file `.env` đã được cấu hình đúng với các API keys cần thiết.

## 🖥️ Chạy ứng dụng

### Cách 1: Chạy tự động (Khuyến nghị)

```bash
python run_servers.py
```

Script này sẽ tự động khởi động cả FastAPI server và Streamlit app.

### Cách 2: Chạy thủ công

#### Khởi động FastAPI server:
```bash
python api.py
```
hoặc
```bash
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

#### Khởi động Streamlit app (terminal khác):
```bash
streamlit run streamlit_app.py --server.port 8501
```

## 🔗 Truy cập ứng dụng

- **Streamlit Web App**: http://localhost:8501
- **FastAPI Documentation**: http://localhost:8000/docs
- **FastAPI Health Check**: http://localhost:8000/health

## 📋 API Endpoints

### 1. Health Check
```
GET /health
```
Kiểm tra trạng thái hệ thống.

### 2. Chat
```
POST /chat
```
**Request Body:**
```json
{
    "message": "Tư vấn kem chống nắng cho da nhạy cảm",
    "session_id": "optional_session_id"
}
```

**Response:**
```json
{
    "success": true,
    "answer": "Câu trả lời từ chatbot...",
    "intent": "GENERAL_QUESTION",
    "id_product": "12345",
    "name_product": "Tên sản phẩm",
    "error": null
}
```

### 3. Clear History
```
POST /clear-history
```
Xóa lịch sử hội thoại.

## 🌐 Giao diện Streamlit

### Tính năng chính:
- 💬 Chat interface thân thiện
- 🔍 Hiển thị thông tin chi tiết (intent, ID sản phẩm, tên sản phẩm)
- 🗑️ Xóa lịch sử hội thoại
- ✅ Kiểm tra trạng thái API real-time
- 📋 Hướng dẫn sử dụng tích hợp

### Cách sử dụng:
1. Mở trình duyệt và truy cập http://localhost:8501
2. Đảm bảo API server đang chạy (kiểm tra sidebar)
3. Nhập câu hỏi vào ô chat
4. Xem phản hồi và thông tin chi tiết

## 🔧 Cấu trúc dự án

```
rag_chatbot_hasaki/
├── api.py                 # FastAPI server
├── streamlit_app.py       # Streamlit web app
├── run_servers.py         # Script khởi động t��� động
├── main.py               # Terminal interface (cũ)
├── requirements.txt      # Dependencies
├── services/             # RAG services
├── config/              # Cấu hình
├── data/                # Dữ liệu
└── README_API.md        # Hướng dẫn này
```

## 🎯 Các loại câu hỏi được hỗ trợ

### 1. Sản phẩm cụ thể (SPECIFIC_PRODUCT)
- "Thông tin về kem chống nắng Anessa"
- "Giá của sản phẩm ID: 12345"
- "Sản phẩm này có tốt không?"

### 2. Câu hỏi tổng quát (GENERAL_QUESTION)
- "Có những loại sữa rửa mặt nào?"
- "Tư vấn kem dưỡng ẩm cho da khô"
- "Sản phẩm nào phù hợp với da nhạy cảm?"

### 3. Chào hỏi và cảm ơn
- "Xin chào"
- "Cảm ơn bạn"
- "Tạm biệt"

## 🛠️ Troubleshooting

### API không khả dụng
1. Kiểm tra FastAPI server có đang chạy không
2. Kiểm tra port 8000 có bị chiếm không
3. Xem log lỗi trong terminal

### Streamlit không kết nối được API
1. Đảm bảo API server chạy trước Streamlit
2. Kiểm tra URL API trong `streamlit_app.py`
3. Kiểm tra firewall/antivirus

### Lỗi khởi tạo RAG Service
1. Kiểm tra file `.env` và API keys
2. Đảm bảo tất cả dependencies đã được cài đặt
3. Kiểm tra kết nối internet

## 📝 Ghi chú

- Streamlit app sẽ tự động kiểm tra trạng thái API
- Lịch sử hội thoại được lưu trong session của Streamlit
- API hỗ trợ CORS để có thể gọi từ frontend khác
- Timeout cho API calls là 30 giây

## 🤝 Đóng góp

Nếu bạn muốn đóng góp cho dự án, vui lòng tạo pull request hoặc báo cáo issues.

---

**Phát triển bởi**: Hasaki RAG Team  
**Phiên bản**: 1.0.0