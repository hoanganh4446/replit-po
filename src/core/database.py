"""
Database module for PO System
Handles SQLite database operations for history, statistics, and serial numbers
"""

import sqlite3
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import json

class DatabaseManager:
    """Quản lý database SQLite cho hệ thống PO"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Đường dẫn tương đối từ src/core/ đến config/database/
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.db_path = os.path.join(current_dir, '../../config/database/po_system.db')
        else:
            self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Khởi tạo database và tạo các bảng cần thiết"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Bảng lịch sử tạo file PO
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS po_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id TEXT NOT NULL,
                product_name TEXT NOT NULL,
                po_number TEXT NOT NULL,
                date_code TEXT NOT NULL,
                serial_numbers TEXT NOT NULL,
                file_path TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_agent TEXT,
                ip_address TEXT
            )
        ''')
        
        # Bảng serial number tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS serial_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id TEXT NOT NULL,
                last_serial_number INTEGER DEFAULT 0,
                serial_pattern TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Bảng statistics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                product_id TEXT NOT NULL,
                count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Bảng user preferences
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Bảng search history
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                search_term TEXT NOT NULL,
                search_type TEXT NOT NULL,
                results_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_po_record(self, product_id: str, product_name: str, po_number: str, 
                     date_code: str, serial_numbers: List[str], file_path: str,
                     user_agent: str = None, ip_address: str = None) -> int:
        """Thêm record mới vào lịch sử PO"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO po_history 
            (product_id, product_name, po_number, date_code, serial_numbers, file_path, user_agent, ip_address)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (product_id, product_name, po_number, date_code, 
              json.dumps(serial_numbers), file_path, user_agent, ip_address))
        
        record_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Update statistics
        self.update_statistics(product_id)
        
        return record_id
    
    def get_po_history(self, limit: int = 100, offset: int = 0, 
                      product_id: str = None, date_from: str = None, 
                      date_to: str = None) -> List[Dict]:
        """Lấy lịch sử PO với filter"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM po_history WHERE 1=1"
        params = []
        
        if product_id:
            query += " AND product_id = ?"
            params.append(product_id)
        
        if date_from:
            query += " AND DATE(created_at) >= ?"
            params.append(date_from)
        
        if date_to:
            query += " AND DATE(created_at) <= ?"
            params.append(date_to)
        
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Convert to dict
        columns = [description[0] for description in cursor.description]
        result = []
        for row in rows:
            record = dict(zip(columns, row))
            record['serial_numbers'] = json.loads(record['serial_numbers'])
            result.append(record)
        
        conn.close()
        return result
    
    def get_next_serial_number(self, product_id: str, pattern: str = None) -> str:
        """Lấy serial number tiếp theo cho sản phẩm"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Lấy pattern mặc định nếu không có
        if not pattern:
            pattern = f"{product_id}-{{:03d}}"
        
        # Kiểm tra xem đã có record chưa
        cursor.execute('''
            SELECT last_serial_number, serial_pattern FROM serial_tracking 
            WHERE product_id = ?
        ''', (product_id,))
        
        row = cursor.fetchone()
        
        if row:
            last_number, current_pattern = row
            next_number = last_number + 1
            
            # Update số tiếp theo
            cursor.execute('''
                UPDATE serial_tracking 
                SET last_serial_number = ?, updated_at = CURRENT_TIMESTAMP
                WHERE product_id = ?
            ''', (next_number, product_id))
        else:
            # Tạo record mới
            next_number = 1
            cursor.execute('''
                INSERT INTO serial_tracking (product_id, last_serial_number, serial_pattern)
                VALUES (?, ?, ?)
            ''', (product_id, next_number, pattern))
        
        conn.commit()
        conn.close()
        
        return pattern.format(next_number)
    
    def update_statistics(self, product_id: str):
        """Cập nhật thống kê"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Kiểm tra xem đã có record hôm nay chưa
        cursor.execute('''
            SELECT count FROM statistics 
            WHERE date = ? AND product_id = ?
        ''', (today, product_id))
        
        row = cursor.fetchone()
        
        if row:
            # Update count
            cursor.execute('''
                UPDATE statistics 
                SET count = count + 1 
                WHERE date = ? AND product_id = ?
            ''', (today, product_id))
        else:
            # Tạo record mới
            cursor.execute('''
                INSERT INTO statistics (date, product_id, count)
                VALUES (?, ?, 1)
            ''', (today, product_id))
        
        conn.commit()
        conn.close()
    
    def get_statistics(self, days: int = 30) -> Dict:
        """Lấy thống kê"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Thống kê theo sản phẩm
        cursor.execute('''
            SELECT product_id, SUM(count) as total_count
            FROM statistics 
            WHERE date >= date('now', '-{} days')
            GROUP BY product_id
            ORDER BY total_count DESC
        '''.format(days))
        
        product_stats = cursor.fetchall()
        
        # Thống kê theo ngày
        cursor.execute('''
            SELECT date, SUM(count) as daily_count
            FROM statistics 
            WHERE date >= date('now', '-{} days')
            GROUP BY date
            ORDER BY date DESC
        '''.format(days))
        
        daily_stats = cursor.fetchall()
        
        # Tổng số file đã tạo
        cursor.execute('SELECT COUNT(*) FROM po_history')
        total_files = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'product_stats': product_stats,
            'daily_stats': daily_stats,
            'total_files': total_files,
            'period_days': days
        }
    
    def search_history(self, search_term: str, search_type: str = 'all') -> List[Dict]:
        """Tìm kiếm trong lịch sử"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if search_type == 'all':
            query = '''
                SELECT * FROM po_history 
                WHERE product_name LIKE ? OR po_number LIKE ? OR serial_numbers LIKE ?
                ORDER BY created_at DESC
            '''
            params = [f'%{search_term}%', f'%{search_term}%', f'%{search_term}%']
        elif search_type == 'product':
            query = 'SELECT * FROM po_history WHERE product_name LIKE ? ORDER BY created_at DESC'
            params = [f'%{search_term}%']
        elif search_type == 'po':
            query = 'SELECT * FROM po_history WHERE po_number LIKE ? ORDER BY created_at DESC'
            params = [f'%{search_term}%']
        else:
            query = 'SELECT * FROM po_history WHERE serial_numbers LIKE ? ORDER BY created_at DESC'
            params = [f'%{search_term}%']
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Convert to dict
        columns = [description[0] for description in cursor.description]
        result = []
        for row in rows:
            record = dict(zip(columns, row))
            record['serial_numbers'] = json.loads(record['serial_numbers'])
            result.append(record)
        
        # Lưu search history
        self.add_search_history(search_term, search_type, len(result))
        
        conn.close()
        return result
    
    def add_search_history(self, search_term: str, search_type: str, results_count: int):
        """Lưu lịch sử tìm kiếm"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO search_history (search_term, search_type, results_count)
            VALUES (?, ?, ?)
        ''', (search_term, search_type, results_count))
        
        conn.commit()
        conn.close()
    
    def get_user_preference(self, key: str, default_value: str = None) -> str:
        """Lấy user preference"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT value FROM user_preferences WHERE key = ?', (key,))
        row = cursor.fetchone()
        
        conn.close()
        
        return row[0] if row else default_value
    
    def set_user_preference(self, key: str, value: str):
        """Set user preference"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO user_preferences (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (key, value))
        
        conn.commit()
        conn.close()
    
    def get_recent_searches(self, limit: int = 10) -> List[Dict]:
        """Lấy tìm kiếm gần đây"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT DISTINCT search_term, search_type, MAX(created_at) as last_searched
            FROM search_history 
            GROUP BY search_term, search_type
            ORDER BY last_searched DESC
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        
        result = []
        for row in rows:
            result.append({
                'search_term': row[0],
                'search_type': row[1],
                'last_searched': row[2]
            })
        
        conn.close()
        return result
    
    def cleanup_old_data(self, days: int = 90):
        """Dọn dẹp dữ liệu cũ"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Xóa search history cũ
        cursor.execute('''
            DELETE FROM search_history 
            WHERE created_at < date('now', '-{} days')
        '''.format(days))
        
        conn.commit()
        conn.close()
    
    def export_history_to_csv(self, file_path: str, product_id: str = None):
        """Export lịch sử ra CSV"""
        import csv
        
        history = self.get_po_history(limit=10000, product_id=product_id)
        
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            if history:
                fieldnames = history[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(history)
    
    def get_database_stats(self) -> Dict:
        """Lấy thống kê database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        # Đếm records trong mỗi bảng
        tables = ['po_history', 'serial_tracking', 'statistics', 'user_preferences', 'search_history']
        for table in tables:
            cursor.execute(f'SELECT COUNT(*) FROM {table}')
            stats[f'{table}_count'] = cursor.fetchone()[0]
        
        # Kích thước database
        cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
        stats['database_size'] = cursor.fetchone()[0]
        
        conn.close()
        return stats

# Global database instance
db_manager = DatabaseManager()

