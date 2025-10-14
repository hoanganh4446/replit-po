"""
Dashboard & Analytics Module
Provides comprehensive dashboard with charts and analytics
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from database import db_manager

class DashboardAnalytics:
    """Dashboard analytics and chart data provider"""
    
    def __init__(self):
        self.chart_types = {
            'line': 'Line Chart',
            'bar': 'Bar Chart',
            'pie': 'Pie Chart',
            'doughnut': 'Doughnut Chart',
            'area': 'Area Chart'
        }
    
    def get_dashboard_data(self, period_days: int = 30) -> Dict:
        """Get complete dashboard data"""
        return {
            'overview': self.get_overview_stats(period_days),
            'charts': self.get_chart_data(period_days),
            'recent_activity': self.get_recent_activity(),
            'top_products': self.get_top_products(period_days),
            'performance_metrics': self.get_performance_metrics(period_days)
        }
    
    def get_overview_stats(self, period_days: int = 30) -> Dict:
        """Get overview statistics"""
        stats = db_manager.get_statistics(period_days)
        
        # Calculate additional stats
        total_files = stats['total_files']
        product_count = len(stats['product_stats'])
        
        # Calculate growth
        current_period = sum([day[1] for day in stats['daily_stats'][:7]])  # Last 7 days
        previous_period = sum([day[1] for day in stats['daily_stats'][7:14]])  # Previous 7 days
        
        growth_rate = 0
        if previous_period > 0:
            growth_rate = ((current_period - previous_period) / previous_period) * 100
        
        return {
            'total_files': total_files,
            'active_products': product_count,
            'period_files': sum([day[1] for day in stats['daily_stats']]),
            'growth_rate': round(growth_rate, 2),
            'avg_daily': round(sum([day[1] for day in stats['daily_stats']]) / period_days, 2),
            'period_days': period_days
        }
    
    def get_chart_data(self, period_days: int = 30) -> Dict:
        """Get data for all charts"""
        return {
            'daily_activity': self.get_daily_activity_chart(period_days),
            'product_distribution': self.get_product_distribution_chart(period_days),
            'monthly_trend': self.get_monthly_trend_chart(),
            'hourly_activity': self.get_hourly_activity_chart(period_days)
        }
    
    def get_daily_activity_chart(self, period_days: int = 30) -> Dict:
        """Get daily activity chart data"""
        stats = db_manager.get_statistics(period_days)
        
        labels = []
        data = []
        
        for day_stat in reversed(stats['daily_stats']):  # Reverse to get chronological order
            labels.append(day_stat[0])
            data.append(day_stat[1])
        
        return {
            'type': 'line',
            'title': 'Hoạt động hàng ngày',
            'labels': labels,
            'datasets': [{
                'label': 'Số file tạo',
                'data': data,
                'borderColor': '#667eea',
                'backgroundColor': 'rgba(102, 126, 234, 0.1)',
                'fill': True
            }]
        }
    
    def get_product_distribution_chart(self, period_days: int = 30) -> Dict:
        """Get product distribution pie chart data"""
        stats = db_manager.get_statistics(period_days)
        
        labels = []
        data = []
        colors = [
            '#667eea', '#764ba2', '#f093fb', '#f5576c',
            '#4facfe', '#00f2fe', '#43e97b', '#38f9d7',
            '#ffecd2', '#fcb69f', '#a8edea', '#fed6e3'
        ]
        
        for product_stat in stats['product_stats'][:10]:  # Top 10 products
            labels.append(product_stat[0])
            data.append(product_stat[1])
        
        return {
            'type': 'doughnut',
            'title': 'Phân bố sản phẩm',
            'labels': labels,
            'datasets': [{
                'data': data,
                'backgroundColor': colors[:len(labels)],
                'borderWidth': 2,
                'borderColor': '#ffffff'
            }]
        }
    
    def get_monthly_trend_chart(self) -> Dict:
        """Get monthly trend chart data"""
        conn = db_manager.db_path
        import sqlite3
        
        conn = sqlite3.connect(conn)
        cursor = conn.cursor()
        
        # Get monthly data for last 12 months
        cursor.execute('''
            SELECT strftime('%Y-%m', created_at) as month, COUNT(*) as count
            FROM po_history
            WHERE created_at >= date('now', '-12 months')
            GROUP BY strftime('%Y-%m', created_at)
            ORDER BY month
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        labels = []
        data = []
        
        for row in rows:
            labels.append(row[0])
            data.append(row[1])
        
        return {
            'type': 'bar',
            'title': 'Xu hướng hàng tháng',
            'labels': labels,
            'datasets': [{
                'label': 'Số file tạo',
                'data': data,
                'backgroundColor': 'rgba(102, 126, 234, 0.8)',
                'borderColor': '#667eea',
                'borderWidth': 1
            }]
        }
    
    def get_hourly_activity_chart(self, period_days: int = 30) -> Dict:
        """Get hourly activity chart data"""
        conn = db_manager.db_path
        import sqlite3
        
        conn = sqlite3.connect(conn)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT strftime('%H', created_at) as hour, COUNT(*) as count
            FROM po_history
            WHERE created_at >= date('now', '-{} days')
            GROUP BY strftime('%H', created_at)
            ORDER BY hour
        '''.format(period_days))
        
        rows = cursor.fetchall()
        conn.close()
        
        # Create full 24-hour data
        hourly_data = [0] * 24
        for row in rows:
            hour = int(row[0])
            hourly_data[hour] = row[1]
        
        labels = [f"{i:02d}:00" for i in range(24)]
        
        return {
            'type': 'area',
            'title': 'Hoạt động theo giờ',
            'labels': labels,
            'datasets': [{
                'label': 'Số file tạo',
                'data': hourly_data,
                'backgroundColor': 'rgba(102, 126, 234, 0.3)',
                'borderColor': '#667eea',
                'fill': True
            }]
        }
    
    def get_recent_activity(self, limit: int = 10) -> List[Dict]:
        """Get recent activity"""
        return db_manager.get_po_history(limit=limit)
    
    def get_top_products(self, period_days: int = 30) -> List[Dict]:
        """Get top products by usage"""
        stats = db_manager.get_statistics(period_days)
        
        top_products = []
        for product_stat in stats['product_stats'][:5]:
            top_products.append({
                'product_id': product_stat[0],
                'count': product_stat[1],
                'percentage': round((product_stat[1] / sum([p[1] for p in stats['product_stats']])) * 100, 1)
            })
        
        return top_products
    
    def get_performance_metrics(self, period_days: int = 30) -> Dict:
        """Get performance metrics"""
        conn = db_manager.db_path
        import sqlite3
        
        conn = sqlite3.connect(conn)
        cursor = conn.cursor()
        
        # Average files per day
        cursor.execute('''
            SELECT AVG(daily_count) FROM (
                SELECT DATE(created_at) as date, COUNT(*) as daily_count
                FROM po_history
                WHERE created_at >= date('now', '-{} days')
                GROUP BY DATE(created_at)
            )
        '''.format(period_days))
        
        avg_daily = cursor.fetchone()[0] or 0
        
        # Peak day
        cursor.execute('''
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM po_history
            WHERE created_at >= date('now', '-{} days')
            GROUP BY DATE(created_at)
            ORDER BY count DESC
            LIMIT 1
        '''.format(period_days))
        
        peak_day = cursor.fetchone()
        
        # Most active hour
        cursor.execute('''
            SELECT strftime('%H', created_at) as hour, COUNT(*) as count
            FROM po_history
            WHERE created_at >= date('now', '-{} days')
            GROUP BY strftime('%H', created_at)
            ORDER BY count DESC
            LIMIT 1
        '''.format(period_days))
        
        peak_hour = cursor.fetchone()
        
        conn.close()
        
        return {
            'avg_daily_files': round(avg_daily, 2),
            'peak_day': {
                'date': peak_day[0] if peak_day else None,
                'count': peak_day[1] if peak_day else 0
            },
            'peak_hour': {
                'hour': peak_hour[0] if peak_hour else None,
                'count': peak_hour[1] if peak_hour else 0
            }
        }
    
    def get_export_data(self, period_days: int = 30, format: str = 'json') -> str:
        """Get dashboard data for export"""
        data = self.get_dashboard_data(period_days)
        
        if format == 'json':
            return json.dumps(data, indent=2, ensure_ascii=False)
        elif format == 'csv':
            # Convert to CSV format
            csv_data = []
            
            # Overview stats
            csv_data.append(['Metric', 'Value'])
            for key, value in data['overview'].items():
                csv_data.append([key, value])
            
            # Top products
            csv_data.append(['', ''])
            csv_data.append(['Product ID', 'Count', 'Percentage'])
            for product in data['top_products']:
                csv_data.append([product['product_id'], product['count'], product['percentage']])
            
            # Convert to CSV string
            csv_string = '\n'.join([','.join([str(cell) for cell in row]) for row in csv_data])
            return csv_string
        
        return str(data)
    
    def get_custom_chart(self, chart_type: str, data_source: str, 
                        period_days: int = 30, filters: Dict = None) -> Dict:
        """Get custom chart data"""
        if chart_type == 'line':
            return self.get_daily_activity_chart(period_days)
        elif chart_type == 'pie':
            return self.get_product_distribution_chart(period_days)
        elif chart_type == 'bar':
            return self.get_monthly_trend_chart()
        elif chart_type == 'area':
            return self.get_hourly_activity_chart(period_days)
        else:
            return {}
    
    def get_dashboard_widgets(self) -> List[Dict]:
        """Get dashboard widget configurations"""
        return [
            {
                'id': 'overview_stats',
                'title': 'Tổng quan',
                'type': 'stats',
                'size': 'large',
                'position': {'x': 0, 'y': 0}
            },
            {
                'id': 'daily_activity',
                'title': 'Hoạt động hàng ngày',
                'type': 'chart',
                'chart_type': 'line',
                'size': 'large',
                'position': {'x': 0, 'y': 1}
            },
            {
                'id': 'product_distribution',
                'title': 'Phân bố sản phẩm',
                'type': 'chart',
                'chart_type': 'doughnut',
                'size': 'medium',
                'position': {'x': 1, 'y': 1}
            },
            {
                'id': 'top_products',
                'title': 'Sản phẩm phổ biến',
                'type': 'list',
                'size': 'medium',
                'position': {'x': 1, 'y': 0}
            },
            {
                'id': 'recent_activity',
                'title': 'Hoạt động gần đây',
                'type': 'table',
                'size': 'large',
                'position': {'x': 0, 'y': 2}
            },
            {
                'id': 'performance_metrics',
                'title': 'Chỉ số hiệu suất',
                'type': 'metrics',
                'size': 'medium',
                'position': {'x': 1, 'y': 2}
            }
        ]
    
    def save_dashboard_layout(self, layout: List[Dict]):
        """Save dashboard layout configuration"""
        db_manager.set_user_preference('dashboard_layout', json.dumps(layout))
    
    def get_dashboard_layout(self) -> List[Dict]:
        """Get saved dashboard layout"""
        layout_json = db_manager.get_user_preference('dashboard_layout')
        if layout_json:
            return json.loads(layout_json)
        return self.get_dashboard_widgets()

# Global instance
dashboard_analytics = DashboardAnalytics()

