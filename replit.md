# PO System - Production Order Management System

## Overview
This is a Flask-based Production Order Management System (Hệ thống quản lý đơn hàng sản xuất) that helps manage and generate Excel PO files automatically. The system includes features for analytics, bulk operations, advanced search, and user management.

## Project Status
- **Setup Date**: October 14, 2025
- **Current State**: Successfully deployed and running on Replit
- **Language**: Python 3.11 with Flask 2.3.3
- **Database**: SQLite (local)

## Architecture

### Tech Stack
- **Backend**: Flask (Python)
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap
- **Database**: SQLite
- **Excel Processing**: openpyxl
- **Production Server**: Gunicorn

### Project Structure
```
po-system-deployment/
├── main.py                 # Entry point for Replit
├── requirements.txt        # Python dependencies
├── src/
│   ├── apps/
│   │   └── app.py         # Main Flask application
│   ├── core/              # Core modules
│   ├── managers/          # Business logic managers
│   └── utils/             # Utility functions
├── web/
│   ├── templates/         # HTML templates
│   └── static/            # CSS, JS, images
├── products/              # Product configurations and templates
├── output/                # Generated PO files
├── config/database/       # SQLite database
└── logs/                  # Application logs
```

### Key Features
- Dashboard analytics with real-time data
- Bulk operations for processing multiple POs
- Advanced search functionality
- Data export/import capabilities
- User management and authentication
- Real-time system monitoring

## Configuration

### Environment
- **Port**: 5000 (development and production)
- **Host**: 0.0.0.0 (allows Replit proxy access)
- **Debug Mode**: Enabled in development

### Database
- **Type**: SQLite
- **Location**: `config/database/po_system.db`
- **Tables**: users, sessions, operations, analytics

### Default Credentials
- Username: admin
- Password: admin123

## Running the Application

### Development
The Flask development server runs automatically:
- Command: `python main.py`
- URL: Accessible via Replit webview

### Production Deployment
- Platform: Replit Autoscale deployment
- Server: Gunicorn with --reuse-port flag
- Command: `gunicorn --bind 0.0.0.0:5000 --reuse-port src.apps.app:app`

## Recent Changes
- **2025-10-14**: Initial setup on Replit
  - Installed Python 3.11 and all dependencies
  - Fixed template/static folder paths to use absolute paths
  - Created required directories (logs, config/database, output)
  - Configured deployment with Gunicorn
  - Verified app is working correctly with login page

## Known Issues
- Minor 404 for favicon.ico (cosmetic, no impact on functionality)

## Notes
- The app uses openpyxl for Excel file generation (xlwings removed for Replit compatibility)
- Products folder contains Excel templates for each product type
- All paths are configured to work with Replit's file system structure
