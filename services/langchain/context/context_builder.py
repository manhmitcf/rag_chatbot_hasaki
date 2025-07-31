from typing import List, Dict, Any
from config.settings import settings


class ContextBuilder:
    """Xây dựng context từ search results - Đơn giản hóa cho 2 routes"""
    
    @staticmethod
    def build_context_smart(search_results: List[Dict[str, Any]], route: str) -> str:
        """Build context thông minh theo route - Đơn giản hóa"""
        
        if route == "GREETING":
            return ""
        
        # QUESTION - Cung cấp thông tin chi tiết
        if not search_results:
            return "Không có thông tin sản phẩm."
        
        return ContextBuilder._build_product_context(search_results)
    
    @staticmethod
    def _build_product_context(search_results: List[Dict[str, Any]]) -> str:
        """Build context đơn giản - Chỉ name, chunk và điểm"""
        # Lấy top documents theo settings
        top_docs = search_results[:settings.CONTEXT_TOP_K]
        
        context_parts = []
        for i, doc in enumerate(top_docs, 1):
            metadata = doc.get('metadata', {})
            text = doc.get('text', '')
            
            # Chỉ lấy name
            name = metadata.get('name', f'Sản phẩm {i}')
            
            # Lấy điểm số (score) nếu có
            score = doc.get('score', '')
            
            # Format đơn giản: [STT] Name (Score): Chunk
            if score:
                product_info = f"[{i}] {name} (Score: {score:.3f})"
            else:
                product_info = f"[{i}] {name}"
            
            # Thêm chunk text
            if text:
                product_info += f"\n{text}"
            
            context_parts.append(product_info)
        
        return "\n\n".join(context_parts)