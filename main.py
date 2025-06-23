#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
RAG Chatbot Demo - Terminal Interface
Chatbot tư vấn mỹ phẩm sử dụng RAG (Retrieval-Augmented Generation)
"""

import os
import sys
from services.rag_service import RAGService

def print_banner():
    """In banner chào mừng"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                    🌸 HASAKI RAG CHATBOT 🌸                  ║
    ║                  Tư vấn mỹ phẩm thông minh                   ║
    ╠══════════════════════════════════════════════════════════════╣
    ║  💄 Hỏi về sản phẩm mỹ phẩm                                 ║
    ║  🧴 Tư vấn chăm sóc da                                      ║
    ║  💅 Gợi ý sản phẩm phù hợp                                  ║
    ║                                                              ║
    ║  Gõ 'exit' hoặc 'quit' để thoát                            ║
    ║  Gõ 'clear' để xóa màn hình                                ║
    ║  Gõ 'help' để xem hướng dẫn                                ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def print_help():
    """In hướng dẫn sử dụng"""
    help_text = """
    📋 HƯỚNG DẪN SỬ DỤNG:
    
    🔍 CÁC LOẠI CÂU HỎI BẠN CÓ THỂ HỎI:
    
    1️⃣ Hỏi về sản phẩm cụ thể:
       • "Thông tin về kem chống nắng Anessa"
       • "Giá của sản phẩm ID: 12345"
       • "Sản phẩm này có tốt không?" (sau khi đã hỏi về 1 sản phẩm)
    
    2️⃣ Câu hỏi tổng quát:
       • "Có những loại sữa rửa mặt nào?"
       • "Tư vấn kem dưỡng ẩm cho da khô"
       • "Sản phẩm nào phù hợp với da nhạy cảm?"
    
    3️⃣ Chào hỏi và cảm ơn:
       • "Xin chào"
       • "Cảm ơn bạn"
       • "Tạm biệt"
    
    💡 MẸO SỬ DỤNG:
    • Bot có thể nhớ ngữ cảnh cuộc trò chuyện
    • Bạn có thể hỏi tiếp về sản phẩm vừa được đề cập
    • Sử dụng từ khóa rõ ràng để có kết quả tốt nhất
    
    ⌨️  LỆNH ĐIỀU KHIỂN:
    • exit/quit: Thoát chương trình
    • clear: Xóa màn hình
    • help: Hiển thị hướng dẫn này
    """
    print(help_text)

def clear_screen():
    """Xóa màn hình"""
    os.system('cls' if os.name == 'nt' else 'clear')

def main():
    """Hàm chính chạy chatbot"""
    try:
        # Xóa màn hình và hiển thị banner
        clear_screen()
        print_banner()
        
        print("🚀 Đang khởi tạo RAG Chatbot...")
        print("⏳ Vui lòng đợi trong giây lát...")
        
        # Khởi tạo RAG Service
        rag_service = RAGService(use_rerank=True)
        
        print("✅ Chatbot đã sẵn sàng!")
        print("💬 Bạn có thể bắt đầu trò chuyện ngay bây giờ!\n")
        
        # Vòng lặp chat chính
        while True:
            try:
                # Nhận input từ người dùng
                user_input = input("🙋 Bạn: ").strip()
                
                # Xử lý các lệnh đặc biệt
                if user_input.lower() in ['exit', 'quit', 'thoát']:
                    print("\n👋 Cảm ơn bạn đã sử dụng Hasaki RAG Chatbot!")
                    print("🌸 Chúc bạn một ngày tốt lành!")
                    break
                
                elif user_input.lower() in ['clear', 'xóa']:
                    clear_screen()
                    print_banner()
                    continue
                
                elif user_input.lower() in ['help', 'hướng dẫn', 'giúp đỡ']:
                    print_help()
                    continue
                
                elif not user_input:
                    print("⚠️  Vui lòng nhập câu hỏi của bạn!")
                    continue
                
                # Xử lý câu hỏi
                print("\n🤖 Bot đang suy nghĩ...")
                
                # Tăng cường query với lịch sử hội thoại
                enhanced_query = rag_service.gemini_service.enhance_query_with_history(user_input)
                
                # Phân tích ý định
                intent = rag_service.gemini_service.build_promt_intent(enhanced_query)
                print(f"🎯 Phân loại: {intent}")
                
                # Xử lý theo ý định
                if intent == "SPECIFIC_PRODUCT":
                    # Xác định filter cho sản phẩm cụ thể
                    filters = rag_service.gemini_service.identify_key_for_filter(enhanced_query)
                    print(f"🔍 Filters được tạo: {filters}")
                    
                    # Thử tìm kiếm với filter trước
                    result = rag_service.query(enhanced_query, filters=filters, rerank_top_k=5, top_k=20)
                    
                    # Nếu không tìm thấy kết quả với filter, thử không filter
                    if result["success"] and result["answer"] == "Xin lỗi, tôi không tìm thấy thông tin phù hợp để trả lời câu hỏi của bạn.":
                        print("⚠️ Không tìm thấy với filter, thử tìm kiếm không filter...")
                        result = rag_service.query(enhanced_query, filters=None, rerank_top_k=5, top_k=20)
                    
                    if result["success"]:
                        print(f"\n🤖 Bot: {result['answer']}\n")
                        # Lưu vào lịch sử hội thoại
                        rag_service.gemini_service.append_to_conversation(
                            enhanced_query, 
                            result["answer"], 
                            intent,
                            result.get("id_product"),
                            result.get("name_product")
                        )
                    else:
                        print(f"\n❌ Bot: {result['answer']}\n")
                        rag_service.gemini_service.append_to_conversation(
                            enhanced_query, 
                            result["answer"], 
                            intent
                        )
                
                elif intent == "GENERAL_QUESTION":
                    # Xử lý câu hỏi tổng quát
                    result = rag_service.query(enhanced_query, rerank_top_k=5, top_k=20, filters=None)
                    
                    if result["success"]:
                        print(f"\n🤖 Bot: {result['answer']}\n")
                        rag_service.gemini_service.append_to_conversation(
                            enhanced_query, 
                            result["answer"], 
                            intent
                        )
                    else:
                        print(f"\n❌ Bot: {result['answer']}\n")
                        rag_service.gemini_service.append_to_conversation(
                            enhanced_query, 
                            result["answer"], 
                            intent
                        )
                
                else:
                    print("\n🤖 Bot: Xin lỗi, tôi không hiểu câu hỏi của bạn. Vui lòng thử lại!\n")
                
            except KeyboardInterrupt:
                print("\n\n👋 Tạm biệt! Cảm ơn bạn đã sử dụng Hasaki RAG Chatbot!")
                break
            except Exception as e:
                print(f"\n❌ Đã xảy ra lỗi: {str(e)}")
                print("🔄 Vui lòng thử lại!\n")
                
    except Exception as e:
        print(f"❌ Lỗi khởi tạo chatbot: {str(e)}")
        print("🔧 Vui lòng kiểm tra cấu hình và thử lại!")
        sys.exit(1)

if __name__ == "__main__":
    main()