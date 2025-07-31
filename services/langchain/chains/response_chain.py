from typing import Dict, Any, List
from langchain.chains import LLMChain
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate


class ResponseChain:
    """Chain để tạo response - Focus vào sản phẩm hiện tại, tránh nhầm lẫn với lịch sử và tạo link sản phẩm"""
    
    def __init__(self, llm: ChatGoogleGenerativeAI):
        self.llm = llm
        self.greeting_template = self._get_greeting_template()
        self.question_template = self._get_question_template()
        
        self.greeting_chain = LLMChain(llm=self.llm, prompt=self.greeting_template, verbose=False)
        self.question_chain = LLMChain(llm=self.llm, prompt=self.question_template, verbose=False)
    
    def generate_response(self, query_info: Dict[str, Any], context: str, chat_history: str, route: str) -> str:
        """Tạo response - focus vào câu hỏi hiện tại và tạo link sản phẩm"""
        try:
            if route == "GREETING":
                return self._generate_greeting_response(query_info, chat_history)
            else:  # QUESTION
                return self._generate_question_response(query_info, context, chat_history)
        except Exception as e:
            print(f"Error generating response: {e}")
            return "Xin lỗi, tôi không thể tạo phản hồi cho câu hỏi này."
    
    def _generate_greeting_response(self, query_info: Dict[str, Any], chat_history: str) -> str:
        """Tạo response cho greeting"""
        query = query_info.get("enhanced_query", "")
        
        print(f"Greeting - Chat history length: {len(chat_history)} characters")
        
        return self.greeting_chain.run(
            query=query,
            chat_history=chat_history
        )
    
    def _generate_question_response(self, query_info: Dict[str, Any], context: str, chat_history: str) -> str:
        """Tạo response cho question - focus vào sản phẩm hiện tại và tạo link"""
        query = query_info.get("enhanced_query", "")
        
        print(f"Question - Context length: {len(context)} characters")
        print(f"Question - Chat history length: {len(chat_history)} characters")
        print(f"Question - Total input length: {len(context) + len(chat_history) + len(query)} characters")
        
        return self.question_chain.run(
            query=query,
            context=context,
            chat_history=chat_history
        )
    
    def _get_greeting_template(self) -> PromptTemplate:
        """Template cho greeting"""
        template = """Bạn là chuyên gia tư vấn mỹ phẩm thân thiện của Hasaki.

Lịch sử hội thoại:
{chat_history}

Câu chào: {query}

Hướng dẫn:
- Trả lời thân thiện, tự nhiên
- Nếu có lịch sử, tham khảo để trả lời phù hợp
- Mời khách hàng đặt câu hỏi về mỹ phẩm
- Ngắn gọn, ấm áp

Trả lời:"""
        return PromptTemplate(
            input_variables=["query", "chat_history"],
            template=template
        )
    
    def _get_question_template(self) -> PromptTemplate:
        """Template cho question với focus vào sản phẩm hiện tại và tạo link"""
        template = """Bạn là chuyên gia tư vấn mỹ phẩm chuyên nghiệp của Hasaki.

THÔNG TIN SẢN PHẨM LIÊN QUAN ĐẾN CÂU HỎI HIỆN TẠI:
{context}

LỊCH SỬ HỘI THOẠI (chỉ để tham khảo ngữ cảnh):
{chat_history}

CÂU HỎI HIỆN TẠI: {query}

🎯 HƯỚNG DẪN TRẢ LỜI QUAN TRỌNG:

1. LUÔN ƯU TIÊN CÂU HỎI HIỆN TẠI:
   - Phân tích kỹ câu hỏi hiện tại để xác định chính xác sản phẩm/chủ đề được hỏi
   - Trả lời dựa trên THÔNG TIN SẢN PHẨM LIÊN QUAN ở trên (đã được tìm kiếm và rerank cho câu hỏi này)
   - Chỉ sử dụng lịch sử hội thoại để hiểu ngữ cảnh, KHÔNG để lẫn lộn sản phẩm

2. PHÂN BIỆT RÕ SẢN PHẨM:
   - Nếu câu hỏi hiện tại về sản phẩm A, chỉ trả lời về sản phẩm A
   - Nếu lịch sử có sản phẩm B nhưng câu hỏi hiện tại về sản phẩm A, tập trung hoàn toàn vào sản phẩm A
   - Khi có đại từ (nó, sản phẩm này, cái đó), xác định rõ đang nói về sản phẩm nào dựa trên context hiện tại

3. TẠO LINK SẢN PHẨM:
   ✅ KHI NÀO TẠO LINK:
   - Khi đề cập đến sản phẩm cụ thể có tên rõ ràng
   - Khi tư vấn sản phẩm cho khách hàng
   - Khi khách hàng hỏi về giá, thông tin chi tiết sản phẩm
   
   ✅ CÁCH TẠO LINK:
   - BẮT BUỘC sử dụng URL chính xác từ THÔNG TIN SẢN PHẨM LIÊN QUAN
   - Tìm field "url" hoặc "product_url" trong context
   - Sử dụng format: [Tên sản phẩm](URL_từ_context)
   - KHÔNG tự tạo URL hoặc slug
   
   ✅ QUY TẮC QUAN TRỌNG:
   - CHỈ sử dụng URL có sẵn trong context
   - Nếu không có URL trong context, KHÔNG tạo link
   - URL phải chính xác 100% từ data
   - Ví dụ: Nếu context có "url": "https://hasaki.vn/san-pham/sua-rua-mat-cerave-sach-sau-cho-da-thuong-den-da-dau-473ml-102959.html"
   - Thì dùng: [Sữa Rửa Mặt CeraVe](https://hasaki.vn/san-pham/sua-rua-mat-cerave-sach-sau-cho-da-thuong-den-da-dau-473ml-102959.html)

4. QUY TRÌNH TRẢ LỜI:
   a) Đọc và hiểu câu hỏi hiện tại
   b) Xác định sản phẩm/chủ đề được hỏi
   c) Tìm thông tin liên quan trong THÔNG TIN SẢN PHẨM LIÊN QUAN
   d) Tìm URL chính xác của sản phẩm trong context nếu không có thì thôi
   e) Trả lời dựa trên thông tin đó
   f) Tạo link với URL chính xác từ context
   g) Chỉ tham khảo lịch sử nếu thực sự cần thiết cho ngữ cảnh

5. CÁCH TRẢ LỜI TỐT:
   ✅ Trả lời trực tiếp và chính xác câu hỏi hiện tại
   ✅ Sử dụng thông tin từ context (đã được rerank cho câu hỏi này)
   ✅ Đề cập tên sản phẩm cụ thể để tránh nhầm lẫn
   ✅ Tạo link clickable với URL chính xác từ context
   ✅ Thân thiện và chuyên nghiệp
   ✅ Nếu cần so sánh, chỉ so sánh khi được hỏi rõ ràng

6. TRÁNH:
   ❌ Trả lời về sản phẩm khác không liên quan đến câu hỏi hiện tại
   ❌ Lẫn lộn thông tin giữa các sản phẩm khác nhau
   ❌ Sử dụng thông tin cũ không phù hợp với câu hỏi hiện tại
   ❌ Tự động so sánh với sản phẩm trong lịch sử khi không được yêu cầu
   ❌ Tạo link sai format hoặc không chính xác
   ❌ Tự tạo URL thay vì dùng URL từ context

VÍ DỤ TRẢ LỜI CÓ LINK (sử dụng URL từ context):

Nếu context có:
"url": "https://hasaki.vn/san-pham/sua-rua-mat-cerave-sach-sau-cho-da-thuong-den-da-dau-473ml-102959.html"
"name": "Sữa Rửa Mặt CeraVe Sạch Sâu Cho Da Thường Đến Da Dầu 473ml"

Câu hỏi: "Sữa rửa mặt CeraVe có tốt không?"
Trả lời: "[Sữa Rửa Mặt CeraVe Sạch Sâu Cho Da Thường Đến Da Dầu 473ml](https://hasaki.vn/san-pham/sua-rua-mat-cerave-sach-sau-cho-da-thuong-den-da-dau-473ml-102959.html) là một sản phẩm rất tốt..."

Trả lời:"""
        return PromptTemplate(
            input_variables=["query", "context", "chat_history"],
            template=template
        )