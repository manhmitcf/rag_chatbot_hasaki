from typing import List, Dict, Any, Optional
from langchain.memory import ConversationBufferWindowMemory
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, AIMessage


class ConversationMemoryManager:
    """Quản lý memory với ConversationBufferWindowMemory - Không giới hạn text"""
    
    def __init__(self, llm: ChatGoogleGenerativeAI, k: int = 3):
        self.llm = llm
        self.k = k  # Số lượng turns gần nhất
        
        # Sử dụng ConversationBufferWindowMemory thay vì ConversationSummaryMemory
        self.memory = ConversationBufferWindowMemory(
            k=k,  # Chỉ giữ k turns gần nhất
            return_messages=True,
            memory_key="chat_history"
        )
        
        # Lưu trữ context quan trọng từ các turns gần đây
        self._recent_products = []  # Sản phẩm được đ�� cập gần đây
        self._recent_brands = []    # Thương hiệu được đề cập gần đây
        self._recent_categories = [] # Danh mục được đề cập gần đây
    
    def add_conversation_turn(self, user_message: str, ai_message: str):
        """Thêm một lượt hội thoại vào memory"""
        try:
            self.memory.chat_memory.add_user_message(user_message)
            self.memory.chat_memory.add_ai_message(ai_message)
            
            # Trích xuất và lưu context quan trọng
            self._extract_important_entities(user_message, ai_message)
            
        except Exception as e:
            print(f"Lỗi thêm conversation turn: {e}")
    
    def _extract_important_entities(self, user_message: str, ai_message: str):
        """Trích xuất entities quan trọng từ cuộc hội thoại"""
        # Danh sách thương hiệu phổ biến
        brands = ['Anessa', 'Cetaphil', 'La Roche', 'Vichy', 'Eucerin', 'Neutrogena', 
                 'Bioré', 'Nivea', 'Olay', 'L\'Oreal', 'Maybelline', 'Innisfree']
        
        # Danh sách danh mục sản phẩm
        categories = ['kem chống nắng', 'sữa rửa mặt', 'serum', 'toner', 'kem dưỡng',
                     'mask', 'tẩy trang', 'nước hoa hồng', 'kem mắt', 'son m��i']
        
        # Trích xuất từ user message
        user_lower = user_message.lower()
        for brand in brands:
            if brand.lower() in user_lower:
                if brand not in self._recent_brands:
                    self._recent_brands.append(brand)
        
        for category in categories:
            if category in user_lower:
                if category not in self._recent_categories:
                    self._recent_categories.append(category)
        
        # Trích xuất từ AI response
        ai_lower = ai_message.lower()
        for brand in brands:
            if brand.lower() in ai_lower:
                if brand not in self._recent_brands:
                    self._recent_brands.append(brand)
        
        # Trích xuất tên sản phẩm cụ thể từ AI response
        if any(indicator in ai_message for indicator in ['VND', 'đ', 'Giá:', 'Tên sản phẩm:']):
            lines = ai_message.split('\n')
            for line in lines:
                if any(brand in line for brand in brands) and len(line.strip()) > 10:
                    product_name = line.strip()[:100]  # Giới hạn độ dài
                    if product_name not in self._recent_products:
                        self._recent_products.append(product_name)
        
        # Giới hạn số lư��ng để tránh quá dài
        self._recent_brands = self._recent_brands[-5:]
        self._recent_categories = self._recent_categories[-5:]
        self._recent_products = self._recent_products[-3:]
    
    def get_conversation_summary(self) -> str:
        """Lấy summary ngắn gọn từ buffer window"""
        try:
            messages = self.memory.chat_memory.messages
            if not messages:
                return "Chưa có lịch sử hội thoại."
            
            # Tạo summary ngắn gọn từ các turns gần đây
            summary_parts = []
            
            # Thêm context về entities quan trọng
            if self._recent_brands:
                summary_parts.append(f"Thương hiệu đã đề cập: {', '.join(self._recent_brands)}")
            
            if self._recent_categories:
                summary_parts.append(f"Loại sản phẩm quan tâm: {', '.join(self._recent_categories)}")
            
            if self._recent_products:
                summary_parts.append(f"Sản phẩm đã tư vấn: {'; '.join(self._recent_products[:2])}")
            
            # Thêm summary từ 2 turns gần nhất
            recent_messages = messages[-4:] if len(messages) >= 4 else messages
            for i in range(0, len(recent_messages), 2):
                if i + 1 < len(recent_messages):
                    human_msg = recent_messages[i].content
                    ai_msg = recent_messages[i + 1].content
                    
                    # Tóm tắt ngắn gọn
                    if len(human_msg) > 50:
                        human_summary = human_msg[:50] + "..."
                    else:
                        human_summary = human_msg
                    
                    summary_parts.append(f"Đã hỏi: {human_summary}")
            
            return " | ".join(summary_parts) if summary_parts else "Chưa có lịch sử hội thoại."
            
        except Exception as e:
            print(f"Lỗi lấy conversation summary: {e}")
            return "Chưa có lịch sử hội thoại."
    
    def get_formatted_history(self, max_turns: int = None) -> str:
        """Lấy lịch sử hội thoại đã format từ buffer window - KHÔNG GIỚI HẠN TEXT"""
        try:
            messages = self.memory.chat_memory.messages
            if not messages:
                return "Chưa có lịch sử hội thoại."
            
            formatted_history = []
            
            # Buffer window đã giới hạn số messages, không cần giới hạn thêm
            for i in range(0, len(messages), 2):
                if i + 1 < len(messages):
                    human_msg = messages[i]
                    ai_msg = messages[i + 1]
                    
                    # KHÔNG GIỚI HẠN độ dài - sử dụng toàn bộ content
                    human_content = human_msg.content
                    ai_content = ai_msg.content
                    
                    formatted_history.append(f"Người dùng: {human_content}")
                    formatted_history.append(f"Bot: {ai_content}")
            
            formatted_result = "\n".join(formatted_history)
            print(f"Formatted history length: {len(formatted_result)} characters (UNLIMITED)")
            
            return formatted_result
            
        except Exception as e:
            print(f"Lỗi format history: {e}")
            return "Chưa có lịch sử hội thoại."
    
    def get_recent_context(self) -> str:
        """Lấy context gần đây để enhance query"""
        try:
            context_parts = []
            
            # Thêm entities quan trọng
            if self._recent_brands:
                context_parts.append(f"Thương hiệu: {', '.join(self._recent_brands[-2:])}")
            
            if self._recent_categories:
                context_parts.append(f"Loại: {', '.join(self._recent_categories[-2:])}")
            
            # Thêm sản phẩm gần nhất
            if self._recent_products:
                context_parts.append(f"Sản phẩm: {self._recent_products[-1]}")
            
            return " | ".join(context_parts)
            
        except Exception as e:
            print(f"Lỗi lấy recent context: {e}")
            return ""
    
    def enhance_query_with_context(self, query: str) -> str:
        """Enhance query với context từ memory"""
        try:
            # Kiểm tra xem query có đại từ không
            pronouns = ['nó', 'cái đó', 'sản phẩm này', 'thứ này', 'loại này', 'thương hiệu đó']
            has_pronoun = any(pronoun in query.lower() for pronoun in pronouns)
            
            if not has_pronoun:
                return query
            
            # Lấy context để thay thế đại từ
            recent_context = self.get_recent_context()
            if not recent_context:
                return query
            
            # Thay thế đại từ bằng context cụ thể
            enhanced_query = f"{recent_context} - {query}"
            
            # Không giới hạn độ dài nữa
            return enhanced_query
            
        except Exception as e:
            print(f"Lỗi enhance query: {e}")
            return query
    
    def clear_memory(self):
        """Xóa memory"""
        try:
            self.memory.clear()
            self._recent_products = []
            self._recent_brands = []
            self._recent_categories = []
        except Exception as e:
            print(f"Lỗi xóa memory: {e}")
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Lấy thống kê về memory"""
        try:
            total_chars = sum(len(msg.content) for msg in self.memory.chat_memory.messages)
            return {
                "total_messages": len(self.memory.chat_memory.messages),
                "total_characters": total_chars,
                "window_size": self.k,
                "recent_brands": len(self._recent_brands),
                "recent_categories": len(self._recent_categories),
                "recent_products": len(self._recent_products),
                "memory_type": "ConversationBufferWindowMemory",
                "text_limit": "UNLIMITED"
            }
        except Exception as e:
            print(f"Lỗi lấy memory stats: {e}")
            return {
                "total_messages": 0,
                "total_characters": 0,
                "window_size": self.k,
                "recent_brands": 0,
                "recent_categories": 0,
                "recent_products": 0,
                "memory_type": "ConversationBufferWindowMemory",
                "text_limit": "UNLIMITED"
            }