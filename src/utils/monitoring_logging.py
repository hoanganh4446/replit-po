"""
Phase 4: Monitoring & Logging System
Hệ thống monitoring và logging toàn diện cho production
"""

import os
import json
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import sqlite3
from collections import defaultdict, deque
import psutil
import requests

class LogManager:
    def __init__(self, log_dir="logs"):
        self.log_dir = log_dir
        self.log_files = {}
        self.log_levels = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        
        # Tạo thư mục logs
        os.makedirs(log_dir, exist_ok=True)
        
        # Setup logging
        self.setup_logging()
        
        # Log rotation thread
        self.rotation_thread = threading.Thread(target=self._rotate_logs, daemon=True)
        self.rotation_thread.start()
    
    def setup_logging(self):
        """Setup logging configuration"""
        # Main application logger
        self.app_logger = logging.getLogger('po_system')
        self.app_logger.setLevel(logging.INFO)
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # File handler for detailed logs
        file_handler = logging.FileHandler(
            os.path.join(self.log_dir, 'app.log'),
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        
        # Console handler for simple logs
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)
        
        # Add handlers
        self.app_logger.addHandler(file_handler)
        self.app_logger.addHandler(console_handler)
        
        # Error log handler
        error_handler = logging.FileHandler(
            os.path.join(self.log_dir, 'errors.log'),
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        self.app_logger.addHandler(error_handler)
        
        # Security log handler
        security_handler = logging.FileHandler(
            os.path.join(self.log_dir, 'security.log'),
            encoding='utf-8'
        )
        security_handler.setLevel(logging.WARNING)
        security_handler.setFormatter(detailed_formatter)
        
        security_logger = logging.getLogger('security')
        security_logger.addHandler(security_handler)
        security_logger.setLevel(logging.WARNING)
        
        print("Logging system initialized")
    
    def log_user_action(self, user_id: str, action: str, details: Dict[str, Any] = None):
        """Log user actions"""
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id,
            'action': action,
            'details': details or {},
            'ip_address': self._get_client_ip(),
            'user_agent': self._get_user_agent()
        }
        
        self.app_logger.info(f"User Action: {json.dumps(log_data)}")
    
    def log_system_event(self, event_type: str, message: str, level: str = 'INFO'):
        """Log system events"""
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'message': message,
            'level': level
        }
        
        if level == 'ERROR':
            self.app_logger.error(f"System Event: {json.dumps(log_data)}")
        elif level == 'WARNING':
            self.app_logger.warning(f"System Event: {json.dumps(log_data)}")
        else:
            self.app_logger.info(f"System Event: {json.dumps(log_data)}")
    
    def log_performance(self, operation: str, duration: float, details: Dict[str, Any] = None):
        """Log performance metrics"""
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'duration_ms': duration * 1000,
            'details': details or {}
        }
        
        self.app_logger.info(f"Performance: {json.dumps(log_data)}")
    
    def log_security_event(self, event_type: str, severity: str, message: str, details: Dict[str, Any] = None):
        """Log security events"""
        security_logger = logging.getLogger('security')
        
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'severity': severity,
            'message': message,
            'details': details or {},
            'ip_address': self._get_client_ip()
        }
        
        if severity == 'CRITICAL':
            security_logger.critical(f"Security Event: {json.dumps(log_data)}")
        elif severity == 'HIGH':
            security_logger.error(f"Security Event: {json.dumps(log_data)}")
        else:
            security_logger.warning(f"Security Event: {json.dumps(log_data)}")
    
    def _get_client_ip(self):
        """Get client IP address"""
        try:
            # This would be implemented based on your Flask setup
            return "127.0.0.1"  # Placeholder
        except:
            return "unknown"
    
    def _get_user_agent(self):
        """Get user agent"""
        try:
            # This would be implemented based on your Flask setup
            return "Unknown"  # Placeholder
        except:
            return "unknown"
    
    def _rotate_logs(self):
        """Rotate log files (runs in background thread)"""
        while True:
            try:
                time.sleep(86400)  # Check daily
                
                # Rotate files larger than 10MB
                for filename in os.listdir(self.log_dir):
                    if filename.endswith('.log'):
                        filepath = os.path.join(self.log_dir, filename)
                        if os.path.getsize(filepath) > 10 * 1024 * 1024:  # 10MB
                            self._rotate_file(filepath)
                            
            except Exception as e:
                print(f"Log rotation error: {e}")
    
    def _rotate_file(self, filepath: str):
        """Rotate a single log file"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            rotated_path = f"{filepath}.{timestamp}"
            
            os.rename(filepath, rotated_path)
            
            # Compress old log
            import gzip
            with open(rotated_path, 'rb') as f_in:
                with gzip.open(f"{rotated_path}.gz", 'wb') as f_out:
                    f_out.writelines(f_in)
            
            os.remove(rotated_path)
            print(f"Rotated log file: {filepath}")
            
        except Exception as e:
            print(f"Error rotating log file {filepath}: {e}")

class SystemMonitor:
    def __init__(self):
        self.metrics = defaultdict(list)
        self.alerts = []
        self.monitoring_active = True
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self._monitor_system, daemon=True)
        self.monitor_thread.start()
    
    def _monitor_system(self):
        """Monitor system metrics (runs in background thread)"""
        while self.monitoring_active:
            try:
                # Collect system metrics
                metrics = self._collect_metrics()
                
                # Store metrics
                timestamp = datetime.now()
                for key, value in metrics.items():
                    self.metrics[key].append((timestamp, value))
                    
                    # Keep only last 1000 entries
                    if len(self.metrics[key]) > 1000:
                        self.metrics[key] = self.metrics[key][-1000:]
                
                # Check for alerts
                self._check_alerts(metrics)
                
                time.sleep(30)  # Monitor every 30 seconds
                
            except Exception as e:
                print(f"Monitoring error: {e}")
                time.sleep(60)  # Wait longer on error
    
    def _collect_metrics(self):
        """Collect system metrics"""
        metrics = {}
        
        try:
            # CPU usage
            metrics['cpu_percent'] = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            metrics['memory_percent'] = memory.percent
            metrics['memory_available_gb'] = memory.available / (1024**3)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            metrics['disk_percent'] = disk.percent
            metrics['disk_free_gb'] = disk.free / (1024**3)
            
            # Network I/O
            network = psutil.net_io_counters()
            metrics['network_bytes_sent'] = network.bytes_sent
            metrics['network_bytes_recv'] = network.bytes_recv
            
            # Process count
            metrics['process_count'] = len(psutil.pids())
            
            # Load average (Unix only)
            try:
                load_avg = psutil.getloadavg()
                metrics['load_avg_1min'] = load_avg[0]
                metrics['load_avg_5min'] = load_avg[1]
                metrics['load_avg_15min'] = load_avg[2]
            except:
                pass
            
        except Exception as e:
            print(f"Error collecting metrics: {e}")
        
        return metrics
    
    def _check_alerts(self, metrics: Dict[str, Any]):
        """Check for alert conditions"""
        alerts = []
        
        # CPU alert
        if metrics.get('cpu_percent', 0) > 80:
            alerts.append({
                'type': 'cpu_high',
                'severity': 'warning',
                'message': f"High CPU usage: {metrics['cpu_percent']:.1f}%",
                'timestamp': datetime.now().isoformat()
            })
        
        # Memory alert
        if metrics.get('memory_percent', 0) > 85:
            alerts.append({
                'type': 'memory_high',
                'severity': 'warning',
                'message': f"High memory usage: {metrics['memory_percent']:.1f}%",
                'timestamp': datetime.now().isoformat()
            })
        
        # Disk alert
        if metrics.get('disk_percent', 0) > 90:
            alerts.append({
                'type': 'disk_full',
                'severity': 'critical',
                'message': f"Disk space low: {metrics['disk_percent']:.1f}%",
                'timestamp': datetime.now().isoformat()
            })
        
        # Add new alerts
        for alert in alerts:
            self.alerts.append(alert)
            
            # Keep only last 100 alerts
            if len(self.alerts) > 100:
                self.alerts = self.alerts[-100:]
    
    def get_metrics_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get metrics summary for specified hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        summary = {}
        
        for metric_name, data_points in self.metrics.items():
            # Filter data points within time range
            recent_data = [
                (timestamp, value) for timestamp, value in data_points
                if timestamp >= cutoff_time
            ]
            
            if recent_data:
                values = [value for _, value in recent_data]
                summary[metric_name] = {
                    'current': values[-1] if values else 0,
                    'average': sum(values) / len(values),
                    'min': min(values),
                    'max': max(values),
                    'data_points': len(values)
                }
        
        return summary
    
    def get_recent_alerts(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent alerts"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        recent_alerts = [
            alert for alert in self.alerts
            if datetime.fromisoformat(alert['timestamp']) >= cutoff_time
        ]
        
        return recent_alerts
    
    def stop_monitoring(self):
        """Stop system monitoring"""
        self.monitoring_active = False

class HealthChecker:
    def __init__(self):
        self.checks = {}
        self.last_check_results = {}
    
    def register_check(self, name: str, check_func, interval_seconds: int = 300):
        """Register a health check"""
        self.checks[name] = {
            'function': check_func,
            'interval': interval_seconds,
            'last_run': None
        }
    
    def run_health_checks(self) -> Dict[str, Any]:
        """Run all registered health checks"""
        results = {}
        
        for name, check_info in self.checks.items():
            try:
                # Check if it's time to run this check
                now = datetime.now()
                last_run = check_info['last_run']
                
                if last_run is None or (now - last_run).total_seconds() >= check_info['interval']:
                    # Run the check
                    result = check_info['function']()
                    
                    results[name] = {
                        'status': 'healthy' if result else 'unhealthy',
                        'timestamp': now.isoformat(),
                        'details': result if isinstance(result, dict) else {}
                    }
                    
                    # Update last run time
                    check_info['last_run'] = now
                    
            except Exception as e:
                results[name] = {
                    'status': 'error',
                    'timestamp': datetime.now().isoformat(),
                    'error': str(e)
                }
        
        self.last_check_results = results
        return results
    
    def get_overall_health(self) -> Dict[str, Any]:
        """Get overall system health"""
        if not self.last_check_results:
            return {'status': 'unknown', 'message': 'No health checks run yet'}
        
        # Count statuses
        status_counts = defaultdict(int)
        for result in self.last_check_results.values():
            status_counts[result['status']] += 1
        
        total_checks = len(self.last_check_results)
        healthy_checks = status_counts['healthy']
        
        # Determine overall status
        if healthy_checks == total_checks:
            overall_status = 'healthy'
        elif healthy_checks > total_checks // 2:
            overall_status = 'degraded'
        else:
            overall_status = 'unhealthy'
        
        return {
            'status': overall_status,
            'healthy_checks': healthy_checks,
            'total_checks': total_checks,
            'status_counts': dict(status_counts),
            'last_check': max(
                result['timestamp'] for result in self.last_check_results.values()
            ) if self.last_check_results else None
        }

class DatabaseHealthChecker:
    def __init__(self, db_path: str = "po_system.db"):
        self.db_path = db_path
    
    def check_database_connection(self):
        """Check database connection"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            conn.close()
            return True
        except Exception as e:
            return {'error': str(e)}
    
    def check_database_size(self):
        """Check database size"""
        try:
            size_bytes = os.path.getsize(self.db_path)
            size_mb = size_bytes / (1024 * 1024)
            
            return {
                'size_mb': size_mb,
                'status': 'ok' if size_mb < 1000 else 'warning'  # Warning if > 1GB
            }
        except Exception as e:
            return {'error': str(e)}
    
    def check_database_integrity(self):
        """Check database integrity"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()
            conn.close()
            
            return result[0] == 'ok'
        except Exception as e:
            return {'error': str(e)}

# Global instances
log_manager = LogManager()
system_monitor = SystemMonitor()
health_checker = HealthChecker()

# Register default health checks
db_health_checker = DatabaseHealthChecker()
health_checker.register_check('database_connection', db_health_checker.check_database_connection)
health_checker.register_check('database_size', db_health_checker.check_database_size)
health_checker.register_check('database_integrity', db_health_checker.check_database_integrity)

def init_monitoring_system():
    """Khởi tạo hệ thống monitoring"""
    print("Initializing monitoring and logging system...")
    
    # Log system startup
    log_manager.log_system_event('system_startup', 'Monitoring system initialized')
    
    # Run initial health checks
    health_results = health_checker.run_health_checks()
    log_manager.log_system_event('health_check', f'Initial health check completed: {health_results}')
    
    print("Monitoring and logging system initialized successfully!")
    return health_results

if __name__ == "__main__":
    init_monitoring_system()
    
    # Test logging
    log_manager.log_user_action('test_user', 'login', {'ip': '127.0.0.1'})
    log_manager.log_system_event('test_event', 'Test system event')
    log_manager.log_performance('test_operation', 0.5, {'records': 100})
    
    # Test monitoring
    time.sleep(5)
    metrics = system_monitor.get_metrics_summary()
    print(f"System metrics: {json.dumps(metrics, indent=2)}")
    
    # Test health checks
    health_results = health_checker.run_health_checks()
    print(f"Health check results: {json.dumps(health_results, indent=2)}")
    
    overall_health = health_checker.get_overall_health()
    print(f"Overall health: {json.dumps(overall_health, indent=2)}")
