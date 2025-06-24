from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
from dataclasses import dataclass
from enum import Enum
from text_chunker import TextChunker  


class ContentType(Enum):
    """Enum cho các loại nội dung khác nhau của sản phẩm (mô tả, thông tin chung, bình luận, thông số kỹ thuật, thành phần, hướng dẫn)."""
    DESCRIPTION = "description"
    GENERAL_INFO = "general_info"
    COMMENT = "comment"
    SPECIFICATION = "specification"
    INGREDIENT = "ingredient"
    GUIDE = "guide"


@dataclass
class ChunkData:
    """Lưu trữ thông tin về một đoạn (chunk) văn bản đã được chia nhỏ từ nội dung sản phẩm."""
    text: str
    chunk_id: int
    content_type: ContentType


@dataclass
class ProductEmbedding:
    """Lưu trữ embedding của sản phẩm cùng với các thông tin metadata liên quan."""
    id: str
    values: List[float]
    metadata: Dict[str, Any]



class ProductEmbeddingGenerator:
    """Xử lý việc tạo embedding cho các loại nội dung khác nhau của sản phẩm."""
    
    def __init__(self, model: SentenceTransformer, chunker: TextChunker):
        """
        Khởi tạo với mô hình embedding và bộ chia đoạn văn bản.
        Args:
            model: Mô hình SentenceTransformer để tạo embedding.
            chunker: Đối tượng TextChunker để chia nhỏ văn bản.
        """
        self.model = model
        self.chunker = chunker
        
        # Vietnamese field labels
        self.field_labels = {
            'name': 'Tên sản phẩm',
            'english_name': 'Tên tiếng anh',
            'brand': 'Thương hiệu',
            'category_name': 'Danh mục con',
            'price': 'Giá hiện tại',
            'market_price': 'Giá thị trường',
            'total_rating': 'Tổng số đánh giá',
            'average_rating': 'Đánh giá trung bình',
            'comment': 'Số lượng bình luận',
            'categorys': 'Danh mục chính',
            'item_count_by': 'Số lượng sản phẩm đã mua',
            'data_variant': 'Dữ liệu biến thể',
            'stars': 'Chi tiết đánh giá'
        }
    
    def _create_base_metadata(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Tạo metadata cơ bản cho embedding của sản phẩm.
        Args:
            product: Thông tin sản phẩm dạng dict.
        Returns:
            dict chứa các trường metadata cơ bản.
        """
        return {
            "product_id": product.get('data_product'),
            "name": product.get('name', ''),
            "english_name": product.get('english_name', ''),
            "category_name": product.get('category_name', ''),
            "brand": product.get('brand', ''),
            "price": product.get('price'),
            "total_rating": product.get('total_rating', ''),
            "average_rating": product.get('average_rating', ''),
            "data_variant": product.get('data_variant', ''),
            "item_count_by": product.get('item_count_by', '')
        }
    
    def _create_product_embedding(self, product_id: str, content_type: ContentType, 
                                text: str, embedding: List[float], 
                                base_metadata: Dict[str, Any], 
                                chunk_id: Optional[int] = None) -> ProductEmbedding:
        """
        Tạo một đối tượng embedding chuẩn hóa cho sản phẩm.
        Args:
            product_id: ID sản phẩm.
            content_type: Loại nội dung.
            text: Văn bản gốc.
            embedding: Vector embedding.
            base_metadata: Metadata cơ bản.
            chunk_id: ID của đoạn (nếu có).
        Returns:
            ProductEmbedding
        """
        embedding_id = product_id + content_type.value
        if chunk_id is not None:
            embedding_id += str(chunk_id)
        
        metadata = base_metadata.copy()
        metadata.update({
            "type": content_type.value,
            "text": text
        })
        
        return ProductEmbedding(
            id=embedding_id,
            values=embedding,
            metadata=metadata
        )
    
    def generate_general_info_embedding(self, product: Dict[str, Any]) -> ProductEmbedding:
        """
        Sinh embedding cho thông tin chung của sản phẩm.
        Args:
            product: Thông tin sản phẩm.
        Returns:
            ProductEmbedding
        """
        info_parts = []
        
        for field, label in self.field_labels.items():
            value = product.get(field, f'Không có {field.lower()}')
            if field == 'stars':
                value = self.chunker.clean_text(str(value))
            info_parts.append(f"{label}: {value}")
        
        general_info = f"Thông tin chung của sản phẩm: {product.get('name', '')}" + ". ".join(info_parts) + "."
        cleaned_info = self.chunker.clean_text(general_info)
        embedding = self.model.encode([cleaned_info]).tolist()[0]
        
        base_metadata = self._create_base_metadata(product)
        
        return self._create_product_embedding(
            product.get('data_product'),
            ContentType.GENERAL_INFO,
            cleaned_info,
            embedding,
            base_metadata
        )
    
def generate_comment_embeddings(self, product: Dict[str, Any]) -> List[ProductEmbedding]: 
    """
    Sinh embedding cho các bình luận của sản phẩm bằng cách gộp 3 bình luận một lần.
    Args:
        product: Thông tin sản phẩm.
    Returns:
        List[ProductEmbedding]
    """
    comments = product.get('comments', [])
    if not comments:
        return []
    
    embeddings = []
    base_metadata = self._create_base_metadata(product)

    # Làm sạch và lọc các bình luận rỗng
    cleaned_comments = [c.strip() for c in comments if c.strip()]
    
    # Ghép 3 bình luận một lần
    for i in range(0, len(cleaned_comments), 3):
        group = cleaned_comments[i:i + 3]
        combined_comment = " ".join(
            [f"Hỏi đáp giữa khách hàng với Nhân viên cửa hàng về sản phẩm: {c}" for c in group]
        )
        cleaned_combined = self.chunker.clean_text(combined_comment)
        embedding = self.model.encode([cleaned_combined]).tolist()[0]

        # Sử dụng chỉ số nhóm đầu tiên làm id đại diện
        product_embedding = self._create_product_embedding(
            product.get('data_product'),
            ContentType.COMMENT,
            combined_comment,
            embedding,
            base_metadata,
            i  # id đại diện cho cụm
        )
        embeddings.append(product_embedding)
    
    return embeddings
    
    def generate_specification_embedding(self, product: Dict[str, Any]) -> Optional[ProductEmbedding]:
        """
        Sinh embedding cho thông số kỹ thuật của sản phẩm.
        Args:
            product: Thông tin sản phẩm.
        Returns:
            ProductEmbedding hoặc None nếu không có thông số kỹ thuật.
        """
        specification = product.get('specificationinfo', '')
        if not specification:
            return None
        
        cleaned_spec = self.chunker.clean_text(specification)
        cleaned_spec = "Thông số kỹ thuật của sản phẩm: " + cleaned_spec
        embedding = self.model.encode([cleaned_spec]).tolist()[0]
        base_metadata = self._create_base_metadata(product)
        
        return self._create_product_embedding(
            product.get('data_product'),
            ContentType.SPECIFICATION,
            specification,
            embedding,
            base_metadata
        )
    
    def generate_content_chunk_embeddings(self, product: Dict[str, Any], 
                                        content_field: str, 
                                        content_type: ContentType) -> List[ProductEmbedding]:
        """
        Sinh embedding cho các đoạn nội dung đã được chia nhỏ (ví dụ: mô tả, thành phần, hướng dẫn).
        Args:
            product: Thông tin sản phẩm.
            content_field: Tên trường nội dung.
            content_type: Loại nội dung.
        Returns:
            List[ProductEmbedding]
        """
        content = product.get(content_field, '')
        if not content:
            return []
        
        chunks = self.chunker.chunk_text(content)
        embeddings = []
        base_metadata = self._create_base_metadata(product)
        
        # Generate embeddings for all chunks at once for efficiency
        chunk_texts = [chunk.text for chunk in chunks]
        if content_field == 'descriptioninfo':
            chunk_texts = [f"Mô tả sản phẩm: {text}" for text in chunk_texts]
        elif content_field == 'ingredientinfo':
            chunk_texts = [f"Thành phần của sản phẩm: {text}" for text in chunk_texts]
        elif content_field == 'guideinfo':
            chunk_texts = [f"Hướng dẫn sử dụng sản phẩm: {text}" for text in chunk_texts]
        chunk_embeddings = self.model.encode(chunk_texts)
        
        for chunk, embedding in zip(chunks, chunk_embeddings):
            product_embedding = self._create_product_embedding(
                product.get('data_product'),
                content_type,
                chunk.text,
                embedding.tolist(),
                base_metadata,
                chunk.chunk_id
            )
            embeddings.append(product_embedding)
        
        return embeddings

class ProductProcessor:
    """Lớp chính để xử lý sản phẩm và sinh ra các embedding."""
    
    def __init__(self, model: SentenceTransformer, chunk_size: int = 300, overlap: int = 50):
        """
        Khởi tạo bộ xử lý sản phẩm với mô hình embedding và tham số chia đoạn.
        Args:
            model: Mô hình SentenceTransformer.
            chunk_size: Số ký tự tối đa mỗi đoạn.
            overlap: Số ký tự chồng lặp giữa các đoạn.
        """
        self.chunker = TextChunker(chunk_size=chunk_size, overlap=overlap)
        self.embedding_generator = ProductEmbeddingGenerator(model, self.chunker)
    
    def process_single_product(self, product: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Xử lý một sản phẩm và trả về tất cả các embedding của nó.
        Args:
            product: Thông tin sản phẩm.
        Returns:
            List[dict]: Danh sách embedding dạng dict.
        """
        all_embeddings = []
        
        try:
            # General information embedding
            general_embedding = self.embedding_generator.generate_general_info_embedding(product)
            all_embeddings.append(general_embedding.__dict__)
            
            # Description chunks
            desc_embeddings = self.embedding_generator.generate_content_chunk_embeddings(
                product, 'descriptioninfo', ContentType.DESCRIPTION
            )
            all_embeddings.extend([emb.__dict__ for emb in desc_embeddings])
            
            # Comment embeddings
            comment_embeddings = self.embedding_generator.generate_comment_embeddings(product)
            all_embeddings.extend([emb.__dict__ for emb in comment_embeddings])
            
            # Specification embedding
            spec_embedding = self.embedding_generator.generate_specification_embedding(product)
            if spec_embedding:
                all_embeddings.append(spec_embedding.__dict__)
            
            # Ingredient chunks
            ingredient_embeddings = self.embedding_generator.generate_content_chunk_embeddings(
                product, 'ingredientinfo', ContentType.INGREDIENT
            )
            all_embeddings.extend([emb.__dict__ for emb in ingredient_embeddings])
            
            # Guide chunks
            guide_embeddings = self.embedding_generator.generate_content_chunk_embeddings(
                product, 'guideinfo', ContentType.GUIDE
            )
            all_embeddings.extend([emb.__dict__ for emb in guide_embeddings])
            
        except Exception as e:
            print(f"Lỗi khi xử lý sản phẩm {product.get('data_product', 'unknown')}: {str(e)}")
            return []
        
        return all_embeddings
    
    def process_products_batch(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Xử lý một loạt sản phẩm và theo dõi tiến trình.
        Args:
            products: Danh sách sản phẩm.
        Returns:
            List[dict]: Danh sách embedding của tất cả sản phẩm.
        """
        all_documents = []
        
        print(f"Đang xử lý {len(products)} sản phẩm với chunking...")
        
        for i, product in enumerate(products):
            if i % 100 == 0:
                print(f"Đã xử lý {i}/{len(products)} sản phẩm")
            
            product_name = product.get('name', 'No Name')
            print(f"Đang xử lý sản phẩm {i+1}/{len(products)}: {product_name}")
            
            product_embeddings = self.process_single_product(product)
            all_documents.extend(product_embeddings)
            
            print(f"Đã sinh {len(product_embeddings)} embedding cho sản phẩm này")
            print(f"Tổng số document hiện tại: {len(all_documents)}")
            
            
            if i == 49:  # Giới hạn 50 sản phẩm để test
                print("Dừng lại sau khi xử lý 50 sản phẩm để kiểm thử")
                break
        
        print(f"Đã tạo {len(all_documents)} document chunks từ {len(products)} sản phẩm")
        return all_documents


def process_products_with_chunking(products: List[Dict[str, Any]], 
                                 model: SentenceTransformer,
                                 chunk_size: int = 300, 
                                 overlap: int = 50) -> List[Dict[str, Any]]:
    """
    Hàm chính để xử lý danh sách sản phẩm, chia nhỏ nội dung và sinh embedding.

    Args:
        products: Danh sách các dictionary sản phẩm
        model: Mô hình SentenceTransformer để tạo embedding
        chunk_size: Số ký tự tối đa mỗi đoạn
        overlap: Số ký tự chồng lặp giữa các đoạn

    Returns:
        Danh sách các document đã được embedding
    """
    processor = ProductProcessor(model, chunk_size, overlap)
    return processor.process_products_batch(products)