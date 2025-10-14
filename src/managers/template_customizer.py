"""
Template Customization Module
Provides visual template editor with drag & drop functionality
"""

import json
import os
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import uuid

class TemplateCustomizer:
    """Visual template editor with drag & drop"""
    
    def __init__(self):
        self.template_types = {
            'standard': 'Standard Template',
            'special': 'Special Template', 
            'merge_cells': 'Merge Cells Template',
            'complex': 'Complex Template',
            'unique_row': 'Unique Row Template'
        }
        
        self.field_types = {
            'text': 'Text Field',
            'number': 'Number Field',
            'date': 'Date Field',
            'serial': 'Serial Number',
            'po_number': 'PO Number',
            'product_name': 'Product Name',
            'random_value': 'Random Value',
            'formula': 'Formula'
        }
        
        self.layout_options = {
            'single_column': 'Single Column',
            'two_column': 'Two Column',
            'three_column': 'Three Column',
            'grid': 'Grid Layout',
            'custom': 'Custom Layout'
        }
    
    def create_template(self, template_data: Dict) -> Dict:
        """Create new template from customization data"""
        template_id = str(uuid.uuid4())
        
        template = {
            'id': template_id,
            'name': template_data.get('name', 'Custom Template'),
            'type': template_data.get('type', 'standard'),
            'description': template_data.get('description', ''),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'version': '1.0',
            'layout': template_data.get('layout', {}),
            'fields': template_data.get('fields', []),
            'merge_config': template_data.get('merge_config', {}),
            'random_config': template_data.get('random_config', []),
            'serial_config': template_data.get('serial_config', {}),
            'styling': template_data.get('styling', {}),
            'validation_rules': template_data.get('validation_rules', []),
            'permissions': template_data.get('permissions', {}),
            'is_active': True,
            'is_public': template_data.get('is_public', False)
        }
        
        return template
    
    def update_template(self, template_id: str, updates: Dict) -> Dict:
        """Update existing template"""
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        # Update fields
        for key, value in updates.items():
            if key in template:
                template[key] = value
        
        template['updated_at'] = datetime.now().isoformat()
        template['version'] = self._increment_version(template['version'])
        
        return template
    
    def get_template(self, template_id: str) -> Optional[Dict]:
        """Get template by ID"""
        # This would typically load from database
        # For now, return mock data
        return None
    
    def list_templates(self, user_id: str = None, public_only: bool = False) -> List[Dict]:
        """List available templates"""
        # This would load from database
        return []
    
    def delete_template(self, template_id: str, user_id: str) -> bool:
        """Delete template"""
        # This would delete from database
        return True
    
    def clone_template(self, template_id: str, new_name: str, user_id: str) -> Dict:
        """Clone existing template"""
        original = self.get_template(template_id)
        if not original:
            raise ValueError(f"Template {template_id} not found")
        
        cloned_data = original.copy()
        cloned_data['name'] = new_name
        cloned_data['created_at'] = datetime.now().isoformat()
        cloned_data['updated_at'] = datetime.now().isoformat()
        cloned_data['version'] = '1.0'
        
        return self.create_template(cloned_data)
    
    def validate_template(self, template_data: Dict) -> Dict:
        """Validate template configuration"""
        errors = []
        warnings = []
        
        # Check required fields
        required_fields = ['name', 'type', 'fields']
        for field in required_fields:
            if field not in template_data or not template_data[field]:
                errors.append(f"Missing required field: {field}")
        
        # Validate fields
        if 'fields' in template_data:
            for i, field in enumerate(template_data['fields']):
                if 'type' not in field:
                    errors.append(f"Field {i+1}: Missing field type")
                if 'position' not in field:
                    warnings.append(f"Field {i+1}: Missing position")
        
        # Validate merge config
        if 'merge_config' in template_data:
            merge_config = template_data['merge_config']
            for key, value in merge_config.items():
                if not isinstance(value, str) or not value:
                    warnings.append(f"Invalid merge config for {key}")
        
        # Validate random config
        if 'random_config' in template_data:
            random_config = template_data['random_config']
            for i, config in enumerate(random_config):
                if not isinstance(config, (list, tuple)) or len(config) < 2:
                    errors.append(f"Invalid random config {i+1}")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def preview_template(self, template_data: Dict) -> Dict:
        """Generate template preview"""
        preview = {
            'layout_preview': self._generate_layout_preview(template_data),
            'field_preview': self._generate_field_preview(template_data),
            'merge_preview': self._generate_merge_preview(template_data),
            'styling_preview': self._generate_styling_preview(template_data)
        }
        
        return preview
    
    def export_template(self, template_id: str, format: str = 'json') -> str:
        """Export template in specified format"""
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        if format == 'json':
            return json.dumps(template, indent=2, ensure_ascii=False)
        elif format == 'yaml':
            import yaml
            return yaml.dump(template, default_flow_style=False, allow_unicode=True)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def import_template(self, template_data: str, format: str = 'json') -> Dict:
        """Import template from file"""
        if format == 'json':
            data = json.loads(template_data)
        elif format == 'yaml':
            import yaml
            data = yaml.safe_load(template_data)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        # Validate imported template
        validation = self.validate_template(data)
        if not validation['valid']:
            raise ValueError(f"Invalid template: {validation['errors']}")
        
        return self.create_template(data)
    
    def get_template_statistics(self, template_id: str) -> Dict:
        """Get template usage statistics"""
        # This would query database for usage stats
        return {
            'usage_count': 0,
            'last_used': None,
            'popular_fields': [],
            'error_rate': 0.0,
            'average_completion_time': 0
        }
    
    def _generate_layout_preview(self, template_data: Dict) -> Dict:
        """Generate layout preview"""
        layout = template_data.get('layout', {})
        
        return {
            'type': layout.get('type', 'single_column'),
            'columns': layout.get('columns', 1),
            'rows': layout.get('rows', 1),
            'spacing': layout.get('spacing', 'normal'),
            'alignment': layout.get('alignment', 'left')
        }
    
    def _generate_field_preview(self, template_data: Dict) -> List[Dict]:
        """Generate field preview"""
        fields = template_data.get('fields', [])
        
        preview = []
        for field in fields:
            preview.append({
                'id': field.get('id', ''),
                'name': field.get('name', ''),
                'type': field.get('type', 'text'),
                'position': field.get('position', {}),
                'required': field.get('required', False),
                'validation': field.get('validation', {}),
                'styling': field.get('styling', {})
            })
        
        return preview
    
    def _generate_merge_preview(self, template_data: Dict) -> Dict:
        """Generate merge configuration preview"""
        merge_config = template_data.get('merge_config', {})
        
        return {
            'product_cells': merge_config.get('product', ''),
            'po_cells': merge_config.get('po', ''),
            'date_cells': merge_config.get('date', ''),
            'serial_cells': merge_config.get('serial', ''),
            'custom_merges': merge_config.get('custom', [])
        }
    
    def _generate_styling_preview(self, template_data: Dict) -> Dict:
        """Generate styling preview"""
        styling = template_data.get('styling', {})
        
        return {
            'theme': styling.get('theme', 'default'),
            'colors': styling.get('colors', {}),
            'fonts': styling.get('fonts', {}),
            'spacing': styling.get('spacing', {}),
            'borders': styling.get('borders', {})
        }
    
    def _increment_version(self, version: str) -> str:
        """Increment version number"""
        try:
            major, minor = version.split('.')
            return f"{major}.{int(minor) + 1}"
        except:
            return "1.1"
    
    def get_field_templates(self) -> List[Dict]:
        """Get predefined field templates"""
        return [
            {
                'id': 'product_name',
                'name': 'Product Name',
                'type': 'text',
                'required': True,
                'validation': {'min_length': 1, 'max_length': 50},
                'styling': {'font_size': 14, 'bold': True}
            },
            {
                'id': 'po_number',
                'name': 'PO Number',
                'type': 'text',
                'required': True,
                'validation': {'pattern': r'^[A-Z0-9-]+$'},
                'styling': {'font_size': 12, 'color': '#0066cc'}
            },
            {
                'id': 'date_code',
                'name': 'Date Code',
                'type': 'date',
                'required': True,
                'validation': {'format': 'YYYY-MM-DD'},
                'styling': {'font_size': 12}
            },
            {
                'id': 'serial_numbers',
                'name': 'Serial Numbers',
                'type': 'serial',
                'required': True,
                'validation': {'count': 5},
                'styling': {'font_size': 11, 'monospace': True}
            },
            {
                'id': 'random_value',
                'name': 'Random Value',
                'type': 'random_value',
                'required': False,
                'validation': {'min': 0, 'max': 10000},
                'styling': {'font_size': 12, 'color': '#666666'}
            }
        ]
    
    def get_layout_templates(self) -> List[Dict]:
        """Get predefined layout templates"""
        return [
            {
                'id': 'standard_layout',
                'name': 'Standard Layout',
                'type': 'single_column',
                'description': 'Single column layout for standard templates',
                'preview': '/static/layouts/standard.png'
            },
            {
                'id': 'two_column_layout',
                'name': 'Two Column Layout',
                'type': 'two_column',
                'description': 'Two column layout for complex templates',
                'preview': '/static/layouts/two_column.png'
            },
            {
                'id': 'grid_layout',
                'name': 'Grid Layout',
                'type': 'grid',
                'description': 'Grid layout for organized data entry',
                'preview': '/static/layouts/grid.png'
            },
            {
                'id': 'merge_layout',
                'name': 'Merge Cells Layout',
                'type': 'merge_cells',
                'description': 'Layout optimized for merged cells',
                'preview': '/static/layouts/merge.png'
            }
        ]
    
    def generate_template_code(self, template_data: Dict) -> str:
        """Generate Python code for template"""
        code = f"""
# Generated template code for {template_data.get('name', 'Custom Template')}
# Generated on {datetime.now().isoformat()}

template_config = {{
    'name': '{template_data.get('name', '')}',
    'type': '{template_data.get('type', 'standard')}',
    'template': '{template_data.get('template_path', '')}',
    'random_config': {template_data.get('random_config', [])},
    'random_columns': {template_data.get('random_columns', [])},
    'merge_config': {template_data.get('merge_config', {})},
    'serial_range': '{template_data.get('serial_range', 'A11:A15')}'
}}
"""
        return code
    
    def backup_templates(self, user_id: str = None) -> str:
        """Create backup of all templates"""
        templates = self.list_templates(user_id)
        
        backup_data = {
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id,
            'templates': templates,
            'version': '1.0'
        }
        
        backup_filename = f"templates_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(backup_filename, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2, ensure_ascii=False)
        
        return backup_filename
    
    def restore_templates(self, backup_file: str) -> Dict:
        """Restore templates from backup"""
        with open(backup_file, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
        
        restored_count = 0
        errors = []
        
        for template in backup_data.get('templates', []):
            try:
                self.create_template(template)
                restored_count += 1
            except Exception as e:
                errors.append(f"Failed to restore {template.get('name', 'Unknown')}: {str(e)}")
        
        return {
            'restored_count': restored_count,
            'errors': errors,
            'backup_date': backup_data.get('timestamp')
        }

# Global instance
template_customizer = TemplateCustomizer()
