import re
from typing import List
from dataclasses import dataclass
from enum import Enum

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

class TextChunker:
    """
    Lớp tiện ích để chia nhỏ văn bản dài thành các đoạn nhỏ hơn, đảm bảo ý nghĩa ngữ nghĩa.
    """
    
    def __init__(self, chunk_size: int = 300, overlap: int = 50):
        """
        Khởi tạo TextChunker với kích thước đoạn và số ký tự chồng lặp.
        
        Args:
            chunk_size: Số ký tự tối đa mỗi đoạn.
            overlap: Số ký tự chồng lặp giữa các đoạn.
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self._sentence_pattern = re.compile(r'[.!?](?:\s|$)')
        self._whitespace_pattern = re.compile(r'\s+')
    
    def clean_text(self, text: str) -> str:
        """
        Làm sạch và chuẩn hóa văn bản.
        
        Args:
            text: Chuỗi văn bản cần làm sạch.
        Returns:
            Chuỗi văn bản đã được loại bỏ khoảng trắng thừa và xuống dòng.
        """
        if not text:
            return ""
        
        # Loại bỏ khoảng trắng và xuống dòng thừa
        text = self._whitespace_pattern.sub(' ', text)
        return text.strip()
    
    def split_by_sentences(self, text: str) -> List[str]:
        """
        Tách văn bản thành các câu dựa trên dấu câu.
        
        Args:
            text: Chuỗi văn bản cần tách.
        Returns:
            Danh sách các câu đã được tách.
        """
        sentences = self._sentence_pattern.split(text)
        return [s.strip() for s in sentences if s.strip()]
    
    def chunk_text(self, text: str) -> List[ChunkData]:
        """
        Chia văn bản thành các đoạn nhỏ có thể chồng lặp.
        
        Args:
            text: Chuỗi văn bản cần chia nhỏ.
        Returns:
            Danh sách các đối tượng ChunkData chứa thông tin đoạn văn bản và metadata.
        """
        if not text or len(text) <= self.chunk_size:
            return [ChunkData(text=self.clean_text(text), chunk_id=0, content_type=ContentType.DESCRIPTION)]
        
        text = self.clean_text(text)
        chunks = []
        
        # Cố gắng tách theo câu để đảm bảo ý nghĩa ngữ nghĩa
        sentences = self.split_by_sentences(text)
        
        if len(sentences) > 1:
            chunks = self._chunk_by_sentences(sentences)
        else:
            chunks = self._chunk_by_characters(text)
        
        return chunks
    
    def _chunk_by_sentences(self, sentences: List[str]) -> List[ChunkData]:
        """
        Gom nhóm các câu thành các đoạn nhỏ.
        
        Args:
            sentences: Danh sách các câu đã được tách.
        Returns:
            Danh sách các đối tượng ChunkData.
        """
        chunks = []
        current_chunk = ""
        chunk_id = 0
        
        for sentence in sentences:
            # Nếu thêm câu này sẽ vượt quá kích thước đoạn, lưu lại đoạn hiện tại
            if len(current_chunk) + len(sentence) > self.chunk_size and current_chunk:
                chunks.append(ChunkData(
                    text=current_chunk.strip(),
                    chunk_id=chunk_id,
                    content_type=ContentType.DESCRIPTION
                ))
                
                # Bắt đầu đoạn mới với phần chồng lặp
                overlap_text = current_chunk[-self.overlap:] if len(current_chunk) > self.overlap else current_chunk
                current_chunk = overlap_text + " " + sentence
                chunk_id += 1
            else:
                current_chunk += " " + sentence if current_chunk else sentence
        
        # Thêm đoạn cuối cùng
        if current_chunk.strip():
            chunks.append(ChunkData(
                text=current_chunk.strip(),
                chunk_id=chunk_id,
                content_type=ContentType.DESCRIPTION
            ))
        
        return chunks
    
    def _chunk_by_characters(self, text: str) -> List[ChunkData]:
        """
        Chia nhỏ văn bản dựa trên số ký tự (dùng khi không thể tách theo câu).
        
        Args:
            text: Chuỗi văn bản cần chia nhỏ.
        Returns:
            Danh sách các đối tượng ChunkData.
        """
        chunks = []
        for i in range(0, len(text), self.chunk_size - self.overlap):
            chunk_text = text[i:i + self.chunk_size]
            chunks.append(ChunkData(
                text=chunk_text,
                chunk_id=i // (self.chunk_size - self.overlap),
                content_type=ContentType.DESCRIPTION
            ))
        return chunks