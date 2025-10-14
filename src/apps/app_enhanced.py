"""
Enhanced PO System with Advanced Features
Integrated with Database, Serial Generator, Advanced Search, Dashboard, and Bulk Operations
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

# Import new modules
from database import db_manager
from serial_generator import serial_generator
from advanced_search import advanced_search
from dashboard_analytics import dashboard_analytics
from bulk_import_export import bulk_import_export

app = Flask(__name__)
app.secret_key = 'po_system_secret_key_2024'

# Cấu hình global
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")

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
                'template': 'HD400/HD400.xlsx',
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
                'template': 'LA480/LA480WM.xlsx',
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
                'name': 'HP152',
                'template': 'products/HP152/HP152.xlsx',
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
            'HD600': {
                'name': 'HD600',
                'template': 'HD600/HD600.xlsx',
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
            'NV360': {
                'name': 'NV360',
                'template': 'NV360/NV360.xlsx',
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
            'AZ3002': {
                'name': 'AZ3002',
                'template': 'AZ3002/AZ3002.xlsx',
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
            'HD500': {
                'name': 'HD500',
                'template': 'HD500/HD500.xlsx',
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
            'IZ381H': {
                'name': 'IZ381H',
                'template': 'IZ381H/IZ381H.xlsx',
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
            'IX141': {
                'name': 'IX141',
                'template': 'IX141/IX141.xlsx',
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
            'WD161': {
                'name': 'WD161',
                'template': 'WD161/WD161.xlsx',
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
            'VS100': {
                'name': 'VS100',
                'template': 'VS100/VS100.xlsx',
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
            'UV440': {
                'name': 'UV440',
                'template': 'UV440/UV440.xlsx',
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
            'UH205': {
                'name': 'UH205',
                'template': 'UH205/UH205.xlsx',
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
            'UA1450': {
                'name': 'UA1450',
                'template': 'UA1450/UA1450.xlsx',
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
            'LA480': {
                'name': 'LA480',
                'template': 'LA480/LA480WM.xlsx',
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
            'HP301': {
                'name': 'HP301',
                'template': 'HP301/HP301.xlsx',
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
            'HD700': {
                'name': 'HD700',
                'template': 'HD700/HD700.xlsx',
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
            'HD400': {
                'name': 'HD400',
                'template': 'HD400/HD400.xlsx',
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
            'HD300': {
                'name': 'HD300',
                'template': 'HD300/HD300.xlsx',
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
            'FA225': {
                'name': 'FA225',
                'template': 'FA225/FA225.xlsx',
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
            'AW261': {
                'name': 'AW261',
                'template': 'AW261/AW261.xlsx',
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
            }
        }
        
        self.products = product_configs
    
    def get_product(self, product_id: str) -> Optional[Dict]:
        """Lấy thông tin sản phẩm"""
        return self.products.get(product_id)
    
    def get_all_products(self) -> Dict:
        """Lấy tất cả sản phẩm"""
        return self.products
    
    def get_product_list(self) -> List[Dict]:
        """Lấy danh sách sản phẩm dạng list"""
        return [
            {
                'id': product_id,
                'name': config['name'],
                'type': config['type'],
                'template': config['template']
            }
            for product_id, config in self.products.items()
        ]

# Initialize managers
product_manager = ProductManager()

# === ROUTES ===

@app.route('/')
def index():
    """Trang chủ"""
    return render_template('index.html', products=product_manager.get_product_list())

@app.route('/product/<product_id>')
def product_page(product_id):
    """Trang sản phẩm"""
    product = product_manager.get_product(product_id)
    if not product:
        flash('Sản phẩm không tồn tại!', 'error')
        return redirect(url_for('index'))
    
    # Get serial number suggestions
    suggested_serials = serial_generator.generate_serial_numbers(
        product_id, count=5, pattern='default'
    )
    
    return render_template('product.html', 
                         product=product, 
                         product_id=product_id,
                         suggested_serials=suggested_serials)

@app.route('/batch')
def batch_page():
    """Trang xử lý hàng loạt"""
    return render_template('batch.html', products=product_manager.get_product_list())

@app.route('/dashboard')
def dashboard():
    """Trang dashboard"""
    period_days = request.args.get('period', 30, type=int)
    dashboard_data = dashboard_analytics.get_dashboard_data(period_days)
    
    return render_template('dashboard.html', 
                         dashboard_data=dashboard_data,
                         period_days=period_days)

@app.route('/search')
def search_page():
    """Trang tìm kiếm nâng cao"""
    return render_template('search.html')

@app.route('/history')
def history_page():
    """Trang lịch sử"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    history = db_manager.get_po_history(
        limit=per_page,
        offset=(page - 1) * per_page
    )
    
    return render_template('history.html', 
                         history=history,
                         page=page,
                         per_page=per_page)

@app.route('/import-export')
def import_export_page():
    """Trang import/export"""
    return render_template('import_export.html')

# === API ROUTES ===

@app.route('/api/create-po', methods=['POST'])
def api_create_po():
    """API tạo file PO"""
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        po_number = data.get('po_number')
        date_code = data.get('date_code')
        serial_numbers = data.get('serial_numbers', [])
        
        if not product_id or not po_number:
            return jsonify({'error': 'Missing required fields'}), 400
        
        product = product_manager.get_product(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        # Generate file
        file_path = create_po_file(product, po_number, date_code, serial_numbers)
        
        # Save to database
        record_id = db_manager.add_po_record(
            product_id=product_id,
            product_name=product['name'],
            po_number=po_number,
            date_code=date_code,
            serial_numbers=serial_numbers,
            file_path=file_path,
            user_agent=request.headers.get('User-Agent'),
            ip_address=request.remote_addr
        )
        
        return jsonify({
            'success': True,
            'file_path': file_path,
            'record_id': record_id
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate-serials', methods=['POST'])
def api_generate_serials():
    """API tạo serial numbers"""
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        count = data.get('count', 5)
        pattern = data.get('pattern', 'default')
        custom_text = data.get('custom_text')
        
        if not product_id:
            return jsonify({'error': 'Product ID required'}), 400
        
        serials = serial_generator.generate_serial_numbers(
            product_id, count, pattern, custom_text
        )
        
        return jsonify({
            'success': True,
            'serials': serials
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/search', methods=['POST'])
def api_search():
    """API tìm kiếm nâng cao"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        search_type = data.get('search_type', 'all')
        filters = data.get('filters', {})
        limit = data.get('limit', 100)
        
        results = advanced_search.search(query, search_type, filters, limit)
        
        return jsonify(results)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard-data')
def api_dashboard_data():
    """API lấy dữ liệu dashboard"""
    try:
        period_days = request.args.get('period', 30, type=int)
        data = dashboard_analytics.get_dashboard_data(period_days)
        
        return jsonify(data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/export', methods=['POST'])
def api_export():
    """API export dữ liệu"""
    try:
        data = request.get_json()
        export_type = data.get('export_type')
        format_type = data.get('format', 'csv')
        filters = data.get('filters', {})
        
        file_path = bulk_import_export.export_data(
            export_type, format_type, filters
        )
        
        return jsonify({
            'success': True,
            'file_path': file_path
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/import', methods=['POST'])
def api_import():
    """API import dữ liệu"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        import_type = request.form.get('import_type')
        options = json.loads(request.form.get('options', '{}'))
        
        if not file.filename:
            return jsonify({'error': 'No file selected'}), 400
        
        # Save uploaded file
        file_path = os.path.join(OUTPUT_DIR, file.filename)
        file.save(file_path)
        
        # Import data
        results = bulk_import_export.import_data(file_path, import_type, options=options)
        
        # Clean up
        os.remove(file_path)
        
        return jsonify(results)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/statistics')
def api_statistics():
    """API lấy thống kê"""
    try:
        period_days = request.args.get('period', 30, type=int)
        stats = db_manager.get_statistics(period_days)
        
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/serial-stats')
def api_serial_stats():
    """API lấy thống kê serial numbers"""
    try:
        product_id = request.args.get('product_id')
        stats = serial_generator.get_serial_statistics(product_id)
        
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# === UTILITY FUNCTIONS ===

def create_po_file(product: Dict, po_number: str, date_code: str, serial_numbers: List[str]) -> str:
    """Tạo file PO"""
    try:
        # Get template path
        template_path = os.path.join(BASE_DIR, product['template'])
        
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template not found: {template_path}")
        
        # Create output filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_filename = f"{product['name']}_{po_number}_{timestamp}.xlsx"
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        
        # Open Excel file
        app = xw.App(visible=False)
        wb = app.books.open(template_path)
        ws = wb.sheets[0]
        
        # Apply merge configurations
        merge_config = product['merge_config']
        
        # Set product name
        if 'product' in merge_config:
            ws.range(merge_config['product']).value = product['name']
        
        # Set PO number
        if 'po' in merge_config:
            ws.range(merge_config['po']).value = po_number
        
        # Set date
        if 'date' in merge_config:
            ws.range(merge_config['date']).value = date_code
        
        # Set serial numbers
        serial_range = product.get('serial_range', 'A11:A15')
        for i, serial in enumerate(serial_numbers[:5]):  # Max 5 serials
            if serial:
                cell_range = f"{serial_range.split(':')[0][0]}{int(serial_range.split(':')[0][1:]) + i}"
                ws.range(cell_range).value = serial
        
        # Apply random configurations
        if product['type'] == 'standard' and 'random_config' in product:
            random_config = product['random_config']
            random_columns = product['random_columns']
            
            for i, (min_val, max_val, operation) in enumerate(random_config):
                if i < len(random_columns):
                    col = random_columns[i]
                    value = random.randint(min_val, max_val)
                    
                    if operation == "div100":
                        value = value / 100
                    elif operation == "div10":
                        value = value / 10
                    
                    ws.range(f"{col}11").value = value
        
        # Save file
        wb.save(output_path)
        wb.close()
        app.quit()
        
        return output_path
        
    except Exception as e:
        raise Exception(f"Error creating PO file: {str(e)}")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

