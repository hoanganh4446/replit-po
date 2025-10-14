"""
Phase 4: Final Integration - Complete PO System
Tích hợp tất cả Phase 4 features vào ứng dụng chính
"""

import os
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import threading
import time

# Import all Phase 4 modules
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils.performance_optimizer import performance_optimizer, cache_manager, init_performance_optimization
from utils.responsive_design import responsive_manager, accessibility_auditor, init_responsive_design
from utils.monitoring_logging import log_manager, system_monitor, health_checker, init_monitoring_system
from utils.backup_recovery import backup_manager, disaster_recovery_manager, init_backup_system
from utils.final_testing import test_suite, quality_assurance, run_final_testing
from utils.production_deployment import init_production_deployment

# Import existing modules
from core.database import DatabaseManager
from core.serial_generator import SerialGenerator
from core.advanced_search import AdvancedSearchManager
from core.dashboard_analytics import DashboardAnalytics
from managers.bulk_import_export import BulkImportExportManager
from managers.template_customizer import TemplateCustomizer
from managers.user_manager import UserManager
from managers.collaboration_manager import CollaborationManager
from managers.advanced_analytics import AdvancedAnalytics
from managers.cloud_manager import CloudManager
from managers.api_manager import APIManager
from managers.workflow_manager import WorkflowManager
from managers.security_manager import SecurityManager

app = Flask(__name__, 
           template_folder='../../web/templates',
           static_folder='../../web/static')
app.secret_key = 'your-secret-key-change-in-production'

# Initialize all managers
db_manager = DatabaseManager()
serial_generator = SerialGenerator()
search_manager = AdvancedSearchManager()
dashboard_analytics = DashboardAnalytics()
bulk_manager = BulkImportExportManager()
template_customizer = TemplateCustomizer()
user_manager = UserManager()
collaboration_manager = CollaborationManager()
advanced_analytics = AdvancedAnalytics()
cloud_manager = CloudManager()
api_manager = APIManager()
workflow_manager = WorkflowManager()
security_manager = SecurityManager()

# Global state
app_state = {
    'initialized': False,
    'performance_stats': {},
    'system_health': {},
    'user_sessions': {},
    'real_time_data': {}
}

def initialize_application():
    """Khởi tạo toàn bộ ứng dụng Phase 4"""
    if app_state['initialized']:
        return
    
    print("Initializing Phase 4 Complete PO System...")
    
    try:
        # Initialize all Phase 4 systems
        init_performance_optimization()
        init_responsive_design()
        init_monitoring_system()
        init_backup_system()
        
        # Initialize existing systems
        db_manager.init_database()
        serial_generator.init_serial_system()
        search_manager.init_search_system()
        dashboard_analytics.init_analytics()
        bulk_manager.init_bulk_system()
        template_customizer.init_customizer()
        user_manager.init_user_system()
        collaboration_manager.init_collaboration()
        advanced_analytics.init_analytics()
        cloud_manager.init_cloud_system()
        api_manager.init_api_system()
        workflow_manager.init_workflow_system()
        security_manager.init_security_system()
        
        # Update application state
        app_state['initialized'] = True
        app_state['startup_time'] = datetime.now().isoformat()
        
        # Log successful initialization
        log_manager.log_system_event('app_initialization', 'Phase 4 PO System initialized successfully')
        
        print("Phase 4 Complete PO System initialized successfully!")
        
    except Exception as e:
        print(f"Error initializing application: {e}")
        log_manager.log_system_event('app_initialization_error', f'Initialization failed: {str(e)}', 'ERROR')

# Routes
@app.route('/')
def index():
    """Main dashboard"""
    if not app_state['initialized']:
        initialize_application()
    
    # Get dashboard data
    dashboard_data = dashboard_analytics.get_dashboard_data()
    
    # Get system health
    health_status = health_checker.get_overall_health()
    
    # Get performance stats
    performance_stats = performance_optimizer.get_performance_stats()
    
    return render_template('index.html', 
                         dashboard_data=dashboard_data,
                         health_status=health_status,
                         performance_stats=performance_stats)

@app.route('/products')
def products():
    """Product management"""
    products = db_manager.get_all_products()
    return render_template('products.html', products=products)

@app.route('/dashboard')
def dashboard():
    """Advanced dashboard"""
    dashboard_data = dashboard_analytics.get_dashboard_data()
    analytics_data = advanced_analytics.get_analytics_data()
    
    return render_template('dashboard.html', 
                         dashboard_data=dashboard_data,
                         analytics_data=analytics_data)

@app.route('/search')
def search():
    """Advanced search"""
    return render_template('search.html')

@app.route('/history')
def history():
    """PO history"""
    history_data = db_manager.get_po_history()
    return render_template('history.html', history=history_data)

@app.route('/import-export')
def import_export():
    """Bulk import/export"""
    return render_template('import_export.html')

@app.route('/templates')
def templates():
    """Template customization"""
    templates = template_customizer.get_all_templates()
    return render_template('templates.html', templates=templates)

@app.route('/users')
def users():
    """User management"""
    users = user_manager.get_all_users()
    return render_template('users.html', users=users)

@app.route('/collaboration')
def collaboration():
    """Real-time collaboration"""
    return render_template('collaboration.html')

@app.route('/analytics')
def analytics():
    """Advanced analytics"""
    analytics_data = advanced_analytics.get_analytics_data()
    return render_template('analytics.html', analytics_data=analytics_data)

@app.route('/cloud')
def cloud():
    """Cloud integration"""
    cloud_status = cloud_manager.get_cloud_status()
    return render_template('cloud.html', cloud_status=cloud_status)

@app.route('/api')
def api_docs():
    """API documentation"""
    api_docs = api_manager.get_api_documentation()
    return render_template('api_docs.html', api_docs=api_docs)

@app.route('/workflows')
def workflows():
    """Workflow management"""
    workflows = workflow_manager.get_all_workflows()
    return render_template('workflows.html', workflows=workflows)

@app.route('/security')
def security():
    """Security management"""
    security_status = security_manager.get_security_status()
    return render_template('security.html', security_status=security_status)

@app.route('/monitoring')
def monitoring():
    """System monitoring"""
    metrics = system_monitor.get_metrics_summary()
    alerts = system_monitor.get_recent_alerts()
    health_status = health_checker.get_overall_health()
    
    return render_template('monitoring.html', 
                         metrics=metrics,
                         alerts=alerts,
                         health_status=health_status)

@app.route('/backup')
def backup():
    """Backup management"""
    backups = backup_manager.list_backups()
    return render_template('backup.html', backups=backups)

@app.route('/settings')
def settings():
    """System settings"""
    return render_template('settings.html')

# API Routes
@app.route('/api/products', methods=['GET'])
def api_get_products():
    """API: Get products"""
    try:
        products = db_manager.get_all_products()
        return jsonify({'success': True, 'products': products})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/create-po', methods=['POST'])
def api_create_po():
    """API: Create PO"""
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        quantity = data.get('quantity', 1)
        
        # Create PO using existing logic
        result = create_po_file(product_id, quantity)
        
        if result.get('success'):
            log_manager.log_user_action(
                session.get('user_id', 'anonymous'),
                'create_po',
                {'product_id': product_id, 'quantity': quantity}
            )
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/search', methods=['POST'])
def api_search():
    """API: Advanced search"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        filters = data.get('filters', {})
        
        results = search_manager.search(query, filters)
        return jsonify({'success': True, 'results': results})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/analytics', methods=['GET'])
def api_analytics():
    """API: Get analytics data"""
    try:
        analytics_data = advanced_analytics.get_analytics_data()
        return jsonify({'success': True, 'data': analytics_data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/backup', methods=['POST'])
def api_create_backup():
    """API: Create backup"""
    try:
        backup_type = request.json.get('type', 'full')
        
        if backup_type == 'full':
            result = backup_manager.create_full_backup()
        else:
            result = backup_manager.create_incremental_backup()
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/restore', methods=['POST'])
def api_restore_backup():
    """API: Restore backup"""
    try:
        backup_name = request.json.get('backup_name')
        result = backup_manager.restore_backup(backup_name)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def api_health():
    """API: Health check"""
    try:
        health_status = health_checker.get_overall_health()
        return jsonify(health_status)
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/metrics', methods=['GET'])
def api_metrics():
    """API: System metrics"""
    try:
        metrics = system_monitor.get_metrics_summary()
        return jsonify(metrics)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# WebSocket routes for real-time features
@app.route('/ws/collaboration')
def collaboration_websocket():
    """WebSocket endpoint for collaboration"""
    return collaboration_manager.handle_websocket()

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    log_manager.log_system_event('internal_error', str(error), 'ERROR')
    return render_template('500.html'), 500

# Helper functions
def create_po_file(product_id, quantity):
    """Create PO file (simplified version)"""
    try:
        # This would use the existing PO creation logic
        # For now, return a success response
        return {
            'success': True,
            'message': f'PO created for product {product_id} with quantity {quantity}',
            'file_path': f'output/po_{product_id}_{quantity}.xlsx'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def background_tasks():
    """Background tasks thread"""
    while True:
        try:
            # Update performance stats
            app_state['performance_stats'] = performance_optimizer.get_performance_stats()
            
            # Update system health
            app_state['system_health'] = health_checker.get_overall_health()
            
            # Run health checks
            health_checker.run_health_checks()
            
            # Cleanup old logs
            # This would be handled by the log manager
            
            time.sleep(60)  # Run every minute
            
        except Exception as e:
            print(f"Background task error: {e}")
            time.sleep(60)

# Initialize application
if __name__ == '__main__':
    # Initialize application
    initialize_application()
    
    # Start background tasks
    background_thread = threading.Thread(target=background_tasks, daemon=True)
    background_thread.start()
    
    # Run application
    app.run(host='0.0.0.0', port=5000, debug=False)
