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
                    "total_rating": hit.payload.get("total_rating"),
                    "average_rating": hit.payload.get("average_rating"),
                    "data_variant": hit.payload.get("data_variant"),
                    "item_count_by": hit.payload.get("item_count_by"),
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
    
    def _build_filter(self, filters: Dict[str, Any]) -> Filter:
        """Xây dựng filter cho Qdrant query - chỉ hỗ trợ operator 'in'"""
        conditions = []
        
        # Mapping từ filter keys sang metadata keys thực tế
        field_mapping = {
            "name_product": "name",  # Map name_product -> name
            "id_product": "product_id",  # Map id_product -> product_id
            "category_name": "category_name",  # Giữ nguyên
            "brand": "brand"  # Giữ nguyên
        }
        
        for field, value in filters.items():
            # Bỏ qua các giá trị None hoặc rỗng
            if value is None or value == "" or value == []:
                continue
            
            # Map field name
            actual_field = field_mapping.get(field, field)
                
            if isinstance(value, dict):
                # Chỉ xử lý operator "in"
                if "in" in value and value["in"] is not None and value["in"] != []:
                    # Lọc bỏ các giá trị None trong list
                    filtered_values = [v for v in value["in"] if v is not None and v != ""]
                    if filtered_values:
                        conditions.append(
                            FieldCondition(key=actual_field, match=MatchAny(any=filtered_values))
                        )
            else:
                # Xử lý giá trị đơn giản - chuy���n thành dạng "in" với một phần tử
                # Chỉ thêm nếu giá trị không phải None hoặc rỗng
                if value is not None and value != "":
                    conditions.append(
                        FieldCondition(key=actual_field, match=MatchAny(any=[value]))
                    )
        
        return Filter(must=conditions) if conditions else None