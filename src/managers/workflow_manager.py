"""
Workflow Automation Module
Provides automated workflows, triggers, and business process automation
"""

import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
import sqlite3
import uuid

class TriggerType(Enum):
    """Types of workflow triggers"""
    SCHEDULED = "scheduled"
    EVENT_BASED = "event_based"
    CONDITION_BASED = "condition_based"
    MANUAL = "manual"
    API_CALL = "api_call"

class ActionType(Enum):
    """Types of workflow actions"""
    CREATE_PO = "create_po"
    SEND_EMAIL = "send_email"
    GENERATE_REPORT = "generate_report"
    SYNC_CLOUD = "sync_cloud"
    VALIDATE_DATA = "validate_data"
    NOTIFY_USER = "notify_user"
    EXPORT_DATA = "export_data"
    IMPORT_DATA = "import_data"
    CUSTOM_SCRIPT = "custom_script"

class WorkflowStatus(Enum):
    """Workflow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class WorkflowManager:
    """Workflow automation management"""
    
    def __init__(self, db_path: str = "po_system.db"):
        self.db_path = db_path
        self.active_workflows = {}
        self.workflow_executions = {}
        self.triggers = {}
        self.actions = {}
        self.scheduler_thread = None
        self.is_running = False
        
        # Initialize database
        self.init_workflow_tables()
        
        # Load predefined workflows
        self._load_predefined_workflows()
        
        # Start scheduler
        self.start_scheduler()
    
    def init_workflow_tables(self):
        """Initialize workflow-related database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Workflows table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS workflows (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                trigger_type TEXT NOT NULL,
                trigger_config TEXT NOT NULL,
                actions TEXT NOT NULL,
                conditions TEXT DEFAULT '[]',
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                last_executed TIMESTAMP,
                execution_count INTEGER DEFAULT 0,
                success_count INTEGER DEFAULT 0,
                failure_count INTEGER DEFAULT 0
            )
        ''')
        
        # Workflow executions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS workflow_executions (
                id TEXT PRIMARY KEY,
                workflow_id TEXT NOT NULL,
                status TEXT NOT NULL,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                error_message TEXT,
                execution_data TEXT DEFAULT '{}',
                FOREIGN KEY (workflow_id) REFERENCES workflows (id)
            )
        ''')
        
        # Workflow logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS workflow_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workflow_id TEXT NOT NULL,
                execution_id TEXT,
                log_level TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT DEFAULT '{}',
                FOREIGN KEY (workflow_id) REFERENCES workflows (id),
                FOREIGN KEY (execution_id) REFERENCES workflow_executions (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_workflow(self, workflow_data: Dict) -> str:
        """Create new workflow"""
        workflow_id = str(uuid.uuid4())
        
        workflow = {
            'id': workflow_id,
            'name': workflow_data['name'],
            'description': workflow_data.get('description', ''),
            'trigger_type': workflow_data['trigger_type'],
            'trigger_config': json.dumps(workflow_data['trigger_config']),
            'actions': json.dumps(workflow_data['actions']),
            'conditions': json.dumps(workflow_data.get('conditions', [])),
            'is_active': workflow_data.get('is_active', True),
            'created_by': workflow_data.get('created_by'),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        # Save to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO workflows (id, name, description, trigger_type, trigger_config, 
                                 actions, conditions, is_active, created_by, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            workflow['id'], workflow['name'], workflow['description'],
            workflow['trigger_type'], workflow['trigger_config'],
            workflow['actions'], workflow['conditions'], workflow['is_active'],
            workflow['created_by'], workflow['created_at'], workflow['updated_at']
        ))
        
        conn.commit()
        conn.close()
        
        # Register workflow
        self._register_workflow(workflow)
        
        return workflow_id
    
    def execute_workflow(self, workflow_id: str, trigger_data: Dict = None) -> str:
        """Execute workflow"""
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        if not workflow['is_active']:
            raise ValueError(f"Workflow {workflow_id} is not active")
        
        # Create execution record
        execution_id = str(uuid.uuid4())
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO workflow_executions (id, workflow_id, status, execution_data)
            VALUES (?, ?, ?, ?)
        ''', (execution_id, workflow_id, WorkflowStatus.RUNNING.value, 
              json.dumps(trigger_data or {})))
        
        conn.commit()
        conn.close()
        
        # Execute workflow in separate thread
        execution_thread = threading.Thread(
            target=self._execute_workflow_thread,
            args=(workflow_id, execution_id, trigger_data)
        )
        execution_thread.start()
        
        return execution_id
    
    def _execute_workflow_thread(self, workflow_id: str, execution_id: str, trigger_data: Dict):
        """Execute workflow in separate thread"""
        try:
            workflow = self.get_workflow(workflow_id)
            actions = json.loads(workflow['actions'])
            conditions = json.loads(workflow['conditions'])
            
            # Check conditions
            if not self._check_conditions(conditions, trigger_data):
                self._update_execution_status(execution_id, WorkflowStatus.CANCELLED.value)
                return
            
            # Execute actions
            execution_data = trigger_data or {}
            
            for action_config in actions:
                action_type = action_config['type']
                action_params = action_config.get('params', {})
                
                # Execute action
                result = self._execute_action(action_type, action_params, execution_data)
                
                # Update execution data
                execution_data.update(result)
                
                # Log action execution
                self._log_workflow_event(
                    workflow_id, execution_id, 'INFO',
                    f"Executed action: {action_type}", result
                )
            
            # Mark as completed
            self._update_execution_status(execution_id, WorkflowStatus.COMPLETED.value)
            
            # Update workflow statistics
            self._update_workflow_stats(workflow_id, success=True)
            
        except Exception as e:
            # Mark as failed
            self._update_execution_status(execution_id, WorkflowStatus.FAILED.value, str(e))
            
            # Log error
            self._log_workflow_event(
                workflow_id, execution_id, 'ERROR',
                f"Workflow execution failed: {str(e)}"
            )
            
            # Update workflow statistics
            self._update_workflow_stats(workflow_id, success=False)
    
    def _execute_action(self, action_type: str, params: Dict, execution_data: Dict) -> Dict:
        """Execute workflow action"""
        if action_type == ActionType.CREATE_PO.value:
            return self._action_create_po(params, execution_data)
        elif action_type == ActionType.SEND_EMAIL.value:
            return self._action_send_email(params, execution_data)
        elif action_type == ActionType.GENERATE_REPORT.value:
            return self._action_generate_report(params, execution_data)
        elif action_type == ActionType.SYNC_CLOUD.value:
            return self._action_sync_cloud(params, execution_data)
        elif action_type == ActionType.VALIDATE_DATA.value:
            return self._action_validate_data(params, execution_data)
        elif action_type == ActionType.NOTIFY_USER.value:
            return self._action_notify_user(params, execution_data)
        elif action_type == ActionType.EXPORT_DATA.value:
            return self._action_export_data(params, execution_data)
        elif action_type == ActionType.IMPORT_DATA.value:
            return self._action_import_data(params, execution_data)
        elif action_type == ActionType.CUSTOM_SCRIPT.value:
            return self._action_custom_script(params, execution_data)
        else:
            raise ValueError(f"Unknown action type: {action_type}")
    
    def _action_create_po(self, params: Dict, execution_data: Dict) -> Dict:
        """Action: Create PO"""
        # This would integrate with PO creation logic
        product_id = params.get('product_id', execution_data.get('product_id'))
        po_number = params.get('po_number', execution_data.get('po_number'))
        
        # Mock PO creation
        po_id = f"PO_{int(time.time())}"
        
        return {
            'po_id': po_id,
            'product_id': product_id,
            'po_number': po_number,
            'created_at': datetime.now().isoformat()
        }
    
    def _action_send_email(self, params: Dict, execution_data: Dict) -> Dict:
        """Action: Send email"""
        # This would integrate with email service
        to = params.get('to', execution_data.get('email'))
        subject = params.get('subject', 'Workflow Notification')
        body = params.get('body', 'Workflow executed successfully')
        
        # Mock email sending
        email_id = f"email_{int(time.time())}"
        
        return {
            'email_id': email_id,
            'to': to,
            'subject': subject,
            'sent_at': datetime.now().isoformat()
        }
    
    def _action_generate_report(self, params: Dict, execution_data: Dict) -> Dict:
        """Action: Generate report"""
        report_type = params.get('report_type', 'summary')
        format_type = params.get('format', 'pdf')
        
        # This would integrate with reporting system
        report_id = f"report_{int(time.time())}"
        
        return {
            'report_id': report_id,
            'report_type': report_type,
            'format': format_type,
            'generated_at': datetime.now().isoformat()
        }
    
    def _action_sync_cloud(self, params: Dict, execution_data: Dict) -> Dict:
        """Action: Sync to cloud"""
        provider = params.get('provider', 'google_drive')
        
        # This would integrate with cloud_manager
        sync_id = f"sync_{int(time.time())}"
        
        return {
            'sync_id': sync_id,
            'provider': provider,
            'synced_at': datetime.now().isoformat()
        }
    
    def _action_validate_data(self, params: Dict, execution_data: Dict) -> Dict:
        """Action: Validate data"""
        validation_rules = params.get('rules', [])
        
        # Mock validation
        is_valid = True
        errors = []
        
        return {
            'is_valid': is_valid,
            'errors': errors,
            'validated_at': datetime.now().isoformat()
        }
    
    def _action_notify_user(self, params: Dict, execution_data: Dict) -> Dict:
        """Action: Notify user"""
        user_id = params.get('user_id', execution_data.get('user_id'))
        message = params.get('message', 'Workflow notification')
        notification_type = params.get('type', 'info')
        
        # This would integrate with notification system
        notification_id = f"notif_{int(time.time())}"
        
        return {
            'notification_id': notification_id,
            'user_id': user_id,
            'message': message,
            'type': notification_type,
            'sent_at': datetime.now().isoformat()
        }
    
    def _action_export_data(self, params: Dict, execution_data: Dict) -> Dict:
        """Action: Export data"""
        export_type = params.get('export_type', 'po_history')
        format_type = params.get('format', 'csv')
        
        # This would integrate with bulk_import_export
        export_id = f"export_{int(time.time())}"
        
        return {
            'export_id': export_id,
            'export_type': export_type,
            'format': format_type,
            'exported_at': datetime.now().isoformat()
        }
    
    def _action_import_data(self, params: Dict, execution_data: Dict) -> Dict:
        """Action: Import data"""
        import_type = params.get('import_type', 'po_data')
        file_path = params.get('file_path')
        
        # This would integrate with bulk_import_export
        import_id = f"import_{int(time.time())}"
        
        return {
            'import_id': import_id,
            'import_type': import_type,
            'file_path': file_path,
            'imported_at': datetime.now().isoformat()
        }
    
    def _action_custom_script(self, params: Dict, execution_data: Dict) -> Dict:
        """Action: Execute custom script"""
        script_code = params.get('script_code')
        
        # This would execute custom Python code
        # For security, this should be sandboxed
        try:
            # Mock script execution
            result = {'script_result': 'executed successfully'}
        except Exception as e:
            result = {'script_error': str(e)}
        
        return result
    
    def _check_conditions(self, conditions: List[Dict], execution_data: Dict) -> bool:
        """Check workflow conditions"""
        if not conditions:
            return True
        
        for condition in conditions:
            condition_type = condition['type']
            condition_params = condition.get('params', {})
            
            if not self._evaluate_condition(condition_type, condition_params, execution_data):
                return False
        
        return True
    
    def _evaluate_condition(self, condition_type: str, params: Dict, execution_data: Dict) -> bool:
        """Evaluate single condition"""
        if condition_type == 'data_exists':
            field = params.get('field')
            return field in execution_data and execution_data[field] is not None
        
        elif condition_type == 'value_equals':
            field = params.get('field')
            expected_value = params.get('value')
            return execution_data.get(field) == expected_value
        
        elif condition_type == 'value_greater_than':
            field = params.get('field')
            threshold = params.get('threshold')
            return execution_data.get(field, 0) > threshold
        
        elif condition_type == 'time_based':
            time_condition = params.get('condition')
            current_hour = datetime.now().hour
            
            if time_condition == 'business_hours':
                return 9 <= current_hour <= 17
            elif time_condition == 'after_hours':
                return current_hour < 9 or current_hour > 17
        
        return True
    
    def get_workflow(self, workflow_id: str) -> Optional[Dict]:
        """Get workflow by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM workflows WHERE id = ?', (workflow_id,))
        row = cursor.fetchone()
        
        conn.close()
        
        if not row:
            return None
        
        columns = [description[0] for description in cursor.description]
        workflow = dict(zip(columns, row))
        
        # Parse JSON fields
        workflow['trigger_config'] = json.loads(workflow['trigger_config'])
        workflow['actions'] = json.loads(workflow['actions'])
        workflow['conditions'] = json.loads(workflow['conditions'])
        
        return workflow
    
    def list_workflows(self, active_only: bool = False) -> List[Dict]:
        """List workflows"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = 'SELECT * FROM workflows'
        if active_only:
            query += ' WHERE is_active = 1'
        query += ' ORDER BY created_at DESC'
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        columns = [description[0] for description in cursor.description]
        workflows = []
        
        for row in rows:
            workflow = dict(zip(columns, row))
            # Parse JSON fields
            workflow['trigger_config'] = json.loads(workflow['trigger_config'])
            workflow['actions'] = json.loads(workflow['actions'])
            workflow['conditions'] = json.loads(workflow['conditions'])
            workflows.append(workflow)
        
        conn.close()
        
        return workflows
    
    def update_workflow(self, workflow_id: str, updates: Dict) -> bool:
        """Update workflow"""
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            return False
        
        # Update fields
        allowed_fields = ['name', 'description', 'trigger_config', 'actions', 'conditions', 'is_active']
        
        update_fields = []
        update_values = []
        
        for field, value in updates.items():
            if field in allowed_fields:
                if field in ['trigger_config', 'actions', 'conditions']:
                    value = json.dumps(value)
                
                update_fields.append(f"{field} = ?")
                update_values.append(value)
        
        if not update_fields:
            return False
        
        update_values.append(workflow_id)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = f"UPDATE workflows SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
        cursor.execute(query, update_values)
        
        conn.commit()
        conn.close()
        
        return True
    
    def delete_workflow(self, workflow_id: str) -> bool:
        """Delete workflow"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM workflows WHERE id = ?', (workflow_id,))
        affected_rows = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        return affected_rows > 0
    
    def get_workflow_executions(self, workflow_id: str = None, limit: int = 100) -> List[Dict]:
        """Get workflow executions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = 'SELECT * FROM workflow_executions'
        params = []
        
        if workflow_id:
            query += ' WHERE workflow_id = ?'
            params.append(workflow_id)
        
        query += ' ORDER BY started_at DESC LIMIT ?'
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        columns = [description[0] for description in cursor.description]
        executions = []
        
        for row in rows:
            execution = dict(zip(columns, row))
            execution['execution_data'] = json.loads(execution['execution_data'])
            executions.append(execution)
        
        conn.close()
        
        return executions
    
    def _register_workflow(self, workflow: Dict):
        """Register workflow for execution"""
        workflow_id = workflow['id']
        trigger_type = workflow['trigger_type']
        
        if trigger_type == TriggerType.SCHEDULED.value:
            # Register scheduled workflow
            self.triggers[workflow_id] = {
                'type': trigger_type,
                'config': json.loads(workflow['trigger_config']),
                'workflow': workflow
            }
    
    def start_scheduler(self):
        """Start workflow scheduler"""
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            return
        
        self.is_running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
    
    def stop_scheduler(self):
        """Stop workflow scheduler"""
        self.is_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join()
    
    def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.is_running:
            try:
                # Check scheduled workflows
                self._check_scheduled_workflows()
                
                # Sleep for 1 minute
                time.sleep(60)
            
            except Exception as e:
                print(f"Scheduler error: {e}")
                time.sleep(60)
    
    def _check_scheduled_workflows(self):
        """Check for scheduled workflows to execute"""
        current_time = datetime.now()
        
        for workflow_id, trigger_info in self.triggers.items():
            if trigger_info['type'] == TriggerType.SCHEDULED.value:
                config = trigger_info['config']
                schedule_type = config.get('schedule_type')
                
                should_execute = False
                
                if schedule_type == 'daily':
                    hour = config.get('hour', 0)
                    minute = config.get('minute', 0)
                    should_execute = (current_time.hour == hour and 
                                   current_time.minute == minute)
                
                elif schedule_type == 'weekly':
                    weekday = config.get('weekday', 0)
                    hour = config.get('hour', 0)
                    minute = config.get('minute', 0)
                    should_execute = (current_time.weekday() == weekday and 
                                   current_time.hour == hour and 
                                   current_time.minute == minute)
                
                elif schedule_type == 'interval':
                    interval_minutes = config.get('interval_minutes', 60)
                    last_execution = trigger_info.get('last_execution')
                    
                    if not last_execution:
                        should_execute = True
                    else:
                        last_time = datetime.fromisoformat(last_execution)
                        if (current_time - last_time).total_seconds() >= interval_minutes * 60:
                            should_execute = True
                
                if should_execute:
                    # Execute workflow
                    self.execute_workflow(workflow_id)
                    
                    # Update last execution time
                    trigger_info['last_execution'] = current_time.isoformat()
    
    def _update_execution_status(self, execution_id: str, status: str, error_message: str = None):
        """Update workflow execution status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if status == WorkflowStatus.COMPLETED.value:
            cursor.execute('''
                UPDATE workflow_executions 
                SET status = ?, completed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (status, execution_id))
        else:
            cursor.execute('''
                UPDATE workflow_executions 
                SET status = ?, completed_at = CURRENT_TIMESTAMP, error_message = ?
                WHERE id = ?
            ''', (status, error_message, execution_id))
        
        conn.commit()
        conn.close()
    
    def _update_workflow_stats(self, workflow_id: str, success: bool):
        """Update workflow statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if success:
            cursor.execute('''
                UPDATE workflows 
                SET execution_count = execution_count + 1, 
                    success_count = success_count + 1,
                    last_executed = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (workflow_id,))
        else:
            cursor.execute('''
                UPDATE workflows 
                SET execution_count = execution_count + 1, 
                    failure_count = failure_count + 1,
                    last_executed = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (workflow_id,))
        
        conn.commit()
        conn.close()
    
    def _log_workflow_event(self, workflow_id: str, execution_id: str, 
                           log_level: str, message: str, metadata: Dict = None):
        """Log workflow event"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO workflow_logs (workflow_id, execution_id, log_level, message, metadata)
            VALUES (?, ?, ?, ?, ?)
        ''', (workflow_id, execution_id, log_level, message, 
              json.dumps(metadata or {})))
        
        conn.commit()
        conn.close()
    
    def _load_predefined_workflows(self):
        """Load predefined workflows"""
        predefined_workflows = [
            {
                'name': 'Daily Backup',
                'description': 'Automatically backup database daily',
                'trigger_type': TriggerType.SCHEDULED.value,
                'trigger_config': {
                    'schedule_type': 'daily',
                    'hour': 2,
                    'minute': 0
                },
                'actions': [
                    {
                        'type': ActionType.SYNC_CLOUD.value,
                        'params': {
                            'provider': 'google_drive',
                            'backup_type': 'database'
                        }
                    }
                ],
                'conditions': []
            },
            {
                'name': 'Weekly Report',
                'description': 'Generate weekly analytics report',
                'trigger_type': TriggerType.SCHEDULED.value,
                'trigger_config': {
                    'schedule_type': 'weekly',
                    'weekday': 0,  # Monday
                    'hour': 9,
                    'minute': 0
                },
                'actions': [
                    {
                        'type': ActionType.GENERATE_REPORT.value,
                        'params': {
                            'report_type': 'weekly_summary',
                            'format': 'pdf'
                        }
                    },
                    {
                        'type': ActionType.SEND_EMAIL.value,
                        'params': {
                            'to': 'admin@company.com',
                            'subject': 'Weekly Report',
                            'body': 'Weekly analytics report is ready'
                        }
                    }
                ],
                'conditions': []
            },
            {
                'name': 'PO Creation Notification',
                'description': 'Notify users when PO is created',
                'trigger_type': TriggerType.EVENT_BASED.value,
                'trigger_config': {
                    'event': 'po_created'
                },
                'actions': [
                    {
                        'type': ActionType.NOTIFY_USER.value,
                        'params': {
                            'message': 'New PO created: {{po_number}}',
                            'type': 'success'
                        }
                    }
                ],
                'conditions': [
                    {
                        'type': 'data_exists',
                        'params': {
                            'field': 'po_number'
                        }
                    }
                ]
            }
        ]
        
        # Create predefined workflows
        for workflow_data in predefined_workflows:
            try:
                self.create_workflow(workflow_data)
            except Exception as e:
                print(f"Error creating predefined workflow {workflow_data['name']}: {e}")
    
    def get_workflow_statistics(self) -> Dict:
        """Get workflow statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total workflows
        cursor.execute('SELECT COUNT(*) FROM workflows')
        total_workflows = cursor.fetchone()[0]
        
        # Active workflows
        cursor.execute('SELECT COUNT(*) FROM workflows WHERE is_active = 1')
        active_workflows = cursor.fetchone()[0]
        
        # Total executions
        cursor.execute('SELECT COUNT(*) FROM workflow_executions')
        total_executions = cursor.fetchone()[0]
        
        # Successful executions
        cursor.execute('SELECT COUNT(*) FROM workflow_executions WHERE status = ?', 
                      (WorkflowStatus.COMPLETED.value,))
        successful_executions = cursor.fetchone()[0]
        
        # Failed executions
        cursor.execute('SELECT COUNT(*) FROM workflow_executions WHERE status = ?', 
                      (WorkflowStatus.FAILED.value,))
        failed_executions = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_workflows': total_workflows,
            'active_workflows': active_workflows,
            'total_executions': total_executions,
            'successful_executions': successful_executions,
            'failed_executions': failed_executions,
            'success_rate': (successful_executions / max(total_executions, 1)) * 100
        }

# Global instance
workflow_manager = WorkflowManager()
