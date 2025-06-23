import pickle
import os


class Identity_Brand:
    def __init__(self):
        # Sử dụng đường dẫn tuyệt đối từ thư mục gốc project
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        brand_path = os.path.join(base_dir, "data", "brand.pkl")
        
        with open(brand_path, "rb") as f:
            self.brand = pickle.load(f)

class Identity_Category_Name:
    def __init__(self):
        # Sử dụng đường dẫn tuyệt đối từ thư mục gốc project
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        category_path = os.path.join(base_dir, "data", "category_name.pkl")
        
        with open(category_path, "rb") as f:
            self.category_name = pickle.load(f)

     
    