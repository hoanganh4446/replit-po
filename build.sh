#!/bin/bash
# Build script for Render.com deployment

echo "🚀 Building PO System for Render.com..."

# Create necessary directories
mkdir -p logs
mkdir -p output
mkdir -p config/database

# Set permissions
chmod 755 logs
chmod 755 output
chmod 755 config/database

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Create database if not exists
echo "🗄️ Initializing database..."
python -c "
import os
import sqlite3
from src.apps.app import DatabaseManager

# Initialize database
db_manager = DatabaseManager()
print('Database initialized successfully')
"

echo "✅ Build completed successfully!"
echo "🌐 Ready for deployment on Render.com"
