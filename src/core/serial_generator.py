"""
Serial Number Generator Module
Handles automatic serial number generation and management
"""

import re
from datetime import datetime
from typing import List, Dict, Optional
from database import db_manager

class SerialNumberGenerator:
    """Generator cho serial numbers tự động"""
    
    def __init__(self):
        self.patterns = {
            'default': '{product_id}-{number:03d}',
            'date': '{product_id}-{date}-{number:03d}',
            'custom': '{product_id}-{custom}-{number:03d}'
        }
    
    def generate_serial_numbers(self, product_id: str, count: int = 5, 
                              pattern: str = None, custom_text: str = None) -> List[str]:
        """Tạo danh sách serial numbers"""
        if not pattern:
            pattern = self.patterns['default']
        
        serial_numbers = []
        
        for i in range(count):
            if pattern == self.patterns['date']:
                date_str = datetime.now().strftime('%y%m%d')
                serial = pattern.format(
                    product_id=product_id,
                    date=date_str,
                    number=i + 1
                )
            elif pattern == self.patterns['custom'] and custom_text:
                serial = pattern.format(
                    product_id=product_id,
                    custom=custom_text,
                    number=i + 1
                )
            else:
                # Sử dụng database để lấy số tiếp theo
                next_number = self._get_next_number(product_id)
                serial = pattern.format(
                    product_id=product_id,
                    number=next_number + i
                )
            
            serial_numbers.append(serial)
        
        return serial_numbers
    
    def _get_next_number(self, product_id: str) -> int:
        """Lấy số tiếp theo từ database"""
        pattern = self.patterns['default']
        serial = db_manager.get_next_serial_number(product_id, pattern)
        
        # Extract number from serial
        match = re.search(r'-(\d+)$', serial)
        if match:
            return int(match.group(1))
        return 1
    
    def validate_serial_number(self, serial: str, product_id: str) -> bool:
        """Validate serial number format"""
        if not serial:
            return False
        
        # Check if starts with product_id
        if not serial.startswith(product_id):
            return False
        
        # Check format
        pattern = r'^' + re.escape(product_id) + r'-\d+$'
        return bool(re.match(pattern, serial))
    
    def get_serial_patterns(self) -> Dict[str, str]:
        """Lấy danh sách patterns có sẵn"""
        return {
            'default': 'Mặc định (LA800-001)',
            'date': 'Có ngày (LA800-250105-001)',
            'custom': 'Tùy chỉnh (LA800-CUSTOM-001)'
        }
    
    def parse_serial_number(self, serial: str) -> Dict:
        """Parse serial number thành các thành phần"""
        if not serial:
            return {}
        
        # Extract product_id
        parts = serial.split('-')
        if len(parts) < 2:
            return {}
        
        product_id = parts[0]
        number = parts[-1]
        
        result = {
            'product_id': product_id,
            'number': number,
            'full_serial': serial
        }
        
        # Check if has date
        if len(parts) == 3 and len(parts[1]) == 6:
            try:
                int(parts[1])
                result['date'] = parts[1]
                result['pattern'] = 'date'
            except ValueError:
                result['custom'] = parts[1]
                result['pattern'] = 'custom'
        else:
            result['pattern'] = 'default'
        
        return result
    
    def suggest_next_serial(self, product_id: str, pattern: str = 'default') -> str:
        """Gợi ý serial number tiếp theo"""
        if pattern == 'date':
            date_str = datetime.now().strftime('%y%m%d')
            pattern_str = f"{product_id}-{date_str}-{{:03d}}"
        elif pattern == 'custom':
            pattern_str = f"{product_id}-CUSTOM-{{:03d}}"
        else:
            pattern_str = f"{product_id}-{{:03d}}"
        
        return db_manager.get_next_serial_number(product_id, pattern_str)
    
    def get_serial_statistics(self, product_id: str = None) -> Dict:
        """Lấy thống kê serial numbers"""
        conn = db_manager.db_path
        import sqlite3
        
        conn = sqlite3.connect(conn)
        cursor = conn.cursor()
        
        if product_id:
            cursor.execute('''
                SELECT COUNT(*) FROM po_history 
                WHERE product_id = ?
            ''', (product_id,))
            total_count = cursor.fetchone()[0]
            
            cursor.execute('''
                SELECT MAX(last_serial_number) FROM serial_tracking 
                WHERE product_id = ?
            ''', (product_id,))
            last_number = cursor.fetchone()[0] or 0
        else:
            cursor.execute('SELECT COUNT(*) FROM po_history')
            total_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT MAX(last_serial_number) FROM serial_tracking')
            last_number = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            'total_generated': total_count,
            'last_number': last_number,
            'next_number': last_number + 1,
            'product_id': product_id
        }
    
    def reset_serial_counter(self, product_id: str, new_start: int = 1):
        """Reset counter cho sản phẩm"""
        conn = db_manager.db_path
        import sqlite3
        
        conn = sqlite3.connect(conn)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE serial_tracking 
            SET last_serial_number = ?, updated_at = CURRENT_TIMESTAMP
            WHERE product_id = ?
        ''', (new_start - 1, product_id))
        
        conn.commit()
        conn.close()
    
    def bulk_generate_serials(self, product_id: str, count: int, 
                            pattern: str = 'default', start_number: int = None) -> List[str]:
        """Tạo hàng loạt serial numbers"""
        if start_number:
            self.reset_serial_counter(product_id, start_number)
        
        return self.generate_serial_numbers(product_id, count, pattern)
    
    def export_serial_list(self, product_id: str, file_path: str):
        """Export danh sách serial numbers ra file"""
        history = db_manager.get_po_history(product_id=product_id, limit=10000)
        
        serials = []
        for record in history:
            serials.extend(record['serial_numbers'])
        
        with open(file_path, 'w', encoding='utf-8') as f:
            for serial in serials:
                f.write(f"{serial}\n")
    
    def import_serial_list(self, file_path: str) -> List[str]:
        """Import danh sách serial numbers từ file"""
        serials = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    serial = line.strip()
                    if serial:
                        serials.append(serial)
        except FileNotFoundError:
            pass
        
        return serials
    
    def check_duplicate_serials(self, serials: List[str]) -> List[str]:
        """Kiểm tra serial numbers trùng lặp"""
        conn = db_manager.db_path
        import sqlite3
        
        conn = sqlite3.connect(conn)
        cursor = conn.cursor()
        
        duplicates = []
        
        for serial in serials:
            cursor.execute('''
                SELECT COUNT(*) FROM po_history 
                WHERE serial_numbers LIKE ?
            ''', (f'%{serial}%',))
            
            count = cursor.fetchone()[0]
            if count > 0:
                duplicates.append(serial)
        
        conn.close()
        return duplicates
    
    def get_serial_range(self, product_id: str, start_date: str = None, 
                        end_date: str = None) -> List[str]:
        """Lấy serial numbers trong khoảng thời gian"""
        history = db_manager.get_po_history(
            product_id=product_id,
            date_from=start_date,
            date_to=end_date,
            limit=10000
        )
        
        serials = []
        for record in history:
            serials.extend(record['serial_numbers'])
        
        return sorted(serials)

# Global instance
serial_generator = SerialNumberGenerator()

