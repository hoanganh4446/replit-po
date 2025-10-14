"""
Phase 4: Performance Optimization & Caching System
Tối ưu hóa hiệu suất và hệ thống cache cho toàn bộ ứng dụng
"""

import os
import json
import time
import hashlib
import threading
from datetime import datetime, timedelta
from functools import wraps
from typing import Dict, Any, Optional, List
import sqlite3
import pickle
import gzip
from collections import defaultdict

class CacheManager:
    def __init__(self, cache_dir="cache", max_size_mb=100):
        self.cache_dir = cache_dir
        self.max_size_mb = max_size_mb
        self.cache_stats = defaultdict(int)
        self.lock = threading.RLock()
        
        # Tạo thư mục cache
        os.makedirs(cache_dir, exist_ok=True)
        
        # Khởi tạo cache database
        self.init_cache_db()
        
        # Cleanup thread
        self.cleanup_thread = threading.Thread(target=self._cleanup_expired, daemon=True)
        self.cleanup_thread.start()
    
    def init_cache_db(self):
        """Khởi tạo database cho cache management"""
        conn = sqlite3.connect(os.path.join(self.cache_dir, 'cache.db'))
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cache_entries (
                key TEXT PRIMARY KEY,
                value BLOB,
                created_at TIMESTAMP,
                expires_at TIMESTAMP,
                access_count INTEGER DEFAULT 0,
                last_accessed TIMESTAMP,
                size_bytes INTEGER
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_expires_at ON cache_entries(expires_at)
        ''')
        
        conn.commit()
        conn.close()
    
    def _generate_key(self, prefix: str, *args) -> str:
        """Tạo cache key từ arguments"""
        key_data = f"{prefix}:{':'.join(str(arg) for arg in args)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, prefix: str, *args) -> Optional[Any]:
        """Lấy dữ liệu từ cache"""
        with self.lock:
            key = self._generate_key(prefix, *args)
            
            conn = sqlite3.connect(os.path.join(self.cache_dir, 'cache.db'))
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT value, expires_at FROM cache_entries 
                WHERE key = ? AND (expires_at IS NULL OR expires_at > ?)
            ''', (key, datetime.now()))
            
            result = cursor.fetchone()
            
            if result:
                # Update access stats
                cursor.execute('''
                    UPDATE cache_entries 
                    SET access_count = access_count + 1, last_accessed = ?
                    WHERE key = ?
                ''', (datetime.now(), key))
                
                conn.commit()
                conn.close()
                
                # Decompress và deserialize
                compressed_data = result[0]
                data = pickle.loads(gzip.decompress(compressed_data))
                
                self.cache_stats['hits'] += 1
                return data
            
            conn.close()
            self.cache_stats['misses'] += 1
            return None
    
    def set(self, prefix: str, value: Any, *args, ttl_seconds: int = 3600):
        """Lưu dữ liệu vào cache"""
        with self.lock:
            key = self._generate_key(prefix, *args)
            
            # Serialize và compress
            serialized_data = pickle.dumps(value)
            compressed_data = gzip.compress(serialized_data)
            
            expires_at = datetime.now() + timedelta(seconds=ttl_seconds) if ttl_seconds > 0 else None
            
            conn = sqlite3.connect(os.path.join(self.cache_dir, 'cache.db'))
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO cache_entries 
                (key, value, created_at, expires_at, access_count, last_accessed, size_bytes)
                VALUES (?, ?, ?, ?, 0, ?, ?)
            ''', (key, compressed_data, datetime.now(), expires_at, datetime.now(), len(compressed_data)))
            
            conn.commit()
            conn.close()
            
            self.cache_stats['sets'] += 1
    
    def delete(self, prefix: str, *args):
        """Xóa dữ liệu khỏi cache"""
        with self.lock:
            key = self._generate_key(prefix, *args)
            
            conn = sqlite3.connect(os.path.join(self.cache_dir, 'cache.db'))
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM cache_entries WHERE key = ?', (key,))
            
            conn.commit()
            conn.close()
            
            self.cache_stats['deletes'] += 1
    
    def clear(self, prefix: str = None):
        """Xóa tất cả cache hoặc cache theo prefix"""
        with self.lock:
            conn = sqlite3.connect(os.path.join(self.cache_dir, 'cache.db'))
            cursor = conn.cursor()
            
            if prefix:
                # Xóa cache theo pattern
                pattern = f"{prefix}%"
                cursor.execute('DELETE FROM cache_entries WHERE key LIKE ?', (pattern,))
            else:
                cursor.execute('DELETE FROM cache_entries')
            
            conn.commit()
            conn.close()
            
            self.cache_stats['clears'] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Lấy thống kê cache"""
        with self.lock:
            conn = sqlite3.connect(os.path.join(self.cache_dir, 'cache.db'))
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*), SUM(size_bytes) FROM cache_entries')
            count, total_size = cursor.fetchone()
            
            cursor.execute('SELECT COUNT(*) FROM cache_entries WHERE expires_at < ?', (datetime.now(),))
            expired_count = cursor.fetchone()[0]
            
            conn.close()
            
            hit_rate = 0
            if self.cache_stats['hits'] + self.cache_stats['misses'] > 0:
                hit_rate = self.cache_stats['hits'] / (self.cache_stats['hits'] + self.cache_stats['misses'])
            
            return {
                'total_entries': count or 0,
                'total_size_mb': (total_size or 0) / (1024 * 1024),
                'expired_entries': expired_count,
                'hit_rate': hit_rate,
                'stats': dict(self.cache_stats)
            }
    
    def _cleanup_expired(self):
        """Cleanup expired entries (chạy trong background thread)"""
        while True:
            try:
                time.sleep(300)  # Cleanup mỗi 5 phút
                
                conn = sqlite3.connect(os.path.join(self.cache_dir, 'cache.db'))
                cursor = conn.cursor()
                
                cursor.execute('DELETE FROM cache_entries WHERE expires_at < ?', (datetime.now(),))
                deleted = cursor.rowcount
                
                conn.commit()
                conn.close()
                
                if deleted > 0:
                    print(f"Cleaned up {deleted} expired cache entries")
                    
            except Exception as e:
                print(f"Cache cleanup error: {e}")

class PerformanceOptimizer:
    def __init__(self):
        self.cache_manager = CacheManager()
        self.query_cache = {}
        self.template_cache = {}
        self.static_cache = {}
        
    def cache_query(self, ttl_seconds: int = 300):
        """Decorator để cache database queries"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Tạo cache key từ function name và arguments
                cache_key = f"query_{func.__name__}_{hash(str(args) + str(kwargs))}"
                
                # Thử lấy từ cache
                cached_result = self.cache_manager.get("query", cache_key)
                if cached_result is not None:
                    return cached_result
                
                # Thực hiện query và cache kết quả
                result = func(*args, **kwargs)
                self.cache_manager.set("query", result, cache_key, ttl_seconds=ttl_seconds)
                
                return result
            return wrapper
        return decorator
    
    def cache_template(self, ttl_seconds: int = 1800):
        """Decorator để cache template rendering"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                cache_key = f"template_{func.__name__}_{hash(str(args) + str(kwargs))}"
                
                cached_result = self.cache_manager.get("template", cache_key)
                if cached_result is not None:
                    return cached_result
                
                result = func(*args, **kwargs)
                self.cache_manager.set("template", result, cache_key, ttl_seconds=ttl_seconds)
                
                return result
            return wrapper
        return decorator
    
    def optimize_database_queries(self, db_path: str):
        """Tối ưu hóa database queries"""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Enable WAL mode cho better concurrency
        cursor.execute("PRAGMA journal_mode=WAL")
        
        # Enable foreign keys
        cursor.execute("PRAGMA foreign_keys=ON")
        
        # Optimize page size
        cursor.execute("PRAGMA page_size=4096")
        
        # Enable memory-mapped I/O
        cursor.execute("PRAGMA mmap_size=268435456")  # 256MB
        
        # Analyze tables for better query planning
        cursor.execute("ANALYZE")
        
        conn.commit()
        conn.close()
        
        print("Database optimization completed")
    
    def preload_frequent_data(self):
        """Preload dữ liệu thường dùng"""
        print("Preloading frequent data...")
        
        # Preload product configurations
        try:
            from database import DatabaseManager
            db = DatabaseManager()
            
            # Cache product list
            products = db.get_all_products()
            self.cache_manager.set("preload", products, "products", ttl_seconds=3600)
            
            # Cache recent PO history
            recent_pos = db.get_recent_pos(limit=50)
            self.cache_manager.set("preload", recent_pos, "recent_pos", ttl_seconds=1800)
            
            print(f"Preloaded {len(products)} products and {len(recent_pos)} recent POs")
            
        except Exception as e:
            print(f"Preload error: {e}")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Lấy thống kê hiệu suất"""
        cache_stats = self.cache_manager.get_stats()
        
        return {
            'cache_stats': cache_stats,
            'memory_usage': self._get_memory_usage(),
            'optimization_status': 'active'
        }
    
    def _get_memory_usage(self) -> Dict[str, float]:
        """Lấy thông tin sử dụng memory"""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            
            return {
                'rss_mb': memory_info.rss / (1024 * 1024),
                'vms_mb': memory_info.vms / (1024 * 1024),
                'percent': process.memory_percent()
            }
        except ImportError:
            return {'error': 'psutil not available'}

class StaticAssetOptimizer:
    def __init__(self, static_dir="static"):
        self.static_dir = static_dir
        self.compressed_assets = {}
        
    def compress_static_assets(self):
        """Nén static assets"""
        print("Compressing static assets...")
        
        for root, dirs, files in os.walk(self.static_dir):
            for file in files:
                if file.endswith(('.css', '.js', '.html')):
                    file_path = os.path.join(root, file)
                    self._compress_file(file_path)
        
        print(f"Compressed {len(self.compressed_assets)} static assets")
    
    def _compress_file(self, file_path: str):
        """Nén một file"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            
            compressed = gzip.compress(content)
            
            # Lưu file nén
            compressed_path = file_path + '.gz'
            with open(compressed_path, 'wb') as f:
                f.write(compressed)
            
            self.compressed_assets[file_path] = {
                'original_size': len(content),
                'compressed_size': len(compressed),
                'compression_ratio': len(compressed) / len(content)
            }
            
        except Exception as e:
            print(f"Error compressing {file_path}: {e}")
    
    def get_compression_stats(self) -> Dict[str, Any]:
        """Lấy thống kê compression"""
        total_original = sum(info['original_size'] for info in self.compressed_assets.values())
        total_compressed = sum(info['compressed_size'] for info in self.compressed_assets.values())
        
        return {
            'total_files': len(self.compressed_assets),
            'total_original_size_mb': total_original / (1024 * 1024),
            'total_compressed_size_mb': total_compressed / (1024 * 1024),
            'total_savings_mb': (total_original - total_compressed) / (1024 * 1024),
            'compression_ratio': total_compressed / total_original if total_original > 0 else 0
        }

# Global instances
cache_manager = CacheManager()
performance_optimizer = PerformanceOptimizer()
static_optimizer = StaticAssetOptimizer()

def init_performance_optimization():
    """Khởi tạo tối ưu hóa hiệu suất"""
    print("Initializing performance optimization...")
    
    # Optimize database
    performance_optimizer.optimize_database_queries("po_system.db")
    
    # Compress static assets
    static_optimizer.compress_static_assets()
    
    # Preload frequent data
    performance_optimizer.preload_frequent_data()
    
    print("Performance optimization completed!")

if __name__ == "__main__":
    init_performance_optimization()
    
    # Test cache functionality
    print("\nTesting cache functionality...")
    
    # Test basic cache
    cache_manager.set("test", "Hello World", "basic", ttl_seconds=60)
    result = cache_manager.get("test", "basic")
    print(f"Cache test result: {result}")
    
    # Test performance stats
    stats = performance_optimizer.get_performance_stats()
    print(f"Performance stats: {json.dumps(stats, indent=2)}")
    
    # Test compression stats
    compression_stats = static_optimizer.get_compression_stats()
    print(f"Compression stats: {json.dumps(compression_stats, indent=2)}")
