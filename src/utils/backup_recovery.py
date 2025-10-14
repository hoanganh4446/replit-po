"""
Phase 4: Backup & Disaster Recovery System
Hệ thống backup và disaster recovery toàn diện
"""

import os
import json
import shutil
import zipfile
import sqlite3
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import hashlib
import schedule

class BackupManager:
    def __init__(self, backup_dir="backups"):
        self.backup_dir = backup_dir
        self.backup_config = {
            'full_backup_interval': 7,  # days
            'incremental_backup_interval': 1,  # days
            'retention_days': 30,
            'compression': True,
            'encryption': False
        }
        
        # Tạo thư mục backup
        os.makedirs(backup_dir, exist_ok=True)
        
        # Backup thread
        self.backup_thread = threading.Thread(target=self._backup_scheduler, daemon=True)
        self.backup_thread.start()
    
    def create_full_backup(self) -> Dict[str, Any]:
        """Tạo full backup"""
        print("Creating full backup...")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"full_backup_{timestamp}"
        backup_path = os.path.join(self.backup_dir, backup_name)
        
        try:
            # Tạo thư mục backup
            os.makedirs(backup_path, exist_ok=True)
            
            # Backup database
            db_backup_path = self._backup_database(backup_path)
            
            # Backup configuration files
            config_backup_path = self._backup_config_files(backup_path)
            
            # Backup templates
            templates_backup_path = self._backup_templates(backup_path)
            
            # Backup static files
            static_backup_path = self._backup_static_files(backup_path)
            
            # Backup logs
            logs_backup_path = self._backup_logs(backup_path)
            
            # Create backup manifest
            manifest = {
                'backup_type': 'full',
                'timestamp': datetime.now().isoformat(),
                'backup_name': backup_name,
                'files': {
                    'database': db_backup_path,
                    'config': config_backup_path,
                    'templates': templates_backup_path,
                    'static': static_backup_path,
                    'logs': logs_backup_path
                },
                'size_bytes': self._calculate_backup_size(backup_path),
                'checksum': self._calculate_checksum(backup_path)
            }
            
            # Save manifest
            manifest_path = os.path.join(backup_path, 'manifest.json')
            with open(manifest_path, 'w', encoding='utf-8') as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False)
            
            # Compress if enabled
            if self.backup_config['compression']:
                compressed_path = f"{backup_path}.zip"
                self._compress_backup(backup_path, compressed_path)
                shutil.rmtree(backup_path)  # Remove uncompressed version
                backup_path = compressed_path
            
            print(f"Full backup created: {backup_path}")
            return manifest
            
        except Exception as e:
            print(f"Error creating full backup: {e}")
            return {'error': str(e)}
    
    def create_incremental_backup(self) -> Dict[str, Any]:
        """Tạo incremental backup"""
        print("Creating incremental backup...")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"incremental_backup_{timestamp}"
        backup_path = os.path.join(self.backup_dir, backup_name)
        
        try:
            # Tạo thư mục backup
            os.makedirs(backup_path, exist_ok=True)
            
            # Get last backup timestamp
            last_backup_time = self._get_last_backup_time()
            
            # Backup only changed files
            changed_files = self._get_changed_files(last_backup_time)
            
            backup_files = []
            for file_path in changed_files:
                backup_file_path = self._backup_file(file_path, backup_path)
                if backup_file_path:
                    backup_files.append(backup_file_path)
            
            # Create backup manifest
            manifest = {
                'backup_type': 'incremental',
                'timestamp': datetime.now().isoformat(),
                'backup_name': backup_name,
                'base_backup': self._get_last_full_backup(),
                'files': backup_files,
                'size_bytes': self._calculate_backup_size(backup_path),
                'checksum': self._calculate_checksum(backup_path)
            }
            
            # Save manifest
            manifest_path = os.path.join(backup_path, 'manifest.json')
            with open(manifest_path, 'w', encoding='utf-8') as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False)
            
            # Compress if enabled
            if self.backup_config['compression']:
                compressed_path = f"{backup_path}.zip"
                self._compress_backup(backup_path, compressed_path)
                shutil.rmtree(backup_path)
                backup_path = compressed_path
            
            print(f"Incremental backup created: {backup_path}")
            return manifest
            
        except Exception as e:
            print(f"Error creating incremental backup: {e}")
            return {'error': str(e)}
    
    def _backup_database(self, backup_path: str) -> str:
        """Backup database"""
        db_path = "po_system.db"
        if os.path.exists(db_path):
            backup_db_path = os.path.join(backup_path, "po_system.db")
            shutil.copy2(db_path, backup_db_path)
            return backup_db_path
        return None
    
    def _backup_config_files(self, backup_path: str) -> List[str]:
        """Backup configuration files"""
        config_files = [
            'requirements.txt',
            'requirements_phase3.txt',
            'config.json',
            'settings.json'
        ]
        
        backed_up_files = []
        for config_file in config_files:
            if os.path.exists(config_file):
                backup_file_path = os.path.join(backup_path, config_file)
                shutil.copy2(config_file, backup_file_path)
                backed_up_files.append(backup_file_path)
        
        return backed_up_files
    
    def _backup_templates(self, backup_path: str) -> str:
        """Backup templates directory"""
        templates_dir = "templates"
        if os.path.exists(templates_dir):
            backup_templates_path = os.path.join(backup_path, "templates")
            shutil.copytree(templates_dir, backup_templates_path)
            return backup_templates_path
        return None
    
    def _backup_static_files(self, backup_path: str) -> str:
        """Backup static files directory"""
        static_dir = "static"
        if os.path.exists(static_dir):
            backup_static_path = os.path.join(backup_path, "static")
            shutil.copytree(static_dir, backup_static_path)
            return backup_static_path
        return None
    
    def _backup_logs(self, backup_path: str) -> str:
        """Backup logs directory"""
        logs_dir = "logs"
        if os.path.exists(logs_dir):
            backup_logs_path = os.path.join(backup_path, "logs")
            shutil.copytree(logs_dir, backup_logs_path)
            return backup_logs_path
        return None
    
    def _backup_file(self, file_path: str, backup_path: str) -> Optional[str]:
        """Backup a single file"""
        try:
            if os.path.exists(file_path):
                # Maintain directory structure
                relative_path = os.path.relpath(file_path)
                backup_file_path = os.path.join(backup_path, relative_path)
                
                # Create directory if needed
                os.makedirs(os.path.dirname(backup_file_path), exist_ok=True)
                
                shutil.copy2(file_path, backup_file_path)
                return backup_file_path
        except Exception as e:
            print(f"Error backing up file {file_path}: {e}")
        
        return None
    
    def _get_changed_files(self, since_time: datetime) -> List[str]:
        """Get files changed since specified time"""
        changed_files = []
        
        # Directories to monitor
        monitor_dirs = ['templates', 'static', 'logs']
        monitor_files = ['po_system.db', 'config.json', 'settings.json']
        
        # Check files
        for file_path in monitor_files:
            if os.path.exists(file_path):
                if datetime.fromtimestamp(os.path.getmtime(file_path)) > since_time:
                    changed_files.append(file_path)
        
        # Check directories
        for dir_path in monitor_dirs:
            if os.path.exists(dir_path):
                for root, dirs, files in os.walk(dir_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        if datetime.fromtimestamp(os.path.getmtime(file_path)) > since_time:
                            changed_files.append(file_path)
        
        return changed_files
    
    def _get_last_backup_time(self) -> datetime:
        """Get timestamp of last backup"""
        try:
            backups = self.list_backups()
            if backups:
                last_backup = max(backups, key=lambda x: x['timestamp'])
                return datetime.fromisoformat(last_backup['timestamp'])
        except:
            pass
        
        # Default to 24 hours ago if no backups found
        return datetime.now() - timedelta(days=1)
    
    def _get_last_full_backup(self) -> Optional[str]:
        """Get name of last full backup"""
        try:
            backups = self.list_backups()
            full_backups = [b for b in backups if b['backup_type'] == 'full']
            if full_backups:
                last_full = max(full_backups, key=lambda x: x['timestamp'])
                return last_full['backup_name']
        except:
            pass
        
        return None
    
    def _calculate_backup_size(self, backup_path: str) -> int:
        """Calculate total size of backup"""
        total_size = 0
        
        if os.path.isfile(backup_path):
            return os.path.getsize(backup_path)
        
        for root, dirs, files in os.walk(backup_path):
            for file in files:
                file_path = os.path.join(root, file)
                total_size += os.path.getsize(file_path)
        
        return total_size
    
    def _calculate_checksum(self, backup_path: str) -> str:
        """Calculate checksum of backup"""
        hasher = hashlib.md5()
        
        if os.path.isfile(backup_path):
            with open(backup_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
        else:
            # Calculate checksum for directory
            for root, dirs, files in os.walk(backup_path):
                for file in sorted(files):  # Sort for consistent checksum
                    file_path = os.path.join(root, file)
                    with open(file_path, 'rb') as f:
                        for chunk in iter(lambda: f.read(4096), b""):
                            hasher.update(chunk)
        
        return hasher.hexdigest()
    
    def _compress_backup(self, source_path: str, target_path: str):
        """Compress backup directory"""
        with zipfile.ZipFile(target_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            if os.path.isfile(source_path):
                zipf.write(source_path, os.path.basename(source_path))
            else:
                for root, dirs, files in os.walk(source_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, source_path)
                        zipf.write(file_path, arcname)
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """List all available backups"""
        backups = []
        
        for item in os.listdir(self.backup_dir):
            item_path = os.path.join(self.backup_dir, item)
            
            if os.path.isdir(item_path):
                manifest_path = os.path.join(item_path, 'manifest.json')
            elif item.endswith('.zip'):
                manifest_path = os.path.join(self.backup_dir, item.replace('.zip', ''), 'manifest.json')
            else:
                continue
            
            if os.path.exists(manifest_path):
                try:
                    with open(manifest_path, 'r', encoding='utf-8') as f:
                        manifest = json.load(f)
                    backups.append(manifest)
                except:
                    pass
        
        return sorted(backups, key=lambda x: x['timestamp'], reverse=True)
    
    def restore_backup(self, backup_name: str) -> Dict[str, Any]:
        """Restore from backup"""
        print(f"Restoring backup: {backup_name}")
        
        try:
            # Find backup
            backups = self.list_backups()
            backup_manifest = None
            
            for backup in backups:
                if backup['backup_name'] == backup_name:
                    backup_manifest = backup
                    break
            
            if not backup_manifest:
                return {'error': f'Backup {backup_name} not found'}
            
            # Determine backup path
            if backup_manifest['backup_type'] == 'full':
                backup_path = os.path.join(self.backup_dir, backup_name)
            else:
                # For incremental, need to restore from base backup first
                base_backup = backup_manifest.get('base_backup')
                if base_backup:
                    self.restore_backup(base_backup)
                backup_path = os.path.join(self.backup_dir, backup_name)
            
            # Check if compressed
            compressed_path = f"{backup_path}.zip"
            if os.path.exists(compressed_path):
                self._decompress_backup(compressed_path, backup_path)
                backup_path = compressed_path.replace('.zip', '')
            
            # Restore files
            restored_files = []
            
            # Restore database
            if 'database' in backup_manifest['files']:
                db_backup_path = backup_manifest['files']['database']
                if os.path.exists(db_backup_path):
                    shutil.copy2(db_backup_path, 'po_system.db')
                    restored_files.append('po_system.db')
            
            # Restore other files
            for file_type, file_path in backup_manifest['files'].items():
                if file_type != 'database' and file_path and os.path.exists(file_path):
                    if os.path.isfile(file_path):
                        shutil.copy2(file_path, os.path.basename(file_path))
                        restored_files.append(os.path.basename(file_path))
                    elif os.path.isdir(file_path):
                        dir_name = os.path.basename(file_path)
                        if os.path.exists(dir_name):
                            shutil.rmtree(dir_name)
                        shutil.copytree(file_path, dir_name)
                        restored_files.append(dir_name)
            
            print(f"Backup restored successfully. Files restored: {restored_files}")
            return {
                'success': True,
                'restored_files': restored_files,
                'backup_name': backup_name
            }
            
        except Exception as e:
            print(f"Error restoring backup: {e}")
            return {'error': str(e)}
    
    def _decompress_backup(self, compressed_path: str, target_path: str):
        """Decompress backup"""
        with zipfile.ZipFile(compressed_path, 'r') as zipf:
            zipf.extractall(target_path)
    
    def cleanup_old_backups(self):
        """Cleanup old backups based on retention policy"""
        print("Cleaning up old backups...")
        
        cutoff_date = datetime.now() - timedelta(days=self.backup_config['retention_days'])
        backups = self.list_backups()
        
        deleted_count = 0
        for backup in backups:
            backup_date = datetime.fromisoformat(backup['timestamp'])
            if backup_date < cutoff_date:
                try:
                    backup_path = os.path.join(self.backup_dir, backup['backup_name'])
                    
                    # Remove directory or zip file
                    if os.path.exists(backup_path):
                        if os.path.isdir(backup_path):
                            shutil.rmtree(backup_path)
                        else:
                            os.remove(backup_path)
                    
                    # Remove compressed version if exists
                    compressed_path = f"{backup_path}.zip"
                    if os.path.exists(compressed_path):
                        os.remove(compressed_path)
                    
                    deleted_count += 1
                    print(f"Deleted old backup: {backup['backup_name']}")
                    
                except Exception as e:
                    print(f"Error deleting backup {backup['backup_name']}: {e}")
        
        print(f"Cleaned up {deleted_count} old backups")
    
    def _backup_scheduler(self):
        """Backup scheduler (runs in background thread)"""
        while True:
            try:
                # Schedule full backup
                schedule.every(self.backup_config['full_backup_interval']).days.at("02:00").do(
                    self.create_full_backup
                )
                
                # Schedule incremental backup
                schedule.every(self.backup_config['incremental_backup_interval']).days.at("03:00").do(
                    self.create_incremental_backup
                )
                
                # Schedule cleanup
                schedule.every().day.at("04:00").do(
                    self.cleanup_old_backups
                )
                
                # Run scheduled tasks
                schedule.run_pending()
                time.sleep(3600)  # Check every hour
                
            except Exception as e:
                print(f"Backup scheduler error: {e}")
                time.sleep(3600)

class DisasterRecoveryManager:
    def __init__(self):
        self.recovery_procedures = {}
        self.recovery_tests = {}
    
    def register_recovery_procedure(self, name: str, procedure_func):
        """Register a disaster recovery procedure"""
        self.recovery_procedures[name] = procedure_func
    
    def test_recovery_procedure(self, name: str) -> Dict[str, Any]:
        """Test a recovery procedure"""
        if name not in self.recovery_procedures:
            return {'error': f'Recovery procedure {name} not found'}
        
        try:
            print(f"Testing recovery procedure: {name}")
            result = self.recovery_procedures[name]()
            
            self.recovery_tests[name] = {
                'last_test': datetime.now().isoformat(),
                'status': 'passed' if result else 'failed',
                'result': result
            }
            
            return {
                'status': 'passed' if result else 'failed',
                'result': result
            }
            
        except Exception as e:
            self.recovery_tests[name] = {
                'last_test': datetime.now().isoformat(),
                'status': 'error',
                'error': str(e)
            }
            
            return {'error': str(e)}
    
    def run_recovery_procedure(self, name: str) -> Dict[str, Any]:
        """Run a recovery procedure"""
        if name not in self.recovery_procedures:
            return {'error': f'Recovery procedure {name} not found'}
        
        try:
            print(f"Running recovery procedure: {name}")
            result = self.recovery_procedures[name]()
            
            return {
                'success': True,
                'result': result
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_recovery_status(self) -> Dict[str, Any]:
        """Get recovery procedures status"""
        return {
            'procedures': list(self.recovery_procedures.keys()),
            'test_results': self.recovery_tests,
            'last_updated': datetime.now().isoformat()
        }

# Global instances
backup_manager = BackupManager()
disaster_recovery_manager = DisasterRecoveryManager()

# Register default recovery procedures
def database_recovery_procedure():
    """Database recovery procedure"""
    try:
        # Check database integrity
        conn = sqlite3.connect('po_system.db')
        cursor = conn.cursor()
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()
        conn.close()
        
        return result[0] == 'ok'
    except:
        return False

def application_recovery_procedure():
    """Application recovery procedure"""
    try:
        # Check if main application files exist
        required_files = ['app.py', 'app_enhanced.py', 'app_phase3.py']
        for file in required_files:
            if not os.path.exists(file):
                return False
        
        return True
    except:
        return False

# Register procedures
disaster_recovery_manager.register_recovery_procedure('database', database_recovery_procedure)
disaster_recovery_manager.register_recovery_procedure('application', application_recovery_procedure)

def init_backup_system():
    """Khởi tạo hệ thống backup"""
    print("Initializing backup and disaster recovery system...")
    
    # Create initial full backup
    backup_result = backup_manager.create_full_backup()
    print(f"Initial backup created: {backup_result}")
    
    # Test recovery procedures
    for procedure_name in disaster_recovery_manager.recovery_procedures.keys():
        test_result = disaster_recovery_manager.test_recovery_procedure(procedure_name)
        print(f"Recovery procedure {procedure_name} test: {test_result}")
    
    print("Backup and disaster recovery system initialized successfully!")
    return backup_result

if __name__ == "__main__":
    init_backup_system()
    
    # Test backup creation
    print("\nTesting backup creation...")
    full_backup = backup_manager.create_full_backup()
    print(f"Full backup result: {json.dumps(full_backup, indent=2)}")
    
    # Test backup listing
    backups = backup_manager.list_backups()
    print(f"Available backups: {len(backups)}")
    
    # Test recovery procedures
    recovery_status = disaster_recovery_manager.get_recovery_status()
    print(f"Recovery status: {json.dumps(recovery_status, indent=2)}")
