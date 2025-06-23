from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue, MatchAny, Range
from sentence_transformers import SentenceTransformer
from config.settings import settings
import uuid
from typing import List, Dict, Any, Optional

class QdrantService:
    def __init__(self):
        self.client = QdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT
        )
        self.collection_name = settings.QDRANT_COLLECTION_NAME
        self.embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
    
    

    def search_similar(self, query: str, limit: int = 5, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Tìm kiếm documents tương tự với filter"""
        try:
            # Tạo embedding cho query
            query_embedding = self.embedding_model.encode([query])[0]
            
            # Tạo filter nếu có
            query_filter = self._build_filter(filters) if filters else None
            
            # Tìm kiếm
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding.tolist(),
                query_filter=query_filter,
                limit=limit
            )
            
            # Format kết quả
            results = []
            for hit in search_result:
                results.append({
                    "text": hit.payload.get("text", ""),
                    "score": hit.score,
                    "metadata": hit.payload.get("metadata", {})
                })
            
            return results
        except Exception as e:
            print(f"Error searching: {e}")
            return []
    
    def _build_filter(self, filters: Dict[str, Any]) -> Filter:
        """Xây dựng filter cho Qdrant query - chỉ hỗ trợ operator 'in'"""
        conditions = []
        
        for field, value in filters.items():
            if isinstance(value, dict):
                # Chỉ xử lý operator "in"
                if "in" in value:
                    conditions.append(
                        FieldCondition(key=f"metadata.{field}", match=MatchAny(any=value["in"]))
                    )
            else:
                # Xử lý giá trị đơn giản - chuyển thành dạng "in" với một phần tử
                conditions.append(
                    FieldCondition(key=f"metadata.{field}", match=MatchAny(any=[value]))
                )
        
        return Filter(must=conditions) if conditions else None