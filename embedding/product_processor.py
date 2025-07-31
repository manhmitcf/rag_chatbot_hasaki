from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
from embedding_generator import AdvancedEmbeddingGenerator
from text_splitter import AdvancedTextSplitter
from config import (
    DEFAULT_CHUNK_SIZE, DEFAULT_OVERLAP, 
    MARKDOWN_CHUNK_SIZE, MARKDOWN_OVERLAP
)

class AdvancedProductProcessor:
    """
    Lớp xử lý sản phẩm nâng cao với hỗ trợ MarkdownTextSplitter
    """
    
    def __init__(self, 
                 model: SentenceTransformer,
                 chunk_size: int = DEFAULT_CHUNK_SIZE,
                 overlap: int = DEFAULT_OVERLAP,
                 markdown_chunk_size: int = MARKDOWN_CHUNK_SIZE,
                 markdown_overlap: int = MARKDOWN_OVERLAP):
        """
        Khởi tạo processor với các tham số cấu hình
        
        Args:
            model: SentenceTransformer model
            chunk_size: Kích thước chunk mặc định
            overlap: Độ chồng lấp mặc định
            markdown_chunk_size: Kích thước chunk cho markdown
            markdown_overlap: Độ chồng lấp cho markdown
        """
        self.model = model
        self.text_splitter = AdvancedTextSplitter(
            chunk_size=chunk_size,
            overlap=overlap,
            markdown_chunk_size=markdown_chunk_size,
            markdown_overlap=markdown_overlap
        )
        self.embedding_generator = AdvancedEmbeddingGenerator(model, self.text_splitter)
    
    def process_single_product(self, product: Dict[str, Any], 
                             include_markdown: bool = True) -> List[Dict[str, Any]]:
        """
        Xử lý một sản phẩm và tạo tất cả embeddings
        
        Args:
            product: Thông tin sản phẩm
            include_markdown: Có xử lý markdown description không
        Returns:
            List[dict]: Danh sách embeddings dạng dict
        """
        all_embeddings = []
        product_id = product.get('data_product', 'unknown')
        product_name = product.get('name', 'No Name')
        
        try:
            print(f"Đang xử lý sản phẩm: {product_name} (ID: {product_id})")
            
            # 1. General information embedding
            general_embedding = self.embedding_generator.generate_general_info_embedding(product)
            all_embeddings.append(general_embedding.__dict__)
            print(f"  - Tạo general info embedding")
            
            # 2. Markdown description embeddings (chỉ xử lý loại này)
            if include_markdown:
                markdown_embeddings = self.embedding_generator.generate_markdown_description_embeddings(product)
                all_embeddings.extend([emb.__dict__ for emb in markdown_embeddings])
                print(f"  - Tạo {len(markdown_embeddings)} markdown description embeddings")
            
            # 3. Specification embedding (với context header)
            spec_embedding = self.embedding_generator.generate_specification_embedding(product)
            if spec_embedding:
                all_embeddings.append(spec_embedding.__dict__)
                print(f"  - Tạo specification embedding (với context header)")
            
            # 4. Ingredient embeddings (với context header)
            ingredient_embeddings = self.embedding_generator.generate_ingredient_embeddings(product)
            all_embeddings.extend([emb.__dict__ for emb in ingredient_embeddings])
            print(f"  - Tạo {len(ingredient_embeddings)} ingredient embeddings (với context header)")
            
            # 5. Guide embedding (với context header, không split)
            guide_embedding = self.embedding_generator.generate_guide_embedding(product)
            if guide_embedding:
                all_embeddings.append(guide_embedding.__dict__)
                print(f"  - Tạo guide embedding (với context header, không split)")
            
            print(f"  - Tổng cộng: {len(all_embeddings)} embeddings cho sản phẩm này")
            
        except Exception as e:
            print(f"Lỗi khi xử lý sản phẩm {product_id}: {str(e)}")
            return []
        
        return all_embeddings
    
    def process_products_batch(self, products: List[Dict[str, Any]], 
                             max_products: int = None,
                             include_markdown: bool = True) -> List[Dict[str, Any]]:
        """
        Xử lý một batch sản phẩm
        
        Args:
            products: Danh sách sản phẩm
            max_products: Số lượng sản phẩm tối đa để xử lý (None = tất cả)
            include_markdown: Có xử lý markdown description không
        Returns:
            List[dict]: Danh sách tất cả embeddings
        """
        all_documents = []
        
        # Giới hạn số lượng sản phẩm nếu được chỉ định
        if max_products:
            products = products[:max_products]
        
        print(f"Bắt đầu xử lý {len(products)} sản phẩm với MarkdownTextSplitter...")
        print(f"Cấu hình:")
        print(f"  - Chunk size: {self.text_splitter.chunk_size}")
        print(f"  - Overlap: {self.text_splitter.overlap}")
        print(f"  - Markdown chunk size: {self.text_splitter.markdown_chunk_size}")
        print(f"  - Markdown overlap: {self.text_splitter.markdown_overlap}")
        print(f"  - Include markdown: {include_markdown}")
        print("-" * 50)
        
        for i, product in enumerate(products):
            print(f"\n[{i+1}/{len(products)}]", end=" ")
            
            product_embeddings = self.process_single_product(
                product,
                include_markdown=include_markdown
            )
            
            all_documents.extend(product_embeddings)
            
            # Progress report
            if (i + 1) % 10 == 0:
                print(f"\n--- Đã xử lý {i+1}/{len(products)} sản phẩm ---")
                print(f"--- Tổng số embeddings hiện tại: {len(all_documents)} ---")
        
        print(f"\n{'='*50}")
        print(f"Hoàn thành xử lý!")
        print(f"Tổng số sản phẩm: {len(products)}")
        print(f"Tổng số embeddings: {len(all_documents)}")
        print(f"Trung bình embeddings/sản phẩm: {len(all_documents)/len(products):.1f}")
        print(f"{'='*50}")
        
        return all_documents
    
    def get_processing_stats(self, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Lấy thống kê về dữ liệu sẽ được xử lý
        
        Args:
            products: Danh sách sản phẩm
        Returns:
            Dictionary chứa thống kê
        """
        stats = {
            "total_products": len(products),
            "has_markdown_description": 0,
            "has_specification": 0,
            "has_ingredient": 0,
            "has_guide": 0,
            "avg_markdown_length": 0
        }
        
        markdown_lengths = []
        
        for product in products:
            if product.get('descriptioninfo_markdown'):
                stats["has_markdown_description"] += 1
                markdown_lengths.append(len(product['descriptioninfo_markdown']))
            
            if product.get('specificationinfo'):
                stats["has_specification"] += 1
            
            if product.get('ingredientinfo'):
                stats["has_ingredient"] += 1
            
            if product.get('guideinfo'):
                stats["has_guide"] += 1
        
        # Tính trung bình
        if markdown_lengths:
            stats["avg_markdown_length"] = sum(markdown_lengths) / len(markdown_lengths)
        
        return stats

def process_products_with_advanced_chunking(products: List[Dict[str, Any]], 
                                          model: SentenceTransformer,
                                          chunk_size: int = DEFAULT_CHUNK_SIZE,
                                          overlap: int = DEFAULT_OVERLAP,
                                          markdown_chunk_size: int = MARKDOWN_CHUNK_SIZE,
                                          markdown_overlap: int = MARKDOWN_OVERLAP,
                                          max_products: int = None,
                                          include_markdown: bool = True) -> List[Dict[str, Any]]:
    """
    Hàm chính để xử lý sản phẩm với MarkdownTextSplitter
    
    Args:
        products: Danh sách sản phẩm
        model: SentenceTransformer model
        chunk_size: Kích thước chunk mặc định
        overlap: Độ chồng lấp mặc định
        markdown_chunk_size: Kích thước chunk cho markdown
        markdown_overlap: Độ chồng lấp cho markdown
        max_products: Số lượng sản phẩm tối đa
        include_markdown: Có xử lý markdown description không
    Returns:
        List[dict]: Danh sách embeddings
    """
    processor = AdvancedProductProcessor(
        model=model,
        chunk_size=chunk_size,
        overlap=overlap,
        markdown_chunk_size=markdown_chunk_size,
        markdown_overlap=markdown_overlap
    )
    
    # In thống kê trước khi xử lý
    stats = processor.get_processing_stats(products)
    print("Thống kê dữ liệu:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    print("-" * 50)
    
    return processor.process_products_batch(
        products=products,
        max_products=max_products,
        include_markdown=include_markdown
    )