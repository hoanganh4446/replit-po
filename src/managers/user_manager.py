"""
Multi-user Support Module
Provides user authentication, authorization, and multi-user features
"""

import hashlib
import secrets
import jwt
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import sqlite3
import json
import uuid

class UserManager:
    """User management with authentication and authorization"""
    
    def __init__(self, db_path: str = "po_system.db"):
        self.db_path = db_path
        self.secret_key = "po_system_secret_key_2024_phase3"
        self.init_user_tables()
    
    def init_user_tables(self):
        """Initialize user-related tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                first_name TEXT,
                last_name TEXT,
                role TEXT DEFAULT 'user',
                is_active BOOLEAN DEFAULT 1,
                is_verified BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                login_count INTEGER DEFAULT 0,
                preferences TEXT DEFAULT '{}'
            )
        ''')
        
        # User sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_token TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # User roles table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                permissions TEXT DEFAULT '[]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # User activities table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                activity_type TEXT NOT NULL,
                description TEXT,
                ip_address TEXT,
                user_agent TEXT,
                metadata TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # User permissions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                permission TEXT NOT NULL,
                resource TEXT,
                granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                granted_by INTEGER,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (granted_by) REFERENCES users (id)
            )
        ''')
        
        # Insert default roles
        default_roles = [
            ('admin', 'Administrator', '["all"]'),
            ('manager', 'Manager', '["read", "write", "export", "import"]'),
            ('user', 'Regular User', '["read", "write"]'),
            ('viewer', 'Viewer Only', '["read"]')
        ]
        
        for role_name, description, permissions in default_roles:
            cursor.execute('''
                INSERT OR IGNORE INTO user_roles (name, description, permissions)
                VALUES (?, ?, ?)
            ''', (role_name, description, permissions))
        
        conn.commit()
        conn.close()
    
    def hash_password(self, password: str, salt: str = None) -> Tuple[str, str]:
        """Hash password with salt"""
        if salt is None:
            salt = secrets.token_hex(16)
        
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        ).hex()
        
        return password_hash, salt
    
    def verify_password(self, password: str, password_hash: str, salt: str) -> bool:
        """Verify password against hash"""
        computed_hash, _ = self.hash_password(password, salt)
        return computed_hash == password_hash
    
    def create_user(self, username: str, email: str, password: str, 
                   first_name: str = None, last_name: str = None, 
                   role: str = 'user') -> Dict:
        """Create new user"""
        # Check if user already exists
        if self.get_user_by_username(username):
            raise ValueError("Username already exists")
        
        if self.get_user_by_email(email):
            raise ValueError("Email already exists")
        
        # Hash password
        password_hash, salt = self.hash_password(password)
        
        # Create user
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, salt, first_name, last_name, role)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (username, email, password_hash, salt, first_name, last_name, role))
        
        user_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        # Log activity
        self.log_activity(user_id, 'user_created', f"User {username} created")
        
        return self.get_user_by_id(user_id)
    
    def authenticate_user(self, username: str, password: str, 
                          ip_address: str = None, user_agent: str = None) -> Dict:
        """Authenticate user and create session"""
        user = self.get_user_by_username(username)
        if not user:
            raise ValueError("Invalid username or password")
        
        if not user['is_active']:
            raise ValueError("Account is disabled")
        
        if not self.verify_password(password, user['password_hash'], user['salt']):
            raise ValueError("Invalid username or password")
        
        # Update login info
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users 
            SET last_login = CURRENT_TIMESTAMP, login_count = login_count + 1
            WHERE id = ?
        ''', (user['id'],))
        
        conn.commit()
        conn.close()
        
        # Create session
        session_token = self.create_session(user['id'], ip_address, user_agent)
        
        # Log activity
        self.log_activity(user['id'], 'user_login', f"User {username} logged in")
        
        return {
            'user': user,
            'session_token': session_token
        }
    
    def create_session(self, user_id: int, ip_address: str = None, 
                      user_agent: str = None) -> str:
        """Create user session"""
        session_token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(days=7)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO user_sessions (user_id, session_token, expires_at, ip_address, user_agent)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, session_token, expires_at.isoformat(), ip_address, user_agent))
        
        conn.commit()
        conn.close()
        
        return session_token
    
    def validate_session(self, session_token: str) -> Optional[Dict]:
        """Validate session token and return user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT u.*, s.expires_at, s.ip_address, s.user_agent
            FROM users u
            JOIN user_sessions s ON u.id = s.user_id
            WHERE s.session_token = ? AND s.is_active = 1 AND s.expires_at > CURRENT_TIMESTAMP
        ''', (session_token,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        columns = [description[0] for description in cursor.description]
        user = dict(zip(columns, row))
        
        return user
    
    def logout_user(self, session_token: str) -> bool:
        """Logout user by invalidating session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE user_sessions 
            SET is_active = 0 
            WHERE session_token = ?
        ''', (session_token,))
        
        affected_rows = cursor.rowcount
        conn.commit()
        conn.close()
        
        return affected_rows > 0
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        row = cursor.fetchone()
        
        conn.close()
        
        if not row:
            return None
        
        columns = [description[0] for description in cursor.description]
        user = dict(zip(columns, row))
        
        # Remove sensitive data
        user.pop('password_hash', None)
        user.pop('salt', None)
        
        return user
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get user by username"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        row = cursor.fetchone()
        
        conn.close()
        
        if not row:
            return None
        
        columns = [description[0] for description in cursor.description]
        user = dict(zip(columns, row))
        
        return user
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        row = cursor.fetchone()
        
        conn.close()
        
        if not row:
            return None
        
        columns = [description[0] for description in cursor.description]
        user = dict(zip(columns, row))
        
        return user
    
    def update_user(self, user_id: int, updates: Dict) -> Dict:
        """Update user information"""
        allowed_fields = ['first_name', 'last_name', 'email', 'role', 'is_active', 'preferences']
        
        update_fields = []
        update_values = []
        
        for field, value in updates.items():
            if field in allowed_fields:
                update_fields.append(f"{field} = ?")
                update_values.append(value)
        
        if not update_fields:
            raise ValueError("No valid fields to update")
        
        update_values.append(user_id)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = f"UPDATE users SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
        cursor.execute(query, update_values)
        
        conn.commit()
        conn.close()
        
        # Log activity
        self.log_activity(user_id, 'user_updated', f"User updated: {', '.join(update_fields)}")
        
        return self.get_user_by_id(user_id)
    
    def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """Change user password"""
        user = self.get_user_by_username(self.get_user_by_id(user_id)['username'])
        if not user:
            raise ValueError("User not found")
        
        if not self.verify_password(old_password, user['password_hash'], user['salt']):
            raise ValueError("Invalid old password")
        
        password_hash, salt = self.hash_password(new_password)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users 
            SET password_hash = ?, salt = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (password_hash, salt, user_id))
        
        conn.commit()
        conn.close()
        
        # Log activity
        self.log_activity(user_id, 'password_changed', "Password changed")
        
        return True
    
    def get_user_permissions(self, user_id: int) -> List[str]:
        """Get user permissions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get role permissions
        cursor.execute('''
            SELECT ur.permissions
            FROM users u
            JOIN user_roles ur ON u.role = ur.name
            WHERE u.id = ?
        ''', (user_id,))
        
        role_row = cursor.fetchone()
        permissions = []
        
        if role_row:
            role_permissions = json.loads(role_row[0])
            permissions.extend(role_permissions)
        
        # Get additional permissions
        cursor.execute('''
            SELECT permission FROM user_permissions WHERE user_id = ?
        ''', (user_id,))
        
        additional_permissions = [row[0] for row in cursor.fetchall()]
        permissions.extend(additional_permissions)
        
        conn.close()
        
        return list(set(permissions))  # Remove duplicates
    
    def check_permission(self, user_id: int, permission: str, resource: str = None) -> bool:
        """Check if user has specific permission"""
        permissions = self.get_user_permissions(user_id)
        
        if 'all' in permissions:
            return True
        
        if permission in permissions:
            return True
        
        return False
    
    def log_activity(self, user_id: int, activity_type: str, description: str,
                    ip_address: str = None, user_agent: str = None, metadata: Dict = None):
        """Log user activity"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO user_activities (user_id, activity_type, description, ip_address, user_agent, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, activity_type, description, ip_address, user_agent, 
              json.dumps(metadata or {})))
        
        conn.commit()
        conn.close()
    
    def get_user_activities(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Get user activities"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM user_activities 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (user_id, limit))
        
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        
        activities = []
        for row in rows:
            activity = dict(zip(columns, row))
            activity['metadata'] = json.loads(activity['metadata'])
            activities.append(activity)
        
        conn.close()
        
        return activities
    
    def get_all_users(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Get all users"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, email, first_name, last_name, role, is_active, 
                   is_verified, created_at, last_login, login_count
            FROM users 
            ORDER BY created_at DESC 
            LIMIT ? OFFSET ?
        ''', (limit, offset))
        
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        
        users = [dict(zip(columns, row)) for row in rows]
        
        conn.close()
        
        return users
    
    def get_user_statistics(self) -> Dict:
        """Get user statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total users
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]
        
        # Active users
        cursor.execute('SELECT COUNT(*) FROM users WHERE is_active = 1')
        active_users = cursor.fetchone()[0]
        
        # Users by role
        cursor.execute('''
            SELECT role, COUNT(*) as count 
            FROM users 
            GROUP BY role
        ''')
        users_by_role = dict(cursor.fetchall())
        
        # Recent logins
        cursor.execute('''
            SELECT COUNT(*) FROM users 
            WHERE last_login > datetime('now', '-7 days')
        ''')
        recent_logins = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'users_by_role': users_by_role,
            'recent_logins': recent_logins
        }
    
    def generate_jwt_token(self, user_id: int) -> str:
        """Generate JWT token for user"""
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(days=1),
            'iat': datetime.utcnow()
        }
        
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def validate_jwt_token(self, token: str) -> Optional[Dict]:
        """Validate JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            user_id = payload['user_id']
            return self.get_user_by_id(user_id)
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE user_sessions 
            SET is_active = 0 
            WHERE expires_at < CURRENT_TIMESTAMP
        ''')
        
        affected_rows = cursor.rowcount
        conn.commit()
        conn.close()
        
        return affected_rows

# Global instance
user_manager = UserManager()
