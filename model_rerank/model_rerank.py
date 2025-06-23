"""
Model Rerank sử dụng BAAI/bge-reranker-v2-m3
Cải thiện độ chính xác của kết quả tìm kiếm bằng cách rerank lại các documents
"""

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from typing import List, Dict, Any, Tuple
import numpy as np


class BGEReranker:
    def __init__(self, model_name: str = "BAAI/bge-reranker-v2-m3"):
        """
        Khởi tạo BGE Reranker model
        
        Args:
            model_name: Tên model reranker (mặc định: BAAI/bge-reranker-v2-m3)
        """
        self.model_name = model_name
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        print(f"Đang tải BGE Reranker model: {model_name}")
        print(f"Device: {self.device}")
        
        try:
            # Load tokenizer và model
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
            self.model.to(self.device)
            self.model.eval()
            
            print("✅ BGE Reranker model đã sẵn sàng!")
            
        except Exception as e:
            print(f"❌ Lỗi khi tải model: {e}")
            raise e
    
    def rerank(self, query: str, documents: List[Dict[str, Any]], top_k: int = None) -> List[Dict[str, Any]]:
        """
        Rerank lại danh sách documents dựa trên query
        
        Args:
            query: Câu hỏi/truy vấn
            documents: Danh sách documents từ vector search
            top_k: Số lượng documents trả về sau rerank (None = tất cả)
            
        Returns:
            Danh sách documents đã được rerank theo độ liên quan
        """
        if not documents:
            return []
        
        print(f"🔄 Đang rerank {len(documents)} documents...")
        
        try:
            # Tính rerank scores
            rerank_scores = self._compute_rerank_scores(query, documents)
            
            # Gán scores mới cho documents
            for i, doc in enumerate(documents):
                doc['rerank_score'] = rerank_scores[i]
                # Giữ lại original score từ vector search
                if 'score' in doc:
                    doc['vector_score'] = doc['score']
                doc['score'] = rerank_scores[i]  # Cập nhật score chính
            
            # Sắp xếp theo rerank score (cao → thấp)
            reranked_docs = sorted(documents, key=lambda x: x['rerank_score'], reverse=True)
            
            # Lấy top_k nếu được chỉ định
            if top_k is not None:
                reranked_docs = reranked_docs[:top_k]
            
            print(f"✅ Hoàn thành rerank, trả về {len(reranked_docs)} documents")
            
            return reranked_docs
            
        except Exception as e:
            print(f"❌ Lỗi trong quá trình rerank: {e}")
            # Trả về documents gốc nếu có lỗi
            return documents
    
    def _compute_rerank_scores(self, query: str, documents: List[Dict[str, Any]]) -> List[float]:
        """
        Tính toán rerank scores cho từng document
        
        Args:
            query: Câu hỏi
            documents: Danh sách documents
            
        Returns:
            List scores tương ứng với từng document
        """
        scores = []
        
        # Xử lý từng document
        for doc in documents:
            # Lấy text content từ document
            doc_text = doc.get('text', '')
            if not doc_text:
                scores.append(0.0)
                continue
            
            # Tính score cho cặp (query, document)
            score = self._compute_pair_score(query, doc_text)
            scores.append(score)
        
        return scores
    
    def _compute_pair_score(self, query: str, document: str) -> float:
        """
        Tính score cho một cặp (query, document)
        
        Args:
            query: Câu hỏi
            document: Nội dung document
            
        Returns:
            Score từ 0.0 đến 1.0
        """
        try:
            # Tokenize input
            inputs = self.tokenizer(
                query, 
                document,
                padding=True,
                truncation=True,
                max_length=512,  
                return_tensors="pt"
            )
            
            # Chuyển sang device
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Forward pass
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits
                score = torch.sigmoid(logits).cpu().item()
                
            return float(score)
            
        except Exception as e:
            print(f"⚠️ Lỗi khi tính score cho document: {e}")
            return 0.0
    
    def rerank_with_batch(self, query: str, documents: List[Dict[str, Any]], 
                         batch_size: int = 8, top_k: int = None) -> List[Dict[str, Any]]:
        """
        Rerank với batch processing để tăng tốc độ
        
        Args:
            query: Câu hỏi
            documents: Danh sách documents
            batch_size: Kích thước batch
            top_k: Số lượng documents trả về
            
        Returns:
            Danh sách documents đã được rerank
        """
        if not documents:
            return []
        
        print(f"🔄 Đang rerank {len(documents)} documents với batch_size={batch_size}")
        
        try:
            all_scores = []
            
            # Xử lý theo batch
            for i in range(0, len(documents), batch_size):
                batch_docs = documents[i:i + batch_size]
                batch_texts = [doc.get('text', '') for doc in batch_docs]
                
                # Tính scores cho batch
                batch_scores = self._compute_batch_scores(query, batch_texts)
                all_scores.extend(batch_scores)
            
            # Gán scores cho documents
            for i, doc in enumerate(documents):
                doc['rerank_score'] = all_scores[i]
                if 'score' in doc:
                    doc['vector_score'] = doc['score']
                doc['score'] = all_scores[i]
            
            # Sắp xếp và trả về
            reranked_docs = sorted(documents, key=lambda x: x['rerank_score'], reverse=True)
            
            if top_k is not None:
                reranked_docs = reranked_docs[:top_k]
            
            print(f"✅ Hoàn thành batch rerank, trả về {len(reranked_docs)} documents")
            
            return reranked_docs
            
        except Exception as e:
            print(f"❌ Lỗi trong batch rerank: {e}")
            return documents
    
    def _compute_batch_scores(self, query: str, documents: List[str]) -> List[float]:
        """
        Tính scores cho một batch documents
        
        Args:
            query: Câu hỏi
            documents: List text của documents
            
        Returns:
            List scores
        """
        try:
            # Tạo pairs (query, doc) cho toàn bộ batch
            queries = [query] * len(documents)
            
            # Tokenize batch
            inputs = self.tokenizer(
                queries,
                documents,
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors="pt"
            )
            
            # Chuyển sang device
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Forward pass
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits
                
                # Chuyển thành scores
                scores = torch.sigmoid(logits).cpu().numpy().flatten()
                
            return scores.tolist()
            
        except Exception as e:
            print(f"⚠️ Lỗi trong batch scoring: {e}")
            return [0.0] * len(documents)
    
    def compare_scores(self, documents: List[Dict[str, Any]]) -> None:
        """
        So sánh vector scores vs rerank scores để debug
        
        Args:
            documents: Danh sách documents đã rerank
        """
        print("\n📊 SO SÁNH SCORES:")
        print("-" * 80)
        print(f"{'#':<3} {'Vector Score':<12} {'Rerank Score':<12} {'Improvement':<12} {'Document':<30}")
        print("-" * 80)
        
        for i, doc in enumerate(documents[:10], 1):  # Chỉ hiển thị top 10
            vector_score = doc.get('vector_score', 0.0)
            rerank_score = doc.get('rerank_score', 0.0)
            improvement = rerank_score - vector_score
            doc_preview = doc.get('text', '')[:30] + "..." if len(doc.get('text', '')) > 30 else doc.get('text', '')
            
            print(f"{i:<3} {vector_score:<12.4f} {rerank_score:<12.4f} {improvement:<+12.4f} {doc_preview:<30}")
        
        print("-" * 80)


class RerankService:
    """
    Service wrapper cho BGE Reranker
    """
    
    def __init__(self, model_name: str = "BAAI/bge-reranker-v2-m3"):
        """
        Khởi tạo Rerank Service
        
        Args:
            model_name: Tên model reranker
        """
        self.reranker = BGEReranker(model_name)
    
    def enhance_search_results(self, query: str, search_results: List[Dict[str, Any]], 
                             top_k: int = 5, use_batch: bool = True) -> List[Dict[str, Any]]:
        """
        Cải thiện kết quả tìm kiếm bằng reranking
        
        Args:
            query: Câu hỏi gốc
            search_results: Kết quả từ vector search
            top_k: Số lượng kết quả cuối cùng
            use_batch: Sử dụng batch rerank
            
        Returns:
            Kết quả đã được rerank và cải thiện
        """
        if not search_results:
            return []
        
        print(f"Đang cải thiện {len(search_results)} kết quả tìm kiếm...")
        
        # Rerank
        if use_batch and len(search_results) > 4:
            reranked_results = self.reranker.rerank_with_batch(
                query=query,
                documents=search_results,
                batch_size=8,
                top_k=top_k
            )
        else:
            reranked_results = self.reranker.rerank(
                query=query,
                documents=search_results,
                top_k=top_k
            )
        
        # Debug: So sánh scores
        if len(reranked_results) > 0:
            self.reranker.compare_scores(reranked_results)
        
        return reranked_results
    