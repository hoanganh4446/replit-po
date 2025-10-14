"""
Advanced Security Module
Provides comprehensive security features including encryption, audit logging, and threat detection
"""

import hashlib
import hmac
import secrets
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import sqlite3
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import ipaddress
import re

class SecurityManager:
    """Advanced security management"""
    
    def __init__(self, db_path: str = "po_system.db"):
        self.db_path = db_path
        self.encryption_key = None
        self.security_config = self._load_security_config()
        self.threat_detection = ThreatDetector()
        self.audit_logger = AuditLogger(db_path)
        self.access_control = AccessControl(db_path)
        
        # Initialize security tables
        self.init_security_tables()
        
        # Generate encryption key if not exists
        self._ensure_encryption_key()
    
    def init_security_tables(self):
        """Initialize security-related database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Security events table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS security_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                user_id INTEGER,
                ip_address TEXT,
                user_agent TEXT,
                description TEXT NOT NULL,
                metadata TEXT DEFAULT '{}',
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved BOOLEAN DEFAULT 0,
                resolved_at TIMESTAMP,
                resolved_by INTEGER
            )
        ''')
        
        # Failed login attempts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS failed_logins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                ip_address TEXT NOT NULL,
                user_agent TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                attempt_count INTEGER DEFAULT 1
            )
        ''')
        
        # Security policies table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS security_policies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                policy_type TEXT NOT NULL,
                config TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Encryption keys table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS encryption_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key_name TEXT UNIQUE NOT NULL,
                encrypted_key TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # Session security table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS session_security (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                user_id INTEGER NOT NULL,
                ip_address TEXT NOT NULL,
                user_agent_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_suspicious BOOLEAN DEFAULT 0,
                security_score INTEGER DEFAULT 100
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _load_security_config(self) -> Dict:
        """Load security configuration"""
        default_config = {
            'password_policy': {
                'min_length': 8,
                'require_uppercase': True,
                'require_lowercase': True,
                'require_numbers': True,
                'require_special_chars': True,
                'max_age_days': 90,
                'history_count': 5
            },
            'login_security': {
                'max_failed_attempts': 5,
                'lockout_duration_minutes': 30,
                'require_2fa': False,
                'session_timeout_minutes': 60
            },
            'ip_security': {
                'allowed_ips': [],
                'blocked_ips': [],
                'geo_blocking': False,
                'max_requests_per_minute': 100
            },
            'encryption': {
                'encrypt_sensitive_data': True,
                'encryption_algorithm': 'AES-256',
                'key_rotation_days': 30
            },
            'audit_logging': {
                'log_all_events': True,
                'retention_days': 365,
                'log_level': 'INFO'
            },
            'threat_detection': {
                'enable_real_time': True,
                'suspicious_patterns': True,
                'anomaly_detection': True,
                'auto_block_threats': False
            }
        }
        
        try:
            with open('security_config.json', 'r') as f:
                config = json.load(f)
                # Merge with defaults
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
        except FileNotFoundError:
            # Save default config
            with open('security_config.json', 'w') as f:
                json.dump(default_config, f, indent=2)
            return default_config
    
    def _ensure_encryption_key(self):
        """Ensure encryption key exists"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT encrypted_key FROM encryption_keys WHERE key_name = ? AND is_active = 1', 
                      ('main_key',))
        row = cursor.fetchone()
        
        if row:
            # Decrypt the key (in production, use proper key management)
            self.encryption_key = row[0].encode()
        else:
            # Generate new key
            key = Fernet.generate_key()
            cursor.execute('''
                INSERT INTO encryption_keys (key_name, encrypted_key)
                VALUES (?, ?)
            ''', ('main_key', key.decode()))
            conn.commit()
            self.encryption_key = key
        
        conn.close()
    
    def encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        if not self.encryption_key:
            raise ValueError("Encryption key not available")
        
        f = Fernet(self.encryption_key)
        encrypted_data = f.encrypt(data.encode())
        return base64.b64encode(encrypted_data).decode()
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        if not self.encryption_key:
            raise ValueError("Encryption key not available")
        
        try:
            f = Fernet(self.encryption_key)
            decoded_data = base64.b64decode(encrypted_data.encode())
            decrypted_data = f.decrypt(decoded_data)
            return decrypted_data.decode()
        except Exception as e:
            raise ValueError(f"Decryption failed: {str(e)}")
    
    def hash_password(self, password: str, salt: str = None) -> Tuple[str, str]:
        """Hash password with salt"""
        if salt is None:
            salt = secrets.token_hex(16)
        
        # Use PBKDF2 for password hashing
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt.encode(),
            iterations=100000,
        )
        key = base64.b64encode(kdf.derive(password.encode()))
        return key.decode(), salt
    
    def verify_password(self, password: str, password_hash: str, salt: str) -> bool:
        """Verify password against hash"""
        try:
            computed_hash, _ = self.hash_password(password, salt)
            return hmac.compare_digest(computed_hash, password_hash)
        except Exception:
            return False
    
    def validate_password_policy(self, password: str) -> Dict:
        """Validate password against security policy"""
        policy = self.security_config['password_policy']
        errors = []
        
        if len(password) < policy['min_length']:
            errors.append(f"Password must be at least {policy['min_length']} characters")
        
        if policy['require_uppercase'] and not re.search(r'[A-Z]', password):
            errors.append("Password must contain uppercase letters")
        
        if policy['require_lowercase'] and not re.search(r'[a-z]', password):
            errors.append("Password must contain lowercase letters")
        
        if policy['require_numbers'] and not re.search(r'\d', password):
            errors.append("Password must contain numbers")
        
        if policy['require_special_chars'] and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain special characters")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'strength_score': self._calculate_password_strength(password)
        }
    
    def _calculate_password_strength(self, password: str) -> int:
        """Calculate password strength score (0-100)"""
        score = 0
        
        # Length score
        if len(password) >= 8:
            score += 20
        if len(password) >= 12:
            score += 10
        if len(password) >= 16:
            score += 10
        
        # Character variety score
        if re.search(r'[a-z]', password):
            score += 10
        if re.search(r'[A-Z]', password):
            score += 10
        if re.search(r'\d', password):
            score += 10
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            score += 20
        
        # Complexity score
        if len(set(password)) > len(password) * 0.7:
            score += 10
        
        return min(score, 100)
    
    def check_login_security(self, username: str, ip_address: str) -> Dict:
        """Check login security and detect threats"""
        # Check failed login attempts
        failed_attempts = self._get_failed_login_attempts(username, ip_address)
        
        # Check IP reputation
        ip_reputation = self.threat_detection.check_ip_reputation(ip_address)
        
        # Check for suspicious patterns
        suspicious_patterns = self.threat_detection.detect_suspicious_patterns(username, ip_address)
        
        # Calculate risk score
        risk_score = self._calculate_login_risk_score(failed_attempts, ip_reputation, suspicious_patterns)
        
        # Determine if login should be blocked
        should_block = risk_score > 80 or failed_attempts >= self.security_config['login_security']['max_failed_attempts']
        
        return {
            'allowed': not should_block,
            'risk_score': risk_score,
            'failed_attempts': failed_attempts,
            'ip_reputation': ip_reputation,
            'suspicious_patterns': suspicious_patterns,
            'reason': 'High risk detected' if should_block else None
        }
    
    def record_failed_login(self, username: str, ip_address: str, user_agent: str = None):
        """Record failed login attempt"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if there's an existing failed attempt
        cursor.execute('''
            SELECT id, attempt_count FROM failed_logins 
            WHERE username = ? AND ip_address = ? 
            AND timestamp > datetime('now', '-30 minutes')
        ''', (username, ip_address))
        
        row = cursor.fetchone()
        
        if row:
            # Update existing attempt
            cursor.execute('''
                UPDATE failed_logins 
                SET attempt_count = attempt_count + 1, timestamp = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (row[0],))
        else:
            # Create new attempt
            cursor.execute('''
                INSERT INTO failed_logins (username, ip_address, user_agent)
                VALUES (?, ?, ?)
            ''', (username, ip_address, user_agent))
        
        conn.commit()
        conn.close()
        
        # Log security event
        self.audit_logger.log_security_event(
            'failed_login',
            'medium',
            username=username,
            ip_address=ip_address,
            description=f"Failed login attempt for user {username}"
        )
    
    def clear_failed_logins(self, username: str, ip_address: str):
        """Clear failed login attempts after successful login"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM failed_logins 
            WHERE username = ? AND ip_address = ?
        ''', (username, ip_address))
        
        conn.commit()
        conn.close()
    
    def _get_failed_login_attempts(self, username: str, ip_address: str) -> int:
        """Get number of failed login attempts"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT attempt_count FROM failed_logins 
            WHERE username = ? AND ip_address = ? 
            AND timestamp > datetime('now', '-30 minutes')
        ''', (username, ip_address))
        
        row = cursor.fetchone()
        conn.close()
        
        return row[0] if row else 0
    
    def _calculate_login_risk_score(self, failed_attempts: int, ip_reputation: Dict, 
                                   suspicious_patterns: List[str]) -> int:
        """Calculate login risk score"""
        score = 0
        
        # Failed attempts score
        score += min(failed_attempts * 15, 60)
        
        # IP reputation score
        if ip_reputation.get('is_malicious', False):
            score += 40
        elif ip_reputation.get('is_suspicious', False):
            score += 20
        
        # Suspicious patterns score
        score += len(suspicious_patterns) * 10
        
        return min(score, 100)
    
    def validate_session_security(self, session_id: str, ip_address: str, 
                                user_agent: str) -> Dict:
        """Validate session security"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM session_security 
            WHERE session_id = ?
        ''', (session_id,))
        
        row = cursor.fetchone()
        
        if not row:
            return {'valid': False, 'reason': 'Session not found'}
        
        columns = [description[0] for description in cursor.description]
        session_data = dict(zip(columns, row))
        
        # Check IP address
        if session_data['ip_address'] != ip_address:
            return {'valid': False, 'reason': 'IP address mismatch'}
        
        # Check user agent
        user_agent_hash = hashlib.sha256(user_agent.encode()).hexdigest()
        if session_data['user_agent_hash'] != user_agent_hash:
            return {'valid': False, 'reason': 'User agent mismatch'}
        
        # Check session timeout
        last_activity = datetime.fromisoformat(session_data['last_activity'])
        timeout_minutes = self.security_config['login_security']['session_timeout_minutes']
        
        if datetime.now() - last_activity > timedelta(minutes=timeout_minutes):
            return {'valid': False, 'reason': 'Session expired'}
        
        # Update last activity
        cursor.execute('''
            UPDATE session_security 
            SET last_activity = CURRENT_TIMESTAMP
            WHERE session_id = ?
        ''', (session_id,))
        
        conn.commit()
        conn.close()
        
        return {'valid': True, 'security_score': session_data['security_score']}
    
    def create_secure_session(self, user_id: int, ip_address: str, user_agent: str) -> str:
        """Create secure session"""
        session_id = secrets.token_urlsafe(32)
        user_agent_hash = hashlib.sha256(user_agent.encode()).hexdigest()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO session_security (session_id, user_id, ip_address, user_agent_hash)
            VALUES (?, ?, ?, ?)
        ''', (session_id, user_id, ip_address, user_agent_hash))
        
        conn.commit()
        conn.close()
        
        return session_id
    
    def get_security_events(self, limit: int = 100, severity: str = None) -> List[Dict]:
        """Get security events"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = 'SELECT * FROM security_events'
        params = []
        
        if severity:
            query += ' WHERE severity = ?'
            params.append(severity)
        
        query += ' ORDER BY timestamp DESC LIMIT ?'
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        columns = [description[0] for description in cursor.description]
        events = []
        
        for row in rows:
            event = dict(zip(columns, row))
            event['metadata'] = json.loads(event['metadata'])
            events.append(event)
        
        conn.close()
        
        return events
    
    def get_security_statistics(self) -> Dict:
        """Get security statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total security events
        cursor.execute('SELECT COUNT(*) FROM security_events')
        total_events = cursor.fetchone()[0]
        
        # Events by severity
        cursor.execute('''
            SELECT severity, COUNT(*) as count 
            FROM security_events 
            GROUP BY severity
        ''')
        events_by_severity = dict(cursor.fetchall())
        
        # Failed login attempts
        cursor.execute('''
            SELECT COUNT(*) FROM failed_logins 
            WHERE timestamp > datetime('now', '-24 hours')
        ''')
        recent_failed_logins = cursor.fetchone()[0]
        
        # Active sessions
        cursor.execute('''
            SELECT COUNT(*) FROM session_security 
            WHERE last_activity > datetime('now', '-1 hour')
        ''')
        active_sessions = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_events': total_events,
            'events_by_severity': events_by_severity,
            'recent_failed_logins': recent_failed_logins,
            'active_sessions': active_sessions,
            'security_score': self._calculate_overall_security_score()
        }
    
    def _calculate_overall_security_score(self) -> int:
        """Calculate overall security score"""
        # This would be a complex calculation based on various security metrics
        # For now, return a mock score
        return 85
    
    def update_security_config(self, updates: Dict):
        """Update security configuration"""
        for key, value in updates.items():
            if key in self.security_config:
                self.security_config[key].update(value)
        
        # Save updated config
        with open('security_config.json', 'w') as f:
            json.dump(self.security_config, f, indent=2)


class ThreatDetector:
    """Threat detection and analysis"""
    
    def __init__(self):
        self.suspicious_patterns = [
            r'admin',
            r'root',
            r'test',
            r'guest',
            r'user\d+',
            r'admin\d+'
        ]
        
        self.malicious_ips = set()  # In production, this would be loaded from threat intelligence feeds
        self.suspicious_ips = set()
    
    def check_ip_reputation(self, ip_address: str) -> Dict:
        """Check IP address reputation"""
        try:
            ip_obj = ipaddress.ip_address(ip_address)
            
            # Check if IP is in malicious list
            if ip_address in self.malicious_ips:
                return {
                    'is_malicious': True,
                    'is_suspicious': True,
                    'reputation_score': 0,
                    'threat_types': ['malware', 'botnet']
                }
            
            # Check if IP is in suspicious list
            if ip_address in self.suspicious_ips:
                return {
                    'is_malicious': False,
                    'is_suspicious': True,
                    'reputation_score': 30,
                    'threat_types': ['suspicious_activity']
                }
            
            # Check for private/local IPs
            if ip_obj.is_private:
                return {
                    'is_malicious': False,
                    'is_suspicious': False,
                    'reputation_score': 80,
                    'threat_types': []
                }
            
            # Default reputation for unknown IPs
            return {
                'is_malicious': False,
                'is_suspicious': False,
                'reputation_score': 50,
                'threat_types': []
            }
        
        except ValueError:
            return {
                'is_malicious': True,
                'is_suspicious': True,
                'reputation_score': 0,
                'threat_types': ['invalid_ip']
            }
    
    def detect_suspicious_patterns(self, username: str, ip_address: str) -> List[str]:
        """Detect suspicious patterns in login attempts"""
        patterns = []
        
        # Check username patterns
        for pattern in self.suspicious_patterns:
            if re.search(pattern, username, re.IGNORECASE):
                patterns.append(f'Suspicious username pattern: {pattern}')
        
        # Check for rapid login attempts (would need more data)
        # Check for unusual login times
        current_hour = datetime.now().hour
        if current_hour < 6 or current_hour > 22:
            patterns.append('Unusual login time')
        
        return patterns
    
    def analyze_user_behavior(self, user_id: int, actions: List[Dict]) -> Dict:
        """Analyze user behavior for anomalies"""
        # This would implement behavioral analysis
        # For now, return mock analysis
        return {
            'anomaly_score': 0,
            'suspicious_activities': [],
            'risk_level': 'low'
        }


class AuditLogger:
    """Audit logging system"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def log_security_event(self, event_type: str, severity: str, 
                          user_id: int = None, ip_address: str = None,
                          user_agent: str = None, description: str = None,
                          metadata: Dict = None):
        """Log security event"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO security_events (event_type, severity, user_id, ip_address, 
                                       user_agent, description, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (event_type, severity, user_id, ip_address, user_agent, 
              description, json.dumps(metadata or {})))
        
        conn.commit()
        conn.close()
    
    def log_user_action(self, user_id: int, action: str, resource: str = None,
                       ip_address: str = None, metadata: Dict = None):
        """Log user action"""
        self.log_security_event(
            'user_action',
            'info',
            user_id=user_id,
            ip_address=ip_address,
            description=f"User {user_id} performed action: {action}",
            metadata={
                'action': action,
                'resource': resource,
                **(metadata or {})
            }
        )
    
    def log_data_access(self, user_id: int, data_type: str, operation: str,
                       ip_address: str = None, metadata: Dict = None):
        """Log data access"""
        self.log_security_event(
            'data_access',
            'info',
            user_id=user_id,
            ip_address=ip_address,
            description=f"User {user_id} accessed {data_type} data",
            metadata={
                'data_type': data_type,
                'operation': operation,
                **(metadata or {})
            }
        )


class AccessControl:
    """Access control and permissions"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def check_permission(self, user_id: int, resource: str, action: str) -> bool:
        """Check if user has permission for resource and action"""
        # This would implement RBAC (Role-Based Access Control)
        # For now, return mock permission check
        return True
    
    def get_user_permissions(self, user_id: int) -> List[str]:
        """Get user permissions"""
        # This would query the database for user permissions
        # For now, return mock permissions
        return ['read', 'write', 'export']
    
    def grant_permission(self, user_id: int, resource: str, action: str) -> bool:
        """Grant permission to user"""
        # This would implement permission granting
        return True
    
    def revoke_permission(self, user_id: int, resource: str, action: str) -> bool:
        """Revoke permission from user"""
        # This would implement permission revocation
        return True


# Global instance
security_manager = SecurityManager()
