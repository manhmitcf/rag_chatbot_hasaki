import google.generativeai as genai
from config.settings import settings
from typing import List, Dict, Any
from indentity.indentity import Identity_Brand, Identity_Category_Name
class GeminiService:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('models/gemini-2.5-flash')
        self.conversation_history = []
        self.brand_identity = Identity_Brand().brand
        self.category_identity = Identity_Category_Name().category_name
        self.conversation_history_length = -3
    def generate_response(self, query: str, context_documents: List[Dict[str, Any]]) -> str:
        """Tạo response dựa trên query và context documents"""
        try:
            # Tạo context từ documents
            context = self._build_context(context_documents)
            
            # Tạo prompt
            prompt = self._build_prompt(query, context)
            
            # Generate response
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"Error generating response: {e}")
            return "Xin lỗi, tôi không thể tạo phản hồi cho câu hỏi này."
    
    
    def _build_context(self, search_results):
        """Prepare context from search results với metadata chi tiết và payload data đầy đủ"""
        if not search_results:
            return "Không tìm thấy thông tin sản phẩm phù hợp."
        
        context_parts = []
        
        for idx, result in enumerate(search_results, 1):
            # Lấy metadata từ result dictionary
            metadata = result.get('metadata', {})
            rerank_metadata = result.get('rerank_metadata', {})
            
            # Thông tin cơ bản về sản phẩm với payload data đầy đủ
            product_info = f"""
                        CHUNK #{idx}:
                        =============
                        📋 THÔNG TIN SẢN PHẨM CHI TIẾT:
                        • Sản phẩm ID: {metadata.get('product_id', 'N/A')}
                        • Tên sản phẩm: {metadata.get('name', 'N/A')}
                        • Tên tiếng Anh: {metadata.get('english_name', 'N/A')}
                        • Thương hiệu: {metadata.get('brand', 'N/A')}
                        • Danh mục: {metadata.get('category_name', 'N/A')}
                        • Dung tích/Phiên bản: {metadata.get('data_variant', 'N/A')}
                        • Giá hiện tại: {metadata.get('price', 'N/A')} VND
                        • Đánh giá trung bình: {metadata.get('average_rating', 'N/A')}/5
                        • Tổng số đánh giá: {metadata.get('total_rating', 'N/A')} lượt
                        • Số lượng đã bán: {metadata.get('item_count_by', 'N/A')}
                        • Loại thông tin chunk: {metadata.get('type', 'N/A')}

                        📊 ĐIỂM SỐ TÌM KIẾM & RERANKING:
                        • Vector Score (tìm kiếm ban đầu): {result.get('vector_score', result.get('score', 0)):.4f}
                        • Rerank Score (sau khi rerank): {result.get('rerank_score', result.get('score', 0)):.4f}
                        • Độ cải thiện từ reranking: {rerank_metadata.get('score_improvement', 0):+.4f}
                        • Thứ hạng cuối cùng: #{rerank_metadata.get('final_rank', idx)}
                        • Thay đổi thứ hạng: {rerank_metadata.get('rank_change', 0):+d} vị trí

                        📝 NỘI DUNG CHUNK:
                        {result.get('text', 'N/A')}

                        🔍 ENRICHED CONTENT (được sử dụng trong reranking):
                        {self._create_enriched_preview(result)}
                        """
            context_parts.append(product_info)
        
        return "\n" + "="*80 + "\n".join(context_parts) + "\n" + "="*80
    
    def _create_enriched_preview(self, result: Dict[str, Any]) -> str:
        """Tạo preview của enriched content được sử dụng trong reranking"""
        try:
            metadata = result.get('metadata', {})
            text = result.get('text', '')
            
            # Tạo metadata context giống như trong reranker
            metadata_parts = []
            
            if metadata.get('product_id'):
                metadata_parts.append(f"Mã sản phẩm: {metadata['product_id']}")
            if metadata.get('name'):
                metadata_parts.append(f"Tên sản phẩm: {metadata['name']}")
            if metadata.get('brand'):
                metadata_parts.append(f"Thương hiệu: {metadata['brand']}")
            if metadata.get('category_name'):
                metadata_parts.append(f"Danh mục: {metadata['category_name']}")
            if metadata.get('price'):
                metadata_parts.append(f"Giá: {metadata['price']} VND")
            
            if metadata_parts:
                metadata_context = " | ".join(metadata_parts)
                preview = f"{metadata_context}\n\nNội dung: {text[:100]}..."
            else:
                preview = f"Nội dung: {text[:100]}..."
            
            return preview
            
        except Exception as e:
            return f"Lỗi tạo preview: {e}"
    
    def _build_prompt(self, query: str, context: str) -> str:
        """Xây dựng prompt cho Gemini - tối ưu cho mỹ phẩm"""
        prompt = f"""
                Bạn là một chuyên gia tư vấn mỹ phẩm, chăm sóc sắc đẹp thông minh. Hãy trả lời câu hỏi về mỹ phẩm, chăm sóc sắc đẹp, trả lời dựa trên thông tin sản phẩm được cung cấp.

                THÔNG TIN TÌM THẤY ĐƯỢC (đã được rerank và enriched):
                {context}

                CÂU HỎI KHÁCH HÀNG: {query}

                LỊCH SỬ HỘI THOẠI:
                {self.get_conversation_context()[: self.conversation_history_length]}

                Hướng dẫn trả lời:
                - Trả lời dựa trên thông tin được cung cấp (bao gồm cả metadata và enriched content)
                - Tận dụng thông tin chi tiết về sản phẩm (ID, giá, đánh giá, thương hiệu, etc.)
                - Tập trung vào ngữ cảnh phía trước và yêu cầu của khách hàng hiện tại
                - Nếu thông tin không đủ để trả lời thì trả lời "Không tìm thấy"
                - Trả lời bằng tiếng Việt, thân thiện và chuyên nghiệp
                - Sử dụng thông tin reranking score để ưu tiên chunks có độ liên quan cao hơn

                TRẢ LỜI :
                """
        return prompt
    def build_promt_intent(self, query: str) -> str:
        """Xây dựng prompt cho Gemini - tối ưu cho ý định người dùng"""
        promt = f"""    Bạn là AI phân tích ý định người dùng. Phân loại câu hỏi sau vào một trong hai nhóm:
        1. SPECIFIC_PRODUCT: Người dùng hỏi về một sản phẩm cụ thể, có thể bằng tên, ID, mã, hoặc hỏi về một sản phẩm đang được thảo luận.
        2. GENERAL_QUESTION: Người dùng chào hỏi, cảm ơn, hoặc hỏi những câu không liên quan trực tiếp đến một sản phẩm cụ thể (ví dụ: "shop có những loại dầu gội nào?").

        LỊCH SỬ HỘI THOẠI:
        {self.get_conversation_context()[: self.conversation_history_length]}

        CÂU HỎI HIỆN TẠI: "{query}"

        PHÂN TÍCH VÀ TRẢ VỀ DUY NHẤT DÒNG SAU:
        Intent: <SPECIFIC_PRODUCT|GENERAL_QUESTION>

        VÍ DỤ:
        - "Thông tin của sản phẩm ID: 12345" -> Intent: SPECIFIC_PRODUCT
        - "Giá của kem chống nắng Anessa là bao nhiêu?" -> Intent: SPECIFIC_PRODUCT
        - "Sản phẩm này dùng thế nào?" -> Intent: SPECIFIC_PRODUCT
        - "Xin chào, bạn có khỏe không?" -> Intent: GENERAL_QUESTION
        - "Bạn có thể gợi ý cho tôi một loại sữa rửa mặt không?" -> Intent: GENERAL_QUESTION
        - "Cảm ơn shop đã tư vấn" -> Intent: GENERAL_QUESTION
        - "Các sản phẩm về sửa rửa mặt" -> Intent: GENERAL_QUESTION
        """
        try:
            response = self.model.generate_content(promt)
            return self.parse_intent_response(response.text)
        except Exception as e:
            print(f"Error generating intent response: {e}")
            return "GENERAL_QUESTION"
        

    def parse_intent_response(self, response_text):
        intent = None
        for line in response_text.split("\n"):
            line = line.strip()
            if line.lower().startswith("intent:"):
                intent = line.split(":", 1)[1].strip()
                if intent not in ["SPECIFIC_PRODUCT", "GENERAL_QUESTION"]:
                    intent = "GENERAL_QUESTION"
        return intent
    

    def get_conversation_context(self):
        """Lấy ngữ cảnh hội thoại từ lịch sử"""
        if not self.conversation_history:
            return "Chưa có lịch sử hội thoại."
        
        context_parts = []
        for idx, turn in enumerate(self.conversation_history, 1):
            user_input = turn.get('User Input', '')
            bot_response = turn.get('Bot', '')
            intent = turn.get('intent', '')
            id_product = turn.get('id_product', '')
            name_product = turn.get('name_product', '')
            
            context_part = f"Lượt {idx}:\n"
            context_part += f"Người dùng: {user_input}\n"
            context_part += f"Bot: {bot_response}\n"
            if intent:
                context_part += f"Ý định: {intent}\n"
            if id_product:
                context_part += f"ID sản phẩm: {id_product}\n"
            if name_product:
                context_part += f"Tên sản phẩm: {name_product}\n"
            
            
            context_parts.append(context_part)
        
        return context_parts
    

    def append_to_conversation(self, user_input: str, bot_response: str, intent: str = None, id_product: str = None, name_product: str = None):
        """Thêm câu hỏi và câu trả lời vào lịch sử hội thoại"""
        conversation_turn = {
            "User Input": user_input,
            "Bot": bot_response,
            "intent": intent,
            "name_product": name_product,
            "id_product": id_product
        }
        self.conversation_history.append(conversation_turn)

    def parse_filter_response(self, response_text: str) -> Dict[str, Any]:
        """Xử lý text response từ Gemini để trích xuất thông tin filter"""
        result = {
            "id_product": None,
            "name_product": None, 
            "category_name": None,
            "brand": None
        }
        
        try:
            # Tách response thành các dòng
            lines = response_text.strip().split('\n')
            
            for line in lines:
                line = line.strip()
                
                # Xử lý ID
                if line.upper().startswith('ID:'):
                    value = line.split(':', 1)[1].strip()
                    if value.upper() != 'NONE' and value:
                        result["id_product"] = value
                
                # Xử lý NAME
                elif line.upper().startswith('NAME:'):
                    value = line.split(':', 1)[1].strip()
                    if value.upper() != 'NONE' and value:
                        result["name_product"] = value
                
                # Xử lý CATEGORY
                elif line.upper().startswith('CATEGORY:'):
                    value = line.split(':', 1)[1].strip()
                    if value.upper() != 'NONE' and value:
                        result["category_name"] = value
                
                # Xử lý BRAND
                elif line.upper().startswith('BRAND:'):
                    value = line.split(':', 1)[1].strip()
                    if value.upper() != 'NONE' and value:
                        result["brand"] = value
            
            return result
            
        except Exception as e:
            print(f"Error parsing filter response: {e}")
            return result

    def identify_key_for_filter(self, query: str) -> Dict[str, Any]:
        """Xác định các key để filter sản phẩm từ query và lịch sử hội thoại"""
        
        prompt = f"""Bạn là AI chuyên lấy thông tin cho các trường từ lịch sử chat và câu hỏi hiện tại của người dùng dể xác định hiện tại đang tìm về các trường cần lấy thông tin nào:

        CÁC TRƯỜNG CẦN LẤY:
        product_id: Mã định danh duy nhất của sản phẩm trong hệ thống cơ sở dữ liệu.
        name: Tên sản phẩm bằng tiếng Việt.
        english_name: Tên sản phẩm bằng tiếng Anh, hỗ trợ đa ngôn ngữ hoặc phục vụ các thị trường quốc tế.
        category_name: Tên danh mục sản phẩm, bằng tiếng Việt.
        brand: Tên thương hiệu của sản phẩm.
        
        LỊCH SỬ HỘI THOẠI:
        {self.get_conversation_context()[: self.conversation_history_length]}
        

        CÂU HỎI CỦA NGƯỜI DÙNG HIỆN TẠI: "{query}"

        CÁC BRAND: {self.brand_identity}
        CÁC CATEGORY: {self.category_identity}

        Dựa vào ngữ cảnh phía trước và câu hỏi của người dùng, trả lời các trường cần lấy thông tin như trên.

        TRẢ VỀ ĐÚNG ĐỊNH DẠNG SAU:
        ID: <ID hoặc NONE>
        NAME: <Tên hoặc NONE>
        CATEGORY: <Tên hoặc NONE>
        BRAND: <Tên hoặc NONE>
        """
        
        try:
            response = self.model.generate_content(prompt)
            return self.parse_filter_response(response.text)
        except Exception as e:
            print(f"Error generating filter response: {e}")
            return {"id_product": None, "name_product": None, "category_name": None, "brand": None}
        

    def enhance_query_with_history(self, current_query: str) -> str:
        """
        Tăng cường query từ người dùng bằng cách sử dụng lịch sử hội thoại của 3 đoạn gần nhất
        
        Args:
            current_query (str): Câu hỏi hiện tại của người dùng
            
        Returns:
            str: Câu hỏi đã được tăng cường với ngữ cảnh từ lịch sử hội thoại
        """
    
        # Nếu không có lịch sử hội thoại, trả về query gốc
        if not self.conversation_history:
            return current_query
        
        # Lấy 3 lượt hội thoại gần nhất
        recent_history = self.conversation_history[self.conversation_history_length:]
        
        
        # Xây dựng prompt để tăng cường query
        enhancement_prompt = f"""
        Bạn là AI chuyên gia tăng cường câu hỏi. Nhiệm vụ của bạn là làm cho câu hỏi hiện tại trở nên rõ ràng và đầy đủ hơn bằng cách sử dụng ngữ cảnh từ lịch sử hội thoại.

        LỊCH SỬ HỘI THOẠI GẦN ĐÂY:
        {self.get_conversation_context()[: self.conversation_history_length]}
   
        
    
        
        CÂU HỎI HIỆN TẠI: "{current_query}"
        
        HƯỚNG DẪN TĂNG CƯỜNG:
        1. Nếu câu hỏi hiện tại đề cập đến "sản phẩm này", "nó", "cái đó" - hãy thay thế bằng tên sản phẩm cụ thể từ lịch sử
        2. Nếu câu hỏi thiếu ngữ cảnh, hãy bổ sung thông tin từ cuộc hội thoại trước
        3. Nếu câu hỏi đã đầy đủ và rõ ràng, giữ nguyên
        4. Chỉ trả về câu hỏi đã được tăng cường, không giải thích thêm
        5. Giữ nguyên ngôn ngữ tiếng Việt
        
        Hãy tạo query mở rộng bao gồm:
        1. Từ khóa từ query gốc
        2. Thông tin liên quan từ lịch sử hội thoại
        3. Ngữ cảnh sản phẩm hiện tại (nếu có)

        TRẢ VỀ:
        Enhanced_Query: <query đã được cải thiện>

        VÍ DỤ:
        - Query gốc: "giá bao nhiêu" + Lịch sử: đang hỏi về dầu gội Pantene
        → Enhanced_Query: "giá dầu gội Pantene"

        - Query gốc: "có tốt không" + Lịch sử: đang tư vấn sản phẩm ID 12345
        → Enhanced_Query: "đánh giá chất lượng sản phẩm ID 12345"
        """
        
        try:
            # Gọi Gemini để tăng cường query
            response = self.model.generate_content(enhancement_prompt)
            enhanced_query = self.parse_enhanced_query(response.text)
            return enhanced_query
        except Exception as e:
            print(f"Error enhancing query: {e}")
            return current_query

    def parse_enhanced_query(self, response_text):
        for line in response_text.splitlines():
            line = line.strip()
            if line.lower().startswith("enhanced_query:"):
                enhanced = line.split(":", 1)[1].strip()
                return enhanced
        return None