"""
Bulk Import/Export Module
Handles bulk operations for importing and exporting data
"""

import csv
import json
import os
import zipfile
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
from database import db_manager
from serial_generator import serial_generator

class BulkImportExport:
    """Bulk import/export functionality"""
    
    def __init__(self):
        self.supported_formats = {
            'csv': 'CSV Files',
            'excel': 'Excel Files',
            'json': 'JSON Files',
            'zip': 'ZIP Archives'
        }
        
        self.import_templates = {
            'po_data': {
                'columns': ['product_id', 'product_name', 'po_number', 'date_code', 'serial_numbers'],
                'required': ['product_id', 'po_number'],
                'description': 'Import PO data with serial numbers'
            },
            'serial_numbers': {
                'columns': ['product_id', 'serial_number', 'pattern'],
                'required': ['product_id', 'serial_number'],
                'description': 'Import serial numbers only'
            },
            'product_config': {
                'columns': ['product_id', 'template_path', 'random_config', 'merge_config'],
                'required': ['product_id', 'template_path'],
                'description': 'Import product configurations'
            }
        }
    
    def export_data(self, export_type: str, format: str = 'csv', 
                   filters: Dict = None, file_path: str = None) -> str:
        """Export data in specified format"""
        
        if export_type == 'po_history':
            data = self._export_po_history(filters)
        elif export_type == 'statistics':
            data = self._export_statistics(filters)
        elif export_type == 'serial_numbers':
            data = self._export_serial_numbers(filters)
        elif export_type == 'search_history':
            data = self._export_search_history(filters)
        else:
            raise ValueError(f"Unsupported export type: {export_type}")
        
        if not file_path:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_path = f"export_{export_type}_{timestamp}.{format}"
        
        if format == 'csv':
            return self._export_to_csv(data, file_path)
        elif format == 'excel':
            return self._export_to_excel(data, file_path)
        elif format == 'json':
            return self._export_to_json(data, file_path)
        elif format == 'zip':
            return self._export_to_zip(data, file_path)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _export_po_history(self, filters: Dict = None) -> List[Dict]:
        """Export PO history data"""
        if filters:
            return db_manager.get_po_history(
                limit=filters.get('limit', 10000),
                product_id=filters.get('product_id'),
                date_from=filters.get('date_from'),
                date_to=filters.get('date_to')
            )
        else:
            return db_manager.get_po_history(limit=10000)
    
    def _export_statistics(self, filters: Dict = None) -> List[Dict]:
        """Export statistics data"""
        period_days = filters.get('period_days', 30) if filters else 30
        stats = db_manager.get_statistics(period_days)
        
        # Convert to list format
        data = []
        
        # Product stats
        for product_stat in stats['product_stats']:
            data.append({
                'type': 'product',
                'product_id': product_stat[0],
                'count': product_stat[1],
                'period_days': period_days
            })
        
        # Daily stats
        for daily_stat in stats['daily_stats']:
            data.append({
                'type': 'daily',
                'date': daily_stat[0],
                'count': daily_stat[1],
                'period_days': period_days
            })
        
        return data
    
    def _export_serial_numbers(self, filters: Dict = None) -> List[Dict]:
        """Export serial numbers data"""
        conn = db_manager.db_path
        import sqlite3
        
        conn = sqlite3.connect(conn)
        cursor = conn.cursor()
        
        query = "SELECT * FROM serial_tracking"
        params = []
        
        if filters and 'product_id' in filters:
            query += " WHERE product_id = ?"
            params.append(filters['product_id'])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        columns = [description[0] for description in cursor.description]
        data = []
        
        for row in rows:
            record = dict(zip(columns, row))
            data.append(record)
        
        conn.close()
        return data
    
    def _export_search_history(self, filters: Dict = None) -> List[Dict]:
        """Export search history data"""
        conn = db_manager.db_path
        import sqlite3
        
        conn = sqlite3.connect(conn)
        cursor = conn.cursor()
        
        query = "SELECT * FROM search_history"
        params = []
        
        if filters and 'search_type' in filters:
            query += " WHERE search_type = ?"
            params.append(filters['search_type'])
        
        query += " ORDER BY created_at DESC"
        
        if filters and 'limit' in filters:
            query += " LIMIT ?"
            params.append(filters['limit'])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        columns = [description[0] for description in cursor.description]
        data = []
        
        for row in rows:
            record = dict(zip(columns, row))
            data.append(record)
        
        conn.close()
        return data
    
    def _export_to_csv(self, data: List[Dict], file_path: str) -> str:
        """Export data to CSV"""
        if not data:
            return file_path
        
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = data[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        
        return file_path
    
    def _export_to_excel(self, data: List[Dict], file_path: str) -> str:
        """Export data to Excel"""
        if not data:
            return file_path
        
        df = pd.DataFrame(data)
        df.to_excel(file_path, index=False)
        
        return file_path
    
    def _export_to_json(self, data: List[Dict], file_path: str) -> str:
        """Export data to JSON"""
        with open(file_path, 'w', encoding='utf-8') as jsonfile:
            json.dump(data, jsonfile, indent=2, ensure_ascii=False)
        
        return file_path
    
    def _export_to_zip(self, data: List[Dict], file_path: str) -> str:
        """Export data to ZIP"""
        # Create temporary files
        temp_dir = "temp_export"
        os.makedirs(temp_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Export to multiple formats
        csv_file = os.path.join(temp_dir, f"data_{timestamp}.csv")
        json_file = os.path.join(temp_dir, f"data_{timestamp}.json")
        
        self._export_to_csv(data, csv_file)
        self._export_to_json(data, json_file)
        
        # Create ZIP file
        with zipfile.ZipFile(file_path, 'w') as zipf:
            zipf.write(csv_file, f"data_{timestamp}.csv")
            zipf.write(json_file, f"data_{timestamp}.json")
        
        # Clean up temp files
        os.remove(csv_file)
        os.remove(json_file)
        os.rmdir(temp_dir)
        
        return file_path
    
    def import_data(self, file_path: str, import_type: str, 
                   template: str = None, options: Dict = None) -> Dict:
        """Import data from file"""
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.csv':
            data = self._import_from_csv(file_path)
        elif file_ext in ['.xlsx', '.xls']:
            data = self._import_from_excel(file_path)
        elif file_ext == '.json':
            data = self._import_from_json(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")
        
        # Validate and process data
        if import_type == 'po_data':
            return self._import_po_data(data, options)
        elif import_type == 'serial_numbers':
            return self._import_serial_numbers(data, options)
        elif import_type == 'product_config':
            return self._import_product_config(data, options)
        else:
            raise ValueError(f"Unsupported import type: {import_type}")
    
    def _import_from_csv(self, file_path: str) -> List[Dict]:
        """Import data from CSV"""
        data = []
        
        with open(file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                data.append(row)
        
        return data
    
    def _import_from_excel(self, file_path: str) -> List[Dict]:
        """Import data from Excel"""
        df = pd.read_excel(file_path)
        return df.to_dict('records')
    
    def _import_from_json(self, file_path: str) -> List[Dict]:
        """Import data from JSON"""
        with open(file_path, 'r', encoding='utf-8') as jsonfile:
            return json.load(jsonfile)
    
    def _import_po_data(self, data: List[Dict], options: Dict = None) -> Dict:
        """Import PO data"""
        results = {
            'success': 0,
            'failed': 0,
            'errors': [],
            'imported_records': []
        }
        
        for i, record in enumerate(data):
            try:
                # Validate required fields
                if not record.get('product_id') or not record.get('po_number'):
                    results['errors'].append(f"Row {i+1}: Missing required fields")
                    results['failed'] += 1
                    continue
                
                # Parse serial numbers
                serial_numbers = []
                if record.get('serial_numbers'):
                    if isinstance(record['serial_numbers'], str):
                        serial_numbers = [s.strip() for s in record['serial_numbers'].split(',')]
                    else:
                        serial_numbers = record['serial_numbers']
                
                # Add to database
                record_id = db_manager.add_po_record(
                    product_id=record['product_id'],
                    product_name=record.get('product_name', record['product_id']),
                    po_number=record['po_number'],
                    date_code=record.get('date_code', datetime.now().strftime('%Y-%m-%d')),
                    serial_numbers=serial_numbers,
                    file_path=record.get('file_path', ''),
                    user_agent='Bulk Import',
                    ip_address='127.0.0.1'
                )
                
                results['imported_records'].append({
                    'id': record_id,
                    'product_id': record['product_id'],
                    'po_number': record['po_number']
                })
                
                results['success'] += 1
                
            except Exception as e:
                results['errors'].append(f"Row {i+1}: {str(e)}")
                results['failed'] += 1
        
        return results
    
    def _import_serial_numbers(self, data: List[Dict], options: Dict = None) -> Dict:
        """Import serial numbers"""
        results = {
            'success': 0,
            'failed': 0,
            'errors': [],
            'imported_serials': []
        }
        
        for i, record in enumerate(data):
            try:
                if not record.get('product_id') or not record.get('serial_number'):
                    results['errors'].append(f"Row {i+1}: Missing required fields")
                    results['failed'] += 1
                    continue
                
                # Validate serial number format
                if not serial_generator.validate_serial_number(
                    record['serial_number'], record['product_id']
                ):
                    results['errors'].append(f"Row {i+1}: Invalid serial number format")
                    results['failed'] += 1
                    continue
                
                # Add to tracking
                conn = db_manager.db_path
                import sqlite3
                
                conn = sqlite3.connect(conn)
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO serial_tracking 
                    (product_id, last_serial_number, serial_pattern)
                    VALUES (?, ?, ?)
                ''', (
                    record['product_id'],
                    int(record['serial_number'].split('-')[-1]),
                    record.get('pattern', f"{record['product_id']}-{{:03d}}")
                ))
                
                conn.commit()
                conn.close()
                
                results['imported_serials'].append({
                    'product_id': record['product_id'],
                    'serial_number': record['serial_number']
                })
                
                results['success'] += 1
                
            except Exception as e:
                results['errors'].append(f"Row {i+1}: {str(e)}")
                results['failed'] += 1
        
        return results
    
    def _import_product_config(self, data: List[Dict], options: Dict = None) -> Dict:
        """Import product configuration"""
        results = {
            'success': 0,
            'failed': 0,
            'errors': [],
            'imported_configs': []
        }
        
        for i, record in enumerate(data):
            try:
                if not record.get('product_id') or not record.get('template_path'):
                    results['errors'].append(f"Row {i+1}: Missing required fields")
                    results['failed'] += 1
                    continue
                
                # Validate template path
                if not os.path.exists(record['template_path']):
                    results['errors'].append(f"Row {i+1}: Template file not found")
                    results['failed'] += 1
                    continue
                
                # Save configuration
                config = {
                    'product_id': record['product_id'],
                    'template_path': record['template_path'],
                    'random_config': record.get('random_config', []),
                    'merge_config': record.get('merge_config', {}),
                    'imported_at': datetime.now().isoformat()
                }
                
                db_manager.set_user_preference(
                    f"product_config_{record['product_id']}",
                    json.dumps(config)
                )
                
                results['imported_configs'].append({
                    'product_id': record['product_id'],
                    'template_path': record['template_path']
                })
                
                results['success'] += 1
                
            except Exception as e:
                results['errors'].append(f"Row {i+1}: {str(e)}")
                results['failed'] += 1
        
        return results
    
    def get_import_template(self, import_type: str) -> str:
        """Get import template file"""
        if import_type not in self.import_templates:
            raise ValueError(f"Unsupported import type: {import_type}")
        
        template = self.import_templates[import_type]
        
        # Create template file
        template_file = f"import_template_{import_type}.csv"
        
        with open(template_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header
            writer.writerow(template['columns'])
            
            # Write example data
            if import_type == 'po_data':
                writer.writerow(['LA800', 'LA800', 'PO001', '2025-01-05', 'LA800-001,LA800-002'])
            elif import_type == 'serial_numbers':
                writer.writerow(['LA800', 'LA800-001', 'LA800-{:03d}'])
            elif import_type == 'product_config':
                writer.writerow(['LA800', 'LA800/template.xlsx', '[]', '{}'])
        
        return template_file
    
    def validate_import_file(self, file_path: str, import_type: str) -> Dict:
        """Validate import file before processing"""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'record_count': 0
        }
        
        try:
            # Check file format
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext not in ['.csv', '.xlsx', '.xls', '.json']:
                validation_result['valid'] = False
                validation_result['errors'].append("Unsupported file format")
                return validation_result
            
            # Load data
            if file_ext == '.csv':
                data = self._import_from_csv(file_path)
            elif file_ext in ['.xlsx', '.xls']:
                data = self._import_from_excel(file_path)
            elif file_ext == '.json':
                data = self._import_from_json(file_path)
            
            validation_result['record_count'] = len(data)
            
            if not data:
                validation_result['valid'] = False
                validation_result['errors'].append("File is empty")
                return validation_result
            
            # Validate structure
            template = self.import_templates[import_type]
            required_columns = template['required']
            
            for i, record in enumerate(data):
                for required_col in required_columns:
                    if required_col not in record or not record[required_col]:
                        validation_result['errors'].append(
                            f"Row {i+1}: Missing required column '{required_col}'"
                        )
                        validation_result['valid'] = False
            
            # Check for duplicates
            if import_type == 'po_data':
                po_numbers = [r.get('po_number') for r in data if r.get('po_number')]
                if len(po_numbers) != len(set(po_numbers)):
                    validation_result['warnings'].append("Duplicate PO numbers found")
            
        except Exception as e:
            validation_result['valid'] = False
            validation_result['errors'].append(f"File validation error: {str(e)}")
        
        return validation_result
    
    def get_export_progress(self, export_id: str) -> Dict:
        """Get export progress (for large exports)"""
        # This would be implemented with a job queue system
        # For now, return a simple status
        return {
            'export_id': export_id,
            'status': 'completed',
            'progress': 100,
            'message': 'Export completed successfully'
        }

# Global instance
bulk_import_export = BulkImportExport()

