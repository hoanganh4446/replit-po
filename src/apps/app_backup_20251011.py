"""
Trang web offline quản lý hệ thống PO
Sử dụng Flask để tạo giao diện web tùy biến
"""

from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, flash
import os
import json
from datetime import datetime
import xlwings as xw
import random
from typing import Dict, List, Any, Optional
import threading
import time

app = Flask(__name__, 
           template_folder='../../web/templates',
           static_folder='../../web/static')
app.secret_key = 'po_system_secret_key_2024'

# Cấu hình global
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # Trỏ về thư mục gốc
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
TEMPLATES_DIR = os.path.join(BASE_DIR, "web", "templates")
STATIC_DIR = os.path.join(BASE_DIR, "web", "static")
PRODUCTS_DIR = os.path.join(BASE_DIR, "products")

# Tạo thư mục cần thiết
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

class ProductManager:
    """Quản lý sản phẩm và cấu hình"""
    
    def __init__(self):
        self.products = {}
        self.load_products()
    
    def load_products(self):
        """Tải tất cả sản phẩm từ cấu hình"""
        # Cấu hình sản phẩm dựa trên phân tích
        product_configs = {
            # === SẢN PHẨM GỐC ===
            'LA800': {
                'name': 'LA800',
                'template': 'products/LA800/LA800-PO#20164015-20250320.xlsx',
                'type': 'standard',
                'random_config': [
                    (7520, 8550, "div100"), (6320, 6750, "div100"), (2110, 2170, "div10"),
                    (8220, 9050, "div100"), (3080, 3200, False), (4120, 4790, "div10"),
                    (1860, 1940, False), (3690, 4400, "div10"), (5200, 5400, "div100"),
                    (4400, 4490, "div100")
                ],
                'random_columns': list("EFGHIJKLMN"),
                'merge_config': {
                    "product": "C4:D5",
                    "po": "H4:M5", 
                    "date": "T4:W5"
                },
                'serial_range': 'A11:A15'
            },
            'SV2000': {
                'name': 'SV2000',
                'template': 'products/SV2000/SV2000 Pre-Ship.xlsx',
                'type': 'special',
                'random_config': [
                    (2550, 2680, False), (2550, 2680, False), (1260, 1470, "div100")
                ],
                'random_columns': ['F', 'G', 'E'],
                'merge_config': {
                    "product": "D3",
                    "po": "F3:G3",
                    "date": "M3:N3"
                },
                'serial_range': 'B9:B13'
            },
            'LA555': {
                'name': 'LA555',
                'template': 'products/LA555/LA555 - PO#20141992 - 20241022.xlsx',
                'type': 'standard',
                'random_config': [
                    (7605, 8500, "div100"), (6405, 6900, "div100"), (18005, 19300, "div100"),
                    (9005, 9300, "div100"), (3130, 3200, False), (905, 1065, False),
                    (1720, 1905, False), (506, 550, False), (5105, 5200, "div100"),
                    (4605, 4700, "div100")
                ],
                'random_columns': list("EFGHIJKLMN"),
                'merge_config': {
                    "product": "C4:D5",
                    "po": "H4:M5",
                    "date": "T4:W5"
                },
                'serial_range': 'A11:A15'
            },
            'UV730': {
                'name': 'UV730',
                'template': 'products/UV730/UV730 - PO#20159177- 20250319.xlsx',
                'type': 'standard',
                'random_config': [
                    (8000, 9000, True), (7000, 8200, True), (18000, 21000, True),
                    (8300, 11500, True), (900, 1000, False), (3300, 3500, False),
                    (5100, 6200, True), (4000, 5100, True)
                ],
                'random_columns': list("EFGHIJKL"),
                'merge_config': {
                    "product": "C4:D5",
                    "po": "H4:K5",
                    "date": "R4:U5"
                },
                'serial_range': 'A11:A15'
            },
            'HX100': {
                'name': 'HX100',
                'template': 'products/HX100/hx100.xlsx',
                'type': 'merge_cells',
                'special_config': {
                    "random_ranges": [
                        (2130, 2240, "F:G", "div100"),
                        (7890, 8450, "H:I", False)
                    ],
                    "merge_config": {
                        "product": "C4:E5",
                        "po": "F4:I4",
                        "date": "Q4:T4"
                    }
                },
                'serial_range': 'A11:A15'
            },
            'HD400': {
                'name': 'HD400',
                'template': 'products/HD400/HD400.xlsx',
                'type': 'complex',
                'complex_config': [
                    (1592, 1620, False), (None, None, "/"), (None, None, "/"),
                    (None, None, "/"), (None, None, "/"), (None, None, "/"),
                    (3630, 3680, "div100"), (None, None, "/"), (None, None, "/"),
                    (None, None, "/"), (None, None, "OK"), (None, None, "/"),
                    (None, None, "/"), (None, None, "/"), (None, None, "/"),
                    (None, None, "/"), (None, None, "/"), (None, None, "/"),
                    (None, None, "/"), (None, None, "/"), (9335, 9650, "div100")
                ],
                'merge_config': {
                    "product": "B3",
                    "po": "G3",
                    "date": "S3"
                },
                'serial_range': 'A8:A12'
            },
            'LA700': {
                'name': 'LA700',
                'template': 'products/LA700/LA700 - PO#20166787 - 20250309.xlsx',
                'type': 'standard',
                'random_config': [
                    (7700, 8600, True), (6700, 7400, True), (18500, 19500, True),
                    (8000, 9800, True), (3200, 3500, False), (850, 1000, False),
                    (1750, 1950, False), (500, 600, False), (5200, 5600, True),
                    (4500, 5300, True)
                ],
                'random_columns': list("EFGHIJKLMN"),
                'merge_config': {
                    "product": "C4:D5",
                    "po": "H4:M5",
                    "date": "T4:W5"
                },
                'serial_range': 'A11:A15'
            },
            'VX100': {
                'name': 'VS100',
                'template': 'products/VX100/VS100 - PO#20132547 - 20240905.xlsx',
                'type': 'unique_row',
                'special_config': {
                    "random_ranges": [
                        (8000, 8380, "E", "div100"),
                        (13340, 14050, "F", "div100"),
                        (4070, 4215, "G", "div100")
                    ],
                    "merge_config": {
                        "product": "C4:D5",
                        "po": "F4:G5",
                        "date": "M4:P5"
                    }
                },
                'serial_range': 'A11:A15'
            },
            'LA480': {
                'name': 'LA480',
                'template': 'products/LA480/LA480WM.xlsx',
                'type': 'standard',
                'random_config': [
                    (7280, 7926, True), (6903, 7761, True), (18000, 19700, True),
                    (8700, 9783, True), (747, 910, False), (3320, 3690, False),
                    (5136, 5960, True), (4510, 4940, True)
                ],
                'random_columns': list("EFGHIJKL"),
                'merge_config': {
                    "product": "C4:D5",
                    "po": "H4:K5",
                    "date": "R4:U5"
                },
                'serial_range': 'A11:A15'
            },
            'HP152': {
                'name': 'HP153',
                'template': 'products/HP152/HP152 - PO#20165120 - 20250302.xlsx',
                'type': 'standard',
                'random_config': [
                    (7700, 8600, True), (6700, 7400, True), (18500, 19500, True),
                    (8000, 9800, True), (3200, 3500, False), (850, 1000, False),
                    (1750, 1950, False), (500, 600, False), (5200, 5600, True),
                    (4500, 5300, True)
                ],
                'random_columns': list("EFGHIJKLMN"),
                'merge_config': {
                    "product": "C4:D5",
                    "po": "H4:M5",
                    "date": "T4:W5"
                },
                'serial_range': 'A11:A15'
            },
            
            # === SẢN PHẨM MỚI ===
            'UV440': {
                'name': 'UV440',
                'template': 'products/UV440/UV440 - PO#20161635 - 20250309.xlsx',
                'type': 'standard',
                'random_config': [
                    (8400, 9500, "div100"), (6100, 7400, "div100"), (1980, 2100, "div10"),
                    (9000, 11000, "div100"), (4200, 4400, False), (5600, 5900, "div100"),
                    (4560, 5000, "div100")
                ],
                'random_columns': list("EFGHIJK"),
                'merge_config': {
                    "product": "C4:D5",
                    "po": "H4:J5",
                    "date": "Q4:T5"
                },
                'serial_range': 'A11:A15'
            },
            'VS100': {
                'name': 'VS100',
                'template': 'products/VS100/VS100 - PO#20132547 - 20240905.xlsx',
                'type': 'unique_row',
                'special_config': {
                    "random_ranges": [
                        (8000, 8450, "E", "div100"),
                        (14400, 15300, "F", "div100"),
                        (4210, 4590, "G", "div100")
                    ],
                    "merge_config": {
                        "product": "C4:D5",
                        "po": "F4:G5",
                        "date": "M4:P5"
                    }
                },
                'serial_range': 'A11:A15'
            },
            'AZ3002': {
                'name': 'AZ3002',
                'template': 'products/AZ3002/AZ3002 - PO#20158141 - 20250316.xlsx',
                'type': 'standard',
                'random_config': [
                    (8515, 9105, True), (8515, 9105, True), (28513, 31005, True),
                    (12503, 13845, True), (3200, 3400, False), (900, 1000, False),
                    (1815, 1950, False), (515, 605, False), (6325, 7105, True),
                    (5218, 6195, True)
                ],
                'random_columns': list("EFGHIJKLMN"),
                'merge_config': {
                    "product": "C4:D5",
                    "po": "H4:M5",
                    "date": "T4:W5"
                },
                'serial_range': 'A11:A15',
                'image_path': 'Picture1.png'
            },
            'IZ381H': {
                'name': 'IZ381H',
                'template': 'products/IZ381H/IZ381H - PO#20164777 - 20250304.xlsx',
                'type': 'unique_row',
                'special_config': {
                    "random_ranges": [
                        (8712, 8950, "D", "div100"),
                        (2315, 2750, "E", "div100"),
                        (1290, 1340, "F", False),
                        (2350, 2580, "G", False),
                        (3210, 3500, "H", "div100")
                    ],
                    "merge_config": {
                        "product": "B3:C3",
                        "po": "E3:F3",
                        "date": "I3:J3"
                    }
                },
                'serial_range': 'B9:B13'
            },
            'IX141': {
                'name': 'IX141',
                'template': 'products/IX141/IX141 - PO# 20158119 - 20250331.xlsx',
                'type': 'standard',
                'random_config': [
                    (3605, 4105, "div100"), (7205, 8105, "div100"), (2620, 2810, False),
                    (1400, 1520, False), (2210, 2810, "div100"), (3005, 3305, "div100")
                ],
                'random_columns': list("FGHIJK"),
                'merge_config': {
                    "product": "C4:E5",
                    "po": "F4:I5",
                    "date": "Q4:T5"
                },
                'serial_range': 'A11:A15'
            },
            'UA1450': {
                'name': 'UA1450',
                'template': 'products/UA1450/UA1450 - PO# 20162749 - 20250328.xlsx',
                'type': 'standard',
                'random_config': [
                    (830, 860, False), (1130, 1170, False), (1675, 1720, False),
                    (2025, 2060, False), (2370, 2410, False), (30, 49, "div100"),
                    (430, 550, "div100"), (780, 900, "div100"), (170, 195, "div10"),
                    (295, 330, "div10"), (500, 543, "div10")
                ],
                'random_columns': list("BCDEFGHIJKL"),
                'merge_config': {
                    "product": "C4",
                    "po": "I4",
                    "date": "M4"
                },
                'serial_range': 'A11:A15'
            },
            'HD700': {
                'name': 'HD700',
                'template': 'products/HD700/HD700.xlsx',
                'type': 'complex',
                'complex_config': [
                    (1592, 1620, False), (None, None, "/"), (None, None, "/"),
                    (None, None, "/"), (None, None, "/"), (None, None, "/"),
                    (3630, 3680, "div100"), (None, None, "/"), (None, None, "/"),
                    (None, None, "/"), (None, None, "OK"), (None, None, "/"),
                    (None, None, "/"), (None, None, "/"), (None, None, "/"),
                    (None, None, "/"), (None, None, "/"), (None, None, "/"),
                    (None, None, "/"), (None, None, "/"), (9335, 9650, "div100")
                ],
                'merge_config': {
                    "product": "B3",
                    "po": "G3",
                    "date": "S3"
                },
                'serial_range': 'A8:A12'
            },
            'WD161': {
                'name': 'WD161',
                'template': 'products/WD161/WD161 - PO#20167466 - 20250316.xlsx',
                'type': 'standard',
                'random_config': [
                    (2100, 2799, "div100"), (2100, 2300, "div100"),
                    (515, 600, False), (515, 600, False),
                    (2200, 2399, "div100"), None,
                    (2250, 2499, "div100"), (4623, 4800, "div100"),
                    (11000, 11900, "div100")
                ],
                'random_columns': list("EFGHIKLM"),
                'merge_config': {
                    "product": "C4:E5",
                    "po": "F4:H5",
                    "date": "R4:U5"
                },
                'serial_range': 'A11:A15'
            },
            'NV360': {
                'name': 'NV360',
                'template': 'products/NV360/NV360 - PO#20166970 - 20250319.xlsx',
                'type': 'standard',
                'random_config': [
                    (8225, 9546, True), (6225, 7546, True), (18525, 21546, True),
                    (9225, 10546, True), (4225, 4546, False), (5225, 6546, True),
                    (4225, 5346, True)
                ],
                'random_columns': list("EFGHIJK"),
                'merge_config': {
                    "product": "C4:D5",
                    "po": "H4:J5",
                    "date": "Q4:T5"
                },
                'serial_range': 'A11:A15'
            },
            'AW261': {
                'name': 'AW261',
                'template': 'products/AW261/AW261 - PO#20162744 - 20250222.xlsx',
                'type': 'standard',
                'random_config': [
                    (1215, 1406, "div100"), (1285, 1456, "div100"), (520, 590, False),
                    (520, 590, False), (2180, 2895, "div100"), None,
                    (2215, 2806, "div100"), (4415, 5406, "div100"), (9252, 11856, "div100")
                ],
                'random_columns': list("EFGHIKLM"),
                'merge_config': {
                    "product": "C4:E5",
                    "po": "F4:H5",
                    "date": "R4:U5"
                },
                'serial_range': 'A11:A15'
            },
            'UH205': {
                'name': 'UH205',
                'template': 'products/UH205/UH205 - PO#20165104 - 20250321.xlsx',
                'type': 'standard',
                'random_config': [
                    (360, 380, False), (560, 585, False), (820, 840, False),
                    (1060, 1110, False), (1280, 1300, False), (1470, 1490, False),
                    (1490, 1550, "div100"), (2320, 2390, "div100"), (980, 1072, False),
                    (450, 470, "div100")
                ],
                'random_columns': list("BCDEFGHIJK"),
                'merge_config': {
                    "product": "B4:B5",
                    "po": "E4:F5",
                    "date": "K4:L5"
                },
                'serial_range': 'A11:A15'
            },
            'FA225': {
                'name': 'FA225',
                'template': 'products/FA225/FA225 - PO#20165135 - 202500327.xlsx',
                'type': 'standard',
                'random_config': [
                    (360, 380, False), (560, 585, False), (820, 840, False),
                    (1060, 1110, False), (1280, 1300, False), (1470, 1490, False),
                    (1490, 1550, "div100"), (2320, 2390, "div100"), (980, 1072, False),
                    (450, 470, "div100")
                ],
                'random_columns': list("BCDEFGHIJK"),
                'merge_config': {
                    "product": "C4:D5",
                    "po": "E4:F5",
                    "date": "K4:L5"
                },
                'serial_range': 'A11:A15'
            },
            
            # === SẢN PHẨM HD SERIES ===
            'HD300': {
                'name': 'HD300',
                'template': 'products/HD300/HD400.xlsx',
                'type': 'complex',
                'complex_config': [
                    (1711, 1803, False), (None, None, "/"), (None, None, "/"),
                    (None, None, "/"), (None, None, "/"), (None, None, "/"),
                    (3580, 3718, "div100"), (None, None, "/"), (None, None, "/"),
                    (None, None, "/"), (None, None, "OK"), (None, None, "/"),
                    (None, None, "/"), (None, None, "/"), (None, None, "/"),
                    (None, None, "/"), (None, None, "/"), (None, None, "/"),
                    (None, None, "/"), (None, None, "/"), (9970, 10420, "div100")
                ],
                'merge_config': {
                    "product": "B3",
                    "po": "G3",
                    "date": "S3"
                },
                'serial_range': 'A8:A12'
            },
            'HD500': {
                'name': 'HD500',
                'template': 'products/HD500/HD400.xlsx',
                'type': 'complex',
                'complex_config': [
                    (1730, 1803, False), (None, None, "/"), (None, None, "/"),
                    (None, None, "/"), (None, None, "/"), (None, None, "/"),
                    (3805, 3830, "div100"), (None, None, "/"), (None, None, "/"),
                    (None, None, "/"), (None, None, "OK"), (None, None, "/"),
                    (None, None, "/"), (None, None, "/"), (None, None, "/"),
                    (None, None, "/"), (None, None, "/"), (None, None, "/"),
                    (None, None, "/"), (None, None, "/"), (9935, 10050, "div100")
                ],
                'merge_config': {
                    "product": "B3",
                    "po": "G3",
                    "date": "S3"
                },
                'serial_range': 'A8:A12'
            },
            'HD600': {
                'name': 'HD600',
                'template': 'products/HD600/HD600.xlsx',
                'type': 'complex',
                'complex_config': [
                    (1522, 1633, False), (None, None, "/"), (None, None, "/"),
                    (None, None, "/"), (None, None, "/"), (None, None, "/"),
                    (3290, 3370, "div100"), (None, None, "/"), (None, None, "/"),
                    (None, None, "/"), (None, None, "OK"), (None, None, "/"),
                    (None, None, "/"), (None, None, "/"), (None, None, "/"),
                    (None, None, "/"), (None, None, "/"), (None, None, "/"),
                    (None, None, "/"), (None, None, "/"), (10150, 10500, "div100")
                ],
                'merge_config': {
                    "product": "B3",
                    "po": "G3",
                    "date": "S3"
                },
                'serial_range': 'A8:A12'
            },
            'HD700': {
                'name': 'HD700',
                'template': 'products/HD700/HD700.xlsx',
                'type': 'complex',
                'complex_config': [
                    (1592, 1620, False), (None, None, "/"), (None, None, "/"),
                    (None, None, "/"), (None, None, "/"), (None, None, "/"),
                    (None, None, "/"), (4200, 4420, "div100"), (None, None, "/"),
                    (None, None, "/"), (None, None, "OK"), (None, None, "/"),
                    (None, None, "/"), (None, None, "/"), (None, None, "/"),
                    (None, None, "/"), (None, None, "/"), (None, None, "/"),
                    (None, None, "/"), (None, None, "/"), (9722, 10480, "div100")
                ],
                'merge_config': {
                    "product": "B3",
                    "po": "G3",
                    "date": "S3"
                },
                'serial_range': 'A8:A12'
            },
            'HP152': {
                'name': 'HP152',
                'template': 'products/HP152/HP152 - PO#20165120 - 20250302.xlsx',
                'type': 'standard',
                'random_config': [
                    (890, 940, False), (1120, 1180, False), (1665, 1735, False),
                    (2010, 2080, False), (2415, 2485, False), (30, 47, "div100"),
                    (395, 523, "div100"), (540, 735, "div100"), (1020, 1286, "div100"),
                    (1365, 1658, "div100"), (2388, 2604, "div100")
                ],
                'random_columns': list("BCDEFGHIJKL"),
                'merge_config': {
                    "product": "C4:D5",
                    "po": "I4:L5",
                    "date": "M4:N5"
                },
                'serial_range': 'A11:A15'
            },
            'HP301': {
                'name': 'HP301',
                'template': 'products/HP301/HP301 - PO#20159133 - 20250304.xlsx',
                'type': 'standard',
                'random_config': [
                    (825, 855, False), (1125, 1150, False), (1670, 1720, False),
                    (2030, 2060, False), (2375, 2415, False), (30, 48, "div100"),
                    (420, 589, "div100"), (790, 910, "div100"), (178, 205, "div10"),
                    (299, 328, "div10"), (502, 543, "div10")
                ],
                'random_columns': list("BCDEFGHIJKL"),
                'merge_config': {
                    "product": "C4:D5",
                    "po": "I4:L5",
                    "date": "M4:N5"
                },
                'serial_range': 'A11:A15'
            },
        }
        
        self.products = product_configs
    
    def get_product(self, product_id: str) -> Optional[Dict]:
        """Lấy thông tin sản phẩm"""
        return self.products.get(product_id)
    
    def list_products(self) -> List[str]:
        """Liệt kê tất cả sản phẩm"""
        return list(self.products.keys())
    
    def validate_template(self, product_id: str) -> bool:
        """Kiểm tra template file có tồn tại không"""
        product = self.get_product(product_id)
        if not product:
            return False
        
        template_path = os.path.join(BASE_DIR, product['template'])
        return os.path.exists(template_path)

class ExcelProcessor:
    """Xử lý Excel cho web"""
    
    def __init__(self):
        random.seed(datetime.now().timestamp())
    
    def apply_center(self, ws, cell_range):
        """Căn giữa văn bản"""
        try:
            rng = ws.range(cell_range)
            rng.api.HorizontalAlignment = -4108
            rng.api.VerticalAlignment = -4108
        except:
            pass
    
    def generate_unique_randoms(self, a: int, b: int, count: int) -> List[int]:
        """Tạo số ngẫu nhiên duy nhất"""
        result = set()
        while len(result) < count:
            result.add(random.randint(a, b))
        return list(result)
    
    def process_standard_product(self, ws, config: Dict, data: Dict):
        """Xử lý sản phẩm chuẩn"""
        # Serial numbers
        serial_range = config.get('serial_range', 'A11:A15')
        start_row = int(serial_range.split(':')[0][1:])
        
        for i, sn in enumerate(data['serial_numbers']):
            cell = f"{serial_range[0]}{start_row + i}"
            ws.range(cell).value = sn
            self.apply_center(ws, cell)
        
        # Random data
        if 'random_config' in config and 'random_columns' in config:
            for col_idx, config_item in enumerate(config['random_config']):
                if config_item is None:
                    # Skip None values
                    continue
                a, b, mode = config_item
                if mode == "div100":
                    values = self.generate_unique_randoms(a, b, 5)
                    for row_idx in range(5):
                        val = round(values[row_idx] / 100, 2)
                        cell = f"{config['random_columns'][col_idx]}{start_row + row_idx}"
                        ws.range(cell).value = val
                        self.apply_center(ws, cell)
                elif mode == "div10":
                    values = self.generate_unique_randoms(a, b, 5)
                    for row_idx in range(5):
                        val = round(values[row_idx] / 10, 1)
                        cell = f"{config['random_columns'][col_idx]}{start_row + row_idx}"
                        ws.range(cell).value = val
                        self.apply_center(ws, cell)
                elif mode is True:
                    values = self.generate_unique_randoms(a, b, 5)
                    for row_idx in range(5):
                        val = round(values[row_idx] / 100, 2)
                        cell = f"{config['random_columns'][col_idx]}{start_row + row_idx}"
                        ws.range(cell).value = val
                        self.apply_center(ws, cell)
                else:
                    values = self.generate_unique_randoms(a, b, 5)
                    for row_idx in range(5):
                        val = values[row_idx]
                        cell = f"{config['random_columns'][col_idx]}{start_row + row_idx}"
                        ws.range(cell).value = val
                        self.apply_center(ws, cell)
        
        # Product info
        merge_config = config.get('merge_config', {})
        
        if 'product' in merge_config:
            product_cell = merge_config['product'].split(':')[0]
            try:
                ws.range(merge_config['product']).unmerge()
            except:
                pass
            ws.range(product_cell).value = data['product_name']
            ws.range(merge_config['product']).merge()
            self.apply_center(ws, merge_config['product'])
        
        if 'po' in merge_config:
            po_cell = merge_config['po'].split(':')[0]
            try:
                ws.range(merge_config['po']).unmerge()
            except:
                pass
            ws.range(po_cell).value = data['po_number']
            ws.range(merge_config['po']).merge()
            self.apply_center(ws, merge_config['po'])
        
        if 'date' in merge_config:
            date_cell = merge_config['date'].split(':')[0]
            try:
                ws.range(merge_config['date']).unmerge()
            except:
                pass
            formatted_date = datetime.strptime(data['date_code'], "%Y%m%d").strftime("%Y.%m.%d")
            ws.range(date_cell).value = formatted_date
            ws.range(merge_config['date']).merge()
            self.apply_center(ws, merge_config['date'])
    
    def process_special_product(self, ws, config: Dict, data: Dict):
        """Xử lý sản phẩm đặc biệt"""
        if config['type'] == 'merge_cells':
            self.process_hx100(ws, config, data)
        elif config['type'] == 'complex':
            self.process_hd400(ws, config, data)
        elif config['type'] == 'unique_row':
            if 'IZ381H' in config.get('name', ''):
                self.process_iz381h(ws, config, data)
            else:
                self.process_vx100(ws, config, data)
        else:
            self.process_standard_product(ws, config, data)
    
    def process_hx100(self, ws, config: Dict, data: Dict):
        """Xử lý HX100"""
        # Serial numbers
        for i, sn in enumerate(data['serial_numbers']):
            ws.range(f"A{11+i}").value = sn
            self.apply_center(ws, f"A{11+i}")
        
        # Random data với merge cells
        special_config = config.get('special_config', {})
        if 'random_ranges' in special_config:
            for row in range(11, 16):
                for min_val, max_val, cell_range, mode in special_config['random_ranges']:
                    val = random.randint(min_val, max_val)
                    if mode == "div100":
                        val = round(val / 100, 2)
                    
                    start_cell = cell_range.split(":")[0]
                    ws.range(f"{start_cell}{row}").value = val
                    self.apply_center(ws, f"{cell_range}{row}")
        
        # Product info
        merge_config = special_config.get('merge_config', {})
        
        # Product name
        ws.range("C4").value = data['product_name']
        try:
            ws.range(merge_config.get('product', 'C4:E5')).unmerge()
        except:
            pass
        ws.range(merge_config.get('product', 'C4:E5')).merge()
        self.apply_center(ws, merge_config.get('product', 'C4:E5'))
        
        # PO number
        ws.range("F4").value = data['po_number']
        try:
            ws.range(merge_config.get('po', 'F4:I4')).unmerge()
        except:
            pass
        ws.range(merge_config.get('po', 'F4:I4')).merge()
        self.apply_center(ws, merge_config.get('po', 'F4:I4'))
        
        # Date
        formatted_date = f"{data['date_code'][:4]}.{data['date_code'][4:6]}.{data['date_code'][6:]}"
        ws.range("Q4").value = formatted_date
        try:
            ws.range(merge_config.get('date', 'Q4:T4')).unmerge()
        except:
            pass
        ws.range(merge_config.get('date', 'Q4:T4')).merge()
        self.apply_center(ws, merge_config.get('date', 'Q4:T4'))
    
    def process_hd400(self, ws, config: Dict, data: Dict):
        """Xử lý HD400"""
        # Serial numbers
        for i, serial in enumerate(data['serial_numbers']):
            cell = f"A{8 + i}"
            ws.range(cell).value = serial
            self.apply_center(ws, cell)
        
        # Complex configuration
        complex_config = config.get('complex_config', [])
        used_rows = set()
        
        while len(used_rows) < 5:
            current_row_values = []
            used_numbers_in_current_row = set()
            
            for col_idx, (min_val, max_val, mode_or_fixed_value) in enumerate(complex_config):
                cell_val = None
                if min_val is None and max_val is None:
                    cell_val = mode_or_fixed_value
                else:
                    while True:
                        generated_int = random.randint(min_val, max_val)
                        if generated_int not in used_numbers_in_current_row:
                            used_numbers_in_current_row.add(generated_int)
                            cell_val = generated_int
                            break
                    
                    if mode_or_fixed_value == "div100":
                        cell_val = round(cell_val / 100.0, 2)
                
                current_row_values.append(cell_val)
            
            row_tuple = tuple(current_row_values)
            if row_tuple not in used_rows:
                used_rows.add(row_tuple)
        
        # Write data
        for i, row_data in enumerate(used_rows):
            for j, val_to_write in enumerate(row_data):
                cell_obj = ws.range((8 + i, 2 + j))
                cell_obj.value = val_to_write
                self.apply_center(ws, cell_obj)
        
        # Product info
        merge_config = config.get('merge_config', {})
        
        # Product name
        ws.range("B3").value = data['product_name']
        self.apply_center(ws, "B3")
        
        # PO number
        if ws.range("G3").merge_cells:
            ws.range("G3").unmerge()
        ws.range("G3").value = data['po_number']
        # Merge lại nếu có merge_config
        if 'po' in merge_config:
            try:
                ws.range(merge_config['po']).merge()
                self.apply_center(ws, merge_config['po'])
            except:
                self.apply_center(ws, "G3")
        else:
            self.apply_center(ws, "G3")
        
        # Date
        if ws.range("S3").merge_cells:
            ws.range("S3").unmerge()
        formatted_date = datetime.strptime(data['date_code'], "%Y%m%d").strftime("%Y.%m.%d")
        ws.range("S3").value = formatted_date
        # Merge lại nếu có merge_config
        if 'date' in merge_config:
            try:
                ws.range(merge_config['date']).merge()
                self.apply_center(ws, merge_config['date'])
            except:
                self.apply_center(ws, "S3")
        else:
            self.apply_center(ws, "S3")
    
    def process_vx100(self, ws, config: Dict, data: Dict):
        """Xử lý VX100"""
        # Serial numbers
        for i, sn in enumerate(data['serial_numbers']):
            ws.range(f"A{11+i}").value = sn
        
        # Unique row logic
        def generate_unique_row_e_to_g():
            while True:
                row = [
                    round(random.randint(8000, 8380) / 100, 2),
                    round(random.randint(13340, 14050) / 100, 2),
                    round(random.randint(4070, 4215) / 100, 2),
                ]
                if len(set(row)) == len(row):
                    return row
        
        cols = ["E", "F", "G"]
        for row_idx in range(5):
            values = generate_unique_row_e_to_g()
            for col_idx, val in enumerate(values):
                ws.range(f"{cols[col_idx]}{11+row_idx}").value = val
        
        # Product info
        special_config = config.get('special_config', {})
        merge_config = special_config.get('merge_config', {})
        
        # Product name
        ws.range("C4").value = data['product_name']
        try:
            ws.range(merge_config.get('product', 'C4:D5')).unmerge()
        except:
            pass
        ws.range(merge_config.get('product', 'C4:D5')).merge()
        self.apply_center(ws, merge_config.get('product', 'C4:D5'))
        
        # PO number
        ws.range("F4").value = data['po_number']
        try:
            ws.range(merge_config.get('po', 'F4:G5')).unmerge()
        except:
            pass
        ws.range(merge_config.get('po', 'F4:G5')).merge()
        self.apply_center(ws, merge_config.get('po', 'F4:G5'))
        
        # Date
        formatted_date = datetime.strptime(data['date_code'], "%Y%m%d").strftime("%Y.%m.%d")
        ws.range("M4").value = formatted_date
        try:
            ws.range(merge_config.get('date', 'M4:P5')).unmerge()
        except:
            pass
        ws.range(merge_config.get('date', 'M4:P5')).merge()
        self.apply_center(ws, merge_config.get('date', 'M4:P5'))
        
        # Center alignment for data area
        ws.range("A11:G15").api.HorizontalAlignment = -4108
        ws.range("A11:G15").api.VerticalAlignment = -4108
    
    def process_iz381h(self, ws, config: Dict, data: Dict):
        """Xử lý đặc biệt cho IZ381H"""
        # Serial numbers vào B9:B13
        for i, sn in enumerate(data['serial_numbers']):
            ws.range(f"B{9+i}").value = sn
            self.apply_center(ws, f"B{9+i}")
        
        # Unique row logic cho D9:H13
        def generate_unique_row_d_to_h():
            while True:
                row = [
                    round(random.randint(8712, 8950) / 100, 2),
                    round(random.randint(2315, 2750) / 100, 2),
                    random.randint(1290, 1340),
                    random.randint(2350, 2580),
                    round(random.randint(3210, 3500) / 100, 2)
                ]
                if len(set(row)) == len(row):
                    return row
        
        cols = ["D", "E", "F", "G", "H"]
        for row_idx in range(5):
            values = generate_unique_row_d_to_h()
            for col_idx, val in enumerate(values):
                ws.range(f"{cols[col_idx]}{9+row_idx}").value = val
                self.apply_center(ws, f"{cols[col_idx]}{9+row_idx}")
        
        # Product info
        special_config = config.get('special_config', {})
        merge_config = special_config.get('merge_config', {})
        
        # Product name
        ws.range("B3").value = data['product_name']
        try:
            ws.range(merge_config.get('product', 'B3:C3')).unmerge()
        except:
            pass
        ws.range(merge_config.get('product', 'B3:C3')).merge()
        self.apply_center(ws, merge_config.get('product', 'B3:C3'))
        
        # PO number
        ws.range("E3").value = data['po_number']
        try:
            ws.range(merge_config.get('po', 'E3:F3')).unmerge()
        except:
            pass
        ws.range(merge_config.get('po', 'E3:F3')).merge()
        self.apply_center(ws, merge_config.get('po', 'E3:F3'))
        
        # Date
        formatted_date = f"{data['date_code'][:4]}.{data['date_code'][4:6]}.{data['date_code'][6:]}"
        ws.range("I3").value = formatted_date
        try:
            ws.range(merge_config.get('date', 'I3:J3')).unmerge()
        except:
            pass
        ws.range(merge_config.get('date', 'I3:J3')).merge()
        self.apply_center(ws, merge_config.get('date', 'I3:J3'))
    
    def create_excel_file(self, product_id: str, data: Dict, output_path: str) -> bool:
        """Tạo file Excel"""
        try:
            product_manager = ProductManager()
            config = product_manager.get_product(product_id)
            if not config:
                return False
            
            template_path = os.path.join(BASE_DIR, config['template'])
            if not os.path.exists(template_path):
                return False
            
            with xw.App(visible=False) as app:
                wb = app.books.open(template_path)
                ws = wb.sheets[0]
                
                if config['type'] in ['merge_cells', 'complex', 'unique_row']:
                    self.process_special_product(ws, config, data)
                else:
                    self.process_standard_product(ws, config, data)
                
                wb.save(output_path)
                wb.close()
            
            return True
            
        except Exception as e:
            print(f"Error creating Excel file: {e}")
            return False

# Khởi tạo managers
product_manager = ProductManager()
excel_processor = ExcelProcessor()

@app.route('/')
def index():
    """Trang chủ"""
    products = sorted(product_manager.list_products())  # Sort alphabetically
    return render_template('index.html', products=products)

@app.route('/product/<product_id>')
def product_page(product_id):
    """Trang sản phẩm cụ thể"""
    product = product_manager.get_product(product_id)
    if not product:
        flash('Sản phẩm không tồn tại!', 'error')
        return redirect(url_for('index'))
    
    return render_template('product.html', product_id=product_id, product=product)

@app.route('/api/products')
def api_products():
    """API lấy danh sách sản phẩm"""
    products = {}
    for product_id in product_manager.list_products():
        product = product_manager.get_product(product_id)
        products[product_id] = {
            'name': product['name'],
            'type': product['type'],
            'template_exists': product_manager.validate_template(product_id)
        }
    return jsonify(products)

@app.route('/api/generate', methods=['POST'])
def api_generate():
    """API tạo file Excel"""
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        product_data = data.get('data', {})
        
        if not product_id or not product_data:
            return jsonify({'success': False, 'message': 'Thiếu dữ liệu'})
        
        # Validate data
        required_fields = ['product_name', 'po_number', 'date_code', 'serial_numbers']
        for field in required_fields:
            if field not in product_data:
                return jsonify({'success': False, 'message': f'Thiếu trường: {field}'})
        
        if len(product_data['serial_numbers']) != 5:
            return jsonify({'success': False, 'message': 'Cần đúng 5 serial numbers'})
        
        # Tạo file
        today_str = datetime.today().strftime("%Y-%m-%d")
        file_name = f"{product_data['product_name']} - PO#{product_data['po_number']} - {product_data['date_code']}"
        output_dir = os.path.join(OUTPUT_DIR, today_str, file_name)
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{file_name}.xlsx")
        
        success = excel_processor.create_excel_file(product_id, product_data, output_path)
        
        if success:
            # URL encode filename để tránh lỗi với ký tự đặc biệt
            import urllib.parse
            encoded_filename = urllib.parse.quote(os.path.basename(output_path))
            return jsonify({
                'success': True, 
                'message': 'Tạo file thành công!',
                'file_path': output_path,
                'download_url': f'/download/{encoded_filename}'
            })
        else:
            return jsonify({'success': False, 'message': 'Tạo file thất bại!'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'})

@app.route('/download/<filename>')
def download_file(filename):
    """Download file"""
    try:
        # Decode filename từ URL
        import urllib.parse
        decoded_filename = urllib.parse.unquote(filename)
        
        # Tìm file trong thư mục output
        for root, dirs, files in os.walk(OUTPUT_DIR):
            if decoded_filename in files:
                file_path = os.path.join(root, decoded_filename)
                return send_file(file_path, as_attachment=True)
        
        flash('File không tồn tại!', 'error')
        return redirect(url_for('index'))
        
    except Exception as e:
        flash(f'Lỗi download: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/batch')
def batch_page():
    """Trang xử lý hàng loạt"""
    return render_template('batch.html')

@app.route('/api/batch', methods=['POST'])
def api_batch():
    """API xử lý hàng loạt"""
    try:
        data = request.get_json()
        batch_data = data.get('data', [])
        
        if not batch_data:
            return jsonify({'success': False, 'message': 'Không có dữ liệu để xử lý'})
        
        results = []
        success_count = 0
        
        for item in batch_data:
            product_id = item.get('product_id')
            product_data = item.get('data', {})
            
            if not product_id or not product_data:
                results.append({'success': False, 'message': 'Thiếu dữ liệu'})
                continue
            
            # Tạo file
            today_str = datetime.today().strftime("%Y-%m-%d")
            file_name = f"{product_data['product_name']} - PO#{product_data['po_number']} - {product_data['date_code']}"
            output_dir = os.path.join(OUTPUT_DIR, today_str, file_name)
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f"{file_name}.xlsx")
            
            success = excel_processor.create_excel_file(product_id, product_data, output_path)
            
            if success:
                # URL encode filename để tránh lỗi với ký tự đặc biệt
                import urllib.parse
                encoded_filename = urllib.parse.quote(os.path.basename(output_path))
                results.append({
                    'success': True,
                    'product': product_data['product_name'],
                    'file_path': output_path,
                    'download_url': f'/download/{encoded_filename}'
                })
                success_count += 1
            else:
                results.append({
                    'success': False,
                    'product': product_data['product_name'],
                    'message': 'Tạo file thất bại'
                })
        
        return jsonify({
            'success': True,
            'message': f'Xử lý hoàn thành: {success_count}/{len(batch_data)} thành công',
            'results': results
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'})

@app.route('/config')
def config_page():
    """Trang cấu hình"""
    return render_template('config.html')

if __name__ == '__main__':
    print("🏭 Hệ thống PO Web đang khởi động...")
    print("📱 Truy cập: http://localhost:5000")
    print("🔄 Nhấn Ctrl+C để dừng")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
