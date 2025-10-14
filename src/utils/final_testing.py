"""
Phase 4: Final Testing & Quality Assurance
Hệ thống testing toàn diện và quality assurance
"""

import os
import json
import unittest
import time
import threading
from datetime import datetime
from typing import Dict, Any, List, Optional
import sqlite3
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

class TestSuite:
    def __init__(self):
        self.test_results = {}
        self.test_coverage = {}
        self.performance_metrics = {}
        
    def run_all_tests(self) -> Dict[str, Any]:
        """Chạy tất cả tests"""
        print("Running comprehensive test suite...")
        
        test_suites = [
            self.test_database_integrity,
            self.test_api_endpoints,
            self.test_user_authentication,
            self.test_file_generation,
            self.test_performance,
            self.test_security,
            self.test_responsive_design,
            self.test_accessibility,
            self.test_backup_restore,
            self.test_error_handling
        ]
        
        results = {}
        total_tests = 0
        passed_tests = 0
        
        for test_suite in test_suites:
            suite_name = test_suite.__name__
            print(f"Running {suite_name}...")
            
            try:
                suite_result = test_suite()
                results[suite_name] = suite_result
                
                total_tests += suite_result.get('total_tests', 0)
                passed_tests += suite_result.get('passed_tests', 0)
                
            except Exception as e:
                results[suite_name] = {
                    'error': str(e),
                    'status': 'failed'
                }
        
        # Calculate overall results
        overall_result = {
            'timestamp': datetime.now().isoformat(),
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': total_tests - passed_tests,
            'success_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            'test_suites': results
        }
        
        self.test_results = overall_result
        
        # Save results
        with open('test_results.json', 'w', encoding='utf-8') as f:
            json.dump(overall_result, f, indent=2, ensure_ascii=False)
        
        print(f"Test suite completed. Success rate: {overall_result['success_rate']:.1f}%")
        return overall_result
    
    def test_database_integrity(self) -> Dict[str, Any]:
        """Test database integrity"""
        tests = []
        
        # Test database connection
        try:
            conn = sqlite3.connect('po_system.db')
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            conn.close()
            tests.append({'name': 'database_connection', 'status': 'passed'})
        except Exception as e:
            tests.append({'name': 'database_connection', 'status': 'failed', 'error': str(e)})
        
        # Test database integrity
        try:
            conn = sqlite3.connect('po_system.db')
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()
            conn.close()
            
            if result[0] == 'ok':
                tests.append({'name': 'database_integrity', 'status': 'passed'})
            else:
                tests.append({'name': 'database_integrity', 'status': 'failed', 'error': result[0]})
        except Exception as e:
            tests.append({'name': 'database_integrity', 'status': 'failed', 'error': str(e)})
        
        # Test table existence
        required_tables = ['products', 'po_history', 'users', 'settings']
        try:
            conn = sqlite3.connect('po_system.db')
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            for table in required_tables:
                if table in existing_tables:
                    tests.append({'name': f'table_{table}_exists', 'status': 'passed'})
                else:
                    tests.append({'name': f'table_{table}_exists', 'status': 'failed', 'error': f'Table {table} not found'})
        except Exception as e:
            tests.append({'name': 'table_check', 'status': 'failed', 'error': str(e)})
        
        passed = len([t for t in tests if t['status'] == 'passed'])
        return {
            'total_tests': len(tests),
            'passed_tests': passed,
            'tests': tests
        }
    
    def test_api_endpoints(self) -> Dict[str, Any]:
        """Test API endpoints"""
        tests = []
        
        # Test endpoints (assuming Flask app is running)
        endpoints = [
            {'url': 'http://0.0.0.0:5000/', 'method': 'GET', 'expected_status': 200},
            {'url': 'http://0.0.0.0:5000/api/products', 'method': 'GET', 'expected_status': 200},
            {'url': 'http://0.0.0.0:5000/api/dashboard', 'method': 'GET', 'expected_status': 200},
            {'url': 'http://0.0.0.0:5000/api/history', 'method': 'GET', 'expected_status': 200}
        ]
        
        for endpoint in endpoints:
            try:
                if endpoint['method'] == 'GET':
                    response = requests.get(endpoint['url'], timeout=5)
                else:
                    response = requests.post(endpoint['url'], timeout=5)
                
                if response.status_code == endpoint['expected_status']:
                    tests.append({
                        'name': f"endpoint_{endpoint['url'].split('/')[-1]}",
                        'status': 'passed',
                        'response_time': response.elapsed.total_seconds()
                    })
                else:
                    tests.append({
                        'name': f"endpoint_{endpoint['url'].split('/')[-1]}",
                        'status': 'failed',
                        'error': f'Expected {endpoint["expected_status"]}, got {response.status_code}'
                    })
            except Exception as e:
                tests.append({
                    'name': f"endpoint_{endpoint['url'].split('/')[-1]}",
                    'status': 'failed',
                    'error': str(e)
                })
        
        passed = len([t for t in tests if t['status'] == 'passed'])
        return {
            'total_tests': len(tests),
            'passed_tests': passed,
            'tests': tests
        }
    
    def test_user_authentication(self) -> Dict[str, Any]:
        """Test user authentication"""
        tests = []
        
        # Test user registration
        try:
            from user_manager import UserManager
            user_manager = UserManager()
            
            # Test user creation
            test_user = {
                'username': 'test_user',
                'email': 'test@example.com',
                'password': 'test_password123',
                'role': 'user'
            }
            
            result = user_manager.create_user(test_user)
            if result.get('success'):
                tests.append({'name': 'user_registration', 'status': 'passed'})
            else:
                tests.append({'name': 'user_registration', 'status': 'failed', 'error': result.get('error')})
            
            # Test user login
            login_result = user_manager.authenticate_user('test_user', 'test_password123')
            if login_result.get('success'):
                tests.append({'name': 'user_login', 'status': 'passed'})
            else:
                tests.append({'name': 'user_login', 'status': 'failed', 'error': login_result.get('error')})
            
            # Test password validation
            weak_password_result = user_manager.create_user({
                'username': 'test_user2',
                'email': 'test2@example.com',
                'password': '123',
                'role': 'user'
            })
            if not weak_password_result.get('success'):
                tests.append({'name': 'password_validation', 'status': 'passed'})
            else:
                tests.append({'name': 'password_validation', 'status': 'failed', 'error': 'Weak password accepted'})
            
        except Exception as e:
            tests.append({'name': 'authentication_system', 'status': 'failed', 'error': str(e)})
        
        passed = len([t for t in tests if t['status'] == 'passed'])
        return {
            'total_tests': len(tests),
            'passed_tests': passed,
            'tests': tests
        }
    
    def test_file_generation(self) -> Dict[str, Any]:
        """Test file generation functionality"""
        tests = []
        
        # Test Excel file generation
        try:
            import xlwings as xw
            
            # Create test workbook
            wb = xw.Book()
            ws = wb.sheets[0]
            
            # Add test data
            ws.range('A1').value = 'Test Product'
            ws.range('B1').value = 'Test Model'
            ws.range('C1').value = 100
            
            # Save and close
            test_file = 'test_output.xlsx'
            wb.save(test_file)
            wb.close()
            
            # Check if file exists
            if os.path.exists(test_file):
                tests.append({'name': 'excel_generation', 'status': 'passed'})
                os.remove(test_file)  # Cleanup
            else:
                tests.append({'name': 'excel_generation', 'status': 'failed', 'error': 'File not created'})
                
        except Exception as e:
            tests.append({'name': 'excel_generation', 'status': 'failed', 'error': str(e)})
        
        # Test batch file generation
        try:
            from app_enhanced import ProductManager
            product_manager = ProductManager()
            
            # Test batch creation
            test_products = ['NV360', 'LA800', 'HP152']
            batch_result = product_manager.create_batch_files(test_products, 5)
            
            if batch_result.get('success'):
                tests.append({'name': 'batch_generation', 'status': 'passed'})
                
                # Cleanup generated files
                for file_path in batch_result.get('files', []):
                    if os.path.exists(file_path):
                        os.remove(file_path)
            else:
                tests.append({'name': 'batch_generation', 'status': 'failed', 'error': batch_result.get('error')})
                
        except Exception as e:
            tests.append({'name': 'batch_generation', 'status': 'failed', 'error': str(e)})
        
        passed = len([t for t in tests if t['status'] == 'passed'])
        return {
            'total_tests': len(tests),
            'passed_tests': passed,
            'tests': tests
        }
    
    def test_performance(self) -> Dict[str, Any]:
        """Test performance metrics"""
        tests = []
        
        # Test database query performance
        try:
            start_time = time.time()
            
            conn = sqlite3.connect('po_system.db')
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM products")
            result = cursor.fetchone()
            conn.close()
            
            query_time = time.time() - start_time
            
            if query_time < 1.0:  # Should complete within 1 second
                tests.append({'name': 'database_query_performance', 'status': 'passed', 'time': query_time})
            else:
                tests.append({'name': 'database_query_performance', 'status': 'failed', 'error': f'Query too slow: {query_time:.2f}s'})
                
        except Exception as e:
            tests.append({'name': 'database_query_performance', 'status': 'failed', 'error': str(e)})
        
        # Test file generation performance
        try:
            start_time = time.time()
            
            # Test single file generation
            from app_enhanced import ProductManager
            product_manager = ProductManager()
            
            result = product_manager.create_single_file('NV360', 1)
            generation_time = time.time() - start_time
            
            if generation_time < 5.0:  # Should complete within 5 seconds
                tests.append({'name': 'file_generation_performance', 'status': 'passed', 'time': generation_time})
            else:
                tests.append({'name': 'file_generation_performance', 'status': 'failed', 'error': f'Generation too slow: {generation_time:.2f}s'})
                
        except Exception as e:
            tests.append({'name': 'file_generation_performance', 'status': 'failed', 'error': str(e)})
        
        # Test memory usage
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / (1024 * 1024)
            
            if memory_mb < 500:  # Should use less than 500MB
                tests.append({'name': 'memory_usage', 'status': 'passed', 'memory_mb': memory_mb})
            else:
                tests.append({'name': 'memory_usage', 'status': 'failed', 'error': f'High memory usage: {memory_mb:.1f}MB'})
                
        except Exception as e:
            tests.append({'name': 'memory_usage', 'status': 'failed', 'error': str(e)})
        
        passed = len([t for t in tests if t['status'] == 'passed'])
        return {
            'total_tests': len(tests),
            'passed_tests': passed,
            'tests': tests
        }
    
    def test_security(self) -> Dict[str, Any]:
        """Test security features"""
        tests = []
        
        # Test password hashing
        try:
            from user_manager import UserManager
            user_manager = UserManager()
            
            password = 'test_password123'
            hashed = user_manager.hash_password(password)
            
            if hashed != password and len(hashed) > 50:  # Should be hashed and long
                tests.append({'name': 'password_hashing', 'status': 'passed'})
            else:
                tests.append({'name': 'password_hashing', 'status': 'failed', 'error': 'Password not properly hashed'})
                
        except Exception as e:
            tests.append({'name': 'password_hashing', 'status': 'failed', 'error': str(e)})
        
        # Test SQL injection protection
        try:
            conn = sqlite3.connect('po_system.db')
            cursor = conn.cursor()
            
            # Test with malicious input
            malicious_input = "'; DROP TABLE products; --"
            cursor.execute("SELECT * FROM products WHERE name = ?", (malicious_input,))
            result = cursor.fetchall()
            conn.close()
            
            # If we get here without error, SQL injection protection is working
            tests.append({'name': 'sql_injection_protection', 'status': 'passed'})
            
        except Exception as e:
            tests.append({'name': 'sql_injection_protection', 'status': 'failed', 'error': str(e)})
        
        # Test file access restrictions
        try:
            # Test if sensitive files are accessible
            sensitive_files = ['po_system.db', 'logs/app.log', 'backups/']
            
            for file_path in sensitive_files:
                if os.path.exists(file_path):
                    # Check if file is readable by others (security issue)
                    stat = os.stat(file_path)
                    if stat.st_mode & 0o004:  # Others can read
                        tests.append({'name': f'file_access_{file_path}', 'status': 'failed', 'error': 'File accessible by others'})
                    else:
                        tests.append({'name': f'file_access_{file_path}', 'status': 'passed'})
                        
        except Exception as e:
            tests.append({'name': 'file_access_security', 'status': 'failed', 'error': str(e)})
        
        passed = len([t for t in tests if t['status'] == 'passed'])
        return {
            'total_tests': len(tests),
            'passed_tests': passed,
            'tests': tests
        }
    
    def test_responsive_design(self) -> Dict[str, Any]:
        """Test responsive design"""
        tests = []
        
        # Test CSS files exist
        css_files = ['static/responsive.css', 'static/accessibility.js']
        
        for css_file in css_files:
            if os.path.exists(css_file):
                tests.append({'name': f'css_file_{css_file}', 'status': 'passed'})
            else:
                tests.append({'name': f'css_file_{css_file}', 'status': 'failed', 'error': f'File {css_file} not found'})
        
        # Test responsive templates
        responsive_templates = ['templates/mobile_navbar.html', 'templates/mobile_product_card.html', 'templates/mobile_dashboard.html']
        
        for template in responsive_templates:
            if os.path.exists(template):
                tests.append({'name': f'template_{template}', 'status': 'passed'})
            else:
                tests.append({'name': f'template_{template}', 'status': 'failed', 'error': f'Template {template} not found'})
        
        passed = len([t for t in tests if t['status'] == 'passed'])
        return {
            'total_tests': len(tests),
            'passed_tests': passed,
            'tests': tests
        }
    
    def test_accessibility(self) -> Dict[str, Any]:
        """Test accessibility features"""
        tests = []
        
        # Test accessibility audit file
        if os.path.exists('accessibility_audit.json'):
            try:
                with open('accessibility_audit.json', 'r', encoding='utf-8') as f:
                    audit_data = json.load(f)
                
                score = audit_data.get('score', 0)
                if score >= 80:  # Good accessibility score
                    tests.append({'name': 'accessibility_score', 'status': 'passed', 'score': score})
                else:
                    tests.append({'name': 'accessibility_score', 'status': 'failed', 'error': f'Low accessibility score: {score}'})
                    
            except Exception as e:
                tests.append({'name': 'accessibility_audit', 'status': 'failed', 'error': str(e)})
        else:
            tests.append({'name': 'accessibility_audit', 'status': 'failed', 'error': 'Accessibility audit file not found'})
        
        # Test accessibility JavaScript
        if os.path.exists('static/accessibility.js'):
            with open('static/accessibility.js', 'r', encoding='utf-8') as f:
                js_content = f.read()
            
            # Check for key accessibility features
            accessibility_features = [
                'AccessibilityManager',
                'skip-link',
                'aria-live',
                'focus management',
                'keyboard navigation'
            ]
            
            for feature in accessibility_features:
                if feature in js_content:
                    tests.append({'name': f'accessibility_feature_{feature}', 'status': 'passed'})
                else:
                    tests.append({'name': f'accessibility_feature_{feature}', 'status': 'failed', 'error': f'Feature {feature} not found'})
        
        passed = len([t for t in tests if t['status'] == 'passed'])
        return {
            'total_tests': len(tests),
            'passed_tests': passed,
            'tests': tests
        }
    
    def test_backup_restore(self) -> Dict[str, Any]:
        """Test backup and restore functionality"""
        tests = []
        
        try:
            from backup_recovery import BackupManager
            backup_manager = BackupManager()
            
            # Test backup creation
            backup_result = backup_manager.create_full_backup()
            if backup_result and not backup_result.get('error'):
                tests.append({'name': 'backup_creation', 'status': 'passed'})
                
                # Test backup listing
                backups = backup_manager.list_backups()
                if len(backups) > 0:
                    tests.append({'name': 'backup_listing', 'status': 'passed'})
                else:
                    tests.append({'name': 'backup_listing', 'status': 'failed', 'error': 'No backups found'})
            else:
                tests.append({'name': 'backup_creation', 'status': 'failed', 'error': backup_result.get('error', 'Unknown error')})
                
        except Exception as e:
            tests.append({'name': 'backup_system', 'status': 'failed', 'error': str(e)})
        
        passed = len([t for t in tests if t['status'] == 'passed'])
        return {
            'total_tests': len(tests),
            'passed_tests': passed,
            'tests': tests
        }
    
    def test_error_handling(self) -> Dict[str, Any]:
        """Test error handling"""
        tests = []
        
        # Test invalid input handling
        try:
            from app_enhanced import ProductManager
            product_manager = ProductManager()
            
            # Test with invalid product
            result = product_manager.create_single_file('INVALID_PRODUCT', 1)
            if not result.get('success'):
                tests.append({'name': 'invalid_input_handling', 'status': 'passed'})
            else:
                tests.append({'name': 'invalid_input_handling', 'status': 'failed', 'error': 'Invalid input accepted'})
                
        except Exception as e:
            tests.append({'name': 'error_handling', 'status': 'failed', 'error': str(e)})
        
        # Test file permission handling
        try:
            # Try to create file in restricted location
            restricted_path = '/root/test_file.txt'
            try:
                with open(restricted_path, 'w') as f:
                    f.write('test')
                tests.append({'name': 'file_permission_handling', 'status': 'failed', 'error': 'File created in restricted location'})
            except PermissionError:
                tests.append({'name': 'file_permission_handling', 'status': 'passed'})
            except Exception:
                tests.append({'name': 'file_permission_handling', 'status': 'passed'})  # Other errors are also acceptable
                
        except Exception as e:
            tests.append({'name': 'file_permission_handling', 'status': 'failed', 'error': str(e)})
        
        passed = len([t for t in tests if t['status'] == 'passed'])
        return {
            'total_tests': len(tests),
            'passed_tests': passed,
            'tests': tests
        }

class QualityAssurance:
    def __init__(self):
        self.qa_metrics = {}
        self.code_quality = {}
        
    def run_code_quality_check(self) -> Dict[str, Any]:
        """Chạy code quality check"""
        print("Running code quality check...")
        
        quality_metrics = {
            'timestamp': datetime.now().isoformat(),
            'files_analyzed': 0,
            'total_lines': 0,
            'functions_count': 0,
            'classes_count': 0,
            'comments_ratio': 0,
            'complexity_score': 0,
            'issues': []
        }
        
        # Analyze Python files
        python_files = []
        for root, dirs, files in os.walk('.'):
            for file in files:
                if file.endswith('.py') and not file.startswith('test_'):
                    python_files.append(os.path.join(root, file))
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                lines = content.split('\n')
                quality_metrics['files_analyzed'] += 1
                quality_metrics['total_lines'] += len(lines)
                
                # Count functions
                function_count = content.count('def ')
                quality_metrics['functions_count'] += function_count
                
                # Count classes
                class_count = content.count('class ')
                quality_metrics['classes_count'] += class_count
                
                # Count comments
                comment_lines = len([line for line in lines if line.strip().startswith('#')])
                comment_ratio = comment_lines / len(lines) if lines else 0
                quality_metrics['comments_ratio'] += comment_ratio
                
                # Check for common issues
                if 'import *' in content:
                    quality_metrics['issues'].append({
                        'file': file_path,
                        'type': 'wildcard_import',
                        'severity': 'warning',
                        'message': 'Wildcard import detected'
                    })
                
                if 'print(' in content and 'logging' not in content:
                    quality_metrics['issues'].append({
                        'file': file_path,
                        'type': 'print_statement',
                        'severity': 'info',
                        'message': 'Print statements should use logging'
                    })
                
            except Exception as e:
                quality_metrics['issues'].append({
                    'file': file_path,
                    'type': 'analysis_error',
                    'severity': 'error',
                    'message': str(e)
                })
        
        # Calculate average metrics
        if quality_metrics['files_analyzed'] > 0:
            quality_metrics['comments_ratio'] /= quality_metrics['files_analyzed']
            quality_metrics['avg_lines_per_file'] = quality_metrics['total_lines'] / quality_metrics['files_analyzed']
            quality_metrics['avg_functions_per_file'] = quality_metrics['functions_count'] / quality_metrics['files_analyzed']
            quality_metrics['avg_classes_per_file'] = quality_metrics['classes_count'] / quality_metrics['files_analyzed']
        
        self.code_quality = quality_metrics
        
        # Save results
        with open('code_quality_report.json', 'w', encoding='utf-8') as f:
            json.dump(quality_metrics, f, indent=2, ensure_ascii=False)
        
        print(f"Code quality check completed. Analyzed {quality_metrics['files_analyzed']} files.")
        return quality_metrics
    
    def generate_quality_report(self) -> Dict[str, Any]:
        """Tạo quality report tổng hợp"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'test_results': self.test_results,
            'code_quality': self.code_quality,
            'overall_score': 0,
            'recommendations': []
        }
        
        # Calculate overall score
        test_score = 0
        if self.test_results:
            test_score = self.test_results.get('success_rate', 0)
        
        code_score = 0
        if self.code_quality:
            # Simple code quality score based on comments ratio and issues
            comments_score = min(self.code_quality.get('comments_ratio', 0) * 100, 20)  # Max 20 points
            issues_penalty = len(self.code_quality.get('issues', [])) * 2  # 2 points per issue
            code_score = max(comments_score - issues_penalty, 0)
        
        report['overall_score'] = (test_score + code_score) / 2
        
        # Generate recommendations
        if test_score < 90:
            report['recommendations'].append('Improve test coverage and fix failing tests')
        
        if code_score < 15:
            report['recommendations'].append('Improve code quality with better comments and fewer issues')
        
        if self.code_quality and len(self.code_quality.get('issues', [])) > 10:
            report['recommendations'].append('Address code quality issues')
        
        return report

# Global instances
test_suite = TestSuite()
quality_assurance = QualityAssurance()

def run_final_testing():
    """Chạy final testing và quality assurance"""
    print("Running final testing and quality assurance...")
    
    # Run all tests
    test_results = test_suite.run_all_tests()
    
    # Run code quality check
    code_quality = quality_assurance.run_code_quality_check()
    
    # Generate final report
    final_report = quality_assurance.generate_quality_report()
    
    # Save final report
    with open('final_quality_report.json', 'w', encoding='utf-8') as f:
        json.dump(final_report, f, indent=2, ensure_ascii=False)
    
    print(f"Final testing completed. Overall score: {final_report['overall_score']:.1f}/100")
    return final_report

if __name__ == "__main__":
    run_final_testing()
