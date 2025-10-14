"""
Cloud Integration Module
Provides cloud storage, sync, and backup capabilities
"""

import json
import os
import hashlib
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import sqlite3
import threading
import time
from pathlib import Path
import zipfile
import tempfile

class CloudManager:
    """Cloud integration and sync management"""
    
    def __init__(self, config: Dict = None):
        self.config = config or self._get_default_config()
        self.sync_status = {
            'last_sync': None,
            'sync_in_progress': False,
            'sync_errors': [],
            'pending_changes': 0
        }
        
        # Cloud providers
        self.providers = {
            'google_drive': GoogleDriveProvider(self.config.get('google_drive', {})),
            'dropbox': DropboxProvider(self.config.get('dropbox', {})),
            'onedrive': OneDriveProvider(self.config.get('onedrive', {})),
            'aws_s3': AWSProvider(self.config.get('aws_s3', {}))
        }
        
        # Sync settings
        self.sync_settings = {
            'auto_sync': True,
            'sync_interval': 300,  # 5 minutes
            'conflict_resolution': 'server_wins',  # server_wins, client_wins, manual
            'encrypt_data': True,
            'compress_data': True,
            'exclude_files': ['.tmp', '.log', '__pycache__']
        }
        
        # Initialize sync thread
        if self.sync_settings['auto_sync']:
            self._start_sync_thread()
    
    def _get_default_config(self) -> Dict:
        """Get default cloud configuration"""
        return {
            'google_drive': {
                'enabled': False,
                'client_id': '',
                'client_secret': '',
                'refresh_token': ''
            },
            'dropbox': {
                'enabled': False,
                'access_token': '',
                'app_key': '',
                'app_secret': ''
            },
            'onedrive': {
                'enabled': False,
                'client_id': '',
                'client_secret': '',
                'refresh_token': ''
            },
            'aws_s3': {
                'enabled': False,
                'access_key': '',
                'secret_key': '',
                'bucket_name': '',
                'region': 'us-east-1'
            }
        }
    
    def setup_provider(self, provider_name: str, credentials: Dict) -> bool:
        """Setup cloud provider with credentials"""
        if provider_name not in self.providers:
            raise ValueError(f"Unsupported provider: {provider_name}")
        
        provider = self.providers[provider_name]
        
        try:
            success = provider.setup(credentials)
            if success:
                self.config[provider_name]['enabled'] = True
                self.config[provider_name].update(credentials)
                self._save_config()
                return True
        except Exception as e:
            print(f"Error setting up {provider_name}: {e}")
        
        return False
    
    def upload_file(self, file_path: str, cloud_path: str = None, 
                   provider: str = None) -> Dict:
        """Upload file to cloud storage"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Determine provider
        if not provider:
            provider = self._get_active_provider()
        
        if not provider:
            raise ValueError("No active cloud provider")
        
        cloud_provider = self.providers[provider]
        
        # Prepare file
        if self.sync_settings['compress_data']:
            file_path = self._compress_file(file_path)
        
        if self.sync_settings['encrypt_data']:
            file_path = self._encrypt_file(file_path)
        
        try:
            result = cloud_provider.upload_file(file_path, cloud_path)
            
            # Update sync status
            self.sync_status['last_sync'] = datetime.now().isoformat()
            
            return {
                'success': True,
                'provider': provider,
                'cloud_path': result.get('path'),
                'file_id': result.get('id'),
                'size': result.get('size'),
                'uploaded_at': datetime.now().isoformat()
            }
        
        except Exception as e:
            self.sync_status['sync_errors'].append({
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'file': file_path
            })
            
            return {
                'success': False,
                'error': str(e),
                'provider': provider
            }
    
    def download_file(self, cloud_path: str, local_path: str = None, 
                     provider: str = None) -> Dict:
        """Download file from cloud storage"""
        # Determine provider
        if not provider:
            provider = self._get_active_provider()
        
        if not provider:
            raise ValueError("No active cloud provider")
        
        cloud_provider = self.providers[provider]
        
        try:
            result = cloud_provider.download_file(cloud_path, local_path)
            
            # Decrypt if needed
            if self.sync_settings['encrypt_data']:
                result['local_path'] = self._decrypt_file(result['local_path'])
            
            # Decompress if needed
            if self.sync_settings['compress_data']:
                result['local_path'] = self._decompress_file(result['local_path'])
            
            return {
                'success': True,
                'provider': provider,
                'local_path': result['local_path'],
                'size': result.get('size'),
                'downloaded_at': datetime.now().isoformat()
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'provider': provider
            }
    
    def sync_database(self, provider: str = None) -> Dict:
        """Sync database to cloud"""
        db_path = "po_system.db"
        
        if not os.path.exists(db_path):
            raise FileNotFoundError("Database not found")
        
        # Create backup
        backup_path = self._create_database_backup(db_path)
        
        try:
            # Upload backup
            result = self.upload_file(backup_path, f"backups/db_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db", provider)
            
            # Clean up backup
            os.remove(backup_path)
            
            return result
        
        except Exception as e:
            # Clean up backup on error
            if os.path.exists(backup_path):
                os.remove(backup_path)
            raise e
    
    def sync_files(self, local_dir: str = "output", provider: str = None) -> Dict:
        """Sync local files to cloud"""
        if not os.path.exists(local_dir):
            raise FileNotFoundError(f"Directory not found: {local_dir}")
        
        results = {
            'success': True,
            'uploaded': [],
            'errors': [],
            'total_files': 0,
            'total_size': 0
        }
        
        # Get active provider
        if not provider:
            provider = self._get_active_provider()
        
        if not provider:
            raise ValueError("No active cloud provider")
        
        cloud_provider = self.providers[provider]
        
        # Walk through directory
        for root, dirs, files in os.walk(local_dir):
            for file in files:
                # Skip excluded files
                if any(file.endswith(ext) for ext in self.sync_settings['exclude_files']):
                    continue
                
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, local_dir)
                cloud_path = f"files/{relative_path}"
                
                try:
                    result = self.upload_file(file_path, cloud_path, provider)
                    
                    if result['success']:
                        results['uploaded'].append({
                            'local_path': file_path,
                            'cloud_path': cloud_path,
                            'size': result.get('size', 0)
                        })
                        results['total_size'] += result.get('size', 0)
                    else:
                        results['errors'].append({
                            'file': file_path,
                            'error': result['error']
                        })
                    
                    results['total_files'] += 1
                
                except Exception as e:
                    results['errors'].append({
                        'file': file_path,
                        'error': str(e)
                    })
                    results['total_files'] += 1
        
        results['success'] = len(results['errors']) == 0
        
        return results
    
    def restore_from_backup(self, backup_id: str, provider: str = None) -> Dict:
        """Restore database from cloud backup"""
        # Determine provider
        if not provider:
            provider = self._get_active_provider()
        
        if not provider:
            raise ValueError("No active cloud provider")
        
        cloud_provider = self.providers[provider]
        
        try:
            # Download backup
            temp_path = tempfile.mktemp(suffix='.db')
            result = self.download_file(f"backups/{backup_id}", temp_path, provider)
            
            if not result['success']:
                return result
            
            # Restore database
            import shutil
            shutil.copy2(temp_path, "po_system.db")
            
            # Clean up
            os.remove(temp_path)
            
            return {
                'success': True,
                'restored_at': datetime.now().isoformat(),
                'backup_id': backup_id
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def list_backups(self, provider: str = None) -> List[Dict]:
        """List available backups"""
        # Determine provider
        if not provider:
            provider = self._get_active_provider()
        
        if not provider:
            raise ValueError("No active cloud provider")
        
        cloud_provider = self.providers[provider]
        
        try:
            return cloud_provider.list_files("backups/")
        except Exception as e:
            return []
    
    def get_sync_status(self) -> Dict:
        """Get current sync status"""
        return {
            'last_sync': self.sync_status['last_sync'],
            'sync_in_progress': self.sync_status['sync_in_progress'],
            'sync_errors': self.sync_status['sync_errors'][-10:],  # Last 10 errors
            'pending_changes': self.sync_status['pending_changes'],
            'active_provider': self._get_active_provider(),
            'auto_sync_enabled': self.sync_settings['auto_sync'],
            'sync_interval': self.sync_settings['sync_interval']
        }
    
    def _get_active_provider(self) -> Optional[str]:
        """Get the first active provider"""
        for provider_name, config in self.config.items():
            if config.get('enabled', False):
                return provider_name
        return None
    
    def _compress_file(self, file_path: str) -> str:
        """Compress file for upload"""
        compressed_path = file_path + '.gz'
        
        import gzip
        with open(file_path, 'rb') as f_in:
            with gzip.open(compressed_path, 'wb') as f_out:
                f_out.write(f_in.read())
        
        return compressed_path
    
    def _decompress_file(self, file_path: str) -> str:
        """Decompress downloaded file"""
        if file_path.endswith('.gz'):
            decompressed_path = file_path[:-3]
            
            import gzip
            with gzip.open(file_path, 'rb') as f_in:
                with open(decompressed_path, 'wb') as f_out:
                    f_out.write(f_in.read())
            
            os.remove(file_path)
            return decompressed_path
        
        return file_path
    
    def _encrypt_file(self, file_path: str) -> str:
        """Encrypt file for secure upload"""
        # Simple encryption using XOR (in production, use proper encryption)
        encrypted_path = file_path + '.enc'
        
        with open(file_path, 'rb') as f_in:
            with open(encrypted_path, 'wb') as f_out:
                key = b'po_system_key_2024'
                key_index = 0
                
                while True:
                    byte = f_in.read(1)
                    if not byte:
                        break
                    
                    encrypted_byte = bytes([byte[0] ^ key[key_index % len(key)]])
                    f_out.write(encrypted_byte)
                    key_index += 1
        
        return encrypted_path
    
    def _decrypt_file(self, file_path: str) -> str:
        """Decrypt downloaded file"""
        if file_path.endswith('.enc'):
            decrypted_path = file_path[:-4]
            
            with open(file_path, 'rb') as f_in:
                with open(decrypted_path, 'wb') as f_out:
                    key = b'po_system_key_2024'
                    key_index = 0
                    
                    while True:
                        byte = f_in.read(1)
                        if not byte:
                            break
                        
                        decrypted_byte = bytes([byte[0] ^ key[key_index % len(key)]])
                        f_out.write(decrypted_byte)
                        key_index += 1
            
            os.remove(file_path)
            return decrypted_path
        
        return file_path
    
    def _create_database_backup(self, db_path: str) -> str:
        """Create database backup"""
        backup_path = f"db_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        
        import shutil
        shutil.copy2(db_path, backup_path)
        
        return backup_path
    
    def _start_sync_thread(self):
        """Start automatic sync thread"""
        def sync_loop():
            while True:
                try:
                    if self.sync_settings['auto_sync']:
                        self._perform_auto_sync()
                    
                    time.sleep(self.sync_settings['sync_interval'])
                
                except Exception as e:
                    print(f"Sync error: {e}")
                    time.sleep(60)  # Wait 1 minute on error
        
        sync_thread = threading.Thread(target=sync_loop, daemon=True)
        sync_thread.start()
    
    def _perform_auto_sync(self):
        """Perform automatic sync"""
        if self.sync_status['sync_in_progress']:
            return
        
        self.sync_status['sync_in_progress'] = True
        
        try:
            # Sync database
            self.sync_database()
            
            # Sync files
            self.sync_files()
            
            self.sync_status['last_sync'] = datetime.now().isoformat()
            self.sync_status['pending_changes'] = 0
        
        except Exception as e:
            self.sync_status['sync_errors'].append({
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'type': 'auto_sync'
            })
        
        finally:
            self.sync_status['sync_in_progress'] = False
    
    def _save_config(self):
        """Save configuration to file"""
        with open('cloud_config.json', 'w') as f:
            json.dump(self.config, f, indent=2)


class CloudProvider:
    """Base class for cloud providers"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.authenticated = False
    
    def setup(self, credentials: Dict) -> bool:
        """Setup provider with credentials"""
        raise NotImplementedError
    
    def upload_file(self, file_path: str, cloud_path: str) -> Dict:
        """Upload file to cloud"""
        raise NotImplementedError
    
    def download_file(self, cloud_path: str, local_path: str) -> Dict:
        """Download file from cloud"""
        raise NotImplementedError
    
    def list_files(self, path: str) -> List[Dict]:
        """List files in cloud path"""
        raise NotImplementedError


class GoogleDriveProvider(CloudProvider):
    """Google Drive integration"""
    
    def setup(self, credentials: Dict) -> bool:
        """Setup Google Drive with OAuth credentials"""
        # This would implement Google Drive OAuth flow
        # For now, just store credentials
        self.config.update(credentials)
        self.authenticated = True
        return True
    
    def upload_file(self, file_path: str, cloud_path: str) -> Dict:
        """Upload file to Google Drive"""
        # Mock implementation
        return {
            'id': f"gdrive_{hashlib.md5(file_path.encode()).hexdigest()}",
            'path': cloud_path,
            'size': os.path.getsize(file_path)
        }
    
    def download_file(self, cloud_path: str, local_path: str) -> Dict:
        """Download file from Google Drive"""
        # Mock implementation
        return {
            'local_path': local_path,
            'size': 1024
        }
    
    def list_files(self, path: str) -> List[Dict]:
        """List files in Google Drive path"""
        # Mock implementation
        return [
            {
                'id': 'file1',
                'name': 'backup1.db',
                'size': 1024000,
                'created_at': '2025-01-05T10:00:00Z'
            }
        ]


class DropboxProvider(CloudProvider):
    """Dropbox integration"""
    
    def setup(self, credentials: Dict) -> bool:
        """Setup Dropbox with API credentials"""
        self.config.update(credentials)
        self.authenticated = True
        return True
    
    def upload_file(self, file_path: str, cloud_path: str) -> Dict:
        """Upload file to Dropbox"""
        # Mock implementation
        return {
            'id': f"dropbox_{hashlib.md5(file_path.encode()).hexdigest()}",
            'path': cloud_path,
            'size': os.path.getsize(file_path)
        }
    
    def download_file(self, cloud_path: str, local_path: str) -> Dict:
        """Download file from Dropbox"""
        # Mock implementation
        return {
            'local_path': local_path,
            'size': 1024
        }
    
    def list_files(self, path: str) -> List[Dict]:
        """List files in Dropbox path"""
        # Mock implementation
        return [
            {
                'id': 'file1',
                'name': 'backup1.db',
                'size': 1024000,
                'created_at': '2025-01-05T10:00:00Z'
            }
        ]


class OneDriveProvider(CloudProvider):
    """OneDrive integration"""
    
    def setup(self, credentials: Dict) -> bool:
        """Setup OneDrive with OAuth credentials"""
        self.config.update(credentials)
        self.authenticated = True
        return True
    
    def upload_file(self, file_path: str, cloud_path: str) -> Dict:
        """Upload file to OneDrive"""
        # Mock implementation
        return {
            'id': f"onedrive_{hashlib.md5(file_path.encode()).hexdigest()}",
            'path': cloud_path,
            'size': os.path.getsize(file_path)
        }
    
    def download_file(self, cloud_path: str, local_path: str) -> Dict:
        """Download file from OneDrive"""
        # Mock implementation
        return {
            'local_path': local_path,
            'size': 1024
        }
    
    def list_files(self, path: str) -> List[Dict]:
        """List files in OneDrive path"""
        # Mock implementation
        return [
            {
                'id': 'file1',
                'name': 'backup1.db',
                'size': 1024000,
                'created_at': '2025-01-05T10:00:00Z'
            }
        ]


class AWSProvider(CloudProvider):
    """AWS S3 integration"""
    
    def setup(self, credentials: Dict) -> bool:
        """Setup AWS S3 with credentials"""
        self.config.update(credentials)
        self.authenticated = True
        return True
    
    def upload_file(self, file_path: str, cloud_path: str) -> Dict:
        """Upload file to S3"""
        # Mock implementation
        return {
            'id': f"s3_{hashlib.md5(file_path.encode()).hexdigest()}",
            'path': cloud_path,
            'size': os.path.getsize(file_path)
        }
    
    def download_file(self, cloud_path: str, local_path: str) -> Dict:
        """Download file from S3"""
        # Mock implementation
        return {
            'local_path': local_path,
            'size': 1024
        }
    
    def list_files(self, path: str) -> List[Dict]:
        """List files in S3 path"""
        # Mock implementation
        return [
            {
                'id': 'file1',
                'name': 'backup1.db',
                'size': 1024000,
                'created_at': '2025-01-05T10:00:00Z'
            }
        ]


# Global instance
cloud_manager = CloudManager()
