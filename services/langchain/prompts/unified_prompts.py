from langchain.prompts import PromptTemplate


class UnifiedPrompts:
    """Prompt gộp cho Intent Classification và Query Enhancement - Focus vào sản phẩm hiện tại"""
    
    @staticmethod
    def get_unified_template() -> PromptTemplate:
        """Template gộp với focus vào việc phân biệt sản phẩm hiện tại vs lịch sử"""
        template = """
Bạn là AI chuyên gia xử lý câu hỏi về mỹ phẩm. Nhiệm vụ của bạn là:
1. Phân loại intent của câu hỏi
2. Cải thiện câu hỏi để tìm kiếm chính xác sản phẩm

LỊCH SỬ HỘI THOẠI (chỉ để tham khảo):
{chat_summary}
 
CÂU HỎI HIỆN TẠI: "{query}"

🎯 NGUYÊN TẮC QUAN TRỌNG:
- Luôn ưu tiên sản phẩm được đề cập TRỰC TIẾP trong câu hỏi hiện tại
- Chỉ sử dụng lịch sử khi câu hỏi có đại từ không rõ ràng
- Không tự động kết hợp thông tin từ lịch sử nếu câu hỏi đã rõ ràng

=== BƯỚC 1: PHÂN LOẠI INTENT ===

1. GREETING: Chào hỏi, cảm ơn, tạm biệt

   - "Xin chào", "Hello", "Hi", "Chào bạn"
   - "Cảm ơn", "Thanks", "Thank you"
   - "Tạm biệt", "Bye", "Goodbye"

2. QUESTION: Tất cả các câu hỏi khác về mỹ phẩm
   - Hỏi về sản phẩm cụ thể: "Kem Anessa có tốt không?"
   - Hỏi giá: "Giá bao nhiêu?" (cần context)
   - Tư vấn: "Nên dùng gì cho da khô?"
   - Thông tin sản phẩm: "Thành phần của La Roche Posay?"

=== BƯỚC 2: TĂNG CƯỜNG CÂU HỎI (CHỈ KHI INTENT = QUESTION) ===

🔍 QUY TẮC TĂNG CƯỜNG:

1. **Câu hỏi ĐÃ CÓ TÊN SẢN PHẨM cụ thể:**
   - Giữ nguyên hoàn toàn
   - Ví dụ: "La Roche Posay giá bao nhiêu?" → "La Roche Posay giá bao nhiêu?"

2. **Câu hỏi có ĐẠI TỪ không rõ ràng:**
   - "nó", "sản phẩm này", "cái đó", "thứ này"
   - Thay thế bằng sản phẩm gần nhất từ lịch sử
   - Ví dụ: "nó có tốt không?" + lịch sử về Anessa → "Anessa có tốt không?"

3. **Câu hỏi THIẾU NGỮ CẢNH:**
   - "giá bao nhiêu?", "có tốt không?", "thành phần gì?"
   - Bổ sung sản phẩm từ lịch sử gần nhất
   - Ví dụ: "giá bao nhiêu?" + lịch sử về Cetaphil → "Cetaphil giá bao nhiêu?"

4. **Câu hỏi TƯ VẤN CHUNG:**
   - Không cần sản phẩm cụ thể
   - Giữ nguyên
   - Ví dụ: "Tư vấn kem dưỡng cho da khô" → "Tư vấn kem dưỡng cho da khô"

🚨 TRÁNH LẪN LỘN:
- Nếu câu hỏi về sản phẩm A, KHÔNG thêm thông tin về sản phẩm B từ lịch sử
- Nếu câu hỏi đã rõ ràng, KHÔNG thêm thông tin không cần thiết

=== ĐỊNH DẠNG TRẢ VỀ ===
Intent: <GREETING hoặc QUESTION>
Enhanced_Query: <câu hỏi đã được cải thiện>

=== VÍ DỤ THỰC TẾ ===

Ví dụ 1 - Câu hỏi rõ ràng:
Lịch sử: "Kem chống nắng Anessa có tốt không?"
Query: "La Roche Posay giá bao nhiêu?"
→ Intent: QUESTION
→ Enhanced_Query: La Roche Posay giá bao nhiêu?
(KHÔNG thêm Anessa vì câu hỏi đã rõ về La Roche Posay)

Ví dụ 2 - Đại từ không rõ:
Lịch sử: "Kem chống nắng Anessa có tốt không?"
Query: "nó có phù hợp với da nhạy cảm không?"
→ Intent: QUESTION
→ Enhanced_Query: Anessa có phù hợp với da nhạy cảm không?

Ví dụ 3 - Thiếu ngữ cảnh:
Lịch sử: "Cetaphil có tốt không?"
Query: "giá bao nhiêu?"
→ Intent: QUESTION
→ Enhanced_Query: Cetaphil giá bao nhiêu?

Ví dụ 4 - Tư vấn chung:
Lịch sử: "Kem chống nắng Anessa có tốt không?"
Query: "Tư vấn kem dưỡng ẩm cho da khô"
→ Intent: QUESTION
→ Enhanced_Query: Tư vấn kem dưỡng ẩm cho da khô
(KHÔNG thêm Anessa vì đây là câu hỏi tư vấn mới)

Ví dụ 5 - Greeting:
Query: "Cảm ơn bạn"
→ Intent: GREETING
→ Enhanced_Query: Cảm ơn bạn
"""
        return PromptTemplate(
            input_variables=["query", "chat_summary"],
            template=template
        )