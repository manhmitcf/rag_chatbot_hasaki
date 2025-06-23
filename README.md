# 🧴 Cosmetics Advisor - Hệ thống tư vấn mỹ phẩm thông minh

Hệ thống tư vấn mỹ phẩm sử dụng RAG (Retrieval-Augmented Generation) với Qdrant vector database và Gemini AI để cung cấp lời khuyên chuyên nghiệp về sản phẩm mỹ phẩm qua chat terminal.

## Cấu trúc thư mục

```
rag_chatbot_hasaki/
├── config/
│   ├── __init__.py
│   └── settings.py          # Cấu hình hệ thống
├── services/
│   ├── __init__.py
│   ├── qdrant_service.py    # Service cho Qdrant
│   ├── gemini_service.py    # Service cho Gemini AI
│   └── rag_service.py       # Service chính RAG
├── .env                     # Environment variables
├── simple_chat.py          # Chat terminal đơn giản
├── chat_terminal.py        # Chat terminal với nhiều tính năng
├── advanced_chat.py        # Chat terminal nâng cao với filter
├── requirements.txt         # Dependencies
└─��� README.md               # Hướng dẫn này
```

## Cài đặt

### 1. Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### 2. Cài đặt và chạy Qdrant

```bash
# Tải và chạy Qdrant
curl -L https://github.com/qdrant/qdrant/releases/download/v1.7.0/qdrant-x86_64-pc-windows-msvc.zip -o qdrant.zip
unzip qdrant.zip
./qdrant.exe
```

### 3. Cấu hình API Keys

Chỉnh sửa file `.env`:

```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION_NAME=cosmetics_products
```

## Sử dụng

### Chat trực tiếp trên Terminal

**Chat đơn giản:**
```bash
python simple_chat.py
```

**Chat với nhiều tính năng:**
```bash
python chat_terminal.py
```

**Chat nâng cao với filter tùy chỉnh:**
```bash
python advanced_chat.py
```

### Test Reranker

**Test hiệu suất reranker:**
```bash
python test_rerank.py
```

## Tính năng

- ✅ **Tư vấn mỹ phẩm thông minh** với AI
- ✅ **Vector search** với Qdrant cho tìm kiếm sản phẩm chính xác
- ✅ **Text generation** với Gemini AI cho lời khuyên chuyên nghiệp
- ✅ **Advanced filtering system** cho mỹ phẩm (loại da, thương hiệu, giá cả, thành phần)
- ✅ **BGE Reranker v2-m3** cải thiện độ chính xác tìm kiếm
- ✅ **Vietnamese language support** với embedding model tối ưu
- ✅ **3 chế độ chat terminal** từ đơn giản đến nâng cao
- ✅ **Works with pre-embedded cosmetics data** trong Qdrant

## Ví dụ câu hỏi

- "Tôi có da khô, nên dùng kem dưỡng ẩm nào?"
- "Serum vitamin C nào tốt cho da lão hóa?"
- "Sản phẩm trị mụn giá dưới 300k"
- "So sánh kem chống nắng Anessa và La Roche Posay"
- "Routine skincare cho da nhạy cảm"
- "Kem nền nào phù hợp với da dầu?"

## Filter cho mỹ phẩm

**Các trường filter phổ biến:**
- `category`: cleanser, moisturizer, serum, sunscreen, foundation, toner
- `skin_type`: dry, oily, combination, sensitive, normal
- `brand`: tên thương hiệu
- `skin_concern`: acne, aging, dark_spots, wrinkles
- `price`: khoảng giá (VND)
- `ingredient`: vitamin_c, hyaluronic_acid, niacinamide, retinol
- `alcohol_free`: true/false

## Lưu ý

1. Đảm bảo có API key hợp lệ cho Gemini AI
2. Qdrant server phải chạy trước khi start ứng dụng
3. Hệ thống sẽ tự động tạo collection `cosmetics_products` nếu chưa tồn tại
4. Hệ thống hoạt động với data mỹ phẩm đã được embedding sẵn trong Qdrant
5. Sử dụng filters để tìm kiếm sản phẩm chính xác theo nhu cầu khách hàng
6. Hệ thống hỗ trợ tiếng Việt với Vietnamese embedding model
7. Prompt được tối ưu hóa cho tư vấn mỹ phẩm chuyên nghiệp

## Troubleshooting

### Lỗi kết nối Qdrant
- Kiểm tra Qdrant server có đang chạy không
- Kiểm tra host và port trong file .env

### Lỗi Gemini API
- Kiểm tra API key có hợp lệ không
- Kiểm tra quota API còn lại

### Lỗi dependencies
- Chạy lại: `pip install -r requirements.txt`
- Kiểm tra Python version (khuyến nghị >= 3.8)