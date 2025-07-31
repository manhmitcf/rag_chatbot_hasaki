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
        self.device = getattr(settings, 'QDRANT_DEVICE', 'cpu')
        self.embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
        
        # Chỉ sử dụng to_device nếu method tồn tại
        if hasattr(self.embedding_model, 'to_device'):
            self.embedding_model = self.embedding_model.to_device(self.device)

    def search_similar(self, query: str, limit: int = 5, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Tìm kiếm documents tương tự"""
        try:
            # Tạo embedding cho query
            query_embedding = self.embedding_model.encode([query])[0]
            
            # Tìm kiếm
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding.tolist(),
                limit=limit
            )
            
            # Format kết quả - map payload fields vào metadata structure
            results = []
            for hit in search_result:
                # Tạo metadata từ payload
                metadata = {
                    "product_id": hit.payload.get("product_id"),
                    "name": hit.payload.get("name"),
                    "english_name": hit.payload.get("english_name"),
                    "category_name": hit.payload.get("category_name"),
                    "brand": hit.payload.get("brand"),
                    "price": hit.payload.get("price"),
                    "data_variant": hit.payload.get("data_variant"),
                    "item_count_by": hit.payload.get("item_count_by"),
                    "url": hit.payload.get("url"),
                    "options": hit.payload.get("options") if hit.payload.get("options") else None,
                    "average_rating": hit.payload.get("average_rating"),
                    "total_rating": hit.payload.get("total_rating"),
                    "type": hit.payload.get("type")
                }
                
                results.append({
                    "text": hit.payload.get("text", ""),
                    "score": hit.score,
                    "metadata": metadata
                })
            
            return results
        except Exception as e:
            print(f"Error searching: {e}")
            return []