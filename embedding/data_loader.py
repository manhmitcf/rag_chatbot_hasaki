import json
from typing import List, Dict, Any
from pymongo import MongoClient
from config import MONGODB_URI, MONGODB_DATABASE, MONGO_COLLECTION

class DataLoader:
    """
    Lớp tải dữ liệu từ nhiều nguồn khác nhau
    """
    
    def __init__(self):
        self.mongodb_uri = MONGODB_URI
        self.mongodb_database = MONGODB_DATABASE
        self.mongo_collection = MONGO_COLLECTION
    
    def load_from_mongodb(self, limit: int = None) -> List[Dict[str, Any]]:
        """
        Tải dữ liệu từ MongoDB
        
        Args:
            limit: Giới hạn số lượng documents (None = tất cả)
        Returns:
            List[Dict]: Danh sách sản phẩm
        """
        try:
            print(f"Đang kết nối tới MongoDB: {self.mongodb_database}.{self.mongo_collection}")
            
            client = MongoClient(self.mongodb_uri)
            db = client[self.mongodb_database]
            collection = db[self.mongo_collection]
            
            # Tạo query với limit nếu có
            if limit:
                documents = list(collection.find().limit(limit))
                print(f"Đã tải {len(documents)} documents (giới hạn: {limit})")
            else:
                documents = list(collection.find())
                print(f"Đã tải {len(documents)} documents (tất cả)")
            
            client.close()
            return documents
            
        except Exception as e:
            print(f"Lỗi khi tải dữ liệu từ MongoDB: {str(e)}")
            return []
    
    def load_from_json_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Tải dữ liệu từ file JSON
        
        Args:
            file_path: Đường dẫn tới file JSON
        Returns:
            List[Dict]: Danh sách sản phẩm
        """
        try:
            print(f"Đang tải dữ liệu từ file: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                products = json.load(f)
            
            print(f"Đã tải {len(products)} sản phẩm từ file JSON")
            return products
            
        except FileNotFoundError:
            print(f"Không tìm thấy file: {file_path}")
            return []
        except json.JSONDecodeError as e:
            print(f"Lỗi decode JSON: {str(e)}")
            return []
        except Exception as e:
            print(f"Lỗi khi tải file JSON: {str(e)}")
            return []
    
    def save_to_json_file(self, data: List[Dict[str, Any]], file_path: str) -> bool:
        """
        Lưu dữ liệu vào file JSON
        
        Args:
            data: Dữ liệu cần lưu
            file_path: Đường dẫn file đích
        Returns:
            bool: True nếu thành công
        """
        try:
            print(f"Đang lưu {len(data)} items vào file: {file_path}")
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"Đã lưu thành công vào {file_path}")
            return True
            
        except Exception as e:
            print(f"Lỗi khi lưu file JSON: {str(e)}")
            return False
    
    def validate_product_data(self, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Kiểm tra và thống kê dữ liệu sản phẩm
        
        Args:
            products: Danh sách sản phẩm
        Returns:
            Dict: Thống kê validation
        """
        validation_stats = {
            "total_products": len(products),
            "valid_products": 0,
            "missing_fields": {},
            "empty_fields": {},
            "field_coverage": {}
        }
        
        required_fields = ['data_product', 'name', 'brand', 'category_name']
        optional_fields = [
            'descriptioninfo_markdown', 'descriptioninfo', 'specificationinfo',
            'ingredientinfo', 'guideinfo', 'reviews', 'comments', 'price',
            'average_rating', 'total_rating'
        ]
        
        all_fields = required_fields + optional_fields
        
        # Khởi tạo counters
        for field in all_fields:
            validation_stats["missing_fields"][field] = 0
            validation_stats["empty_fields"][field] = 0
            validation_stats["field_coverage"][field] = 0
        
        valid_count = 0
        
        for product in products:
            is_valid = True
            
            # Kiểm tra required fields
            for field in required_fields:
                if field not in product:
                    validation_stats["missing_fields"][field] += 1
                    is_valid = False
                elif not product[field] or str(product[field]).strip() == "":
                    validation_stats["empty_fields"][field] += 1
                    is_valid = False
                else:
                    validation_stats["field_coverage"][field] += 1
            
            # Kiểm tra optional fields
            for field in optional_fields:
                if field not in product:
                    validation_stats["missing_fields"][field] += 1
                elif not product[field] or (isinstance(product[field], str) and product[field].strip() == ""):
                    validation_stats["empty_fields"][field] += 1
                else:
                    validation_stats["field_coverage"][field] += 1
            
            if is_valid:
                valid_count += 1
        
        validation_stats["valid_products"] = valid_count
        
        # Tính phần trăm coverage
        for field in all_fields:
            coverage_count = validation_stats["field_coverage"][field]
            validation_stats["field_coverage"][field] = {
                "count": coverage_count,
                "percentage": (coverage_count / len(products)) * 100 if products else 0
            }
        
        return validation_stats
    
    def print_validation_report(self, validation_stats: Dict[str, Any]):
        """
        In báo cáo validation
        
        Args:
            validation_stats: Kết quả validation
        """
        print("\n" + "="*60)
        print("BÁO CÁO VALIDATION DỮ LIỆU")
        print("="*60)
        
        print(f"Tổng số sản phẩm: {validation_stats['total_products']}")
        print(f"Sản phẩm hợp lệ: {validation_stats['valid_products']}")
        print(f"Tỷ lệ hợp lệ: {(validation_stats['valid_products']/validation_stats['total_products']*100):.1f}%")
        
        print("\nCoverage các trường dữ liệu:")
        print("-" * 40)
        
        for field, coverage in validation_stats["field_coverage"].items():
            print(f"{field:25}: {coverage['count']:5} ({coverage['percentage']:5.1f}%)")
        
        print("\nTrường bị thiếu nhiều nhất:")
        print("-" * 40)
        missing_sorted = sorted(
            validation_stats["missing_fields"].items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        for field, count in missing_sorted[:5]:
            if count > 0:
                percentage = (count / validation_stats['total_products']) * 100
                print(f"{field:25}: {count:5} ({percentage:5.1f}%)")
        
        print("\nTrường rỗng nhiều nhất:")
        print("-" * 40)
        empty_sorted = sorted(
            validation_stats["empty_fields"].items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        for field, count in empty_sorted[:5]:
            if count > 0:
                percentage = (count / validation_stats['total_products']) * 100
                print(f"{field:25}: {count:5} ({percentage:5.1f}%)")
        
        print("="*60)

def load_and_validate_data(source: str = "json", 
                          file_path: str = "data/hasaki_db.products_info.json",
                          limit: int = None) -> List[Dict[str, Any]]:
    """
    Hàm tiện ích để tải và validate dữ liệu
    
    Args:
        source: Nguồn dữ liệu ("json" hoặc "mongodb")
        file_path: Đường dẫn file JSON (nếu source="json")
        limit: Giới hạn số lượng (chỉ áp dụng cho MongoDB)
    Returns:
        List[Dict]: Danh sách sản phẩm đã được validate
    """
    loader = DataLoader()
    
    # Tải dữ liệu
    if source.lower() == "mongodb":
        products = loader.load_from_mongodb(limit=limit)
    else:
        products = loader.load_from_json_file(file_path)
    
    if not products:
        print("Không có dữ liệu để xử lý!")
        return []
    
    # Validate dữ liệu
    validation_stats = loader.validate_product_data(products)
    loader.print_validation_report(validation_stats)
    
    return products