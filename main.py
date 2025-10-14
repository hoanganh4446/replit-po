"""
Main entry point for Replit deployment
PO System - Production Order Management System
"""

import os
import sys
from flask import Flask

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Import the Flask app from src/apps/app.py
from src.apps.app import app

if __name__ == "__main__":
    # Get port from environment variable (Replit requirement)
    port = int(os.environ.get("PORT", 5000))
    
    # Run the Flask app
    app.run(
        host="0.0.0.0",  # Required for Replit
        port=port,
        debug=True  # Enable debug mode for development
    )
