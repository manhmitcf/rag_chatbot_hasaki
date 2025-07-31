from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
from dataclasses import dataclass
from text_splitter import AdvancedTextSplitter, ContentType, ChunkData
from config import EMBEDDING_BATCH_SIZE

@dataclass
class ProductEmbedding:
    """Lưu trữ embedding của sản phẩm cùng với metadata"""
    id: str
    values: List[float]
    metadata: Dict[str, Any]

class AdvancedEmbeddingGenerator:
    """
    Lớp tạo embedding nâng cao với hỗ trợ GPU và batch processing
    """
    
    def __init__(self, model: SentenceTransformer, text_splitter: AdvancedTextSplitter):
        """
        Khởi tạo với model embedding và text splitter
        
        Args:
            model: SentenceTransformer model (đã được load với device)
            text_splitter: AdvancedTextSplitter instance
        """
        self.model = model
        self.text_splitter = text_splitter
        self.batch_size = EMBEDDING_BATCH_SIZE
        
        # Vietnamese field labels
        self.field_labels = {
            'name': 'Tên sản phẩm',
            'english_name': 'Tên tiếng Anh',
            'brand': 'Thương hiệu',
            'category_name': 'Danh mục',
            'price': 'Giá hiện tại',
            'market_price': 'Giá thị trường',
            'total_rating': 'Tổng số đánh giá',
            'average_rating': 'Đánh giá trung bình',
            'comment': 'Số bình luận',
            'categorys': 'Danh mục đầy đủ',
            'data_variant': 'Biến thể',
            'discount_percent': 'Phần trăm giảm giá',
            'url': 'URL sản phẩm'
        }
    
    def _encode_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Encode texts với batch processing để tối ưu GPU
        
        Args:
            texts: Danh sách văn bản cần encode
        Returns:
            List embeddings
        """
        if not texts:
            return []
        
        # Xử lý theo batch để tối ưu GPU memory
        all_embeddings = []
        for i in range(0, len(texts), self.batch_size):
            batch_texts = texts[i:i + self.batch_size]
            batch_embeddings = self.model.encode(batch_texts, show_progress_bar=False)
            all_embeddings.extend(batch_embeddings.tolist())
        
        return all_embeddings
    
    def _create_base_metadata(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Tạo metadata cơ bản cho embedding
        
        Args:
            product: Thông tin sản phẩm
        Returns:
            Dictionary metadata cơ bản
        """
        return {
            "product_id": product.get('data_product'),
            "name": product.get('name', ''),
            "english_name": product.get('english_name', ''),
            "category_name": product.get('category_name', ''),
            "brand": product.get('brand', ''),
            "price": product.get('price'),
            "market_price": product.get('market_price'),
            "total_rating": product.get('total_rating', 0),
            "average_rating": product.get('average_rating', 0),
            "data_variant": product.get('data_variant', ''),
            "discount_percent": product.get('discount_percent', 0),
            "url": product.get('url', '')
        }
    
    def _create_embedding_id(self, product_id: str, content_type: ContentType, chunk_id: Optional[int] = None) -> str:
        """
        Tạo ID duy nhất cho embedding
        
        Args:
            product_id: ID sản phẩm
            content_type: Loại nội dung
            chunk_id: ID chunk (nếu có)
        Returns:
            String ID duy nhất
        """
        embedding_id = f"{product_id}_{content_type.value}"
        if chunk_id is not None:
            embedding_id += f"_{chunk_id}"
        return embedding_id
    
    def _create_product_embedding(self, product_id: str, content_type: ContentType,
                                text: str, embedding: List[float],
                                base_metadata: Dict[str, Any],
                                chunk_id: Optional[int] = None,
                                additional_metadata: Dict[str, Any] = None) -> ProductEmbedding:
        """
        Tạo ProductEmbedding object
        
        Args:
            product_id: ID sản phẩm
            content_type: Loại nội dung
            text: Văn bản gốc
            embedding: Vector embedding
            base_metadata: Metadata cơ bản
            chunk_id: ID chunk
            additional_metadata: Metadata bổ sung
        Returns:
            ProductEmbedding object
        """
        embedding_id = self._create_embedding_id(product_id, content_type, chunk_id)
        
        metadata = base_metadata.copy()
        metadata.update({
            "type": content_type.value,
            "text": text,
            "chunk_id": chunk_id if chunk_id is not None else 0
        })
        
        if additional_metadata:
            metadata.update(additional_metadata)
        
        return ProductEmbedding(
            id=embedding_id,
            values=embedding,
            metadata=metadata
        )
    
    def _create_context_header(self, product: Dict[str, Any], content_type_name: str) -> str:
        """
        Tạo context header cho chunk dựa trên options (không bao gồm URL)
        
        Args:
            product: Thông tin sản phẩm
            content_type_name: Tên loại nội dung (mô tả, thành phần)
        Returns:
            String context header
        """
        product_name = product.get('name', 'Sản phẩm')
        options = product.get('options', [])
        
        if options and len(options) > 0:
            # Có options - tạo header với tất cả sản phẩm liên quan
            product_list = []
            
            # Thêm sản phẩm chính
            product_list.append(product_name)
            
            # Thêm các options (chỉ tên, không có URL)
            for option in options:
                option_name = option.get('name', '')
                if option_name:
                    product_list.append(option_name)
            
            # Tạo header
            products_text = "; ".join(product_list)
            header = f"Thông tin {content_type_name} của các sản phẩm [{products_text}]:"
        else:
            # Không có options - chỉ sản phẩm hiện tại
            header = f"Thông tin {content_type_name} của sản phẩm [{product_name}]:"
        
        return header
    
    def _create_options_metadata(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Tạo metadata cho options của sản phẩm (không bao gồm ID)
        
        Args:
            product: Thông tin sản phẩm
        Returns:
            Dictionary chứa thông tin options
        """
        options = product.get('options', [])
        options_info = []
        
        for option in options:
            option_info = {
                "name": option.get('name', ''),
                "url": option.get('product_url', ''),
                "brand": option.get('brand', ''),
                "price": option.get('price')
            }
            options_info.append(option_info)
        
        return {
            "has_options": len(options) > 0,
            "options_count": len(options),
            "options": options_info
        }
    
    def generate_general_info_embedding(self, product: Dict[str, Any]) -> ProductEmbedding:
        """
        Tạo embedding cho thông tin tổng quan sản phẩm
        
        Args:
            product: Thông tin sản phẩm
        Returns:
            ProductEmbedding
        """
        info_parts = []
        
        for field, label in self.field_labels.items():
            value = product.get(field, f'Không có {field.lower()}')
            if value is not None and str(value).strip():
                info_parts.append(f"{label}: {value}")
        
        general_info = f"Thông tin tổng quan sản phẩm {product.get('name', '')}: " + ". ".join(info_parts) + "."
        cleaned_info = self.text_splitter.clean_text(general_info)
        
        # Sử dụng batch encoding (dù chỉ 1 text)
        embeddings = self._encode_batch([cleaned_info])
        embedding = embeddings[0]
        
        base_metadata = self._create_base_metadata(product)
        
        # Thêm options metadata
        options_metadata = self._create_options_metadata(product)
        base_metadata.update(options_metadata)
        
        return self._create_product_embedding(
            product.get('data_product'),
            ContentType.GENERAL_INFO,
            cleaned_info,
            embedding,
            base_metadata
        )
    
    def generate_markdown_description_embeddings(self, product: Dict[str, Any]) -> List[ProductEmbedding]:
        """
        Tạo embedding cho mô tả markdown sử dụng MarkdownTextSplitter với GPU optimization
        
        Args:
            product: Thông tin sản phẩm
        Returns:
            List[ProductEmbedding]
        """
        markdown_content = product.get('descriptioninfo_markdown', '')
        if not markdown_content:
            return []
        
        # Sử dụng MarkdownTextSplitter để chia nhỏ
        chunks = self.text_splitter.split_markdown_content(markdown_content, product)
        
        if not chunks:
            return []
        
        embeddings = []
        base_metadata = self._create_base_metadata(product)
        
        # Tạo context header
        context_header = self._create_context_header(product, "mô tả")
        
        # Tạo embedding cho tất cả chunks với context header
        chunk_texts = [f"{context_header}\n\n{chunk.text}" for chunk in chunks]
        chunk_embeddings = self._encode_batch(chunk_texts)
        
        for chunk, embedding, enhanced_text in zip(chunks, chunk_embeddings, chunk_texts):
            # Thêm context header và options vào metadata
            additional_metadata = chunk.metadata.copy() if chunk.metadata else {}
            
            # Thêm options metadata
            options_metadata = self._create_options_metadata(product)
            
            additional_metadata.update({
                "context_header": context_header,
                "original_text": chunk.text,
                "enhanced_text": enhanced_text,
                **options_metadata  # Unpack options metadata
            })
            
            product_embedding = self._create_product_embedding(
                product.get('data_product'),
                ContentType.DESCRIPTION_MARKDOWN,
                enhanced_text,  # Lưu text đã được enhance
                embedding,
                base_metadata,
                chunk.chunk_id,
                additional_metadata
            )
            embeddings.append(product_embedding)
        
        return embeddings
    
    def generate_specification_embedding(self, product: Dict[str, Any]) -> Optional[ProductEmbedding]:
        """
        Tạo embedding cho thông số kỹ thuật
        
        Args:
            product: Thông tin sản phẩm
        Returns:
            ProductEmbedding hoặc None
        """
        specification = product.get('specificationinfo', '')
        if not specification:
            return None
        
        cleaned_spec = self.text_splitter.clean_text(specification)
        
        # Tạo context header cho specification
        product_name = product.get('name', 'Sản phẩm')
        context_header = f'Thông số kỹ thuật sản phẩm "{product_name}":'
        enhanced_spec = f"{context_header}\n\n{cleaned_spec}"
        
        # Sử dụng batch encoding
        embeddings = self._encode_batch([enhanced_spec])
        embedding = embeddings[0]
        
        base_metadata = self._create_base_metadata(product)
        
        # Thêm options metadata
        options_metadata = self._create_options_metadata(product)
        
        # Thêm context header và enhanced text vào metadata
        additional_metadata = {
            "context_header": context_header,
            "original_text": specification,
            "enhanced_text": enhanced_spec,
            **options_metadata
        }
        
        return self._create_product_embedding(
            product.get('data_product'),
            ContentType.SPECIFICATION,
            enhanced_spec,  # Lưu text đã được enhance
            embedding,
            base_metadata,
            None,
            additional_metadata
        )
    
    def generate_ingredient_embeddings(self, product: Dict[str, Any]) -> List[ProductEmbedding]:
        """
        Tạo embedding cho thành phần sản phẩm với GPU optimization
        
        Args:
            product: Thông tin sản phẩm
        Returns:
            List[ProductEmbedding]
        """
        ingredient_content = product.get('ingredientinfo', '')
        if not ingredient_content:
            return []
        
        chunks = self.text_splitter.split_recursive_content(
            ingredient_content,
            ContentType.INGREDIENT,
            product
        )
        
        if not chunks:
            return []
        
        embeddings = []
        base_metadata = self._create_base_metadata(product)
        
        # Tạo context header cho thành phần
        context_header = self._create_context_header(product, "thành phần")
        
        # Batch processing cho ingredients với context header
        chunk_texts = [f"{context_header}\n\n{chunk.text}" for chunk in chunks]
        chunk_embeddings = self._encode_batch(chunk_texts)
        
        for chunk, embedding, enhanced_text in zip(chunks, chunk_embeddings, chunk_texts):
            # Thêm context header và options vào metadata
            additional_metadata = chunk.metadata.copy() if chunk.metadata else {}
            
            # Thêm options metadata
            options_metadata = self._create_options_metadata(product)
            
            additional_metadata.update({
                "context_header": context_header,
                "original_text": chunk.text,
                "enhanced_text": enhanced_text,
                **options_metadata  # Unpack options metadata
            })
            
            product_embedding = self._create_product_embedding(
                product.get('data_product'),
                ContentType.INGREDIENT,
                enhanced_text,  # Lưu text đã được enhance
                embedding,
                base_metadata,
                chunk.chunk_id,
                additional_metadata
            )
            embeddings.append(product_embedding)
        
        return embeddings
    
    def generate_guide_embedding(self, product: Dict[str, Any]) -> Optional[ProductEmbedding]:
        """
        Tạo embedding cho hướng dẫn sử dụng (không split, giữ nguyên cả đoạn)
        
        Args:
            product: Thông tin sản phẩm
        Returns:
            ProductEmbedding hoặc None
        """
        guide_content = product.get('guideinfo', '')
        if not guide_content:
            return None
        
        cleaned_guide = self.text_splitter.clean_text(guide_content)
        
        # Tạo context header cho guide
        product_name = product.get('name', 'Sản phẩm')
        context_header = f'Hướng dẫn sử dụng sản phẩm "{product_name}":'
        enhanced_guide = f"{context_header}\n\n{cleaned_guide}"
        
        # Sử dụng batch encoding
        embeddings = self._encode_batch([enhanced_guide])
        embedding = embeddings[0]
        
        base_metadata = self._create_base_metadata(product)
        
        # Thêm options metadata
        options_metadata = self._create_options_metadata(product)
        
        # Thêm context header và enhanced text vào metadata
        additional_metadata = {
            "context_header": context_header,
            "original_text": guide_content,
            "enhanced_text": enhanced_guide,
            **options_metadata
        }
        
        return self._create_product_embedding(
            product.get('data_product'),
            ContentType.GUIDE,
            enhanced_guide,  # Lưu text đã được enhance
            embedding,
            base_metadata,
            None,
            additional_metadata
        )