
import re
from typing import List, Dict, Any
from dataclasses import dataclass
from enum import Enum
from langchain.text_splitter import MarkdownTextSplitter, RecursiveCharacterTextSplitter

class ContentType(Enum):
    """Enum cho các loại nội dung khác nhau của sản phẩm"""
    DESCRIPTION_MARKDOWN = "description_markdown"
    GENERAL_INFO = "general_info"
    SPECIFICATION = "specification"
    INGREDIENT = "ingredient"
    GUIDE = "guide"

@dataclass
class ChunkData:
    """Lưu trữ thông tin về một đoạn văn bản đã được chia nhỏ"""
    text: str
    chunk_id: int
    content_type: ContentType
    metadata: Dict[str, Any] = None

class AdvancedTextSplitter:
    """
    Lớp xử lý chia nhỏ văn bản với MarkdownTextSplitter và RecursiveCharacterTextSplitter
    """
    
    def __init__(self, 
                 chunk_size: int = 500, 
                 overlap: int = 100,
                 markdown_chunk_size: int = 800,
                 markdown_overlap: int = 150):
        """
        Khởi tạo text splitter với hai loại splitter chính
        
        Args:
            chunk_size: Kích thước chunk cho RecursiveCharacterTextSplitter
            overlap: Độ chồng lấp cho RecursiveCharacterTextSplitter
            markdown_chunk_size: Kích thước chunk cho MarkdownTextSplitter
            markdown_overlap: Độ chồng lấp cho MarkdownTextSplitter
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.markdown_chunk_size = markdown_chunk_size
        self.markdown_overlap = markdown_overlap
        
        # MarkdownTextSplitter cho descriptioninfo_markdown
        self.markdown_splitter = MarkdownTextSplitter(
            chunk_size=markdown_chunk_size,
            chunk_overlap=markdown_overlap,
            length_function=len,
            is_separator_regex=False,
        )
        
        # RecursiveCharacterTextSplitter cho tất cả các trường khác
        self.recursive_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap,
            length_function=len,
            is_separator_regex=False,
        )
        
        # Pattern để làm sạch text
        self._whitespace_pattern = re.compile(r'\s+')
    
    def clean_text(self, text: str) -> str:
        """Làm sạch và chuẩn hóa văn bản"""
        if not text:
            return ""
        text = self._whitespace_pattern.sub(' ', text)
        return text.strip()
    
    def clean_markdown_text(self, text: str) -> str:
        """Làm sạch văn bản markdown, giữ lại cấu trúc quan trọng"""
        if not text:
            return ""
        
        # Chuẩn hóa markdown headers
        text = re.sub(r'#+\s*#+\s*', '## ', text)
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        text = re.sub(r'^\s+|\s+$', '', text, flags=re.MULTILINE)
        
        return text.strip()
    
    def split_markdown_content(self, text: str, product_info: Dict[str, Any] = None) -> List[ChunkData]:
        """
        Chia nhỏ nội dung markdown sử dụng MarkdownTextSplitter
        Chỉ dành cho trường descriptioninfo_markdown
        """
        if not text:
            return []
        
        cleaned_text = self.clean_markdown_text(text)
        
        if len(cleaned_text) <= self.markdown_chunk_size:
            return [ChunkData(
                text=cleaned_text,
                chunk_id=0,
                content_type=ContentType.DESCRIPTION_MARKDOWN,
                metadata=self._create_chunk_metadata(product_info, 0, len(cleaned_text))
            )]
        
        try:
            chunks = self.markdown_splitter.split_text(cleaned_text)
            chunk_data_list = []
            
            for i, chunk in enumerate(chunks):
                if chunk.strip():
                    chunk_data = ChunkData(
                        text=chunk.strip(),
                        chunk_id=i,
                        content_type=ContentType.DESCRIPTION_MARKDOWN,
                        metadata=self._create_chunk_metadata(product_info, i, len(chunk))
                    )
                    chunk_data_list.append(chunk_data)
            
            return chunk_data_list
            
        except Exception as e:
            print(f"Lỗi khi split markdown: {e}")
            # Fallback to recursive splitter
            return self.split_recursive_content(cleaned_text, ContentType.DESCRIPTION_MARKDOWN, product_info)
    
    def split_recursive_content(self, text: str, content_type: ContentType, 
                              product_info: Dict[str, Any] = None) -> List[ChunkData]:
        """
        Chia nhỏ nội dung sử dụng RecursiveCharacterTextSplitter
        Dành cho các trường: descriptioninfo, specificationinfo, ingredientinfo, guideinfo
        """
        if not text:
            return []
        
        cleaned_text = self.clean_text(text)
        
        if len(cleaned_text) <= self.chunk_size:
            return [ChunkData(
                text=cleaned_text,
                chunk_id=0,
                content_type=content_type,
                metadata=self._create_chunk_metadata(product_info, 0, len(cleaned_text))
            )]
        
        try:
            chunks = self.recursive_splitter.split_text(cleaned_text)
            chunk_data_list = []
            
            for i, chunk in enumerate(chunks):
                if chunk.strip():
                    chunk_data = ChunkData(
                        text=chunk.strip(),
                        chunk_id=i,
                        content_type=content_type,
                        metadata=self._create_chunk_metadata(product_info, i, len(chunk))
                    )
                    chunk_data_list.append(chunk_data)
            
            return chunk_data_list
            
        except Exception as e:
            print(f"Lỗi khi split recursive: {e}")
            return []
    
    def _create_chunk_metadata(self, product_info: Dict[str, Any], chunk_id: int, chunk_length: int) -> Dict[str, Any]:
        """Tạo metadata cho chunk"""
        if not product_info:
            return {"chunk_id": chunk_id, "chunk_length": chunk_length}
        
        return {
            "chunk_id": chunk_id,
            "chunk_length": chunk_length,
            "product_id": product_info.get('data_product'),
            "product_name": product_info.get('name', ''),
            "brand": product_info.get('brand', ''),
            "category": product_info.get('category_name', ''),
            "price": product_info.get('price'),
            "rating": product_info.get('average_rating')
        }