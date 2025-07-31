# 🌸 Hasaki Beauty AI Chatbot Frontend

Giao diện web hiện đại cho chatbot tư vấn mỹ phẩm với thiết kế chuyên nghiệp như một sản phẩm thực thụ.

## ✨ Tính năng

### 🎨 **Giao diện đẹp**
- Design hiện đại với gradient và animations
- Responsive design cho mọi thiết bị
- Dark/Light theme tự động
- Icons và typography chuyên nghiệp

### 💬 **Chat Experience**
- Real-time messaging với typing indicators
- Auto-scroll và message animations
- Quick action buttons cho câu hỏi phổ biến
- Character counter và auto-resize textarea

### 🤖 **AI Features**
- Loading states với progress steps
- Error handling và retry logic
- Connection status monitoring
- Memory management (clear chat)

### 📊 **Analytics**
- Message counter
- Product recommendation tracking
- Response time display
- Document count information

## 🚀 Cách chạy

### Option 1: Chạy to��n bộ hệ thống
```bash
cd /home/manhblue/Desktop/rag_chatbot_hasaki
python run_full_system.py
```

### Option 2: Chỉ chạy frontend
```bash
cd /home/manhblue/Desktop/rag_chatbot_hasaki/frontend
python server.py
```

## 🌐 URLs

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8002
- **API Docs**: http://localhost:8002/docs

## 📱 Responsive Design

- **Desktop**: Full features với sidebar
- **Tablet**: Optimized layout
- **Mobile**: Touch-friendly interface

## 🎯 User Experience

### **Welcome Flow**
1. Hiển thị welcome message với hướng dẫn
2. Quick action buttons cho câu hỏi phổ biến
3. Auto-focus vào input field

### **Chat Flow**
1. User nhập câu hỏi
2. Hiển thị loading với progress steps
3. AI response với formatting đẹp
4. Metadata hiển thị (thời gian, số documents)

### **Error Handling**
1. Connection status monitoring
2. Auto-retry với exponential backoff
3. User-friendly error messages
4. Support contact options

## 🛠️ Technical Stack

- **HTML5**: Semantic markup
- **CSS3**: Modern styling với CSS Variables
- **Vanilla JavaScript**: No frameworks, pure performance
- **Font Awesome**: Professional icons
- **Google Fonts**: Inter font family

## 🎨 Design System

### **Colors**
- Primary: `#ff6b9d` (Pink)
- Secondary: `#4ecdc4` (Teal)
- Accent: `#ffd93d` (Yellow)
- Success: `#6bcf7f` (Green)
- Error: `#ff6b6b` (Red)

### **Typography**
- Font: Inter (Google Fonts)
- Sizes: 12px - 30px
- Weights: 300, 400, 500, 600, 700

### **Spacing**
- Base unit: 4px
- Scale: 4px, 8px, 12px, 16px, 20px, 24px, 32px, 40px, 48px

### **Shadows**
- Small: `0 1px 2px rgba(0,0,0,0.05)`
- Medium: `0 4px 6px rgba(0,0,0,0.1)`
- Large: `0 10px 15px rgba(0,0,0,0.1)`
- XL: `0 20px 25px rgba(0,0,0,0.1)`

## 📦 File Structure

```
frontend/
├── index.html          # Main HTML file
├── styles.css          # All CSS styles
├── script.js           # JavaScript functionality
├── server.py           # Simple HTTP server
└── README.md           # This file
```

## 🔧 Configuration

Edit `script.js` để thay đổi cấu hình:

```javascript
const CONFIG = {
    API_BASE_URL: 'http://localhost:8002',
    MAX_MESSAGE_LENGTH: 500,
    TYPING_DELAY: 1000,
    RETRY_ATTEMPTS: 3,
    RETRY_DELAY: 2000
};
```

## 🎭 Features Demo

### **Chat Interface**
- Bubble-style messages
- User/Bot avatars
- Timestamp và metadata
- Smooth animations

### **Loading States**
- Spinner animation
- Progress steps (Search → Analyze → Generate)
- Typing indicator
- Connection status

### **Error Handling**
- Modal dialogs
- Retry buttons
- Support contact
- Graceful degradation

### **Mobile Experience**
- Touch-friendly buttons
- Optimized layouts
- Swipe gestures
- Responsive typography

## 🚀 Performance

- **Lightweight**: No heavy frameworks
- **Fast**: Vanilla JS performance
- **Optimized**: Minimal HTTP requests
- **Cached**: Static assets caching

## 🔒 Security

- **CORS**: Proper headers
- **Input validation**: Client-side checks
- **XSS protection**: Content sanitization
- **Error handling**: No sensitive data exposure

## 🎉 Production Ready

Frontend này được thiết kế như một sản phẩm thực thụ với:

- ✅ Professional UI/UX
- ✅ Error handling
- ✅ Loading states
- ✅ Responsive design
- ✅ Accessibility features
- ✅ Performance optimization
- ✅ SEO friendly
- ✅ Cross-browser compatibility

Sẵn sàng để deploy và sử dụng trong production!