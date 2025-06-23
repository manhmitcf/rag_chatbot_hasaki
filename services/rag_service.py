from services.qdrant_service import QdrantService
from services.gemini_service import GeminiService
from model_rerank.model_rerank import RerankService
from typing import List, Dict, Any

class RAGService:
    def __init__(self, use_rerank: bool = True):
        self.qdrant_service = QdrantService()
        self.gemini_service = GeminiService()
        
        # Khởi tạo reranker nếu được yêu cầu
        self.use_rerank = use_rerank
        if use_rerank:
            try:
                print("Đang khởi tạo Rerank Service...")
                self.rerank_service = RerankService()
                print("✅ Rerank Service đã sẵn sàng!")
            except Exception as e:
                print("📝 Hệ thống sẽ hoạt động không có reranking")
                self.use_rerank = False
                self.rerank_service = None
        else:
            self.rerank_service = None
    
    def query(self, question: str, top_k: int = 5, filters: Dict[str, Any] = None, 
              rerank_top_k: int = None) -> Dict[str, Any]:
        """Xử lý câu hỏi và trả về kết quả với filter và reranking"""
        try:
            # Tìm kiếm documents liên quan với filter
            # Nếu có rerank, lấy nhiều documents hơn để rerank
            search_limit = top_k * 2 if self.use_rerank and self.rerank_service else top_k
            
            print(f"🔍 Tìm kiếm với filters: {filters}")
            relevant_docs = self.qdrant_service.search_similar(
                query=question, 
                limit=search_limit, 
                filters=filters
            )
            
            print(f"📊 Tìm thấy {len(relevant_docs)} documents từ vector search")
            
            # Nếu không tìm thấy documents với filter, thử lại không filter
            if not relevant_docs and filters:
                print("⚠️ Không tìm thấy với filter, thử tìm kiếm không filter...")
                relevant_docs = self.qdrant_service.search_similar(
                    query=question, 
                    limit=search_limit, 
                    filters=None
                )
                print(f"📊 Tìm thấy {len(relevant_docs)} documents không filter")
            
            # Áp dụng reranking nếu có
            if self.use_rerank and self.rerank_service and relevant_docs:
                print(f"🎯 Áp dụng reranking cho {len(relevant_docs)} documents...")
                
                # Xác định số lượng documents sau rerank
                final_top_k = rerank_top_k if rerank_top_k is not None else top_k
                
                # Rerank documents
                relevant_docs = self.rerank_service.enhance_search_results(
                    query=question,
                    search_results=relevant_docs,
                    top_k=final_top_k,
                    use_batch=True
                )
                
                print(f"✅ Reranking hoàn thành, {len(relevant_docs)} documents được chọn")
            
            # Tạo response từ Gemini AI
            if relevant_docs:
                print("🤖 Đang tạo response từ Gemini AI...")
                answer = self.gemini_service.generate_response(question, relevant_docs)
                
                # Lấy thông tin sản phẩm từ document đầu tiên (có score cao nhất)
                first_doc = relevant_docs[0]
                metadata = first_doc.get('metadata', {})
                id_product = metadata.get('product_id')
                name_product = metadata.get('name')
                
                return {
                    "question": question,
                    "answer": answer,
                    "success": True,
                    "id_product": id_product,
                    "name_product": name_product
                }
            else:
                answer = "Xin lỗi, tôi không tìm thấy thông tin phù hợp để trả lời câu hỏi của bạn."
                return {
                    "question": question,
                    "answer": answer,
                    "success": True,
                    "id_product": None,
                    "name_product": None
                }
        except Exception as e:
            print(f"❌ Lỗi trong query: {e}")
            return {
                "question": question,
                "answer": "Xin lỗi, đã xảy ra lỗi khi xử lý câu hỏi của bạn.",
                "success": False
            }

    def pipeline(self):
        """Hàm luống RAG hoạt động"""

        while True:
            # Nhap cau hoi
            question = input("Nhập câu hỏi: ")
            if question.lower() == "exit":
                break

            # Tăng cường query
            queery = self.gemini_service.enhance_query_with_history(question)

            intent = self.gemini_service.build_promt_intent(queery)

            print(f"Intent: {intent}")

            if intent == "SPECIFIC_PRODUCT":
                identify_key = self.gemini_service.identify_key_for_filter(queery)
                result = self.query(queery, filters=identify_key, rerank_top_k=5, top_k=20)

                if result["success"]:
                    print(result["answer"])
                    self.gemini_service.append_to_conversation(queery, result["answer"], intent, result["id_product"], result["name_product"])
                else:
                    print(result["answer"])
                    self.gemini_service.append_to_conversation(queery, result["answer"], intent)
            elif intent == "GENERAL_QUESTION":
                result = self.query(queery, rerank_top_k=5, top_k=20, filters=None)

                if result["success"]:
                    print(result["answer"])
                    self.gemini_service.append_to_conversation(queery, result["answer"], intent)
                else:
                    print(result["answer"])
                    self.gemini_service.append_to_conversation(queery, result["answer"], intent)
            
            



        




            
         
        
        

     

