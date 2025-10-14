"""
Advanced Search & Filtering Module
Provides enhanced search capabilities and filtering options
"""

import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from database import db_manager

class AdvancedSearch:
    """Advanced search and filtering functionality"""
    
    def __init__(self):
        self.search_types = {
            'all': 'Tất cả',
            'product': 'Sản phẩm',
            'po': 'PO Number',
            'serial': 'Serial Number',
            'date': 'Ngày tạo',
            'file': 'Tên file'
        }
        
        self.filter_options = {
            'date_range': 'Khoảng thời gian',
            'product_type': 'Loại sản phẩm',
            'file_size': 'Kích thước file',
            'status': 'Trạng thái'
        }
    
    def search(self, query: str, search_type: str = 'all', 
              filters: Dict = None, limit: int = 100) -> Dict:
        """Tìm kiếm nâng cao với filters"""
        
        # Base search
        if search_type == 'all':
            results = self._search_all(query)
        elif search_type == 'product':
            results = self._search_by_product(query)
        elif search_type == 'po':
            results = self._search_by_po(query)
        elif search_type == 'serial':
            results = self._search_by_serial(query)
        elif search_type == 'date':
            results = self._search_by_date(query)
        elif search_type == 'file':
            results = self._search_by_file(query)
        else:
            results = []
        
        # Apply filters
        if filters:
            results = self._apply_filters(results, filters)
        
        # Limit results
        results = results[:limit]
        
        # Add search suggestions
        suggestions = self._get_search_suggestions(query, search_type)
        
        return {
            'results': results,
            'total_count': len(results),
            'query': query,
            'search_type': search_type,
            'filters_applied': filters or {},
            'suggestions': suggestions,
            'search_time': datetime.now().isoformat()
        }
    
    def _search_all(self, query: str) -> List[Dict]:
        """Tìm kiếm trong tất cả fields"""
        return db_manager.search_history(query, 'all')
    
    def _search_by_product(self, query: str) -> List[Dict]:
        """Tìm kiếm theo tên sản phẩm"""
        return db_manager.search_history(query, 'product')
    
    def _search_by_po(self, query: str) -> List[Dict]:
        """Tìm kiếm theo PO number"""
        return db_manager.search_history(query, 'po')
    
    def _search_by_serial(self, query: str) -> List[Dict]:
        """Tìm kiếm theo serial number"""
        return db_manager.search_history(query, 'serial')
    
    def _search_by_date(self, query: str) -> List[Dict]:
        """Tìm kiếm theo ngày"""
        try:
            # Try to parse date
            date_obj = datetime.strptime(query, '%Y-%m-%d')
            return db_manager.get_po_history(
                date_from=query,
                date_to=query,
                limit=1000
            )
        except ValueError:
            # If not a valid date, search in date strings
            return db_manager.search_history(query, 'all')
    
    def _search_by_file(self, query: str) -> List[Dict]:
        """Tìm kiếm theo tên file"""
        conn = db_manager.db_path
        import sqlite3
        
        conn = sqlite3.connect(conn)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM po_history 
            WHERE file_path LIKE ?
            ORDER BY created_at DESC
        ''', (f'%{query}%',))
        
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        
        results = []
        for row in rows:
            record = dict(zip(columns, row))
            record['serial_numbers'] = eval(record['serial_numbers'])  # Convert string to list
            results.append(record)
        
        conn.close()
        return results
    
    def _apply_filters(self, results: List[Dict], filters: Dict) -> List[Dict]:
        """Apply filters to search results"""
        filtered_results = results.copy()
        
        # Date range filter
        if 'date_range' in filters:
            date_range = filters['date_range']
            if 'start_date' in date_range and 'end_date' in date_range:
                filtered_results = [
                    r for r in filtered_results
                    if date_range['start_date'] <= r['created_at'][:10] <= date_range['end_date']
                ]
        
        # Product type filter
        if 'product_type' in filters:
            product_types = filters['product_type']
            if isinstance(product_types, list):
                filtered_results = [
                    r for r in filtered_results
                    if r['product_id'] in product_types
                ]
        
        # File size filter
        if 'file_size' in filters:
            file_size = filters['file_size']
            filtered_results = [
                r for r in filtered_results
                if self._check_file_size(r['file_path'], file_size)
            ]
        
        # Status filter
        if 'status' in filters:
            status = filters['status']
            filtered_results = [
                r for r in filtered_results
                if self._check_status(r, status)
            ]
        
        return filtered_results
    
    def _check_file_size(self, file_path: str, size_filter: Dict) -> bool:
        """Check if file size matches filter"""
        try:
            import os
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                
                if 'min_size' in size_filter:
                    if file_size < size_filter['min_size']:
                        return False
                
                if 'max_size' in size_filter:
                    if file_size > size_filter['max_size']:
                        return False
                
                return True
        except:
            pass
        
        return False
    
    def _check_status(self, record: Dict, status: str) -> bool:
        """Check record status"""
        if status == 'recent':
            # Created within last 7 days
            created_date = datetime.fromisoformat(record['created_at'].replace('Z', '+00:00'))
            return (datetime.now() - created_date).days <= 7
        elif status == 'old':
            # Created more than 30 days ago
            created_date = datetime.fromisoformat(record['created_at'].replace('Z', '+00:00'))
            return (datetime.now() - created_date).days > 30
        elif status == 'today':
            # Created today
            created_date = datetime.fromisoformat(record['created_at'].replace('Z', '+00:00'))
            return created_date.date() == datetime.now().date()
        
        return True
    
    def _get_search_suggestions(self, query: str, search_type: str) -> List[str]:
        """Get search suggestions based on query"""
        suggestions = []
        
        # Get recent searches
        recent_searches = db_manager.get_recent_searches(limit=5)
        for search in recent_searches:
            if query.lower() in search['search_term'].lower():
                suggestions.append(search['search_term'])
        
        # Get product suggestions
        if search_type in ['all', 'product']:
            conn = db_manager.db_path
            import sqlite3
            
            conn = sqlite3.connect(conn)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT DISTINCT product_name FROM po_history 
                WHERE product_name LIKE ?
                LIMIT 5
            ''', (f'%{query}%',))
            
            for row in cursor.fetchall():
                suggestions.append(row[0])
            
            conn.close()
        
        return suggestions[:5]
    
    def get_quick_filters(self) -> Dict:
        """Get quick filter options"""
        return {
            'today': 'Hôm nay',
            'yesterday': 'Hôm qua',
            'this_week': 'Tuần này',
            'this_month': 'Tháng này',
            'last_month': 'Tháng trước',
            'last_30_days': '30 ngày qua',
            'last_90_days': '90 ngày qua'
        }
    
    def apply_quick_filter(self, filter_name: str) -> Dict:
        """Apply quick date filter"""
        today = datetime.now().date()
        
        if filter_name == 'today':
            return {
                'date_range': {
                    'start_date': today.strftime('%Y-%m-%d'),
                    'end_date': today.strftime('%Y-%m-%d')
                }
            }
        elif filter_name == 'yesterday':
            yesterday = today - timedelta(days=1)
            return {
                'date_range': {
                    'start_date': yesterday.strftime('%Y-%m-%d'),
                    'end_date': yesterday.strftime('%Y-%m-%d')
                }
            }
        elif filter_name == 'this_week':
            start_week = today - timedelta(days=today.weekday())
            return {
                'date_range': {
                    'start_date': start_week.strftime('%Y-%m-%d'),
                    'end_date': today.strftime('%Y-%m-%d')
                }
            }
        elif filter_name == 'this_month':
            start_month = today.replace(day=1)
            return {
                'date_range': {
                    'start_date': start_month.strftime('%Y-%m-%d'),
                    'end_date': today.strftime('%Y-%m-%d')
                }
            }
        elif filter_name == 'last_month':
            if today.month == 1:
                start_last_month = today.replace(year=today.year-1, month=12, day=1)
            else:
                start_last_month = today.replace(month=today.month-1, day=1)
            
            if today.month == 1:
                end_last_month = today.replace(year=today.year-1, month=12, day=31)
            else:
                if today.month in [1, 3, 5, 7, 8, 10, 12]:
                    end_last_month = today.replace(month=today.month-1, day=31)
                elif today.month in [4, 6, 9, 11]:
                    end_last_month = today.replace(month=today.month-1, day=30)
                else:
                    end_last_month = today.replace(month=today.month-1, day=28)
            
            return {
                'date_range': {
                    'start_date': start_last_month.strftime('%Y-%m-%d'),
                    'end_date': end_last_month.strftime('%Y-%m-%d')
                }
            }
        elif filter_name == 'last_30_days':
            start_date = today - timedelta(days=30)
            return {
                'date_range': {
                    'start_date': start_date.strftime('%Y-%m-%d'),
                    'end_date': today.strftime('%Y-%m-%d')
                }
            }
        elif filter_name == 'last_90_days':
            start_date = today - timedelta(days=90)
            return {
                'date_range': {
                    'start_date': start_date.strftime('%Y-%m-%d'),
                    'end_date': today.strftime('%Y-%m-%d')
                }
            }
        
        return {}
    
    def get_search_analytics(self) -> Dict:
        """Get search analytics"""
        conn = db_manager.db_path
        import sqlite3
        
        conn = sqlite3.connect(conn)
        cursor = conn.cursor()
        
        # Most searched terms
        cursor.execute('''
            SELECT search_term, COUNT(*) as count
            FROM search_history
            GROUP BY search_term
            ORDER BY count DESC
            LIMIT 10
        ''')
        popular_searches = cursor.fetchall()
        
        # Search by type
        cursor.execute('''
            SELECT search_type, COUNT(*) as count
            FROM search_history
            GROUP BY search_type
        ''')
        search_by_type = cursor.fetchall()
        
        # Recent searches
        cursor.execute('''
            SELECT search_term, search_type, created_at
            FROM search_history
            ORDER BY created_at DESC
            LIMIT 20
        ''')
        recent_searches = cursor.fetchall()
        
        conn.close()
        
        return {
            'popular_searches': popular_searches,
            'search_by_type': search_by_type,
            'recent_searches': recent_searches
        }
    
    def save_search_query(self, query: str, search_type: str, filters: Dict = None):
        """Save search query for later use"""
        conn = db_manager.db_path
        import sqlite3
        
        conn = sqlite3.connect(conn)
        cursor = conn.cursor()
        
        # Create saved searches table if not exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS saved_searches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                query TEXT NOT NULL,
                search_type TEXT NOT NULL,
                filters TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        filters_json = json.dumps(filters) if filters else None
        
        cursor.execute('''
            INSERT INTO saved_searches (name, query, search_type, filters)
            VALUES (?, ?, ?, ?)
        ''', (f"Search: {query[:50]}", query, search_type, filters_json))
        
        conn.commit()
        conn.close()
    
    def get_saved_searches(self) -> List[Dict]:
        """Get saved searches"""
        conn = db_manager.db_path
        import sqlite3
        
        conn = sqlite3.connect(conn)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM saved_searches
            ORDER BY created_at DESC
        ''')
        
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        
        results = []
        for row in rows:
            record = dict(zip(columns, row))
            if record['filters']:
                record['filters'] = json.loads(record['filters'])
            results.append(record)
        
        conn.close()
        return results

# Global instance
advanced_search = AdvancedSearch()

