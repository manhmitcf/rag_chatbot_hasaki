"""
Model Rerank sử dụng BAAI/bge-reranker-v2-m3
Cải thiện độ chính xác của kết quả tìm kiếm bằng cách rerank lại các documents
Chỉ sử dụng text chunk, không bao gồm metadata
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
            
            print("BGE Reranker model đã sẵn sàng!")
            
        except Exception as e:
            print(f"Lỗi khi tải model: {e}")
            raise e
    
    def rerank(self, query: str, documents: List[Dict[str, Any]], top_k: int = None) -> List[Dict[str, Any]]:
        """
        Rerank lại danh sách documents dựa trên query - chỉ sử dụng text chunk
        
        Args:
            query: Câu hỏi/truy vấn
            documents: Danh sách documents từ vector search
            top_k: Số lượng documents trả về sau rerank (None = tất cả)
            
        Returns:
            Danh sách documents đã được rerank theo độ liên quan với metadata chi tiết
        """
        if not documents:
            return []
        
        print(f"Đang rerank {len(documents)} documents (chỉ sử dụng text chunk)...")
        
        try:
            # Tính rerank scores chỉ với text chunk
            rerank_scores = self._compute_rerank_scores(query, documents)
            
            # Gán scores mới cho documents và thêm metadata chi tiết
            for i, doc in enumerate(documents):
                # Lưu thông tin rerank
                doc['rerank_score'] = rerank_scores[i]
                
                # Giữ lại original score từ vector search
                if 'score' in doc:
                    doc['vector_score'] = doc['score']
                
                # Cập nhật score chính
                doc['score'] = rerank_scores[i]
                
                # Thêm metadata chi tiết cho chunk
                doc['rerank_metadata'] = {
                    'original_rank': i + 1,
                    'vector_score': doc.get('vector_score', 0.0),
                    'rerank_score': rerank_scores[i],
                    'score_improvement': rerank_scores[i] - doc.get('vector_score', 0.0),
                    'query_used': query,
                    'chunk_length': len(doc.get('text', '')),
                    'uses_metadata': False,  # Đánh dấu không sử dụng metadata
                    'product_info': {
                        'product_id': doc.get('metadata', {}).get('product_id'),
                        'product_name': doc.get('metadata', {}).get('name'),
                        'brand': doc.get('metadata', {}).get('brand'),
                        'category': doc.get('metadata', {}).get('category_name'),
                        'chunk_type': doc.get('metadata', {}).get('type')
                    }
                }
            
            # Sắp xếp theo rerank score (cao → thấp)
            reranked_docs = sorted(documents, key=lambda x: x['rerank_score'], reverse=True)
            
            # Cập nhật rank sau khi sắp xếp
            for i, doc in enumerate(reranked_docs):
                doc['rerank_metadata']['final_rank'] = i + 1
                doc['rerank_metadata']['rank_change'] = doc['rerank_metadata']['original_rank'] - (i + 1)
            
            # Lấy top_k nếu được chỉ định
            if top_k is not None:
                reranked_docs = reranked_docs[:top_k]
            
            print(f"Hoàn thành rerank, trả về {len(reranked_docs)} documents")
            
            # In thông tin chi tiết về reranking
            self._print_rerank_details(reranked_docs)
            
            return reranked_docs
            
        except Exception as e:
            print(f"Lỗi trong quá trình rerank: {e}")
            # Trả về documents gốc nếu có lỗi
            return documents
    
    def _compute_rerank_scores(self, query: str, documents: List[Dict[str, Any]]) -> List[float]:
        """
        Tính toán rerank scores cho từng document chỉ với text chunk
        
        Args:
            query: Câu hỏi
            documents: Danh sách documents
            
        Returns:
            List scores tương ứng với từng document
        """
        scores = []
        
        # Xử lý từng document
        for doc in documents:
            # Chỉ lấy text chunk, không dùng metadata
            text_content = doc.get('text', '')
            
            if not text_content:
                scores.append(0.0)
                continue
            
            # Tính score cho cặp (query, text_content)
            score = self._compute_pair_score(query, text_content)
            scores.append(score)
        
        return scores
    
    def _compute_pair_score(self, query: str, document: str) -> float:
        """
        Tính score cho một cặp (query, document)
        
        Args:
            query: Câu hỏi
            document: Nội dung document (chỉ text chunk)
            
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
            print(f"Lỗi khi tính score cho document: {e}")
            return 0.0
    
    def rerank_with_batch(self, query: str, documents: List[Dict[str, Any]], 
                         batch_size: int = 8, top_k: int = None) -> List[Dict[str, Any]]:
        """
        Rerank với batch processing để tăng tốc độ - chỉ sử dụng text chunk
        
        Args:
            query: Câu hỏi
            documents: Danh sách documents
            batch_size: Kích thước batch
            top_k: Số lượng documents trả về
            
        Returns:
            Danh sách documents đã được rerank với metadata chi tiết
        """
        if not documents:
            return []
        
        print(f"Đang rerank {len(documents)} documents với batch_size={batch_size} (chỉ text chunk)")
        
        try:
            all_scores = []
            
            # Xử lý theo batch
            for i in range(0, len(documents), batch_size):
                batch_docs = documents[i:i + batch_size]
                
                # Tính scores cho batch chỉ với text chunk
                batch_scores = self._compute_batch_scores(query, batch_docs)
                all_scores.extend(batch_scores)
            
            # Gán scores cho documents và thêm metadata chi tiết
            for i, doc in enumerate(documents):
                # Lưu thông tin rerank
                doc['rerank_score'] = all_scores[i]
                
                # Giữ lại original score từ vector search
                if 'score' in doc:
                    doc['vector_score'] = doc['score']
                
                # Cập nhật score sau khi rerank
                doc['score'] = all_scores[i]
                
                # Thêm metadata chi tiết cho chunk
                doc['rerank_metadata'] = {
                    'original_rank': i + 1,
                    'vector_score': doc.get('vector_score', 0.0),
                    'rerank_score': all_scores[i],
                    'score_improvement': all_scores[i] - doc.get('vector_score', 0.0),
                    'query_used': query,
                    'chunk_length': len(doc.get('text', '')),
                    'batch_processed': True,
                    'batch_size': batch_size,
                    'uses_metadata': False,  # Đánh dấu không sử dụng metadata
                    'product_info': {
                        'product_id': doc.get('metadata', {}).get('product_id'),
                        'product_name': doc.get('metadata', {}).get('name'),
                        'brand': doc.get('metadata', {}).get('brand'),
                        'category': doc.get('metadata', {}).get('category_name'),
                        'chunk_type': doc.get('metadata', {}).get('type')
                    }
                }
            
            # Sắp xếp và trả về
            reranked_docs = sorted(documents, key=lambda x: x['rerank_score'], reverse=True)
            
            # Cập nhật rank sau khi sắp xếp
            for i, doc in enumerate(reranked_docs):
                doc['rerank_metadata']['final_rank'] = i + 1
                doc['rerank_metadata']['rank_change'] = doc['rerank_metadata']['original_rank'] - (i + 1)
            
            if top_k is not None:
                reranked_docs = reranked_docs[:top_k]
            
            print(f"Hoàn thành batch rerank, trả về {len(reranked_docs)} documents")
            
            # In thông tin chi tiết về reranking
            self._print_rerank_details(reranked_docs)
            
            return reranked_docs
            
        except Exception as e:
            print(f"Lỗi trong batch rerank: {e}")
            return documents
    
    def _compute_batch_scores(self, query: str, documents: List[Dict[str, Any]]) -> List[float]:
        """
        Tính scores cho một batch documents chỉ với text chunk
        
        Args:
            query: Câu hỏi
            documents: List documents
            
        Returns:
            List scores
        """
        try:
            # Chỉ lấy text chunk cho tất cả documents
            text_contents = [doc.get('text', '') for doc in documents]
            
            # Tạo pairs (query, text_content) cho toàn bộ batch
            queries = [query] * len(text_contents)
            
            # Tokenize batch
            inputs = self.tokenizer(
                queries,
                text_contents,
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
            print(f"Lỗi trong batch scoring: {e}")
            return [0.0] * len(documents)
    
    def compare_scores(self, documents: List[Dict[str, Any]]) -> None:
        """
        So sánh vector scores vs rerank scores để debug
        
        Args:
            documents: Danh sách documents đã rerank
        """
        print("\nSO SÁNH SCORES (Text-only Rerank):")
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
    
    def _print_rerank_details(self, documents: List[Dict[str, Any]]) -> None:
        """
        In thông tin chi tiết về quá trình reranking cho từng chunk (text-only)
        
        Args:
            documents: Danh sách documents đã được rerank
        """
        print("\nCHI TIẾT RERANKING CHO TỪNG CHUNK (TEXT-ONLY):")
        print("=" * 120)
        
        for i, doc in enumerate(documents[:5], 1):  # Hiển thị top 5 chunks
            metadata = doc.get('rerank_metadata', {})
            product_info = metadata.get('product_info', {})
            
            print(f"\nCHUNK #{i}:")
            print(f"Sản phẩm: {product_info.get('product_name', 'N/A')} (ID: {product_info.get('product_id', 'N/A')})")
            print(f"Thương hiệu: {product_info.get('brand', 'N/A')}")
            print(f"Danh mục: {product_info.get('category', 'N/A')}")
            print(f"Loại chunk: {product_info.get('chunk_type', 'N/A')}")
            print(f"Độ dài: {metadata.get('chunk_length', 0)} ký tự")
            print(f"Sử dụng metadata: {metadata.get('uses_metadata', 'N/A')}")
            
            print(f"ĐIỂM SỐ:")
            print(f"      • Vector Score: {metadata.get('vector_score', 0.0):.4f}")
            print(f"      • Rerank Score: {metadata.get('rerank_score', 0.0):.4f}")
            print(f"      • Cải thiện: {metadata.get('score_improvement', 0.0):+.4f}")
            
            print(f"THỨ HẠNG:")
            print(f"      • Thứ hạng ban đầu: #{metadata.get('original_rank', 'N/A')}")
            print(f"      • Thứ hạng cuối: #{metadata.get('final_rank', 'N/A')}")
            print(f"      • Thay đổi: {metadata.get('rank_change', 0):+d} vị trí")
            
            # Hiển thị một phần nội dung chunk
            text_preview = doc.get('text', '')[:150] + "..." if len(doc.get('text', '')) > 150 else doc.get('text', '')
            print(f"Nội dung: {text_preview}")
            
            if metadata.get('batch_processed'):
                print(f"Xử lý batch: Có (batch_size={metadata.get('batch_size', 'N/A')})")
            
            print("-" * 120)
        
        # Thống kê tổng quan
        if documents:
            avg_improvement = sum(doc.get('rerank_metadata', {}).get('score_improvement', 0) for doc in documents) / len(documents)
            positive_improvements = sum(1 for doc in documents if doc.get('rerank_metadata', {}).get('score_improvement', 0) > 0)
            
            print(f"\nTHỐNG KÊ TỔNG QUAN (TEXT-ONLY RERANK):")
            print(f"   • Tổng số chunks: {len(documents)}")
            print(f"   • Cải thiện trung bình: {avg_improvement:+.4f}")
            print(f"   • Chunks được cải thiện: {positive_improvements}/{len(documents)} ({positive_improvements/len(documents)*100:.1f}%)")
            print(f"   • Sử dụng metadata: Không")
            print("=" * 120)


class RerankService:
    """
    Service wrapper cho BGE Reranker - chỉ sử dụng text chunk
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
        Cải thiện kết quả tìm kiếm bằng reranking - chỉ sử dụng text chunk
        
        Args:
            query: Câu hỏi gốc
            search_results: Kết quả từ vector search
            top_k: Số lượng kết quả cuối cùng
            use_batch: Sử dụng batch rerank
            
        Returns:
            Kết quả đã được rerank và cải thiện (chỉ dựa trên text chunk)
        """
        if not search_results:
            return []
        
        print(f"Đang cải thiện {len(search_results)} kết quả tìm kiếm (text-only rerank)...")
        
        # Rerank chỉ với text chunk
        if use_batch and len(search_results) > 4:
            reranked_results = self.reranker.rerank_with_batch(
                query=query,
                documents=search_results,
                batch_size=32,
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