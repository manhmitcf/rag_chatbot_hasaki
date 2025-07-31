from services.qdrant_service import QdrantService
from model_rerank.model_rerank import RerankService
from typing import List, Dict, Any
from config.settings import settings

# LangChain imports
from langchain_google_genai import ChatGoogleGenerativeAI

# Local imports
from services.langchain.memory.conversation_memory import ConversationMemoryManager
from services.langchain.chains.unified_processing_chain import UnifiedProcessingChain
from services.langchain.chains.response_chain import ResponseChain
from services.langchain.context.context_builder import ContextBuilder


class UnifiedRAGService:
    """Unified RAG Service - Không giới hạn text history và context"""
    
    def __init__(self, use_rerank: bool = True):
        # Khởi tạo LLM với settings từ env
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=settings.GEMINI_API_KEY,
            temperature=settings.LLM_TEMPERATURE,
            timeout=settings.LLM_TIMEOUT
        )
        
        # Khởi tạo services
        self.qdrant_service = QdrantService()
        # ConversationBufferWindowMemory với k từ settings
        self.memory_manager = ConversationMemoryManager(self.llm, k=settings.CONVERSATION_MEMORY_K)
        
        # Khởi tạo chain gộp
        self.unified_processor = UnifiedProcessingChain(self.llm)
        self.response_chain = ResponseChain(self.llm)
        
        # Khởi tạo reranker
        self.use_rerank = use_rerank
        if use_rerank:
            try:
                print("Đang khởi tạo Rerank Service...")
                self.rerank_service = RerankService()
                print("Rerank Service đã sẵn sàng!")
            except Exception as e:
                print(f"Lỗi khởi tạo Rerank Service: {e}")
                print("Hệ thống sẽ hoạt động không có reranking")
                self.use_rerank = False
                self.rerank_service = None
        else:
            self.rerank_service = None
    
    def process_complete_query(self, user_query: str) -> Dict[str, Any]:
        """Xử lý query đơn giản - Chỉ 2 routes: GREETING và QUESTION"""
        try:
            print(f"Bắt đầu xử lý query: {user_query}")
            
            # Bước 1: Xử lý query và routing đơn giản
            query_info = self._step1_process_and_route(user_query)
            
            # Bước 2: Tìm kiếm (chỉ khi cần)
            search_results = self._step2_search_if_needed(query_info)
            
            # Bước 3: Tạo response
            response = self._step3_generate_response(query_info, search_results)
            
            # Lấy thông tin sản phẩm từ document đầu tiên
            id_product = None
            name_product = None
            if search_results:
                first_doc = search_results[0]
                metadata = first_doc.get('metadata', {})
                id_product = metadata.get('product_id')
                name_product = metadata.get('name')
            
            return {
                "success": True,
                "answer": response,
                "enhanced_query": query_info["enhanced_query"],
                "route": query_info["route"],
                "documents_found": len(search_results),
                "id_product": id_product,
                "name_product": name_product,
                "memory_stats": self.memory_manager.get_memory_stats()
            }
            
        except Exception as e:
            print(f"Lỗi xử lý query: {e}")
            error_response = "Xin lỗi, đã xảy ra lỗi khi xử lý câu hỏi của bạn."
            
            # Vẫn lưu vào memory
            try:
                self.memory_manager.add_conversation_turn(user_query, error_response)
            except:
                pass
            
            return {
                "success": False,
                "answer": error_response,
                "error": str(e)
            }
    
    def process_complete_query_with_details(self, user_query: str, show_details: bool = True) -> Dict[str, Any]:
        """Xử lý query với thông tin chi tiết về transform và chunks - KHÔNG GIỚI HẠN TEXT"""
        try:
            print(f"Bắt đầu xử lý query với details (UNLIMITED TEXT): {user_query}")
            
            # Bước 1: Xử lý query và routing với details
            query_info = self._step1_process_and_route_with_details(user_query, show_details)
            
            # Bước 2: Tìm kiếm với details
            search_results, search_details = self._step2_search_with_details(query_info, show_details)
            
            # Bước 3: Tạo response với details
            response, context_details = self._step3_generate_response_with_details(query_info, search_results, show_details)
            
            # Lấy thông tin sản phẩm từ document đầu tiên
            id_product = None
            name_product = None
            if search_results:
                first_doc = search_results[0]
                metadata = first_doc.get('metadata', {})
                id_product = metadata.get('product_id')
                name_product = metadata.get('name')
            
            result = {
                "success": True,
                "answer": response,
                "enhanced_query": query_info["enhanced_query"],
                "route": query_info["route"],
                "documents_found": len(search_results),
                "id_product": id_product,
                "name_product": name_product,
                "memory_stats": self.memory_manager.get_memory_stats()
            }
            
            # Thêm thông tin chi tiết nếu được yêu cầu
            if show_details:
                result.update({
                    "query_transform_info": query_info.get("transform_details"),
                    "chunks_info": search_details.get("chunks_info"),
                    "context_info": context_details
                })
            
            return result
            
        except Exception as e:
            print(f"Lỗi xử lý query với details: {e}")
            error_response = "Xin lỗi, đã xảy ra lỗi khi xử lý câu hỏi của bạn."
            
            # Vẫn lưu vào memory
            try:
                self.memory_manager.add_conversation_turn(user_query, error_response)
            except:
                pass
            
            return {
                "success": False,
                "answer": error_response,
                "error": str(e)
            }
    
    def _step1_process_and_route(self, user_query: str) -> Dict[str, Any]:
        """Bước 1: Xử lý và routing gộp với unified chain"""
        print("=== BƯỚC 1: XỬ LÝ VÀ ROUTING GỘP ===")
        
        # Lấy chat summary
        chat_summary = self.memory_manager.get_conversation_summary()
        print(f"Chat summary: {chat_summary}")
        
        # Xử lý gộp với unified chain
        try:
            query_info = self.unified_processor.process_query_unified(user_query, chat_summary)
            print(f"Unified processing result: {query_info}")
            return query_info
        except Exception as e:
            print(f"Lỗi unified processing, dùng fallback: {e}")
            # Fallback processing
            greeting_keywords = ['xin chào', 'hello', 'hi', 'chào', 'cảm ơn', 'thanks', 'tạm biệt', 'bye']
            if any(keyword in user_query.lower() for keyword in greeting_keywords):
                route = "GREETING"
            else:
                route = "QUESTION"
            
            return {
                "intent": route,
                "enhanced_query": user_query,
                "route": route,
                "sub_queries": [user_query],
                "query_count": 1,
                "original_query": user_query
            }
    
    def _step1_process_and_route_with_details(self, user_query: str, show_details: bool) -> Dict[str, Any]:
        """Bước 1: Xử lý và routing với thông tin chi tiết"""
        print("=== BƯỚC 1: XỬ LÝ VÀ ROUTING GỘP (WITH DETAILS) ===")
        
        # Lấy chat summary
        chat_summary = self.memory_manager.get_conversation_summary()
        print(f"Chat summary: {chat_summary}")
        
        # Xử lý gộp với unified chain
        try:
            query_info = self.unified_processor.process_query_unified(user_query, chat_summary)
            print(f"Unified processing result: {query_info}")
            
            # Thêm thông tin chi tiết về transform
            if show_details:
                query_info["transform_details"] = {
                    "original_query": user_query,
                    "chat_summary": chat_summary,
                    "enhanced_query": query_info.get("enhanced_query"),
                    "intent_detected": query_info.get("intent"),
                    "route_selected": query_info.get("route"),
                    "enhancement_method": "unified_processing_chain",
                    "context_used": bool(chat_summary and chat_summary != "Chưa có lịch sử."),
                    "memory_entities": {
                        "recent_brands": getattr(self.memory_manager, '_recent_brands', []),
                        "recent_categories": getattr(self.memory_manager, '_recent_categories', []),
                        "recent_products": getattr(self.memory_manager, '_recent_products', [])
                    }
                }
            
            return query_info
            
        except Exception as e:
            print(f"Lỗi unified processing, dùng fallback: {e}")
            # Fallback processing
            greeting_keywords = ['xin chào', 'hello', 'hi', 'chào', 'cảm ơn', 'thanks', 'tạm biệt', 'bye']
            if any(keyword in user_query.lower() for keyword in greeting_keywords):
                route = "GREETING"
            else:
                route = "QUESTION"
            
            result = {
                "intent": route,
                "enhanced_query": user_query,
                "route": route,
                "sub_queries": [user_query],
                "query_count": 1,
                "original_query": user_query
            }
            
            if show_details:
                result["transform_details"] = {
                    "original_query": user_query,
                    "chat_summary": chat_summary,
                    "enhanced_query": user_query,
                    "intent_detected": route,
                    "route_selected": route,
                    "enhancement_method": "fallback_rule_based",
                    "context_used": False,
                    "error": str(e)
                }
            
            return result
    
    def _step2_search_if_needed(self, query_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Bước 2: Tìm kiếm chỉ khi cần (QUESTION)"""
        print("=== BƯỚC 2: TÌM KIẾM NẾU CẦN ===")
        
        route = query_info.get("route")
        
        if route == "GREETING":
            print("Route GREETING - Bỏ qua search")
            return []
        
        # QUESTION - Tìm kiếm
        print("Route QUESTION - Thực hiện search")
        enhanced_query = query_info.get("enhanced_query", "")
        
        return self._search_single_query(enhanced_query)
    
    def _step2_search_with_details(self, query_info: Dict[str, Any], show_details: bool) -> tuple:
        """Bước 2: Tìm kiếm với thông tin chi tiết - KHÔNG GIỚI HẠN TEXT"""
        print("=== BƯỚC 2: TÌM KIẾM NẾU CẦN (WITH DETAILS - UNLIMITED TEXT) ===")
        
        route = query_info.get("route")
        search_details = {"chunks_info": []}
        
        if route == "GREETING":
            print("Route GREETING - Bỏ qua search")
            return [], search_details
        
        # QUESTION - Tìm kiếm
        print("Route QUESTION - Thực hiện search")
        enhanced_query = query_info.get("enhanced_query", "")
        
        search_results = self._search_single_query(enhanced_query)
        
        # Tạo thông tin chi tiết về chunks - KHÔNG GIỚI HẠN TEXT
        if show_details and search_results:
            for i, doc in enumerate(search_results[:10]):  # Top 10 chunks
                metadata = doc.get('metadata', {})
                chunk_info = {
                    "rank": i + 1,
                    "product_id": metadata.get('product_id'),
                    "product_name": metadata.get('name'),
                    "brand": metadata.get('brand'),
                    "category": metadata.get('category_name'),
                    "chunk_type": metadata.get('type'),
                    "chunk_length": len(doc.get('text', '')),
                    "vector_score": doc.get('vector_score', doc.get('score', 0.0)),
                    "rerank_score": doc.get('rerank_score'),
                    "score_improvement": doc.get('rerank_metadata', {}).get('score_improvement', 0.0),
                    "full_text": doc.get('text', ''),  # TOÀN BỘ TEXT, không giới hạn
                    "text_limit": "UNLIMITED"
                }
                search_details["chunks_info"].append(chunk_info)
        
        return search_results, search_details
    
    def _search_single_query(self, query: str) -> List[Dict[str, Any]]:
        """Tìm kiếm với settings từ env"""
        print(f"Tìm kiếm: {query}")
        
        # Semantic search với limit từ settings
        search_results = self.qdrant_service.search_similar(
            query=query,
            limit=settings.SEMANTIC_SEARCH_LIMIT,
            filters=None
        )
        
        print(f"Semantic search: {len(search_results)} documents")
        
        # Rerank với top_k từ settings
        if self.use_rerank and self.rerank_service and search_results:
            print(f"Áp dụng reranking...")
            
            try:
                reranked_results = self.rerank_service.enhance_search_results(
                    query=query,
                    search_results=search_results,
                    top_k=settings.RERANK_TOP_K,
                    use_batch=True
                )
                
                print(f"Reranking hoàn thành: {len(reranked_results)} documents")
                return reranked_results
            except Exception as e:
                print(f"Lỗi reranking: {e}")
                return search_results[:settings.RERANK_TOP_K]
        
        # Không có reranker - trả về theo RERANK_TOP_K
        return search_results[:settings.RERANK_TOP_K]
    
    def _step3_generate_response(self, query_info: Dict[str, Any], search_results: List[Dict[str, Any]]) -> str:
        """Bước 3: Tạo response - KHÔNG GIỚI HẠN TEXT"""
        print("=== BƯỚC 3: TẠO RESPONSE (UNLIMITED TEXT) ===")
        
        route = query_info.get("route", "QUESTION")
        
        # Tạo context
        if route == "GREETING":
            context = ""
        else:
            # QUESTION - Tạo context từ search results với CONTEXT_TOP_K từ settings
            context = ContextBuilder.build_context_smart(search_results[:settings.CONTEXT_TOP_K], "QUESTION")
        
        # Lịch sử từ buffer window - KHÔNG GIỚI HẠN
        chat_history = self.memory_manager.get_formatted_history()
        print(f"Chat history length: {len(chat_history)} characters (UNLIMITED)")
        print(f"Context length: {len(context)} characters (UNLIMITED)")
        
        # Generate response
        try:
            response = self.response_chain.generate_response(
                query_info, 
                context, 
                chat_history, 
                route
            )
            
            print("Response generated successfully")
            
            # Lưu vào memory
            try:
                original_query = query_info.get("enhanced_query", "")
                self.memory_manager.add_conversation_turn(original_query, response)
            except Exception as e:
                print(f"Lỗi lưu memory: {e}")
            
            return response
            
        except Exception as e:
            print(f"Lỗi generate response: {e}")
            # Fallback response
            if route == "GREETING":
                return "Xin chào! Tôi có thể giúp gì cho bạn về mỹ phẩm?"
            else:
                return "Xin lỗi, tôi không thể trả lời câu hỏi này. Bạn có thể hỏi khác không?"
    
    def _step3_generate_response_with_details(self, query_info: Dict[str, Any], search_results: List[Dict[str, Any]], show_details: bool) -> tuple:
        """Bước 3: Tạo response với thông tin chi ti��t - KHÔNG GIỚI HẠN TEXT"""
        print("=== BƯỚC 3: TẠO RESPONSE (WITH DETAILS - UNLIMITED TEXT) ===")
        
        route = query_info.get("route", "QUESTION")
        context_details = {}
        
        # Tạo context
        if route == "GREETING":
            context = ""
        else:
            # QUESTION - Tạo context từ search results với CONTEXT_TOP_K từ settings
            context = ContextBuilder.build_context_smart(search_results[:settings.CONTEXT_TOP_K], "QUESTION")
        
        # Lịch sử từ buffer window - KHÔNG GIỚI HẠN
        chat_history = self.memory_manager.get_formatted_history()
        
        # Thông tin chi tiết về context - KHÔNG GIỚI HẠN TEXT
        if show_details:
            context_details = {
                "context_length": len(context),
                "chat_history_length": len(chat_history),
                "documents_used_for_context": min(len(search_results), settings.CONTEXT_TOP_K),
                "context_full": context,  # TOÀN BỘ CONTEXT, không giới hạn
                "chat_history_full": chat_history,  # TOÀN BỘ CHAT HISTORY, không giới hạn
                "route": route,
                "llm_model": "gemini-2.5-flash",
                "llm_temperature": settings.LLM_TEMPERATURE,
                "llm_timeout": settings.LLM_TIMEOUT,
                "text_limit": "UNLIMITED"
            }
        
        print(f"Chat history length: {len(chat_history)} characters (UNLIMITED)")
        print(f"Context length: {len(context)} characters (UNLIMITED)")
        
        # Generate response
        try:
            response = self.response_chain.generate_response(
                query_info, 
                context, 
                chat_history, 
                route
            )
            
            print("Response generated successfully")
            
            # Lưu vào memory
            try:
                original_query = query_info.get("enhanced_query", "")
                self.memory_manager.add_conversation_turn(original_query, response)
            except Exception as e:
                print(f"Lỗi lưu memory: {e}")
            
            return response, context_details
            
        except Exception as e:
            print(f"Lỗi generate response: {e}")
            # Fallback response
            if route == "GREETING":
                fallback_response = "Xin chào! Tôi có thể giúp gì cho bạn về mỹ phẩm?"
            else:
                fallback_response = "Xin lỗi, tôi không thể trả lời câu hỏi này. Bạn có thể hỏi khác không?"
            
            if show_details:
                context_details["error"] = str(e)
                context_details["fallback_used"] = True
            
            return fallback_response, context_details
    
    def get_conversation_summary(self) -> str:
        """Lấy tóm tắt cuộc hội thoại"""
        return self.memory_manager.get_conversation_summary()
    
    def clear_memory(self):
        """Xóa memory"""
        self.memory_manager.clear_memory()
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Lấy thống kê về memory"""
        return self.memory_manager.get_memory_stats()