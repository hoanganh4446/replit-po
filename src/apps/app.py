"""
Trang web offline quản lý hệ thống PO - Phiên bản nâng cấp
Sử dụng Flask để tạo giao diện web tùy biến với các tính năng mới:
- Dashboard analytics
- Bulk operations
- Advanced search
- Export/Import data
- User management
- Real-time monitoring
"""

from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, flash, session
import os
import json
from datetime import datetime, timedelta
import random
from typing import Dict, List, Any, Optional
import threading
import time
import sqlite3
import hashlib
import logging
from functools import wraps
import csv
import zipfile
import shutil
from werkzeug.utils import secure_filename
import openpyxl
from openpyxl.styles import PatternFill

# Cấu hình global - Calculate BASE_DIR first
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # Trỏ về thư mục gốc
# For Replit compatibility, use current working directory as base
if os.path.exists('web'):
    BASE_DIR = os.getcwd()

# Initialize Flask app with absolute paths
app = Flask(__name__, 
           template_folder=os.path.join(BASE_DIR, 'web', 'templates'),
           static_folder=os.path.join(BASE_DIR, 'web', 'static'))
app.secret_key = 'po_system_secret_key_2024'
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
TEMPLATES_DIR = os.path.join(BASE_DIR, "web", "templates")
STATIC_DIR = os.path.join(BASE_DIR, "web", "static")
PRODUCTS_DIR = os.path.join(BASE_DIR, "products")

# Tạo thư mục cần thiết
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(BASE_DIR, 'logs', 'app.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Cấu hình database
DB_PATH = os.path.join(BASE_DIR, 'config', 'database', 'po_system.db')

class DatabaseManager:
    """Quản lý database SQLite"""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.init_database()

    def init_database(self):
        """Khởi tạo database và các bảng"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Bảng users
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    email TEXT,
                    role TEXT DEFAULT 'user',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP
                )
            ''')

            # Bảng sessions
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    session_token TEXT UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')

            # Bảng operations
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS operations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    operation_type TEXT NOT NULL,
                    product_name TEXT,
                    po_number TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    error_message TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')

            # Bảng analytics
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL,
                    product_name TEXT,
                    operation_count INTEGER DEFAULT 0,
                    success_count INTEGER DEFAULT 0,
                    error_count INTEGER DEFAULT 0,
                    UNIQUE(date, product_name)
                )
            ''')

        # Bảng import_data để lưu dữ liệu từ Excel
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS import_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                po_number TEXT NOT NULL,
                product_name TEXT NOT NULL,
                row_number INTEGER,
                file_name TEXT,
                import_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completion_date TIMESTAMP,
                status TEXT DEFAULT 'pending',
                file_import_date TEXT,
                UNIQUE(po_number, product_name)
            )
        ''')

        # Kiểm tra và thêm các cột cần thiết nếu chưa có
        cursor.execute("PRAGMA table_info(import_data)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'file_import_date' not in columns:
            cursor.execute('ALTER TABLE import_data ADD COLUMN file_import_date TEXT')
            logger.info("Added file_import_date column to import_data table")

        if 'status' not in columns:
            cursor.execute('ALTER TABLE import_data ADD COLUMN status TEXT DEFAULT "pending"')
            logger.info("Added status column to import_data table")

        if 'completion_date' not in columns:
            cursor.execute('ALTER TABLE import_data ADD COLUMN completion_date TIMESTAMP')
            logger.info("Added completion_date column to import_data table")

        # Bảng po_prediction để lưu lịch sử tiên đoán PO
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS po_prediction (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_name TEXT NOT NULL,
                predicted_po TEXT NOT NULL,
                confidence_score REAL DEFAULT 1.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(product_name, predicted_po)
            )
        ''')

        conn.commit()

    def get_connection(self):
        """Lấy kết nối database"""
        return sqlite3.connect(self.db_path)

class UserManager:
    """Quản lý người dùng và xác thực"""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def hash_password(self, password: str) -> str:
        """Mã hóa mật khẩu"""
        return hashlib.sha256(password.encode()).hexdigest()

    def create_user(self, username: str, password: str, email: str = None, role: str = 'user') -> bool:
        """Tạo người dùng mới"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                password_hash = self.hash_password(password)
                cursor.execute('''
                    INSERT INTO users (username, password_hash, email, role)
                    VALUES (?, ?, ?, ?)
                ''', (username, password_hash, email, role))
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False

    def delete_user(self, user_id: int) -> bool:
        """Xóa người dùng"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Error deleting user: {e}")
            return False

    def update_user(self, user_id: int, data: Dict) -> bool:
        """Cập nhật thông tin người dùng"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                fields = []
                values = []
                
                if 'password' in data and data['password']:
                    fields.append("password_hash = ?")
                    values.append(self.hash_password(data['password']))
                
                if 'email' in data:
                    fields.append("email = ?")
                    values.append(data['email'])
                    
                if 'role' in data:
                    fields.append("role = ?")
                    values.append(data['role'])
                
                if not fields:
                    return True
                    
                values.append(user_id)
                query = f"UPDATE users SET {', '.join(fields)} WHERE id = ?"
                
                cursor.execute(query, values)
                conn.commit()
                return True
        except Exception as e:
            print(f"Error updating user: {e}")
            return False

    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """Xác thực người dùng"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            password_hash = self.hash_password(password)
            cursor.execute('''
                SELECT id, username, email, role FROM users
                WHERE username = ? AND password_hash = ?
            ''', (username, password_hash))
            result = cursor.fetchone()

            if result:
                # Cập nhật last_login
                cursor.execute('''
                    UPDATE users SET last_login = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (result[0],))
                conn.commit()

                return {
                    'id': result[0],
                    'username': result[1],
                    'email': result[2],
                    'role': result[3]
                }
            return None

    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Lấy thông tin người dùng theo ID"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, username, email, role, created_at, last_login
                FROM users WHERE id = ?
            ''', (user_id,))
            result = cursor.fetchone()

            if result:
                return {
                    'id': result[0],
                    'username': result[1],
                    'email': result[2],
                    'role': result[3],
                    'created_at': result[4],
                    'last_login': result[5]
                }
            return None

class AnalyticsManager:
    """Quản lý phân tích và thống kê"""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def log_operation(self, user_id: int, operation_type: str, product_name: str = None, 
                     po_number: str = None, status: str = 'completed', error_message: str = None):
        """Ghi log hoạt động"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO operations (user_id, operation_type, product_name, po_number, status, error_message)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, operation_type, product_name, po_number, status, error_message))
            conn.commit()

    def get_dashboard_data(self, days: int = 30) -> Dict:
        """Lấy dữ liệu dashboard"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()

            # Tổng số hoạt động trong 30 ngày
            cursor.execute('''
                SELECT COUNT(*) FROM operations
                WHERE created_at >= datetime('now', '-{} days')
            '''.format(days))
            total_operations = cursor.fetchone()[0]

            # Hoạt động theo loại sản phẩm
            cursor.execute('''
                SELECT product_name, COUNT(*) as count
                FROM operations
                WHERE created_at >= datetime('now', '-{} days')
                AND product_name IS NOT NULL
                GROUP BY product_name
                ORDER BY count DESC
                LIMIT 10
            '''.format(days))
            product_stats = cursor.fetchall()

            # Hoạt động theo ngày
            cursor.execute('''
                SELECT DATE(created_at) as date, COUNT(*) as count
                FROM operations
                WHERE created_at >= datetime('now', '-{} days')
                GROUP BY DATE(created_at)
                ORDER BY date DESC
            '''.format(days))
            daily_stats = cursor.fetchall()

            # Tỷ lệ thành công
            cursor.execute('''
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as success
                FROM operations
                WHERE created_at >= datetime('now', '-{} days')
            '''.format(days))
            success_data = cursor.fetchone()
            success_rate = (success_data[1] / success_data[0] * 100) if success_data[0] > 0 else 0

            return {
                'total_operations': total_operations,
                'product_stats': [{'name': row[0], 'count': row[1]} for row in product_stats],
                'daily_stats': [{'date': row[0], 'count': row[1]} for row in daily_stats],
                'success_rate': round(success_rate, 2)
            }

class ExcelImportManager:
    """Quản lý import dữ liệu từ Excel file"""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def import_daily_line_data(self, file_path: str, max_rows_to_check: int = 50, skip_color_check: bool = False, original_filename: str = None) -> Dict:
        """Import dữ liệu từ file Daily Line Running and PSI"""
        import time
        import tempfile
        import shutil
        import gc

        # Khởi tạo biến để tránh lỗi UnboundLocalError
        imported_data = []
        skipped_rows = []
        errors = []
        rows_with_data = 0
        rows_with_yellow = 0
        start_row = 1
        last_data_row = 1
        max_row = 1

        try:
            # Kiểm tra file có tồn tại không
            if not os.path.exists(file_path):
                return {
                    'success': False,
                    'error': f'File không tồn tại: {file_path}'
                }

            # Kiểm tra file có đang được sử dụng không
            try:
                # Thử mở file với exclusive access
                with open(file_path, 'rb') as f:
                    pass  # Test mở file
            except PermissionError:
                # Thử approach khác - kiểm tra file có đang được sử dụng không
                try:
                    import psutil
                    for proc in psutil.process_iter(['pid', 'name', 'open_files']):
                        try:
                            if proc.info['open_files']:
                                for file_info in proc.info['open_files']:
                                    if file_info.path.lower() == file_path.lower():
                                        return {
                                            'success': False,
                                            'error': f'File đang được sử dụng bởi process {proc.info["name"]} (PID: {proc.info["pid"]}). Vui lòng đóng ứng dụng và thử lại.'
                                        }
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            continue
                except ImportError:
                    pass  # psutil không có sẵn

                return {
                    'success': False,
                    'error': f'File đang được sử dụng bởi ứng dụng khác. Vui lòng đóng Excel và thử lại.'
                }
            except Exception as e:
                return {
                    'success': False,
                    'error': f'Không thể truy cập file: {str(e)}'
                }

            # Tạo temporary file để tránh conflict
            temp_dir = tempfile.gettempdir()
            temp_filename = f"excel_import_{int(time.time())}.xlsx"
            temp_path = os.path.join(temp_dir, temp_filename)

            try:
                # Copy file sang temp directory
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        shutil.copy2(file_path, temp_path)
                        file_path = temp_path  # Sử dụng temp file
                        logger.info(f"Created temp file: {temp_path}")
                        break
                    except PermissionError:
                        if attempt < max_retries - 1:
                            logger.warning(f"Permission denied, retrying in 1 second... (attempt {attempt + 1})")
                            time.sleep(1)
                        else:
                            logger.warning(f"Could not create temp file after {max_retries} attempts")
                            # Tiếp tục với file gốc
                    except Exception as e:
                        logger.warning(f"Could not create temp file: {e}")
                        break

            except Exception as e:
                logger.warning(f"Temp file creation failed: {e}")
                # Tiếp tục với file gốc

            # Đóng file handle trước khi mở với openpyxl
            try:
                gc.collect()  # Force garbage collection
                time.sleep(0.2)  # Đợi lâu hơn
            except:
                pass

            # Sử dụng BytesIO để xử lý file trong memory hoàn toàn
            try:
                with open(file_path, 'rb') as f:
                    # Đọc file vào memory
                    file_data = f.read()

                # Sử dụng BytesIO để xử lý file trong memory
                from io import BytesIO
                file_stream = BytesIO(file_data)

                # Mở workbook từ memory stream
                workbook = openpyxl.load_workbook(file_stream, read_only=True, data_only=True)
                worksheet = workbook.active

                logger.info("Using memory-based file processing with BytesIO")

            except Exception as e:
                logger.warning(f"Could not use memory-based processing: {e}")
                # Fallback: sử dụng file trực tiếp
                workbook = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
                worksheet = workbook.active

            # Biến đã được khởi tạo ở đầu hàm

            # Màu vàng để kiểm tra (FFFF00)
            yellow_fill = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")

            # Tối ưu hóa: bắt đầu từ cuối file và đi ngược lên
            max_row = worksheet.max_row
            start_row = max(1, max_row - max_rows_to_check)  # Chỉ kiểm tra số hàng cuối được chỉ định

            # Tìm hàng cuối cùng có dữ liệu
            last_data_row = max_row
            for row_num in range(max_row, 0, -1):
                po_cell = worksheet.cell(row=row_num, column=2)  # Cột B
                if po_cell.value is not None and str(po_cell.value).strip():
                    last_data_row = row_num
                    break

            logger.info(f"Processing rows {start_row} to {last_data_row} (total: {max_row})")

            # Duyệt từ cuối lên đầu để tìm hàng có màu vàng
            consecutive_empty_rows = 0
            max_consecutive_empty = 50  # Dừng sau 50 hàng trống liên tiếp

            # Debug: Đếm số hàng có dữ liệu (biến đã được khởi tạo ở đầu hàm)

            for row_num in range(last_data_row, start_row - 1, -1):
                try:
                    # Lấy giá trị từ cột B và C
                    po_number_cell = worksheet.cell(row=row_num, column=2)  # Cột B
                    product_name_cell = worksheet.cell(row=row_num, column=3)  # Cột C

                    po_number = po_number_cell.value
                    product_name = product_name_cell.value

                    # Bỏ qua hàng trống
                    if not po_number or not product_name:
                        consecutive_empty_rows += 1
                        if consecutive_empty_rows >= max_consecutive_empty:
                            logger.info(f"Stopping at row {row_num} - too many empty rows")
                            break
                        continue

                    rows_with_data += 1
                    consecutive_empty_rows = 0  # Reset counter

                    # Kiểm tra màu nền của cell PO number (cột B)
                    cell_fill = po_number_cell.fill
                    is_yellow = False

                    # Tùy chọn bỏ qua color check để test
                    if skip_color_check:
                        is_yellow = True
                        logger.info(f"Row {row_num}: Skipping color check - importing all rows")
                    else:
                        # Chỉ kiểm tra color nếu không skip
                        if hasattr(cell_fill, 'start_color') and cell_fill.fill_type == 'solid':
                            try:
                                # Lấy RGB value với error handling
                                rgb = None
                                indexed = None
                                theme = None

                                try:
                                    rgb = cell_fill.start_color.rgb
                                except:
                                    pass

                                try:
                                    indexed = cell_fill.start_color.indexed
                                except:
                                    pass

                                try:
                                    theme = cell_fill.start_color.theme
                                except:
                                    pass

                                # Convert RGB to string nếu cần
                                rgb_str = str(rgb) if rgb else ""

                                # Các cách detect màu vàng - mở rộng thêm
                                is_yellow = (
                                    rgb_str == "FF0000FFFF" or  # ARGB yellow
                                    rgb_str == "FFFF00" or     # RGB yellow
                                    rgb_str == "00FFFF" or     # RGB yellow (alternative)
                                    rgb_str == "FFFF0000" or   # ARGB yellow (alternative)
                                    rgb_str == "FFFFFF00" or  # ARGB yellow (alternative)
                                    rgb_str == "00FFFF00" or  # ARGB yellow (alternative) - THÊM MỚI
                                    rgb_str == "0000FFFF" or  # ARGB yellow (alternative) - THÊM MỚI
                                    rgb_str == "FFFF00FF" or  # ARGB yellow (alternative) - THÊM MỚI
                                    indexed == 27 or           # Yellow index
                                    indexed == 64 or           # Yellow index (alternative)
                                    theme == 4 or              # Yellow theme
                                    rgb_str.upper() == "FF0000FFFF" or
                                    rgb_str.upper() == "FFFF00" or
                                    rgb_str.upper() == "00FFFF" or
                                    rgb_str.upper() == "FFFF0000" or
                                    rgb_str.upper() == "FFFFFF00" or
                                    rgb_str.upper() == "00FFFF00" or  # THÊM MỚI
                                    rgb_str.upper() == "0000FFFF" or  # THÊM MỚI
                                    rgb_str.upper() == "FFFF00FF"     # THÊM MỚI
                                )

                                # Debug log với error handling
                                logger.info(f"Row {row_num}: PO={po_number}, RGB={rgb_str}, Indexed={indexed}, Theme={theme}, FillType={cell_fill.fill_type}, Yellow={is_yellow}")

                            except Exception as e:
                                logger.warning(f"Row {row_num}: Error reading color - {str(e)}")
                                # KHÔNG dùng fallback nếu có lỗi đọc color
                                is_yellow = False

                        # KHÔNG dùng fallback cho color detection thông thường
                        # Chỉ import nếu thực sự detect được màu vàng

                    if is_yellow:
                        rows_with_yellow += 1
                        # Lưu vào database
                        with self.db_manager.get_connection() as conn:
                            cursor = conn.cursor()
                            try:
                                # Lấy ngày từ tên file (DDMMYYYY format) - đây là ngày của file
                                filename_for_date = original_filename if original_filename else os.path.basename(file_path)
                                file_import_date = self.extract_date_from_filename(filename_for_date)

                                # Ngày import thực tế (thời gian hiện tại)
                                from datetime import datetime
                                import_date = datetime.now()

                                # Sử dụng tên file gốc thay vì tên file tạm
                                display_filename = original_filename if original_filename else os.path.basename(file_path)

                                cursor.execute('''
                                    INSERT OR REPLACE INTO import_data 
                                    (po_number, product_name, row_number, file_name, file_import_date, import_date, status)
                                    VALUES (?, ?, ?, ?, ?, ?, ?)
                                ''', (str(po_number), str(product_name), row_num, display_filename, file_import_date, import_date, 'pending'))
                                conn.commit()

                                imported_data.append({
                                    'po_number': str(po_number),
                                    'product_name': str(product_name),
                                    'row_number': row_num,
                                    'file_import_date': file_import_date,
                                    'import_date': import_date.strftime("%Y-%m-%d %H:%M:%S")
                                })

                                logger.info(f"Row {row_num}: Successfully imported PO {po_number} - {product_name} (File date: {file_import_date}, Import date: {import_date.strftime('%Y-%m-%d %H:%M:%S')})")

                            except sqlite3.IntegrityError:
                                # Đã tồn tại, bỏ qua
                                logger.info(f"Row {row_num}: PO {po_number} already exists, skipping")
                                pass
                            except Exception as e:
                                logger.error(f"Row {row_num}: Database error - {str(e)}")
                                errors.append({
                                    'row_number': row_num,
                                    'error': f'Database error: {str(e)}'
                                })
                    else:
                        skipped_rows.append({
                            'row_number': row_num,
                            'po_number': str(po_number) if po_number else '',
                            'product_name': str(product_name) if product_name else '',
                            'reason': 'Không có màu vàng'
                        })

                except Exception as e:
                    errors.append({
                        'row_number': row_num,
                        'error': str(e)
                    })

            # Debug summary
            logger.info(f"Import Summary: {rows_with_data} rows with data, {rows_with_yellow} rows with yellow, {len(imported_data)} imported, {len(skipped_rows)} skipped, {len(errors)} errors")

            # Đóng workbook để giải phóng file handle
            try:
                workbook.close()
                logger.info("Workbook closed successfully")
            except Exception as e:
                logger.warning(f"Could not close workbook: {e}")

            return {
                'success': True,
                'imported_count': len(imported_data),
                'skipped_count': len(skipped_rows),
                'error_count': len(errors),
                'rows_processed': last_data_row - start_row + 1,
                'total_rows_in_file': max_row,
                'processing_efficiency': f"{len(imported_data)}/{last_data_row - start_row + 1} rows",
                'imported_data': imported_data[:10],  # Chỉ trả về 10 record đầu
                'skipped_rows': skipped_rows[:10],
                'errors': errors[:10],
                'debug_info': {
                    'rows_with_data': rows_with_data,
                    'rows_with_yellow': rows_with_yellow,
                    'skip_color_check': skip_color_check,
                    'start_row': start_row,
                    'last_data_row': last_data_row,
                    'max_row': max_row
                }
            }

        except Exception as e:
            logger.error(f"Import error: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__,
                'traceback': traceback.format_exc()
            }
        finally:
            # Đóng workbook nếu chưa đóng
            if 'workbook' in locals():
                try:
                    workbook.close()
                    logger.info("Workbook closed in finally block")
                except Exception as e:
                    logger.warning(f"Could not close workbook in finally: {e}")

            # Cleanup temp file gốc nếu có
            if 'temp_path' in locals() and os.path.exists(temp_path):
                try:
                    # Đợi lâu hơn để đảm bảo file không còn được sử dụng
                    time.sleep(1.0)  # Đợi 1 giây
                    os.remove(temp_path)
                    logger.info(f"Cleaned up temp file: {temp_path}")
                except Exception as e:
                    logger.warning(f"Could not remove temp file {temp_path} (will be cleaned up later): {e}")
                    # Không cần xử lý thêm, file sẽ được cleanup sau

    def extract_date_from_filename(self, filename: str) -> str:
        """Extract date from filename (DDMMYYYY format)"""
        import re
        from datetime import datetime

        # Tìm pattern MM.DD trong tên file (ví dụ: "10.11" = tháng 10, ngày 11)
        # Ví dụ: "Daily Line Runing and PSI 10.11.xlsx" -> "11102025" (11/10/2025)
        date_pattern = r'(\d{1,2})\.(\d{1,2})'
        match = re.search(date_pattern, filename)

        if match:
            month, day = match.groups()  # Đổi thứ tự: month.day -> day.month
            # Lấy năm hiện tại
            current_year = datetime.now().year
            # Format: DDMMYYYY (day.month.year)
            return f"{day.zfill(2)}{month.zfill(2)}{current_year}"

        # Fallback: tìm pattern khác DDMMYYYY
        date_pattern2 = r'(\d{2})(\d{2})(\d{4})'
        match2 = re.search(date_pattern2, filename)

        if match2:
            day, month, year = match2.groups()
            return f"{day}{month}{year}"

        # Fallback: sử dụng ngày hiện tại
        return datetime.now().strftime("%d%m%Y")

    def predict_po_number(self, product_name: str) -> Optional[str]:
        """Tiên đoán số PO dựa trên tên sản phẩm"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()

                # Tìm PO gần nhất cho sản phẩm này
                cursor.execute('''
                    SELECT po_number FROM import_data 
                    WHERE product_name = ? 
                    ORDER BY import_date DESC 
                    LIMIT 1
                ''', (product_name,))

                result = cursor.fetchone()
                if result:
                    return result[0]

                # Nếu không tìm thấy, tìm sản phẩm tương tự
                cursor.execute('''
                    SELECT po_number, product_name FROM import_data 
                    WHERE product_name LIKE ? 
                    ORDER BY import_date DESC 
                    LIMIT 1
                ''', (f'%{product_name}%',))

                result = cursor.fetchone()
                if result:
                    return result[0]

                return None

        except Exception as e:
            logger.error(f"Error predicting PO: {str(e)}")
            return None

    def get_product_by_po(self, po_number: str) -> Optional[str]:
        """Lấy tên sản phẩm dựa trên số PO"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT product_name FROM import_data 
                    WHERE po_number = ? 
                    ORDER BY import_date DESC 
                    LIMIT 1
                ''', (po_number,))

                result = cursor.fetchone()
                if result:
                    return result[0]

                return None

        except Exception as e:
            logger.error(f"Error getting product by PO: {str(e)}")
            return None

    def is_po_processed(self, po_number: str) -> bool:
        """Kiểm tra xem PO đã được xử lý chưa"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT COUNT(*) FROM operations 
                    WHERE po_number = ? AND status = 'completed'
                ''', (po_number,))

                result = cursor.fetchone()
                return result[0] > 0

        except Exception as e:
            logger.error(f"Error checking PO status: {str(e)}")
            return False

class BulkOperationsManager:
    """Quản lý các thao tác hàng loạt"""

    def __init__(self, product_manager, db_manager: DatabaseManager):
        self.product_manager = product_manager
        self.db_manager = db_manager
        self.excel_import_manager = ExcelImportManager(db_manager)

    def bulk_generate_pos(self, requests: List[Dict], user_id: int) -> Dict:
        """Tạo hàng loạt PO"""
        results = {
            'success': [],
            'failed': [],
            'total': len(requests)
        }

        for i, req in enumerate(requests):
            try:
                # Validate request
                if not req.get('product_name') or not req.get('po_number'):
                    results['failed'].append({
                        'index': i,
                        'error': 'Missing product_name or po_number'
                    })
                    continue

                # Generate PO
                result = self.product_manager.generate_po(
                    product_name=req['product_name'],
                    po_number=req['po_number'],
                    date_code=req.get('date_code', datetime.now().strftime('%Y%m%d')),
                    quantity=req.get('quantity', 1)
                )

                if result['success']:
                    results['success'].append({
                        'index': i,
                        'product_name': req['product_name'],
                        'po_number': req['po_number'],
                        'file_path': result['file_path']
                    })

                    # Log success
                    self.db_manager.log_operation(
                        user_id=user_id,
                        operation_type='bulk_generate',
                        product_name=req['product_name'],
                        po_number=req['po_number'],
                        status='completed'
                    )
                else:
                    results['failed'].append({
                        'index': i,
                        'error': result.get('error', 'Unknown error')
                    })

                    # Log failure
                    self.db_manager.log_operation(
                        user_id=user_id,
                        operation_type='bulk_generate',
                        product_name=req['product_name'],
                        po_number=req['po_number'],
                        status='failed',
                        error_message=result.get('error')
                    )

            except Exception as e:
                results['failed'].append({
                    'index': i,
                    'error': str(e)
                })

                # Log error
                self.db_manager.log_operation(
                    user_id=user_id,
                    operation_type='bulk_generate',
                    product_name=req.get('product_name'),
                    po_number=req.get('po_number'),
                    status='error',
                    error_message=str(e)
                )

        return results

    def export_data(self, filters: Dict = None) -> str:
        """Xuất dữ liệu ra file CSV"""
        with self.db_manager.get_connection() as conn:
            query = '''
                SELECT o.id, o.operation_type, o.product_name, o.po_number, 
                       o.status, o.created_at, o.completed_at, o.error_message,
                       u.username
                FROM operations o
                LEFT JOIN users u ON o.user_id = u.id
            '''

            params = []
            if filters:
                conditions = []
                if filters.get('start_date'):
                    conditions.append("o.created_at >= ?")
                    params.append(filters['start_date'])
                if filters.get('end_date'):
                    conditions.append("o.created_at <= ?")
                    params.append(filters['end_date'])
                if filters.get('product_name'):
                    conditions.append("o.product_name = ?")
                    params.append(filters['product_name'])
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)

            query += " ORDER BY o.created_at DESC"

            cursor = conn.cursor()
            cursor.execute(query, params)
            results = cursor.fetchall()

            # Tạo file CSV
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"po_export_{timestamp}.csv"
            filepath = os.path.join(OUTPUT_DIR, filename)

            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                # Header
                writer.writerow(['ID', 'Operation Type', 'Product Name', 'PO Number', 
                               'Status', 'Created At', 'Completed At', 'Error Message', 'Username'])
                # Data
                writer.writerows(results)

            return filepath

# Khởi tạo các manager
db_manager = DatabaseManager()
user_manager = UserManager(db_manager)
analytics_manager = AnalyticsManager(db_manager)

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
                'serial_range': 'A11:A15',
                'image_position': 'A1:C3'
            },
            'SV2000': {
                'name': 'SV2000',
                'template': 'products/SV2000/SV2000 Pre-Ship.xlsx',
                'type': 'special',
                'random_config': [
                    (2550, 2680, False), (3721, 4059, False), (1260, 1470, "div100")
                ],
                'random_columns': ['F', 'G', 'E'],
                'merge_config': {
                    "product": "D3",
                    "po": "F3:G3",
                    "date": "M3:N3"
                },
                'serial_range': 'B9:B13',
                'image_position': 'A1:D2'
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
                'serial_range': 'A11:A15',
                'image_position': 'A1:C3'
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
                'serial_range': 'A11:A15',
                'image_position': 'A1:C3'
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
                'serial_range': 'A11:A15',
                'image_position': 'A1:C3'
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
                'serial_range': 'A8:A12',
                'image_position': 'A1:B2'
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
                'serial_range': 'A11:A15',
                'image_position': 'A1:C3'
            },
            'VX100': {
                'name': 'VX100',
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
                'serial_range': 'A11:A15',
                'image_position': 'A1:C3'
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
                'serial_range': 'A11:A15',
                'image_position': 'A1:C3'
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
                'serial_range': 'A11:A15',
                'image_position': 'A1:C3'
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
                'serial_range': 'A11:A15',
                'image_position': 'A1:C3'
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
                'image_position': 'A1:C3'
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
                'serial_range': 'B9:B13',
                'image_position': 'A1:B2'
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
                'serial_range': 'A11:A15',
                'image_position': 'A1:C3'
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
                'serial_range': 'A11:A15',
                'image_position': 'A1:C3'
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
                'serial_range': 'A11:A15',
                'image_position': 'A1:C3'
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
                'serial_range': 'A11:A15',
                'image_position': 'A1:C3'
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
                'serial_range': 'A11:A15',
                'image_position': 'A1:C3'
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
                'serial_range': 'A11:A15',
                'image_position': 'A1:C3'
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
                'serial_range': 'A11:A15',
                'image_position': 'A1:C3'
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
                'serial_range': 'A8:A12',
                'image_position': 'A1:B2'
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
                'serial_range': 'A8:A12',
                'image_position': 'A1:B2'
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
                'serial_range': 'A8:A12',
                'image_position': 'A1:B2'
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
                'serial_range': 'A8:A12',
                'image_position': 'A1:B2'
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
                'serial_range': 'A11:A15',
                'image_position': 'A1:C3'
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
                'serial_range': 'A11:A15',
                'image_position': 'A1:C3'
            },
            'ZU660': {
                'name': 'ZU660',
                'template': 'products/ZU660/UV730 - PO#20159177- 20250319.xlsx',
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
                'serial_range': 'A11:A15',
                'image_position': 'A1:C3'
            },
            'TF200': {
                'name': 'TF200',
                'template': 'products/TF200/TF200.xlsx',
                'type': 'tf200',
                'required_fields': ['gross_weights', 'net_weights'],
                'requires_weights': True,
                'tf200_config': {
                    'rows': [11, 12, 13, 14, 15],
                    'serial_column': 'A',
                    'product_range': 'D4:H5',
                    'po_range': 'I4:J5',
                    'date_range': 'Q4:S5',
                    'gross_weight_column': 'N',
                    'net_weight_column': 'O',
                    'inactive_value': 'N/A',
                    'random_columns': [
                        {'column': 'B', 'min': 24, 'max': 30, 'mode': 'div100'},
                        {'column': 'C', 'min': 525, 'max': 550, 'mode': 'div100'},
                        {'column': 'D', 'min': 811, 'max': 849, 'mode': 'div100'},
                        {'column': 'E', 'min': 1019, 'max': 1055, 'mode': 'div100'},
                        {'column': 'F', 'min': 1231, 'max': 1279, 'mode': 'div100'},
                        {'column': 'G', 'min': 1515, 'max': 1585, 'mode': 'div100'},
                        {'column': 'H', 'min': 2015, 'max': 2120, 'mode': 'div100'},
                        {'column': 'I', 'min': 2610, 'max': 2760, 'mode': 'div100'},
                        {'column': 'J', 'min': 3900, 'max': 4050, 'mode': 'div100'},
                        {'column': 'K', 'min': 4520, 'max': 4699, 'mode': 'div100'},
                        {'column': 'L', 'min': 5520, 'max': 5590, 'mode': 'div100'},
                        {'column': 'M', 'min': 8550, 'max': 8700, 'mode': 'div100'},
                        {'column': 'R', 'min': 1829, 'max': 1832, 'mode': None, 'suffix': 'mm'},
                        {'column': 'S', 'min': 3, 'max': 9, 'mode': 'div10'}
                    ],
                    'single_row_columns': [
                        {'column': 'P', 'min': 1851, 'max': 1999, 'mode': None, 'suffix': None, 'inactive_value': 'N/A'},
                        {'column': 'Q', 'min': 24, 'max': 27, 'mode': 'div10', 'suffix': None, 'inactive_value': 'N/A'}
                    ]
                },
                'sample_data': {
                    'gross_weights': ["15.20kg", "15.35kg", "15.10kg", "15.42kg", "15.27kg"],
                    'net_weights': ["14.75kg", "14.90kg", "14.68kg", "14.98kg", "14.82kg"]
                }
            },
            'ZD201': {
                'name': 'ZD201',
                'template': 'products/ZD201/UV730 - PO#20159177- 20250319.xlsx',
                'type': 'standard',
                'random_config': [
                    (2550, 2680, False), (2550, 2680, False), (1260, 1470, "div100"),
                    (825, 855, False), (1125, 1150, False), (1670, 1720, False),
                    (2030, 2060, False), (2375, 2415, False), (30, 48, "div100"),
                    (420, 589, "div100"), (790, 910, "div100")
                ],
                'random_columns': list("BCDEFGHIJKL"),
                'merge_config': {
                    "product": "C4:D5",
                    "po": "H4:M5", 
                    "date": "T4:W5"
                },
                'serial_range': 'A11:A15',
                'image_position': 'A1:C3'
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

    def process_standard_product_openpyxl(self, ws, config: Dict, data: Dict):
        """Xử lý sản phẩm chuẩn với openpyxl"""
        try:
            # Apply merge_config data
            merge_config = config.get('merge_config', {})

            # Product name
            if 'product' in merge_config and 'product_name' in data:
                product_range = merge_config['product']
                ws[product_range.split(':')[0]] = data['product_name']
                # Apply center alignment
                from openpyxl.styles import Alignment
                ws[product_range.split(':')[0]].alignment = Alignment(horizontal='center', vertical='center')

            # PO number
            if 'po' in merge_config and 'po_number' in data:
                po_range = merge_config['po']
                ws[po_range.split(':')[0]] = data['po_number']
                from openpyxl.styles import Alignment
                ws[po_range.split(':')[0]].alignment = Alignment(horizontal='center', vertical='center')

            # Date
            if 'date' in merge_config and 'date_code' in data:
                date_range = merge_config['date']
                # Format date from YYYYMMDD to YYYY.MM.DD
                try:
                    from datetime import datetime
                    formatted_date = datetime.strptime(data['date_code'], "%Y%m%d").strftime("%Y.%m.%d")
                    ws[date_range.split(':')[0]] = formatted_date
                except ValueError:
                    ws[date_range.split(':')[0]] = data['date_code']
                from openpyxl.styles import Alignment
                ws[date_range.split(':')[0]].alignment = Alignment(horizontal='center', vertical='center')

            # Handle serial numbers if present
            if 'serial_numbers' in data and config.get('serial_range'):
                serial_range = config['serial_range']
                if isinstance(serial_range, str):
                    # Single range like 'A11:A15'
                    start_row = int(''.join(filter(str.isdigit, serial_range.split(':')[0])))
                    for i, serial in enumerate(data['serial_numbers']):
                        if i < 5:  # Limit to 5 serials
                            cell_ref = f"{serial_range[0]}{start_row + i}"
                            ws[cell_ref] = serial
                            from openpyxl.styles import Alignment
                            ws[cell_ref].alignment = Alignment(horizontal='center', vertical='center')
                elif isinstance(serial_range, list):
                    # List of ranges
                    for i, serial in enumerate(data['serial_numbers']):
                        if i < len(serial_range):
                            ws[serial_range[i]] = serial
                            from openpyxl.styles import Alignment
                            ws[serial_range[i]].alignment = Alignment(horizontal='center', vertical='center')

            # Handle random data generation
            if 'random_config' in config and 'random_columns' in config:
                self._generate_random_data_openpyxl(ws, config, data)

            return True
        except Exception as e:
            print(f"Error processing standard product with openpyxl: {e}")
            return False

    def _generate_random_data_openpyxl(self, ws, config: Dict, data: Dict):
        """Generate random data for openpyxl"""
        try:
            import random
            random.seed()

            random_config = config.get('random_config', [])
            random_columns = config.get('random_columns', [])

            # Determine number of rows to fill
            serial_count = len(data.get('serial_numbers', []))
            rows_to_fill = min(serial_count, 5)  # Max 5 rows

            for row in range(rows_to_fill):
                used_numbers = set()
                for col_idx, (min_val, max_val, mode) in enumerate(random_config):
                    if col_idx >= len(random_columns):
                        break

                    col = random_columns[col_idx]
                    # Determine row number based on serial range
                    serial_range = config.get('serial_range', 'A11:A15')
                    if isinstance(serial_range, str):
                        start_row = int(''.join(filter(str.isdigit, serial_range.split(':')[0])))
                        cell_row = start_row + row
                    else:
                        cell_row = 11 + row  # Default

                    cell_ref = f"{col}{cell_row}"

                    if min_val is None or max_val is None:
                        # Fixed value
                        ws[cell_ref] = mode
                    else:
                        # Random number
                        while True:
                            val = random.randint(min_val, max_val)
                            if val not in used_numbers:
                                used_numbers.add(val)
                                break

                        if mode == "div100" or mode is True:
                            val = round(val / 100.0, 2)
                        elif mode == "div10":
                            val = round(val / 10.0, 1)

                        ws[cell_ref] = val

                    # Apply center alignment
                    from openpyxl.styles import Alignment
                    ws[cell_ref].alignment = Alignment(horizontal='center', vertical='center')

        except Exception as e:
            print(f"Error generating random data with openpyxl: {e}")

    def process_special_product_openpyxl(self, ws, config: Dict, data: Dict):
        """Xử lý sản phẩm đặc biệt với openpyxl"""
        try:
            if config['type'] == 'merge_cells':
                self.process_hx100_openpyxl(ws, config, data)
            elif config['type'] == 'complex':
                self.process_hd400_openpyxl(ws, config, data)
            elif config['type'] == 'unique_row':
                if 'IZ381H' in config.get('name', ''):
                    self.process_iz381h_openpyxl(ws, config, data)
                elif 'VS100' in config.get('name', ''):
                    self.process_vs100_openpyxl(ws, config, data)
                else:
                    self.process_vx100_openpyxl(ws, config, data)
            else:
                self.process_standard_product_openpyxl(ws, config, data)

            return True
        except Exception as e:
            print(f"Error processing special product with openpyxl: {e}")
            return False

    def process_hx100_openpyxl(self, ws, config: Dict, data: Dict):
        """Xử lý HX100 với openpyxl"""
        try:
            import random
            from openpyxl.styles import Alignment

            # Serial numbers
            for i, sn in enumerate(data['serial_numbers']):
                ws[f"A{11+i}"] = sn
                ws[f"A{11+i}"].alignment = Alignment(horizontal='center', vertical='center')

            # Random data với merge cells
            special_config = config.get('special_config', {})
            if 'random_ranges' in special_config:
                for row in range(11, 16):
                    for min_val, max_val, cell_range, mode in special_config['random_ranges']:
                        val = random.randint(min_val, max_val)
                        if mode == "div100":
                            val = round(val / 100, 2)

                        start_cell = cell_range.split(":")[0]
                        ws[f"{start_cell}{row}"] = val
                        ws[f"{start_cell}{row}"].alignment = Alignment(horizontal='center', vertical='center')

            # Product info
            merge_config = special_config.get('merge_config', {})

            # Product name
            ws["C4"] = data['product_name']
            try:
                ws.unmerge_cells(merge_config.get('product', 'C4:E5'))
            except:
                pass
            ws.merge_cells(merge_config.get('product', 'C4:E5'))
            ws["C4"].alignment = Alignment(horizontal='center', vertical='center')

            # PO number
            ws["F4"] = data['po_number']
            try:
                ws.unmerge_cells(merge_config.get('po', 'F4:I4'))
            except:
                pass
            ws.merge_cells(merge_config.get('po', 'F4:I4'))
            ws["F4"].alignment = Alignment(horizontal='center', vertical='center')

            # Date
            formatted_date = f"{data['date_code'][:4]}.{data['date_code'][4:6]}.{data['date_code'][6:]}"
            ws["Q4"] = formatted_date
            try:
                ws.unmerge_cells(merge_config.get('date', 'Q4:T4'))
            except:
                pass
            ws.merge_cells(merge_config.get('date', 'Q4:T4'))
            ws["Q4"].alignment = Alignment(horizontal='center', vertical='center')

        except Exception as e:
            print(f"Error processing HX100 with openpyxl: {e}")

    def process_hd400_openpyxl(self, ws, config: Dict, data: Dict):
        """Xử lý HD400 với openpyxl"""
        try:
            import random
            from openpyxl.styles import Alignment

            # Serial numbers
            for i, sn in enumerate(data['serial_numbers']):
                ws[f"A{8+i}"] = sn
                ws[f"A{8+i}"].alignment = Alignment(horizontal='center', vertical='center')

            # Complex random data
            complex_config = config.get('complex_config', [])
            for row in range(8, 13):
                for col_idx, (min_val, max_val, mode) in enumerate(complex_config):
                    if col_idx >= 20:  # Limit columns
                        break

                    col_letter = chr(ord('B') + col_idx)  # Start from B
                    cell_ref = f"{col_letter}{row}"

                    if min_val is None or max_val is None:
                        # Fixed value
                        ws[cell_ref] = mode
                    else:
                        # Random number
                        val = random.randint(min_val, max_val)
                        if mode == "div100":
                            val = round(val / 100, 2)
                        ws[cell_ref] = val

                    ws[cell_ref].alignment = Alignment(horizontal='center', vertical='center')

            # Product info
            merge_config = config.get('merge_config', {})

            # Product name
            ws["B3"] = data['product_name']
            ws["B3"].alignment = Alignment(horizontal='center', vertical='center')

            # PO number
            ws["G3"] = data['po_number']
            ws["G3"].alignment = Alignment(horizontal='center', vertical='center')

            # Date
            formatted_date = f"{data['date_code'][:4]}.{data['date_code'][4:6]}.{data['date_code'][6:]}"
            ws["S3"] = formatted_date
            ws["S3"].alignment = Alignment(horizontal='center', vertical='center')

        except Exception as e:
            print(f"Error processing HD400 with openpyxl: {e}")

    def process_vx100_openpyxl(self, ws, config: Dict, data: Dict):
        """Xử lý VX100 với openpyxl"""
        try:
            import random
            from openpyxl.styles import Alignment

            # Serial numbers
            for i, sn in enumerate(data['serial_numbers']):
                ws[f"A{11+i}"] = sn
                ws[f"A{11+i}"].alignment = Alignment(horizontal='center', vertical='center')

            # Unique row logic cho E11:G15
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
                    ws[f"{cols[col_idx]}{11+row_idx}"] = val
                    ws[f"{cols[col_idx]}{11+row_idx}"].alignment = Alignment(horizontal='center', vertical='center')

            # Product info
            special_config = config.get('special_config', {})
            merge_config = special_config.get('merge_config', {})

            # Product name - C4 (merge C4:D5)
            ws["C4"] = data['product_name']
            try:
                ws.unmerge_cells(merge_config.get('product', 'C4:D5'))
            except:
                pass
            ws.merge_cells(merge_config.get('product', 'C4:D5'))
            ws["C4"].alignment = Alignment(horizontal='center', vertical='center')

            # PO number - F4 (merge F4:G5)
            ws["F4"] = data['po_number']
            try:
                ws.unmerge_cells(merge_config.get('po', 'F4:G5'))
            except:
                pass
            ws.merge_cells(merge_config.get('po', 'F4:G5'))
            ws["F4"].alignment = Alignment(horizontal='center', vertical='center')

            # Date - M4 (merge M4:P5)
            formatted_date = f"{data['date_code'][:4]}.{data['date_code'][4:6]}.{data['date_code'][6:]}"
            ws["M4"] = formatted_date
            try:
                ws.unmerge_cells(merge_config.get('date', 'M4:P5'))
            except:
                pass
            ws.merge_cells(merge_config.get('date', 'M4:P5'))
            ws["M4"].alignment = Alignment(horizontal='center', vertical='center')

        except Exception as e:
            print(f"Error processing VX100 with openpyxl: {e}")

    def process_vs100_openpyxl(self, ws, config: Dict, data: Dict):
        """Xử lý VS100 với openpyxl"""
        try:
            import random
            from openpyxl.styles import Alignment

            # Serial numbers
            for i, sn in enumerate(data['serial_numbers']):
                ws[f"A{11+i}"] = sn
                ws[f"A{11+i}"].alignment = Alignment(horizontal='center', vertical='center')

            # Unique row logic cho E11:G15 với random ranges của VS100
            def generate_unique_row_e_to_g():
                while True:
                    row = [
                        round(random.randint(8000, 8450) / 100, 2),  # VS100 range
                        round(random.randint(14400, 15300) / 100, 2), # VS100 range
                        round(random.randint(4210, 4590) / 100, 2),   # VS100 range
                    ]
                    if len(set(row)) == len(row):
                        return row

            cols = ["E", "F", "G"]
            for row_idx in range(5):
                values = generate_unique_row_e_to_g()
                for col_idx, val in enumerate(values):
                    ws[f"{cols[col_idx]}{11+row_idx}"] = val
                    ws[f"{cols[col_idx]}{11+row_idx}"].alignment = Alignment(horizontal='center', vertical='center')

            # Product info
            special_config = config.get('special_config', {})
            merge_config = special_config.get('merge_config', {})

            # Product name - C4 (merge C4:D5)
            ws["C4"] = data['product_name']
            try:
                ws.unmerge_cells(merge_config.get('product', 'C4:D5'))
            except:
                pass
            ws.merge_cells(merge_config.get('product', 'C4:D5'))
            ws["C4"].alignment = Alignment(horizontal='center', vertical='center')

            # PO number - F4 (merge F4:G5)
            ws["F4"] = data['po_number']
            try:
                ws.unmerge_cells(merge_config.get('po', 'F4:G5'))
            except:
                pass
            ws.merge_cells(merge_config.get('po', 'F4:G5'))
            ws["F4"].alignment = Alignment(horizontal='center', vertical='center')

            # Date - M4 (merge M4:P5)
            formatted_date = f"{data['date_code'][:4]}.{data['date_code'][4:6]}.{data['date_code'][6:]}"
            ws["M4"] = formatted_date
            try:
                ws.unmerge_cells(merge_config.get('date', 'M4:P5'))
            except:
                pass
            ws.merge_cells(merge_config.get('date', 'M4:P5'))
            ws["M4"].alignment = Alignment(horizontal='center', vertical='center')

        except Exception as e:
            print(f"Error processing VS100 with openpyxl: {e}")

    def process_iz381h_openpyxl(self, ws, config: Dict, data: Dict):
        """Xử lý IZ381H với openpyxl"""
        try:
            from openpyxl.styles import Alignment
            import random

            # Serial numbers vào B9:B13 (đúng theo template)
            for i, sn in enumerate(data['serial_numbers']):
                ws[f"B{9+i}"] = sn
                ws[f"B{9+i}"].alignment = Alignment(horizontal='center', vertical='center')

            # Sinh dữ liệu ngẫu nhiên và duy nhất cho mỗi hàng D9:H13
            def generate_unique_row_d_to_h():
                while True:
                    row = [
                        round(random.randint(8712, 8950) / 100, 2),  # D
                        round(random.randint(2315, 2750) / 100, 2),  # E
                        random.randint(1290, 1340),                  # F
                        random.randint(2350, 2580),                  # G
                        round(random.randint(3210, 3500) / 100, 2),  # H
                    ]
                    if len(set(row)) == len(row):
                        return row

            cols = ["D", "E", "F", "G", "H"]
            for r in range(5):
                values = generate_unique_row_d_to_h()
                for c_idx, val in enumerate(values):
                    cell = f"{cols[c_idx]}{9+r}"
                    ws[cell] = val
                    ws[cell].alignment = Alignment(horizontal='center', vertical='center')

            # Product info với merge_config trong special_config
            special_config = config.get('special_config', {})
            merge_config = special_config.get('merge_config', {})

            # Product name B3:C3 - ghi vào ô đầu mối B3
            product_range = merge_config.get('product', 'B3:C3')
            product_top_left = product_range.split(':')[0]
            try:
                ws.unmerge_cells(product_range)
            except Exception:
                pass
            ws[product_top_left] = data['product_name']
            ws.merge_cells(product_range)
            ws[product_top_left].alignment = Alignment(horizontal='center', vertical='center')

            # PO number E3:F3 - ghi vào ô đầu mối E3
            po_range = merge_config.get('po', 'E3:F3')
            po_top_left = po_range.split(':')[0]
            try:
                ws.unmerge_cells(po_range)
            except Exception:
                pass
            ws[po_top_left] = data['po_number']
            ws.merge_cells(po_range)
            ws[po_top_left].alignment = Alignment(horizontal='center', vertical='center')

            # Date I3:J3 - ghi vào ô đầu mối I3
            date_range = merge_config.get('date', 'I3:J3')
            date_top_left = date_range.split(':')[0]
            try:
                formatted_date = f"{data['date_code'][:4]}.{data['date_code'][4:6]}.{data['date_code'][6:]}"
            except Exception:
                formatted_date = data.get('date_code', '')
            try:
                ws.unmerge_cells(date_range)
            except Exception:
                pass
            ws[date_top_left] = formatted_date
            ws.merge_cells(date_range)
            ws[date_top_left].alignment = Alignment(horizontal='center', vertical='center')

        except Exception as e:
            print(f"Error processing IZ381H with openpyxl: {e}")

    def process_tf200_openpyxl(self, ws, config: Dict, data: Dict) -> bool:
        """Xử lý TF200 với openpyxl"""
        try:
            from openpyxl.styles import Alignment
            import random

            tf200_config = config.get('tf200_config', {})
            rows = tf200_config.get('rows', [])
            if len(rows) != 5:
                raise ValueError("TF200 configuration must define exactly 5 rows")

            alignment = Alignment(horizontal='center', vertical='center')

            serial_numbers = data.get('serial_numbers', [])
            if len(serial_numbers) != len(rows):
                raise ValueError("TF200 cần đúng 5 serial numbers")

            gross_weights = data.get('gross_weights', [])
            net_weights = data.get('net_weights', [])
            if len(gross_weights) != len(rows):
                raise ValueError("TF200 cần đúng 5 giá trị Gross Weight")
            if len(net_weights) != len(rows):
                raise ValueError("TF200 cần đúng 5 giá trị Net Weight")

            serial_column = tf200_config.get('serial_column', 'A')
            gross_col = tf200_config.get('gross_weight_column', 'N')
            net_col = tf200_config.get('net_weight_column', 'O')
            inactive_value = tf200_config.get('inactive_value', 'N/A')

            # Serial numbers
            for idx, row in enumerate(rows):
                serial_cell = f"{serial_column}{row}"
                ws[serial_cell] = serial_numbers[idx]
                ws[serial_cell].alignment = alignment

            # Gross & Net weights
            for idx, row in enumerate(rows):
                gross_cell = f"{gross_col}{row}"
                net_cell = f"{net_col}{row}"
                ws[gross_cell] = gross_weights[idx]
                ws[gross_cell].alignment = alignment
                ws[net_cell] = net_weights[idx]
                ws[net_cell].alignment = alignment

            def transform_value(raw_val: int, mode: Optional[str]) -> float | int:
                if mode == "div100" or mode is True:
                    return round(raw_val / 100, 2)
                if mode == "div10":
                    return round(raw_val / 10, 1)
                return raw_val

            # Random columns for each row
            random_columns = tf200_config.get('random_columns', [])
            for row in rows:
                used_values: set[int] = set()
                for col_cfg in random_columns:
                    column = col_cfg.get('column')
                    if not column:
                        continue
                    min_val = col_cfg.get('min')
                    max_val = col_cfg.get('max')
                    mode = col_cfg.get('mode')
                    suffix = col_cfg.get('suffix')

                    if min_val is None or max_val is None:
                        continue

                    attempts = 0
                    while True:
                        raw_val = random.randint(min_val, max_val)
                        if raw_val not in used_values or attempts > (max_val - min_val + 1):
                            used_values.add(raw_val)
                            break
                        attempts += 1

                    value = transform_value(raw_val, mode)
                    if suffix:
                        display_value = f"{int(raw_val)}{suffix}"
                    else:
                        display_value = value

                    cell_ref = f"{column}{row}"
                    ws[cell_ref] = display_value
                    ws[cell_ref].alignment = alignment

            # Single row columns (only apply to first row, others set to inactive)
            single_row_columns = tf200_config.get('single_row_columns', [])
            first_row = rows[0]
            for col_cfg in single_row_columns:
                column = col_cfg.get('column')
                min_val = col_cfg.get('min')
                max_val = col_cfg.get('max')
                mode = col_cfg.get('mode')
                suffix = col_cfg.get('suffix')
                inactive_val = col_cfg.get('inactive_value', inactive_value)

                if column and min_val is not None and max_val is not None:
                    raw_val = random.randint(min_val, max_val)
                    value = transform_value(raw_val, mode)
                    display_value = f"{int(raw_val)}{suffix}" if suffix else value

                    active_cell = f"{column}{first_row}"
                    ws[active_cell] = display_value
                    ws[active_cell].alignment = alignment

                    for row in rows[1:]:
                        inactive_cell = f"{column}{row}"
                        ws[inactive_cell] = inactive_val
                        ws[inactive_cell].alignment = alignment

            # Header information
            merge_config = {
                'product': tf200_config.get('product_range'),
                'po': tf200_config.get('po_range'),
                'date': tf200_config.get('date_range')
            }

            if merge_config.get('product'):
                product_range = merge_config['product']
                top_left = product_range.split(':')[0]
                try:
                    ws.unmerge_cells(product_range)
                except Exception:
                    pass
                ws[top_left] = data['product_name']
                ws.merge_cells(product_range)
                ws[top_left].alignment = alignment

            if merge_config.get('po'):
                po_range = merge_config['po']
                top_left = po_range.split(':')[0]
                try:
                    ws.unmerge_cells(po_range)
                except Exception:
                    pass
                ws[top_left] = data['po_number']
                ws.merge_cells(po_range)
                ws[top_left].alignment = alignment

            if merge_config.get('date'):
                date_range = merge_config['date']
                top_left = date_range.split(':')[0]
                try:
                    formatted_date = datetime.strptime(data['date_code'], "%Y%m%d").strftime("%Y.%m.%d")
                except Exception:
                    formatted_date = data.get('date_code', '')
                try:
                    ws.unmerge_cells(date_range)
                except Exception:
                    pass
                ws[top_left] = formatted_date
                ws.merge_cells(date_range)
                ws[top_left].alignment = alignment

            return True
        except Exception as e:
            print(f"Error processing TF200 with openpyxl: {e}")
            return False

    def create_excel_file(self, product_id: str, data: Dict, output_path: str) -> bool:
        """Tạo file Excel với hình ảnh Shark Ninja"""
        try:
            product_manager = ProductManager()
            config = product_manager.get_product(product_id)
            if not config:
                return False

            template_path = os.path.join(BASE_DIR, config['template'])
            if not os.path.exists(template_path):
                return False

            # Use openpyxl for Replit compatibility (xlwings doesn't work on Replit)
            wb = openpyxl.load_workbook(template_path)
            ws = wb.active

            if config['type'] == 'tf200':
                self.process_tf200_openpyxl(ws, config, data)
            elif config['type'] in ['merge_cells', 'complex', 'unique_row']:
                self.process_special_product_openpyxl(ws, config, data)
            else:
                self.process_standard_product_openpyxl(ws, config, data)

            # Insert Shark Ninja image with openpyxl
            self._insert_shark_image_openpyxl(ws, config)

            wb.save(output_path)
            return True

        except Exception as e:
            print(f"Error creating Excel file: {e}")
            return False

    def _create_excel_with_xlwings_and_image(self, template_path: str, config: Dict, data: Dict, output_path: str) -> bool:
        """Tạo file Excel với xlwings và chèn hình ảnh Shark Ninja"""
        try:
            import xlwings as xw

            app = xw.App(visible=False)
            wb = app.books.open(template_path)
            ws = wb.sheets[0]

            # Disable alerts and screen updating for better performance
            app.display_alerts = False
            app.screen_updating = False

            try:
                # Process data based on product type
                if config['type'] in ['merge_cells', 'complex', 'unique_row']:
                    self.process_special_product_xlwings(ws, config, data)
                else:
                    self.process_standard_product_xlwings(ws, config, data)

                # Insert Shark Ninja image based on product
                self._insert_shark_image(ws, config)

                # Save with new name (preserves all content including images)
                wb.save(output_path)

            finally:
                wb.close()
                app.quit()

            return True

        except Exception as e:
            print(f"Error creating Excel with xlwings: {e}")
            return False

    def _insert_shark_image(self, ws, config: Dict):
        """Chèn hình ảnh Shark Ninja vào vị trí phù hợp"""
        try:
            import xlwings as xw

            # Đường dẫn đến file hình ảnh
            shark_image_path = os.path.join(BASE_DIR, 'image', 'shark.png')

            if not os.path.exists(shark_image_path):
                print(f"Shark image not found at: {shark_image_path}")
                return

            # Xác định vị trí chèn hình dựa trên sản phẩm
            image_position = self._get_image_position(config)
            if not image_position:
                print(f"No image position defined for product: {config.get('name', 'Unknown')}")
                return

            # Chèn hình ảnh
            try:
                # Xóa hình ảnh cũ nếu có (để tránh trùng lặp)
                try:
                    ws.pictures.clear()
                except:
                    pass

                # Chèn hình ảnh mới
                picture = ws.pictures.add(shark_image_path, 
                                        left=ws.range(image_position['left']).left,
                                        top=ws.range(image_position['top']).top,
                                        width=ws.range(image_position['width']).width,
                                        height=ws.range(image_position['height']).height)

                print(f"Successfully inserted Shark image for {config.get('name', 'Unknown')} at {image_position}")

            except Exception as e:
                print(f"Error inserting image: {e}")

        except Exception as e:
            print(f"Error in _insert_shark_image: {e}")

    def _get_image_position(self, config: Dict) -> Dict:
        """Xác định vị trí chèn hình ảnh dựa trên sản phẩm"""
        product_name = config.get('name', '')

        # Mapping vị trí hình ảnh cho từng sản phẩm
        image_positions = {
            # A1:C3 products
            'AW261': {'left': 'A1', 'top': 'A1', 'width': 'C1', 'height': 'A3'},
            'AZ3002': {'left': 'A1', 'top': 'A1', 'width': 'C1', 'height': 'A3'},
            'FA225': {'left': 'A1', 'top': 'A1', 'width': 'C1', 'height': 'A3'},
            'HP152': {'left': 'A1', 'top': 'A1', 'width': 'C1', 'height': 'A3'},
            'HP301': {'left': 'A1', 'top': 'A1', 'width': 'C1', 'height': 'A3'},
            'HX100': {'left': 'A1', 'top': 'A1', 'width': 'C1', 'height': 'A3'},
            'IX141': {'left': 'A1', 'top': 'A1', 'width': 'C1', 'height': 'A3'},
            'LA480': {'left': 'A1', 'top': 'A1', 'width': 'C1', 'height': 'A3'},
            'LA555': {'left': 'A1', 'top': 'A1', 'width': 'C1', 'height': 'A3'},
            'LA700': {'left': 'A1', 'top': 'A1', 'width': 'C1', 'height': 'A3'},
            'LA800': {'left': 'A1', 'top': 'A1', 'width': 'C1', 'height': 'A3'},
            'NV360': {'left': 'A1', 'top': 'A1', 'width': 'C1', 'height': 'A3'},
            'UA1450': {'left': 'A1', 'top': 'A1', 'width': 'C1', 'height': 'A3'},
            'UH205': {'left': 'A1', 'top': 'A1', 'width': 'C1', 'height': 'A3'},
            'UV440': {'left': 'A1', 'top': 'A1', 'width': 'C1', 'height': 'A3'},
            'UV730': {'left': 'A1', 'top': 'A1', 'width': 'C1', 'height': 'A3'},
            'VS100': {'left': 'A1', 'top': 'A1', 'width': 'C1', 'height': 'A3'},
            'VX100': {'left': 'A1', 'top': 'A1', 'width': 'C1', 'height': 'A3'},
            'WD161': {'left': 'A1', 'top': 'A1', 'width': 'C1', 'height': 'A3'},
            'ZD201': {'left': 'A1', 'top': 'A1', 'width': 'C1', 'height': 'A3'},
            'ZU660': {'left': 'A1', 'top': 'A1', 'width': 'C1', 'height': 'A3'},

            # A1:B2 products
            'HD300': {'left': 'A1', 'top': 'A1', 'width': 'B1', 'height': 'A2'},
            'HD400': {'left': 'A1', 'top': 'A1', 'width': 'B1', 'height': 'A2'},
            'HD500': {'left': 'A1', 'top': 'A1', 'width': 'B1', 'height': 'A2'},
            'HD600': {'left': 'A1', 'top': 'A1', 'width': 'B1', 'height': 'A2'},
            'HD700': {'left': 'A1', 'top': 'A1', 'width': 'B1', 'height': 'A2'},
            'IZ381H': {'left': 'A1', 'top': 'A1', 'width': 'B1', 'height': 'A2'},

            # A1:D2 products (special)
            'SV2000': {'left': 'A1', 'top': 'A1', 'width': 'D1', 'height': 'A2'}
        }

        return image_positions.get(product_name)

    def _insert_shark_image_openpyxl(self, ws, config: Dict):
        """Chèn hình ảnh Shark Ninja với openpyxl"""
        try:
            from openpyxl.drawing.image import Image
            from openpyxl.drawing import Drawing
            from openpyxl.drawing.spreadsheet_drawing import AnchorMarker, TwoCellAnchor

            # Đường dẫn đến file hình ảnh
            shark_image_path = os.path.join(BASE_DIR, 'image', 'shark.png')

            if not os.path.exists(shark_image_path):
                print(f"Shark image not found at: {shark_image_path}")
                return

            # Xác định vị trí chèn hình dựa trên sản phẩm
            image_position = self._get_image_position(config)
            if not image_position:
                print(f"No image position defined for product: {config.get('name', 'Unknown')}")
                return

            try:
                # Load hình ảnh
                img = Image(shark_image_path)

                # Tính toán kích thước và vị trí
                # Lấy kích thước của range để điều chỉnh hình ảnh
                left_cell = image_position['left']
                top_cell = image_position['top']
                width_cell = image_position['width']
                height_cell = image_position['height']

                # Tính toán số cột và hàng
                def cell_to_col_row(cell_ref):
                    col = 0
                    row = 0
                    for char in cell_ref:
                        if char.isalpha():
                            col = col * 26 + (ord(char.upper()) - ord('A') + 1)
                        else:
                            row = row * 10 + int(char)
                    return col - 1, row - 1  # Convert to 0-based indexing

                left_col, left_row = cell_to_col_row(left_cell)
                top_col, top_row = cell_to_col_row(top_cell)
                width_col, width_row = cell_to_col_row(width_cell)
                height_col, height_row = cell_to_col_row(height_cell)

                # Tính toán số cột và hàng cho anchor
                col_span = width_col - left_col + 1
                row_span = height_row - top_row + 1

                # Tạo anchor để định vị hình ảnh
                anchor = TwoCellAnchor()
                anchor._from = AnchorMarker(col=left_col, colOff=0, row=left_row, rowOff=0)
                anchor.to = AnchorMarker(col=left_col + col_span, colOff=0, row=top_row + row_span, rowOff=0)

                # Gán anchor cho hình ảnh
                img.anchor = anchor

                # Thêm hình ảnh vào worksheet
                ws.add_image(img)

                print(f"Successfully inserted Shark image for {config.get('name', 'Unknown')} at {image_position}")

            except Exception as e:
                print(f"Error inserting image with openpyxl: {e}")
                # Fallback: thử cách đơn giản hơn
                try:
                    img = Image(shark_image_path)
                    # Resize hình ảnh nếu cần
                    img.width = 200  # pixels
                    img.height = 100  # pixels
                    # Đặt vị trí đơn giản
                    img.anchor = left_cell
                    ws.add_image(img)
                    print(f"Successfully inserted Shark image (fallback method) for {config.get('name', 'Unknown')}")
                except Exception as e2:
                    print(f"Fallback image insertion also failed: {e2}")

        except Exception as e:
            print(f"Error in _insert_shark_image_openpyxl: {e}")

# Khởi tạo managers
product_manager = ProductManager()
excel_processor = ExcelProcessor()

# ==================== DECORATORS ====================

def login_required(f):
    """Decorator yêu cầu đăng nhập"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator yêu cầu quyền admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        user = user_manager.get_user_by_id(session['user_id'])
        if not user or user['role'] != 'admin':
            flash('Bạn không có quyền truy cập!', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# ==================== ROUTES CƠ BẢN ====================

@app.route('/')
@login_required
def index():
    """Trang chủ"""
    products = sorted(product_manager.list_products())  # Sort alphabetically
    return render_template('index.html', products=products, active_page='index')

@app.route('/product/<product_id>')
def product_page(product_id):
    """Trang sản phẩm cụ thể"""
    product = product_manager.get_product(product_id)
    if not product:
        flash('Sản phẩm không tồn tại!', 'error')
        return redirect(url_for('index'))

    return render_template('product.html', product_id=product_id, product=product, active_page='product')

@app.route('/api/products')
def api_products():
    """API lấy danh sách sản phẩm"""
    products = {}
    for product_id in product_manager.list_products():
        product = product_manager.get_product(product_id)
        products[product_id] = {
            'name': product['name'],
            'type': product['type'],
            'template_exists': product_manager.validate_template(product_id),
            'requires_weights': product.get('requires_weights', False),
            'sample_data': product.get('sample_data', {})
        }
    return jsonify(products)

@app.route('/api/generate', methods=['POST'])
def api_generate():
    """API tạo file Excel"""
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        product_data = data.get('data', {})

        product_config = product_manager.get_product(product_id) if product_id else None
        if not product_config:
            return jsonify({'success': False, 'message': 'Sản phẩm không tồn tại'})

        if not product_id or not product_data:
            return jsonify({'success': False, 'message': 'Thiếu dữ liệu'})

        # Validate data
        required_fields = ['product_name', 'po_number', 'date_code', 'serial_numbers']
        extra_required = product_config.get('required_fields', [])
        if extra_required:
            required_fields.extend(extra_required)

        for field in required_fields:
            if field not in product_data:
                return jsonify({'success': False, 'message': f'Thiếu trường: {field}'})

        if len(product_data['serial_numbers']) != 5:
            return jsonify({'success': False, 'message': 'Cần đúng 5 serial numbers'})

        if 'gross_weights' in product_data and len(product_data['gross_weights']) != 5:
            return jsonify({'success': False, 'message': 'TF200 cần đúng 5 giá trị Gross Weight'})

        if 'net_weights' in product_data and len(product_data['net_weights']) != 5:
            return jsonify({'success': False, 'message': 'TF200 cần đúng 5 giá trị Net Weight'})

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
    return render_template('batch.html', active_page='batch')

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

            product_config = product_manager.get_product(product_id) if product_id else None
            if not product_id or not product_data or not product_config:
                results.append({'success': False, 'message': 'Thiếu dữ liệu'})
                continue

            # Tạo file
            today_str = datetime.today().strftime("%Y-%m-%d")
            file_name = f"{product_data['product_name']} - PO#{product_data['po_number']} - {product_data['date_code']}"
            output_dir = os.path.join(OUTPUT_DIR, today_str, file_name)
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f"{file_name}.xlsx")

            extra_required = product_config.get('required_fields', [])
            missing_extra = [
                field for field in extra_required
                if field not in product_data
            ]
            if missing_extra:
                results.append({
                    'success': False,
                    'product': product_data.get('product_name', product_id),
                    'message': f"Thiếu dữ liệu: {', '.join(missing_extra)}"
                })
                continue

            if 'gross_weights' in product_data and len(product_data['gross_weights']) != 5:
                results.append({
                    'success': False,
                    'product': product_data.get('product_name', product_id),
                    'message': 'TF200 cần đúng 5 giá trị Gross Weight'
                })
                continue

            if 'net_weights' in product_data and len(product_data['net_weights']) != 5:
                results.append({
                    'success': False,
                    'product': product_data.get('product_name', product_id),
                    'message': 'TF200 cần đúng 5 giá trị Net Weight'
                })
                continue

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

# ==================== ROUTES NÂNG CẤP ====================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Trang đăng nhập"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = user_manager.authenticate_user(username, password)
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            flash('Đăng nhập thành công!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Tên đăng nhập hoặc mật khẩu không đúng!', 'error')

    return render_template('login.html', active_page='login', body_class='auth-layout')

@app.route('/logout')
def logout():
    """Đăng xuất"""
    session.clear()
    flash('Đã đăng xuất thành công!', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard analytics"""
    dashboard_data = analytics_manager.get_dashboard_data()
    return render_template('dashboard.html', data=dashboard_data, active_page='dashboard')

@app.route('/users')
@admin_required
def users_page():
    """Trang quản lý người dùng"""
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, username, email, role, created_at, last_login
            FROM users ORDER BY created_at DESC
        ''')
        users = cursor.fetchall()

    return render_template('users.html', users=users, active_page='users')

@app.route('/api/users', methods=['GET'])
@admin_required
def get_users():
    """API lấy danh sách người dùng"""
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, username, email, role, created_at, last_login
                FROM users ORDER BY created_at DESC
            ''')
            users = cursor.fetchall()

        return jsonify({
            'success': True,
            'users': [{
                'id': user[0],
                'username': user[1],
                'email': user[2],
                'role': user[3],
                'created_at': user[4],
                'last_login': user[5]
            } for user in users]
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'})

@app.route('/api/users', methods=['POST'])
@admin_required
def create_user():
    """API tạo người dùng mới"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        role = data.get('role', 'user')

        if not username or not password:
            return jsonify({'success': False, 'message': 'Thiếu tên đăng nhập hoặc mật khẩu'})

        success = user_manager.create_user(username, password, email, role)
        if success:
            return jsonify({'success': True, 'message': 'Tạo người dùng thành công!'})
        else:
            return jsonify({'success': False, 'message': 'Tên đăng nhập đã tồn tại!'})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'})

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    """API xóa người dùng"""
    try:
        # Prevent deleting self
        if session.get('user_id') == user_id:
            return jsonify({'success': False, 'message': 'Không thể tự xóa chính mình!'})

        success = user_manager.delete_user(user_id)
        if success:
            return jsonify({'success': True, 'message': 'Xóa người dùng thành công!'})
        else:
            return jsonify({'success': False, 'message': 'Không tìm thấy người dùng hoặc lỗi khi xóa!'})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'})

@app.route('/api/users/<int:user_id>', methods=['PUT'])
@admin_required
def update_user(user_id):
    """API cập nhật người dùng"""
    try:
        data = request.get_json()
        success = user_manager.update_user(user_id, data)
        
        if success:
            return jsonify({'success': True, 'message': 'Cập nhật thành công!'})
        else:
            return jsonify({'success': False, 'message': 'Lỗi khi cập nhật!'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'})

@app.route('/bulk')
@login_required
def bulk_page():
    """Trang bulk operations"""
    return render_template('bulk.html', active_page='bulk')

@app.route('/api/bulk/generate', methods=['POST'])
@login_required
def bulk_generate():
    """API tạo hàng loạt PO"""
    try:
        data = request.get_json()
        requests = data.get('requests', [])

        if not requests:
            return jsonify({'success': False, 'message': 'Không có dữ liệu để xử lý'})

        results = bulk_manager.bulk_generate_pos(requests, session['user_id'])

        return jsonify({
            'success': True,
            'results': results,
            'message': f'Xử lý hoàn thành: {len(results["success"])}/{results["total"]} thành công'
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'})

@app.route('/api/import/excel', methods=['POST'])
@login_required
def import_excel_data():
    """API import dữ liệu từ Excel file"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'Không có file được upload'})

        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'Không có file được chọn'})

        if not file.filename.endswith(('.xlsx', '.xls')):
            return jsonify({'success': False, 'message': 'File phải có định dạng Excel (.xlsx hoặc .xls)'})

        # Lưu file tạm thời
        original_filename = file.filename  # Tên file gốc
        filename = secure_filename(file.filename)
        temp_path = os.path.join(OUTPUT_DIR, f"temp_{filename}")
        file.save(temp_path)

        # Import dữ liệu với tối ưu hóa
        excel_import_manager = ExcelImportManager(db_manager)
        max_rows = request.form.get('max_rows', 50, type=int)  # Có thể config từ frontend
        skip_color_check = request.form.get('skip_color_check', 'false').lower() == 'true'
        result = excel_import_manager.import_daily_line_data(temp_path, max_rows, skip_color_check, original_filename)

        # Xóa file tạm
        os.remove(temp_path)

        if result['success']:
            # Log operation
            analytics_manager.log_operation(
                user_id=session['user_id'],
                operation_type='import_excel',
                status='completed'
            )

            response_data = {
                'success': True,
                'message': f'Import thành công: {result["imported_count"]} records',
                'details': result
            }

            logger.info(f"Import Excel response: {response_data}")
            return jsonify(response_data)
        else:
            error_response = {
                'success': False,
                'message': f'Lỗi import: {result["error"]}'
            }
            logger.error(f"Import Excel error response: {error_response}")
            return jsonify(error_response)

    except Exception as e:
        logger.error(f"Import Excel error: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            'success': False, 
            'message': f'Lỗi: {str(e)}',
            'error_type': type(e).__name__,
            'traceback': traceback.format_exc()
        })

@app.route('/api/predict/po', methods=['POST'])
@login_required
def predict_po():
    """API tiên đoán số PO dựa trên tên sản phẩm"""
    try:
        data = request.get_json()
        product_name = data.get('product_name')

        if not product_name:
            return jsonify({'success': False, 'message': 'Thiếu tên sản phẩm'})

        excel_import_manager = ExcelImportManager(db_manager)
        predicted_po = excel_import_manager.predict_po_number(product_name)

        if predicted_po:
            # Kiểm tra xem PO đã được xử lý chưa
            is_processed = excel_import_manager.is_po_processed(predicted_po)

            return jsonify({
                'success': True,
                'predicted_po': predicted_po,
                'is_processed': is_processed,
                'message': f'Tiên đoán PO: {predicted_po}' + (' (đã xử lý)' if is_processed else '')
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Không tìm thấy PO cho sản phẩm này'
            })

    except Exception as e:
        logger.error(f"Predict PO error: {str(e)}")
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'})

@app.route('/api/predict/product', methods=['POST'])
@login_required
def predict_product():
    """API lấy tên sản phẩm dựa trên số PO"""
    try:
        data = request.get_json()
        po_number = data.get('po_number')

        if not po_number:
            return jsonify({'success': False, 'message': 'Thiếu số PO'})

        excel_import_manager = ExcelImportManager(db_manager)
        product_name = excel_import_manager.get_product_by_po(po_number)

        if product_name:
            return jsonify({
                'success': True,
                'product_name': product_name,
                'message': f'Sản phẩm: {product_name}'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Không tìm thấy sản phẩm cho PO này'
            })

    except Exception as e:
        logger.error(f"Predict product error: {str(e)}")
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'})

@app.route('/api/import/po-list')
@login_required
def get_imported_po_list():
    """API lấy danh sách PO đã import"""
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()

            # Lấy danh sách PO đã import, sắp xếp theo ngày
            cursor.execute('''
                SELECT 
                    po_number,
                    product_name,
                    file_import_date,
                    import_date,
                    completion_date,
                    status,
                    file_name
                FROM import_data 
                ORDER BY file_import_date DESC, import_date DESC
            ''')

            rows = cursor.fetchall()

            po_list = []
            for row in rows:
                po_list.append({
                    'po_number': row[0],
                    'product_name': row[1],
                    'file_import_date': row[2],
                    'import_date': row[3],
                    'completion_date': row[4],
                    'status': row[5],
                    'file_name': row[6]
                })

            return jsonify({
                'success': True,
                'data': po_list,
                'total': len(po_list)
            })

    except Exception as e:
        logger.error(f"Get imported PO list error: {str(e)}")
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'})

@app.route('/api/import/update-status', methods=['POST'])
@login_required
def update_po_status():
    """API cập nhật trạng thái PO"""
    try:
        data = request.get_json()
        po_number = data.get('po_number')
        status = data.get('status', 'completed')

        if not po_number:
            return jsonify({'success': False, 'message': 'Thiếu PO number'})

        with db_manager.get_connection() as conn:
            cursor = conn.cursor()

            if status == 'completed':
                cursor.execute('''
                    UPDATE import_data 
                    SET status = ?, completion_date = CURRENT_TIMESTAMP
                    WHERE po_number = ?
                ''', (status, po_number))
            else:
                cursor.execute('''
                    UPDATE import_data 
                    SET status = ?, completion_date = NULL
                    WHERE po_number = ?
                ''', (status, po_number))

            conn.commit()

            return jsonify({
                'success': True,
                'message': f'Cập nhật trạng thái PO {po_number} thành công'
            })

    except Exception as e:
        logger.error(f"Update PO status error: {str(e)}")
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'})

@app.route('/api/import/clear', methods=['POST'])
@login_required
def clear_import_data():
    """API xóa sạch dữ liệu đã import"""
    try:
        logger.info("Clear import data request received")

        with db_manager.get_connection() as conn:
            cursor = conn.cursor()

            # Đếm số records trước khi xóa
            cursor.execute('SELECT COUNT(*) FROM import_data')
            count_before = cursor.fetchone()[0]
            logger.info(f"Records before deletion: {count_before}")

            # Xóa tất cả dữ liệu import
            cursor.execute('DELETE FROM import_data')
            deleted_import = cursor.rowcount

            # Xóa cả dữ liệu prediction (nếu bảng tồn tại)
            try:
                cursor.execute('DELETE FROM po_prediction')
                deleted_prediction = cursor.rowcount
            except sqlite3.OperationalError as e:
                if 'no such table' in str(e).lower():
                    logger.warning("po_prediction table does not exist, skipping deletion")
                    deleted_prediction = 0
                else:
                    raise e

            conn.commit()
            logger.info(f"Deleted {deleted_import} import records and {deleted_prediction} prediction records")

            # Log operation
            analytics_manager.log_operation(
                user_id=session['user_id'],
                operation_type='clear_import_data',
                status='completed'
            )

            response_data = {
                'success': True,
                'message': f'Đã xóa {count_before} records import data',
                'deleted_count': count_before,
                'deleted_import': deleted_import,
                'deleted_prediction': deleted_prediction
            }

            logger.info(f"Clear import data response: {response_data}")
            return jsonify(response_data)

    except Exception as e:
        logger.error(f"Clear import data error: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            'success': False, 
            'message': f'Lỗi: {str(e)}',
            'error_type': type(e).__name__
        })

@app.route('/api/import/status', methods=['GET'])
@login_required
def get_import_status():
    """API lấy trạng thái import data"""
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()

            # Tổng số records đã import
            cursor.execute('SELECT COUNT(*) FROM import_data')
            total_imported = cursor.fetchone()[0]

            # Số PO đã được xử lý
            cursor.execute('''
                SELECT COUNT(DISTINCT po_number) FROM operations 
                WHERE status = 'completed' AND po_number IS NOT NULL
            ''')
            processed_pos = cursor.fetchone()[0]

            # Số PO chưa xử lý
            cursor.execute('''
                SELECT COUNT(DISTINCT po_number) FROM import_data 
                WHERE po_number NOT IN (
                    SELECT DISTINCT po_number FROM operations 
                    WHERE status = 'completed' AND po_number IS NOT NULL
                )
            ''')
            pending_pos = cursor.fetchone()[0]

            return jsonify({
                'success': True,
                'total_imported': total_imported,
                'processed_pos': processed_pos,
                'pending_pos': pending_pos,
                'completion_rate': round((processed_pos / total_imported * 100) if total_imported > 0 else 0, 2)
            })

    except Exception as e:
        logger.error(f"Get import status error: {str(e)}")
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'})

@app.route('/import')
@login_required
def import_page():
    """Trang import Excel riêng"""
    return render_template('import.html', active_page='import')

@app.route('/analytics')
@login_required
def analytics_page():
    """Trang analytics chi tiết"""
    days = request.args.get('days', 30, type=int)
    dashboard_data = analytics_manager.get_dashboard_data(days)

    return render_template('analytics.html', data=dashboard_data, days=days, active_page='analytics')

@app.route('/api/analytics/operations')
@login_required
def get_operations():
    """API lấy danh sách operations"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        product_name = request.args.get('product_name')
        status = request.args.get('status')

        with db_manager.get_connection() as conn:
            cursor = conn.cursor()

            query = '''
                SELECT o.id, o.operation_type, o.product_name, o.po_number, 
                       o.status, o.created_at, o.completed_at, o.error_message,
                       u.username
                FROM operations o
                LEFT JOIN users u ON o.user_id = u.id
            '''

            conditions = []
            params = []

            if product_name:
                conditions.append("o.product_name = ?")
                params.append(product_name)

            if status:
                conditions.append("o.status = ?")
                params.append(status)

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += " ORDER BY o.created_at DESC"

            # Pagination
            offset = (page - 1) * per_page
            query += f" LIMIT {per_page} OFFSET {offset}"

            cursor.execute(query, params)
            operations = cursor.fetchall()

            # Count total
            count_query = '''
                SELECT COUNT(*) FROM operations o
                LEFT JOIN users u ON o.user_id = u.id
            '''
            if conditions:
                count_query += " WHERE " + " AND ".join(conditions)

            cursor.execute(count_query, params)
            total = cursor.fetchone()[0]

            return jsonify({
                'success': True,
                'operations': [{
                    'id': op[0],
                    'operation_type': op[1],
                    'product_name': op[2],
                    'po_number': op[3],
                    'status': op[4],
                    'created_at': op[5],
                    'completed_at': op[6],
                    'error_message': op[7],
                    'username': op[8]
                } for op in operations],
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': (total + per_page - 1) // per_page
            })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'})

@app.route('/api/analytics/stats')
@login_required
def get_stats():
    """API lấy thống kê chi tiết"""
    try:
        days = request.args.get('days', 30, type=int)
        stats = analytics_manager.get_dashboard_data(days)

        return jsonify({
            'success': True,
            'stats': stats
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'})

@app.route('/config')
def config_page():
    """Trang cấu hình"""
    return render_template('config.html', active_page='config')

@app.route('/api/product-image/<product_id>')
def get_product_image(product_id):
    """API lấy hình ảnh sản phẩm"""
    try:
        # Tìm file ảnh trong thư mục sản phẩm
        product_dir = os.path.join(PRODUCTS_DIR, product_id)
        
        if not os.path.exists(product_dir):
            return jsonify({'success': False, 'message': 'Sản phẩm không tồn tại'}), 404
        
        # Tìm file ảnh (png, jpg, jpeg)
        image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.webp']
        image_path = None
        
        for file in os.listdir(product_dir):
            if any(file.lower().endswith(ext) for ext in image_extensions):
                image_path = os.path.join(product_dir, file)
                break
        
        if image_path and os.path.exists(image_path):
            return send_file(image_path, mimetype='image/png')
        else:
            # Trả về ảnh mặc định nếu không tìm thấy
            default_image = os.path.join(BASE_DIR, 'image', 'shark.png')
            if os.path.exists(default_image):
                return send_file(default_image, mimetype='image/png')
            return jsonify({'success': False, 'message': 'Không tìm thấy hình ảnh'}), 404
            
    except Exception as e:
        logger.error(f"Error getting product image: {str(e)}")
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'}), 500

@app.route('/api/files-count')
def api_files_count():
    """API đếm số file đã tạo trong thư mục output"""
    try:
        file_count = 0
        
        # Đếm tất cả file .xlsx trong thư mục output và các thư mục con
        if os.path.exists(OUTPUT_DIR):
            for root, dirs, files in os.walk(OUTPUT_DIR):
                # Chỉ đếm file .xlsx (file Excel đã tạo)
                file_count += sum(1 for file in files if file.endswith('.xlsx'))
        
        return jsonify({
            'success': True,
            'count': file_count
        })
    
    except Exception as e:
        logger.error(f"Error counting files: {str(e)}")
        return jsonify({
            'success': False,
            'count': 0,
            'message': f'Lỗi: {str(e)}'
        })

# Initialize admin user and bulk manager
def initialize_app():
    """Initialize application components"""
    try:
        user_manager.create_user('admin', 'admin123', 'admin@po-system.com', 'admin')
        logger.info("Admin user created successfully")
    except:
        logger.info("Admin user already exists")

    # Khởi tạo bulk operations manager
    global bulk_manager
    bulk_manager = BulkOperationsManager(product_manager, db_manager)

# Initialize app components
initialize_app()

if __name__ == '__main__':
    # Get port from environment variable (for Render.com)
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'

    print("🚀 Hệ thống PO Web nâng cấp đang khởi động...")
    print(f"📊 Dashboard analytics: http://0.0.0.0:{port}/dashboard")
    print(f"👥 User management: http://0.0.0.0:{port}/users")
    print(f"📦 Bulk operations: http://0.0.0.0:{port}/bulk")
    print(f"📈 Analytics: http://0.0.0.0:{port}/analytics")
    print(f"📱 Truy cập: http://0.0.0.0:{port}")
    print("🔄 Nhấn Ctrl+C để dừng")

    app.run(debug=debug, host='0.0.0.0', port=port)
