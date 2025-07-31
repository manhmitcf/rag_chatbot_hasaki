#!/usr/bin/env python3

"""
Main processor cho hệ thống embedding nâng cao với MarkdownTextSplitter
"""

import json
import time
import uuid
from typing import List, Dict, Any
from tqdm import tqdm
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
import os
from config import (
    QDRANT_HOST, QDRANT_PORT, QDRANT_COLLECTION_NAME,
    EMBEDDING_MODEL, EMBEDDING_DIMENSION,
    DEFAULT_CHUNK_SIZE, DEFAULT_OVERLAP,
    MARKDOWN_CHUNK_SIZE, MARKDOWN_OVERLAP,
    DEVICE, EMBEDDING_BATCH_SIZE, MAX_PRODUCTS_LIMIT
)
from data_loader import load_and_validate_data
from product_processor import process_products_with_advanced_chunking

class AdvancedEmbeddingPipeline:
    """
    Pipeline xử lý embedding nâng cao
    """
    
    def __init__(self, 
                 qdrant_host: str = QDRANT_HOST,
                 qdrant_port: int = QDRANT_PORT,
                 collection_name: str = QDRANT_COLLECTION_NAME,
                 embedding_model: str = EMBEDDING_MODEL):
        """
        Khởi tạo pipeline
        
        Args:
            qdrant_host: Host của Qdrant
            qdrant_port: Port của Qdrant
            collection_name: Tên collection
            embedding_model: Tên model embedding
        """
        self.qdrant_host = qdrant_host
        self.qdrant_port = qdrant_port
        self.collection_name = collection_name
        self.embedding_model = embedding_model
        self.model = None
        self.qdrant_client = None
    
    def load_model(self):
        """Tải model embedding với GPU support"""
        print(f"Đang tải model: {self.embedding_model}")
        print(f"Device: {DEVICE}")
        start_time = time.time()
        
        # Tải model
        self.model = SentenceTransformer(self.embedding_model, device=DEVICE)
        
        # Hiển thị thông tin GPU nếu có
        if DEVICE.startswith("cuda"):
            import torch
            gpu_memory = torch.cuda.get_device_properties(DEVICE).total_memory / 1024**3
            print(f"GPU Memory: {gpu_memory:.1f} GB")
            print(f"Embedding batch size: {EMBEDDING_BATCH_SIZE}")
        
        load_time = time.time() - start_time
        print(f"Model đã được tải trong {load_time:.2f} giây")
    
    def connect_qdrant(self):
        """Kết nối tới Qdrant"""
        try:
            print(f"Đang kết nối tới Qdrant: {self.qdrant_host}:{self.qdrant_port}")
            
            self.qdrant_client = QdrantClient(
                host=self.qdrant_host,
                port=self.qdrant_port,
                timeout=60.0
            )
            
            # Test connection
            collections = self.qdrant_client.get_collections()
            print(f"Kết nối thành công! Có {len(collections.collections)} collections")
            
        except Exception as e:
            print(f"Lỗi kết nối Qdrant: {str(e)}")
            raise e
    
    def setup_collection(self, recreate: bool = True):
        """
        Thiết lập collection trong Qdrant
        
        Args:
            recreate: Có tạo lại collection không
        """
        try:
            # Kiểm tra collection tồn tại
            if self.qdrant_client.collection_exists(self.collection_name):
                if recreate:
                    print(f"Collection '{self.collection_name}' đã tồn tại. Đang xóa...")
                    self.qdrant_client.delete_collection(self.collection_name)
                    print("Đã xóa collection cũ")
                else:
                    print(f"Collection '{self.collection_name}' đã tồn tại. Sử dụng collection hiện tại.")
                    return
            
            # Tạo collection mới
            print(f"Đang tạo collection mới: {self.collection_name}")
            self.qdrant_client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=EMBEDDING_DIMENSION,
                    distance=Distance.COSINE
                ),
                shard_number=1
            )
            print("Đã tạo collection thành công")
            
        except Exception as e:
            print(f"Lỗi khi thiết lập collection: {str(e)}")
            raise e
    
    def upload_embeddings(self, embeddings: List[Dict[str, Any]], batch_size: int = 100):
        """
        Upload embeddings lên Qdrant
        
        Args:
            embeddings: Danh sách embeddings
            batch_size: Kích thước batch
        """
        try:
            print(f"Đang upload {len(embeddings)} embeddings với batch size {batch_size}")
            
            for i in tqdm(range(0, len(embeddings), batch_size), desc="Uploading"):
                batch_docs = embeddings[i:i + batch_size]
                batch_points = []
                
                for doc in batch_docs:
                    try:
                        point = PointStruct(
                            id=str(uuid.uuid4()),
                            vector=doc["values"],
                            payload=doc["metadata"]
                        )
                        batch_points.append(point)
                    except Exception as e:
                        print(f"Lỗi tạo point: {str(e)}")
                        continue
                
                if batch_points:
                    self.qdrant_client.upsert(
                        collection_name=self.collection_name,
                        points=batch_points
                    )
            
            print("Upload hoàn thành!")
            
            # Kiểm tra số lượng vectors đã upload
            collection_info = self.qdrant_client.get_collection(self.collection_name)
            print(f"Số vectors trong collection: {collection_info.points_count}")
            
        except Exception as e:
            print(f"Lỗi khi upload embeddings: {str(e)}")
            raise e
    
    def run_full_pipeline(self,
                         data_source: str = "json",
                         data_path: str = "data/hasaki_db.products_info.json",
                         max_products: int = None,
                         chunk_size: int = DEFAULT_CHUNK_SIZE,
                         overlap: int = DEFAULT_OVERLAP,
                         markdown_chunk_size: int = MARKDOWN_CHUNK_SIZE,
                         markdown_overlap: int = MARKDOWN_OVERLAP,
                         include_markdown: bool = True,
                         save_backup: bool = True,
                         backup_path: str = "data/advanced_embeddings.json",
                         recreate_collection: bool = True,
                         upload_batch_size: int = 100):
        """
        Chạy toàn bộ pipeline
        
        Args:
            data_source: Nguồn dữ liệu ("json" hoặc "mongodb")
            data_path: Đường dẫn file dữ liệu
            max_products: Số lượng sản phẩm tối đa
            chunk_size: Kích thước chunk mặc định
            overlap: Độ chồng lấp mặc định
            markdown_chunk_size: Kích thước chunk markdown
            markdown_overlap: Độ chồng lấp markdown
            include_markdown: Có xử lý markdown không
            include_regular_description: Có xử lý description thường không
            include_reviews: Có xử lý reviews không
            include_comments: Có xử lý comments không
            save_backup: Có lưu backup không
            backup_path: Đường dẫn file backup
            recreate_collection: Có tạo lại collection không
            upload_batch_size: Kích thước batch upload
        """
        total_start_time = time.time()
        
        print("="*60)
        print("BẮT ĐẦU PIPELINE EMBEDDING NÂNG CAO")
        print("="*60)
        
        # 1. Tải model
        if not self.model:
            self.load_model()
        
        # 2. Tải và validate dữ liệu
        print("\n" + "-"*40)
        print("BƯỚC 1: TẢI VÀ VALIDATE DỮ LIỆU")
        print("-"*40)
        
        products = load_and_validate_data(
            source=data_source,
            file_path=data_path,
            limit=max_products
        )
        
        if not products:
            print("Không có dữ liệu để xử lý!")
            return
        
        # 3. Xử lý embeddings
        print("\n" + "-"*40)
        print("BƯỚC 2: TẠO EMBEDDINGS")
        print("-"*40)
        
        embedding_start_time = time.time()
        
        embeddings = process_products_with_advanced_chunking(
            products=products,
            model=self.model,
            chunk_size=chunk_size,
            overlap=overlap,
            markdown_chunk_size=markdown_chunk_size,
            markdown_overlap=markdown_overlap,
            max_products=max_products,
            include_markdown=include_markdown
        )
        
        embedding_time = time.time() - embedding_start_time
        print(f"\nTạo embeddings hoàn thành trong {embedding_time:.2f} giây")
        
        # 4. Lưu backup
        if save_backup and embeddings:
            print("\n" + "-"*40)
            print("BƯỚC 3: LƯU BACKUP")
            print("-"*40)
            
            try:
                with open(backup_path, 'w', encoding='utf-8') as f:
                    json.dump(embeddings, f, ensure_ascii=False, indent=2)
                print(f"Đã lưu backup vào: {backup_path}")
            except Exception as e:
                print(f"Lỗi khi lưu backup: {str(e)}")
        
        # 5. Kết nối Qdrant và upload
        print("\n" + "-"*40)
        print("BƯỚC 4: UPLOAD LÊN QDRANT")
        print("-"*40)
        
        if not self.qdrant_client:
            self.connect_qdrant()
        
        self.setup_collection(recreate=recreate_collection)
        
        if embeddings:
            upload_start_time = time.time()
            self.upload_embeddings(embeddings, batch_size=upload_batch_size)
            upload_time = time.time() - upload_start_time
            print(f"Upload hoàn thành trong {upload_time:.2f} giây")
        
        # 6. Tổng kết
        total_time = time.time() - total_start_time
        
        print("\n" + "="*60)
        print("TỔNG KẾT PIPELINE")
        print("="*60)
        print(f"Tổng thời gian: {total_time:.2f} giây")
        print(f"Số sản phẩm xử lý: {len(products)}")
        print(f"Số embeddings tạo: {len(embeddings) if embeddings else 0}")
        print(f"Trung bình embeddings/sản phẩm: {len(embeddings)/len(products):.1f}" if embeddings and products else "N/A")
        print(f"Collection: {self.collection_name}")
        print("="*60)

def main():
    """Hàm main để chạy pipeline"""
    
    print("🚀 HASAKI EMBEDDING PIPELINE")
    print("="*50)
    
    # Lựa chọn nguồn dữ liệu
    print("Chọn nguồn dữ liệu:")
    print("1. JSON file")
    print("2. MongoDB")
    
    choice = input("Nhập lựa chọn (1 hoặc 2): ").strip()
    
    if choice == "1":
        data_source = "json"
        data_path = input("Nhập đường dẫn file JSON (Enter để dùng mặc định): ").strip()
        if not data_path:
            data_path = "data/hasaki_db.products_info.json"
    elif choice == "2":
        data_source = "mongodb"
        data_path = None
        print("Sử dụng MongoDB với cấu hình từ .env file")
    else:
        print("Lựa chọn không hợp lệ, sử dụng JSON mặc định")
        data_source = "json"
        data_path = "data/hasaki_db.products_info.json"
    
    # Cấu hình pipeline
    pipeline = AdvancedEmbeddingPipeline()
    
    # Chạy pipeline
    pipeline.run_full_pipeline(
        data_source=data_source,
        data_path=data_path,
        max_products=int(os.getenv("MAX_PRODUCTS", MAX_PRODUCTS_LIMIT)) if os.getenv("MAX_PRODUCTS") else MAX_PRODUCTS_LIMIT, 
        chunk_size=500,
        overlap=100,
        markdown_chunk_size=800,
        markdown_overlap=150,
        include_markdown=True,
        save_backup=True,
        backup_path="data/advanced_embeddings_markdown.json",
        recreate_collection=True,
        upload_batch_size=50
    )

if __name__ == "__main__":
    main()