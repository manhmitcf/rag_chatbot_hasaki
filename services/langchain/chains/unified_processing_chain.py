from typing import Dict, Any
from langchain.chains import LLMChain
from langchain_google_genai import ChatGoogleGenerativeAI
from services.langchain.prompts.unified_prompts import UnifiedPrompts


class UnifiedProcessingChain:
    """Chain gộp cho cả Intent Classification và Query Enhancement"""
    
    def __init__(self, llm: ChatGoogleGenerativeAI):
        self.llm = llm
        self.prompt_template = UnifiedPrompts.get_unified_template()
        self.chain = LLMChain(
            llm=self.llm,
            prompt=self.prompt_template,
            verbose=False
        )
    
    def process_query_unified(self, query: str, chat_summary: str) -> Dict[str, Any]:
        """Xử lý query gộp - trả về cả intent và enhanced query"""
        try:
            response = self.chain.run(
                query=query,
                chat_summary=chat_summary or "Chưa có lịch sử."
            )
            
            # Parse response
            result = self._parse_unified_response(response)
            
            # Thêm thông tin bổ sung
            result.update({
                "sub_queries": [result["enhanced_query"]],
                "query_count": 1,
                "original_query": query
            })
            
            return result
            
        except Exception as e:
            print(f"Error in unified processing: {e}")
            return self._fallback_processing(query)
    
    def _parse_unified_response(self, response_text: str) -> Dict[str, Any]:
        """Parse response từ LLM"""
        intent = "QUESTION"  # Default
        enhanced_query = ""
        
        lines = response_text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Parse Intent
            if line.startswith("Intent:"):
                intent_value = line.split(":", 1)[1].strip()
                if intent_value in ["GREETING", "QUESTION"]:
                    intent = intent_value
            
            # Parse Enhanced Query
            elif line.startswith("Enhanced_Query:"):
                enhanced_query = line.split(":", 1)[1].strip()
        
        # Fallback nếu không parse được enhanced_query
        if not enhanced_query:
            enhanced_query = self._extract_enhanced_query_fallback(response_text)
        
        return {
            "intent": intent,
            "enhanced_query": enhanced_query,
            "route": intent  # Để tương thích với code cũ
        }
    
    def _extract_enhanced_query_fallback(self, response_text: str) -> str:
        """Fallback để extract enhanced query"""
        lines = response_text.strip().split('\n')
        
        # Tìm dòng cuối cùng không rỗng
        for line in reversed(lines):
            line = line.strip()
            if line and not line.startswith("Intent:") and not line.startswith("Enhanced_Query:"):
                return line
        
        return ""
    
    def _fallback_processing(self, query: str) -> Dict[str, Any]:
        """Fallback processing khi LLM fail"""
        # Simple rule-based intent classification
        greeting_keywords = ['xin chào', 'hello', 'hi', 'chào', 'cảm ơn', 'thanks', 'tạm biệt', 'bye']
        query_lower = query.lower()
        
        if any(keyword in query_lower for keyword in greeting_keywords):
            intent = "GREETING"
        else:
            intent = "QUESTION"
        
        return {
            "intent": intent,
            "enhanced_query": query,
            "route": intent,
            "sub_queries": [query],
            "query_count": 1,
            "original_query": query
        }