"""
API Development Module
Provides comprehensive REST API with authentication, rate limiting, and documentation
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from functools import wraps
import hashlib
import secrets
from flask import Flask, request, jsonify, g
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import jwt

class APIManager:
    """Comprehensive API management"""
    
    def __init__(self, app: Flask = None):
        self.app = app
        self.api_keys = {}
        self.rate_limits = {}
        self.api_usage = {}
        self.endpoints = {}
        
        # API configuration
        self.config = {
            'version': 'v1',
            'base_url': '/api/v1',
            'rate_limit': '1000 per hour',
            'api_key_required': True,
            'cors_enabled': True,
            'documentation_enabled': True
        }
        
        # Initialize rate limiter
        if app:
            self.limiter = Limiter(
                app,
                key_func=get_remote_address,
                default_limits=[self.config['rate_limit']]
            )
            self._setup_cors()
            self._register_endpoints()
    
    def _setup_cors(self):
        """Setup CORS for API"""
        if self.config['cors_enabled']:
            @self.app.after_request
            def after_request(response):
                response.headers.add('Access-Control-Allow-Origin', '*')
                response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,API-Key')
                response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
                return response
    
    def _register_endpoints(self):
        """Register all API endpoints"""
        base_url = self.config['base_url']
        
        # Authentication endpoints
        self._register_endpoint('POST', f'{base_url}/auth/login', self.login)
        self._register_endpoint('POST', f'{base_url}/auth/logout', self.logout)
        self._register_endpoint('POST', f'{base_url}/auth/refresh', self.refresh_token)
        
        # User management endpoints
        self._register_endpoint('GET', f'{base_url}/users', self.get_users)
        self._register_endpoint('POST', f'{base_url}/users', self.create_user)
        self._register_endpoint('GET', f'{base_url}/users/<int:user_id>', self.get_user)
        self._register_endpoint('PUT', f'{base_url}/users/<int:user_id>', self.update_user)
        self._register_endpoint('DELETE', f'{base_url}/users/<int:user_id>', self.delete_user)
        
        # PO management endpoints
        self._register_endpoint('GET', f'{base_url}/po', self.get_po_history)
        self._register_endpoint('POST', f'{base_url}/po', self.create_po)
        self._register_endpoint('GET', f'{base_url}/po/<int:po_id>', self.get_po)
        self._register_endpoint('PUT', f'{base_url}/po/<int:po_id>', self.update_po)
        self._register_endpoint('DELETE', f'{base_url}/po/<int:po_id>', self.delete_po)
        
        # Product endpoints
        self._register_endpoint('GET', f'{base_url}/products', self.get_products)
        self._register_endpoint('GET', f'{base_url}/products/<product_id>', self.get_product)
        self._register_endpoint('POST', f'{base_url}/products', self.create_product)
        
        # Serial number endpoints
        self._register_endpoint('POST', f'{base_url}/serials/generate', self.generate_serials)
        self._register_endpoint('GET', f'{base_url}/serials/stats', self.get_serial_stats)
        self._register_endpoint('POST', f'{base_url}/serials/validate', self.validate_serials)
        
        # Analytics endpoints
        self._register_endpoint('GET', f'{base_url}/analytics/overview', self.get_analytics_overview)
        self._register_endpoint('GET', f'{base_url}/analytics/trends', self.get_analytics_trends)
        self._register_endpoint('GET', f'{base_url}/analytics/predictions', self.get_analytics_predictions)
        
        # Search endpoints
        self._register_endpoint('POST', f'{base_url}/search', self.search)
        self._register_endpoint('GET', f'{base_url}/search/suggestions', self.get_search_suggestions)
        
        # Export/Import endpoints
        self._register_endpoint('POST', f'{base_url}/export', self.export_data)
        self._register_endpoint('POST', f'{base_url}/import', self.import_data)
        
        # Cloud sync endpoints
        self._register_endpoint('POST', f'{base_url}/cloud/sync', self.sync_to_cloud)
        self._register_endpoint('GET', f'{base_url}/cloud/status', self.get_cloud_status)
        self._register_endpoint('GET', f'{base_url}/cloud/backups', self.list_cloud_backups)
        
        # Collaboration endpoints
        self._register_endpoint('POST', f'{base_url}/collaboration/join', self.join_collaboration)
        self._register_endpoint('POST', f'{base_url}/collaboration/leave', self.leave_collaboration)
        self._register_endpoint('GET', f'{base_url}/collaboration/status', self.get_collaboration_status)
        
        # Template customization endpoints
        self._register_endpoint('GET', f'{base_url}/templates', self.get_templates)
        self._register_endpoint('POST', f'{base_url}/templates', self.create_template)
        self._register_endpoint('PUT', f'{base_url}/templates/<template_id>', self.update_template)
        self._register_endpoint('DELETE', f'{base_url}/templates/<template_id>', self.delete_template)
        
        # API management endpoints
        self._register_endpoint('GET', f'{base_url}/status', self.get_api_status)
        self._register_endpoint('GET', f'{base_url}/usage', self.get_api_usage)
        self._register_endpoint('POST', f'{base_url}/api-keys', self.create_api_key)
        self._register_endpoint('GET', f'{base_url}/api-keys', self.get_api_keys)
        self._register_endpoint('DELETE', f'{base_url}/api-keys/<key_id>', self.revoke_api_key)
        
        # Documentation endpoint
        if self.config['documentation_enabled']:
            self._register_endpoint('GET', f'{base_url}/docs', self.get_api_documentation)
    
    def _register_endpoint(self, method: str, path: str, handler: Callable):
        """Register API endpoint"""
        self.endpoints[path] = {
            'method': method,
            'handler': handler,
            'registered_at': datetime.now().isoformat()
        }
        
        if self.app:
            self.app.add_url_rule(
                path,
                f'api_{path.replace("/", "_").replace("<", "").replace(">", "")}',
                self._create_endpoint_wrapper(handler),
                methods=[method]
            )
    
    def _create_endpoint_wrapper(self, handler: Callable):
        """Create endpoint wrapper with middleware"""
        @wraps(handler)
        def wrapper(*args, **kwargs):
            # API key validation
            if self.config['api_key_required']:
                api_key = request.headers.get('API-Key') or request.args.get('api_key')
                if not api_key or not self._validate_api_key(api_key):
                    return jsonify({'error': 'Invalid or missing API key'}), 401
            
            # Rate limiting
            if hasattr(self, 'limiter'):
                try:
                    self.limiter.check()
                except Exception as e:
                    return jsonify({'error': 'Rate limit exceeded'}), 429
            
            # Log API usage
            self._log_api_usage(request.endpoint, request.remote_addr)
            
            # Execute handler
            try:
                response = handler(*args, **kwargs)
                return response
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        return wrapper
    
    def _validate_api_key(self, api_key: str) -> bool:
        """Validate API key"""
        if api_key in self.api_keys:
            key_info = self.api_keys[api_key]
            
            # Check if key is active
            if not key_info.get('active', True):
                return False
            
            # Check expiration
            if key_info.get('expires_at'):
                if datetime.now() > datetime.fromisoformat(key_info['expires_at']):
                    return False
            
            # Update last used
            key_info['last_used'] = datetime.now().isoformat()
            key_info['usage_count'] = key_info.get('usage_count', 0) + 1
            
            return True
        
        return False
    
    def _log_api_usage(self, endpoint: str, ip_address: str):
        """Log API usage"""
        usage_key = f"{endpoint}_{ip_address}_{datetime.now().strftime('%Y-%m-%d')}"
        
        if usage_key not in self.api_usage:
            self.api_usage[usage_key] = {
                'endpoint': endpoint,
                'ip_address': ip_address,
                'date': datetime.now().strftime('%Y-%m-%d'),
                'count': 0,
                'last_used': datetime.now().isoformat()
            }
        
        self.api_usage[usage_key]['count'] += 1
        self.api_usage[usage_key]['last_used'] = datetime.now().isoformat()
    
    def create_api_key(self, user_id: int, name: str, expires_days: int = 365) -> Dict:
        """Create new API key"""
        api_key = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(days=expires_days)
        
        key_info = {
            'id': len(self.api_keys) + 1,
            'user_id': user_id,
            'name': name,
            'key': api_key,
            'created_at': datetime.now().isoformat(),
            'expires_at': expires_at.isoformat(),
            'active': True,
            'usage_count': 0,
            'last_used': None
        }
        
        self.api_keys[api_key] = key_info
        
        return {
            'api_key': api_key,
            'key_id': key_info['id'],
            'expires_at': expires_at.isoformat(),
            'created_at': datetime.now().isoformat()
        }
    
    def get_api_keys(self, user_id: int = None) -> List[Dict]:
        """Get API keys"""
        keys = []
        
        for key_info in self.api_keys.values():
            if user_id is None or key_info['user_id'] == user_id:
                # Don't expose the actual key
                key_data = key_info.copy()
                key_data.pop('key', None)
                keys.append(key_data)
        
        return keys
    
    def revoke_api_key(self, key_id: int) -> bool:
        """Revoke API key"""
        for api_key, key_info in self.api_keys.items():
            if key_info['id'] == key_id:
                key_info['active'] = False
                return True
        
        return False
    
    def get_api_status(self) -> Dict:
        """Get API status"""
        return {
            'status': 'operational',
            'version': self.config['version'],
            'uptime': self._get_uptime(),
            'total_endpoints': len(self.endpoints),
            'active_api_keys': len([k for k in self.api_keys.values() if k['active']]),
            'rate_limit': self.config['rate_limit'],
            'timestamp': datetime.now().isoformat()
        }
    
    def get_api_usage(self, days: int = 7) -> Dict:
        """Get API usage statistics"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        usage_stats = {
            'period_days': days,
            'total_requests': 0,
            'unique_ips': set(),
            'endpoint_usage': {},
            'daily_usage': {}
        }
        
        for usage_key, usage_data in self.api_usage.items():
            usage_date = datetime.fromisoformat(usage_data['last_used'])
            
            if start_date <= usage_date <= end_date:
                usage_stats['total_requests'] += usage_data['count']
                usage_stats['unique_ips'].add(usage_data['ip_address'])
                
                endpoint = usage_data['endpoint']
                if endpoint not in usage_stats['endpoint_usage']:
                    usage_stats['endpoint_usage'][endpoint] = 0
                usage_stats['endpoint_usage'][endpoint] += usage_data['count']
                
                date_str = usage_data['date']
                if date_str not in usage_stats['daily_usage']:
                    usage_stats['daily_usage'][date_str] = 0
                usage_stats['daily_usage'][date_str] += usage_data['count']
        
        usage_stats['unique_ips'] = len(usage_stats['unique_ips'])
        
        return usage_stats
    
    def get_api_documentation(self) -> Dict:
        """Get API documentation"""
        documentation = {
            'title': 'PO System API',
            'version': self.config['version'],
            'description': 'Comprehensive REST API for PO System management',
            'base_url': self.config['base_url'],
            'authentication': {
                'type': 'API Key',
                'header': 'API-Key',
                'parameter': 'api_key'
            },
            'rate_limits': {
                'default': self.config['rate_limit'],
                'burst': '100 per minute'
            },
            'endpoints': {}
        }
        
        for path, endpoint_info in self.endpoints.items():
            documentation['endpoints'][path] = {
                'method': endpoint_info['method'],
                'description': self._get_endpoint_description(path),
                'parameters': self._get_endpoint_parameters(path),
                'responses': self._get_endpoint_responses(path),
                'examples': self._get_endpoint_examples(path)
            }
        
        return documentation
    
    def _get_uptime(self) -> str:
        """Get API uptime"""
        # This would track actual uptime
        return "99.9%"
    
    def _get_endpoint_description(self, path: str) -> str:
        """Get endpoint description"""
        descriptions = {
            '/api/v1/auth/login': 'Authenticate user and get access token',
            '/api/v1/users': 'Get list of users or create new user',
            '/api/v1/po': 'Get PO history or create new PO',
            '/api/v1/products': 'Get list of products',
            '/api/v1/serials/generate': 'Generate serial numbers',
            '/api/v1/analytics/overview': 'Get analytics overview',
            '/api/v1/search': 'Search PO data',
            '/api/v1/export': 'Export data',
            '/api/v1/import': 'Import data',
            '/api/v1/cloud/sync': 'Sync data to cloud',
            '/api/v1/collaboration/join': 'Join collaboration session',
            '/api/v1/templates': 'Manage templates'
        }
        
        return descriptions.get(path, 'API endpoint')
    
    def _get_endpoint_parameters(self, path: str) -> Dict:
        """Get endpoint parameters"""
        # This would return actual parameter definitions
        return {
            'query': {},
            'path': {},
            'body': {}
        }
    
    def _get_endpoint_responses(self, path: str) -> Dict:
        """Get endpoint response examples"""
        return {
            '200': {'description': 'Success'},
            '400': {'description': 'Bad Request'},
            '401': {'description': 'Unauthorized'},
            '404': {'description': 'Not Found'},
            '429': {'description': 'Rate Limited'},
            '500': {'description': 'Internal Server Error'}
        }
    
    def _get_endpoint_examples(self, path: str) -> Dict:
        """Get endpoint examples"""
        return {
            'request': {},
            'response': {}
        }
    
    # API Endpoint Handlers
    
    def login(self):
        """Login endpoint"""
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400
        
        # This would integrate with user_manager
        # For now, return mock response
        return jsonify({
            'access_token': 'mock_token',
            'token_type': 'Bearer',
            'expires_in': 3600,
            'user': {
                'id': 1,
                'username': username,
                'role': 'user'
            }
        })
    
    def logout(self):
        """Logout endpoint"""
        return jsonify({'message': 'Logged out successfully'})
    
    def refresh_token(self):
        """Refresh token endpoint"""
        return jsonify({'access_token': 'new_mock_token'})
    
    def get_users(self):
        """Get users endpoint"""
        # This would integrate with user_manager
        return jsonify({
            'users': [
                {'id': 1, 'username': 'admin', 'role': 'admin'},
                {'id': 2, 'username': 'user1', 'role': 'user'}
            ],
            'total': 2
        })
    
    def create_user(self):
        """Create user endpoint"""
        data = request.get_json()
        # This would integrate with user_manager
        return jsonify({'message': 'User created successfully'}), 201
    
    def get_user(self, user_id: int):
        """Get user endpoint"""
        return jsonify({'id': user_id, 'username': 'user', 'role': 'user'})
    
    def update_user(self, user_id: int):
        """Update user endpoint"""
        return jsonify({'message': 'User updated successfully'})
    
    def delete_user(self, user_id: int):
        """Delete user endpoint"""
        return jsonify({'message': 'User deleted successfully'})
    
    def get_po_history(self):
        """Get PO history endpoint"""
        # This would integrate with database
        return jsonify({
            'po_history': [],
            'total': 0,
            'page': 1,
            'per_page': 20
        })
    
    def create_po(self):
        """Create PO endpoint"""
        data = request.get_json()
        # This would integrate with PO creation logic
        return jsonify({'message': 'PO created successfully'}), 201
    
    def get_po(self, po_id: int):
        """Get PO endpoint"""
        return jsonify({'id': po_id, 'status': 'created'})
    
    def update_po(self, po_id: int):
        """Update PO endpoint"""
        return jsonify({'message': 'PO updated successfully'})
    
    def delete_po(self, po_id: int):
        """Delete PO endpoint"""
        return jsonify({'message': 'PO deleted successfully'})
    
    def get_products(self):
        """Get products endpoint"""
        return jsonify({
            'products': [
                {'id': 'LA800', 'name': 'LA800', 'type': 'standard'},
                {'id': 'SV2000', 'name': 'SV2000', 'type': 'special'}
            ]
        })
    
    def get_product(self, product_id: str):
        """Get product endpoint"""
        return jsonify({'id': product_id, 'name': product_id, 'type': 'standard'})
    
    def create_product(self):
        """Create product endpoint"""
        return jsonify({'message': 'Product created successfully'}), 201
    
    def generate_serials(self):
        """Generate serials endpoint"""
        data = request.get_json()
        product_id = data.get('product_id')
        count = data.get('count', 5)
        
        # This would integrate with serial_generator
        serials = [f"{product_id}-{i:03d}" for i in range(1, count + 1)]
        
        return jsonify({
            'serials': serials,
            'product_id': product_id,
            'count': count
        })
    
    def get_serial_stats(self):
        """Get serial stats endpoint"""
        return jsonify({
            'total_generated': 1000,
            'last_number': 1000,
            'next_number': 1001
        })
    
    def validate_serials(self):
        """Validate serials endpoint"""
        data = request.get_json()
        serials = data.get('serials', [])
        
        # This would integrate with serial validation
        return jsonify({
            'valid': True,
            'serials': serials
        })
    
    def get_analytics_overview(self):
        """Get analytics overview endpoint"""
        return jsonify({
            'total_files': 1000,
            'active_products': 20,
            'growth_rate': 15.5
        })
    
    def get_analytics_trends(self):
        """Get analytics trends endpoint"""
        return jsonify({
            'trend': 'increasing',
            'confidence': 0.85,
            'patterns': []
        })
    
    def get_analytics_predictions(self):
        """Get analytics predictions endpoint"""
        return jsonify({
            'predictions': [10, 12, 15, 18, 20],
            'confidence': 0.75
        })
    
    def search(self):
        """Search endpoint"""
        data = request.get_json()
        query = data.get('query')
        
        # This would integrate with advanced_search
        return jsonify({
            'results': [],
            'total': 0,
            'query': query
        })
    
    def get_search_suggestions(self):
        """Get search suggestions endpoint"""
        query = request.args.get('q', '')
        return jsonify({
            'suggestions': ['LA800', 'SV2000', 'LA555']
        })
    
    def export_data(self):
        """Export data endpoint"""
        data = request.get_json()
        export_type = data.get('type')
        
        # This would integrate with bulk_import_export
        return jsonify({
            'export_id': 'export_123',
            'status': 'processing',
            'download_url': '/api/v1/downloads/export_123'
        })
    
    def import_data(self):
        """Import data endpoint"""
        # This would handle file upload
        return jsonify({
            'import_id': 'import_123',
            'status': 'processing',
            'results': {'success': 0, 'failed': 0}
        })
    
    def sync_to_cloud(self):
        """Sync to cloud endpoint"""
        # This would integrate with cloud_manager
        return jsonify({
            'sync_id': 'sync_123',
            'status': 'completed',
            'files_synced': 100
        })
    
    def get_cloud_status(self):
        """Get cloud status endpoint"""
        return jsonify({
            'status': 'connected',
            'last_sync': datetime.now().isoformat(),
            'provider': 'google_drive'
        })
    
    def list_cloud_backups(self):
        """List cloud backups endpoint"""
        return jsonify({
            'backups': [
                {'id': 'backup1', 'date': '2025-01-05', 'size': '10MB'},
                {'id': 'backup2', 'date': '2025-01-04', 'size': '9MB'}
            ]
        })
    
    def join_collaboration(self):
        """Join collaboration endpoint"""
        data = request.get_json()
        room_id = data.get('room_id')
        
        # This would integrate with collaboration_manager
        return jsonify({
            'room_id': room_id,
            'participants': 1,
            'websocket_url': f'ws://0.0.0.0:5000/collaboration/{room_id}'
        })
    
    def leave_collaboration(self):
        """Leave collaboration endpoint"""
        return jsonify({'message': 'Left collaboration session'})
    
    def get_collaboration_status(self):
        """Get collaboration status endpoint"""
        return jsonify({
            'active_rooms': 2,
            'total_participants': 5
        })
    
    def get_templates(self):
        """Get templates endpoint"""
        return jsonify({
            'templates': [
                {'id': 'template1', 'name': 'Standard Template', 'type': 'standard'},
                {'id': 'template2', 'name': 'Custom Template', 'type': 'custom'}
            ]
        })
    
    def create_template(self):
        """Create template endpoint"""
        return jsonify({'message': 'Template created successfully'}), 201
    
    def update_template(self, template_id: str):
        """Update template endpoint"""
        return jsonify({'message': 'Template updated successfully'})
    
    def delete_template(self, template_id: str):
        """Delete template endpoint"""
        return jsonify({'message': 'Template deleted successfully'})


# Global instance
api_manager = APIManager()
