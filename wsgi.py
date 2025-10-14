"""
WSGI entry point for Render.com deployment
"""
import os
import sys

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Import the Flask app
from src.apps.app import app

if __name__ == "__main__":
    app.run()
