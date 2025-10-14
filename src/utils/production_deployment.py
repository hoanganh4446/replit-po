"""
Phase 4: Production-Ready Deployment
Hệ thống deployment production-ready với Docker, CI/CD và monitoring
"""

import os
import json
import subprocess
import yaml
from datetime import datetime
from typing import Dict, Any, List

class DockerManager:
    def __init__(self):
        self.docker_config = {
            'base_image': 'python:3.9-slim',
            'port': 5000,
            'environment': 'production'
        }
    
    def generate_dockerfile(self):
        """Tạo Dockerfile cho production"""
        dockerfile_content = """
# Phase 4: Production Dockerfile
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    g++ \\
    libc6-dev \\
    libffi-dev \\
    libssl-dev \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements_phase3.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements_phase3.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs backups cache static/uploads

# Set environment variables
ENV FLASK_ENV=production
ENV FLASK_APP=app_phase3.py
ENV PYTHONPATH=/app

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://0.0.0.0:5000/health || exit 1

# Start application
CMD ["python", "app_phase3.py"]
"""
        
        with open('Dockerfile', 'w', encoding='utf-8') as f:
            f.write(dockerfile_content)
        
        print("Dockerfile generated successfully!")
    
    def generate_docker_compose(self):
        """Tạo docker-compose.yml cho production"""
        compose_content = """
version: '3.8'

services:
  po-system:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=sqlite:///app/po_system.db
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./backups:/app/backups
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://0.0.0.0:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - po-system
    restart: unless-stopped

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  redis_data:
"""
        
        with open('docker-compose.yml', 'w', encoding='utf-8') as f:
            f.write(compose_content)
        
        print("Docker Compose file generated successfully!")
    
    def generate_nginx_config(self):
        """Tạo nginx configuration"""
        nginx_config = """
events {
    worker_connections 1024;
}

http {
    upstream po_system {
        server po-system:5000;
    }

    server {
        listen 80;
        server_name 0.0.0.0;

        # Redirect HTTP to HTTPS
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name 0.0.0.0;

        # SSL configuration
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;

        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";

        # Proxy to Flask app
        location / {
            proxy_pass http://po_system;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Static files
        location /static {
            alias /app/static;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }

        # Health check
        location /health {
            proxy_pass http://po_system/health;
            access_log off;
        }
    }
}
"""
        
        with open('nginx.conf', 'w', encoding='utf-8') as f:
            f.write(nginx_config)
        
        print("Nginx configuration generated successfully!")

class CICDManager:
    def __init__(self):
        self.github_actions_config = {}
    
    def generate_github_actions(self):
        """Tạo GitHub Actions workflow"""
        workflow_content = """
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements_phase3.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: |
        python final_testing.py
    
    - name: Run code quality check
      run: |
        pip install flake8 black
        flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
        black --check .
    
    - name: Upload test results
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: test-results
        path: test_results.json

  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Build Docker image
      run: |
        docker build -t po-system:latest .
    
    - name: Run security scan
      run: |
        docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \\
          aquasec/trivy image po-system:latest
    
    - name: Push to registry
      run: |
        echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
        docker tag po-system:latest ${{ secrets.DOCKER_USERNAME }}/po-system:latest
        docker push ${{ secrets.DOCKER_USERNAME }}/po-system:latest

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - name: Deploy to production
      run: |
        echo "Deploying to production server..."
        # Add your deployment commands here
"""
        
        # Tạo thư mục .github/workflows
        os.makedirs('.github/workflows', exist_ok=True)
        
        with open('.github/workflows/ci-cd.yml', 'w', encoding='utf-8') as f:
            f.write(workflow_content)
        
        print("GitHub Actions workflow generated successfully!")
    
    def generate_deployment_script(self):
        """Tạo deployment script"""
        deploy_script = """#!/bin/bash

# Phase 4: Production Deployment Script

set -e

echo "Starting production deployment..."

# Configuration
APP_NAME="po-system"
DOCKER_IMAGE="$APP_NAME:latest"
CONTAINER_NAME="$APP_NAME-prod"
PORT=5000

# Colors for output
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
NC='\\033[0m' # No Color

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    log_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

# Stop existing container
if docker ps -q -f name=$CONTAINER_NAME | grep -q .; then
    log_info "Stopping existing container..."
    docker stop $CONTAINER_NAME
fi

# Remove existing container
if docker ps -aq -f name=$CONTAINER_NAME | grep -q .; then
    log_info "Removing existing container..."
    docker rm $CONTAINER_NAME
fi

# Pull latest image
log_info "Pulling latest image..."
docker pull $DOCKER_IMAGE

# Create necessary directories
log_info "Creating necessary directories..."
mkdir -p data logs backups cache ssl

# Generate SSL certificates (self-signed for development)
if [ ! -f ssl/cert.pem ]; then
    log_info "Generating SSL certificates..."
    openssl req -x509 -newkey rsa:4096 -keyout ssl/key.pem -out ssl/cert.pem -days 365 -nodes -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
fi

# Start new container
log_info "Starting new container..."
docker run -d \\
    --name $CONTAINER_NAME \\
    --restart unless-stopped \\
    -p $PORT:5000 \\
    -v $(pwd)/data:/app/data \\
    -v $(pwd)/logs:/app/logs \\
    -v $(pwd)/backups:/app/backups \\
    -e FLASK_ENV=production \\
    $DOCKER_IMAGE

# Wait for container to start
log_info "Waiting for container to start..."
sleep 10

# Check if container is running
if docker ps -q -f name=$CONTAINER_NAME | grep -q .; then
    log_info "Container started successfully!"
    
    # Check health
    log_info "Checking application health..."
    if curl -f http://0.0.0.0:$PORT/health > /dev/null 2>&1; then
        log_info "Application is healthy!"
    else
        log_warn "Application health check failed. Check logs with: docker logs $CONTAINER_NAME"
    fi
    
    # Show container status
    log_info "Container status:"
    docker ps -f name=$CONTAINER_NAME
    
    log_info "Deployment completed successfully!"
    log_info "Application is available at: http://0.0.0.0:$PORT"
    
else
    log_error "Failed to start container. Check logs with: docker logs $CONTAINER_NAME"
    exit 1
fi
"""
        
        with open('deploy.sh', 'w', encoding='utf-8') as f:
            f.write(deploy_script)
        
        # Make script executable
        os.chmod('deploy.sh', 0o755)
        
        print("Deployment script generated successfully!")

class ProductionConfig:
    def __init__(self):
        self.config = {}
    
    def generate_production_config(self):
        """Tạo production configuration"""
        config = {
            'app': {
                'name': 'PO System',
                'version': '4.0.0',
                'environment': 'production',
                'debug': False,
                'host': '0.0.0.0',
                'port': 5000
            },
            'database': {
                'type': 'sqlite',
                'path': 'po_system.db',
                'backup_interval': 24,  # hours
                'retention_days': 30
            },
            'security': {
                'secret_key': 'CHANGE_THIS_IN_PRODUCTION',
                'session_timeout': 3600,  # seconds
                'max_login_attempts': 5,
                'password_min_length': 8,
                'require_https': True
            },
            'logging': {
                'level': 'INFO',
                'file': 'logs/app.log',
                'max_size': '10MB',
                'backup_count': 5,
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            },
            'monitoring': {
                'enabled': True,
                'metrics_interval': 30,  # seconds
                'alert_thresholds': {
                    'cpu_percent': 80,
                    'memory_percent': 85,
                    'disk_percent': 90
                }
            },
            'backup': {
                'enabled': True,
                'full_backup_interval': 7,  # days
                'incremental_backup_interval': 1,  # days
                'retention_days': 30,
                'compression': True
            },
            'cache': {
                'enabled': True,
                'type': 'memory',
                'ttl': 3600,  # seconds
                'max_size': '100MB'
            },
            'api': {
                'rate_limit': '1000/hour',
                'cors_enabled': True,
                'cors_origins': ['https://yourdomain.com'],
                'api_key_required': False
            }
        }
        
        with open('config_production.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print("Production configuration generated successfully!")
    
    def generate_environment_file(self):
        """Tạo .env file cho production"""
        env_content = """
# Phase 4: Production Environment Variables

# Application
FLASK_ENV=production
FLASK_APP=app_phase3.py
SECRET_KEY=CHANGE_THIS_IN_PRODUCTION_TO_A_SECURE_RANDOM_KEY

# Database
DATABASE_URL=sqlite:///po_system.db

# Security
SESSION_TIMEOUT=3600
MAX_LOGIN_ATTEMPTS=5
PASSWORD_MIN_LENGTH=8

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# Monitoring
MONITORING_ENABLED=true
METRICS_INTERVAL=30

# Backup
BACKUP_ENABLED=true
BACKUP_RETENTION_DAYS=30

# Cache
CACHE_ENABLED=true
CACHE_TTL=3600

# API
API_RATE_LIMIT=1000/hour
API_CORS_ENABLED=true

# SSL/TLS
SSL_CERT_PATH=ssl/cert.pem
SSL_KEY_PATH=ssl/key.pem
"""
        
        with open('.env.production', 'w', encoding='utf-8') as f:
            f.write(env_content)
        
        print("Environment file generated successfully!")

class HealthCheckEndpoint:
    def __init__(self):
        self.health_endpoints = {}
    
    def generate_health_endpoint(self):
        """Tạo health check endpoint cho Flask app"""
        health_code = '''
from flask import Flask, jsonify
import os
import sqlite3
import psutil
from datetime import datetime

def create_health_endpoint(app):
    """Add health check endpoint to Flask app"""
    
    @app.route('/health')
    def health_check():
        """Health check endpoint for monitoring"""
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '4.0.0',
            'checks': {}
        }
        
        # Database check
        try:
            conn = sqlite3.connect('po_system.db')
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            conn.close()
            health_status['checks']['database'] = 'healthy'
        except Exception as e:
            health_status['checks']['database'] = f'unhealthy: {str(e)}'
            health_status['status'] = 'unhealthy'
        
        # Disk space check
        try:
            disk_usage = psutil.disk_usage('/')
            free_percent = (disk_usage.free / disk_usage.total) * 100
            if free_percent > 10:  # More than 10% free
                health_status['checks']['disk_space'] = 'healthy'
            else:
                health_status['checks']['disk_space'] = f'unhealthy: {free_percent:.1f}% free'
                health_status['status'] = 'unhealthy'
        except Exception as e:
            health_status['checks']['disk_space'] = f'unhealthy: {str(e)}'
            health_status['status'] = 'unhealthy'
        
        # Memory check
        try:
            memory = psutil.virtual_memory()
            if memory.percent < 90:  # Less than 90% used
                health_status['checks']['memory'] = 'healthy'
            else:
                health_status['checks']['memory'] = f'unhealthy: {memory.percent:.1f}% used'
                health_status['status'] = 'unhealthy'
        except Exception as e:
            health_status['checks']['memory'] = f'unhealthy: {str(e)}'
            health_status['status'] = 'unhealthy'
        
        # File system check
        try:
            required_files = ['app_phase3.py', 'po_system.db']
            for file in required_files:
                if not os.path.exists(file):
                    health_status['checks']['files'] = f'unhealthy: {file} missing'
                    health_status['status'] = 'unhealthy'
                    break
            else:
                health_status['checks']['files'] = 'healthy'
        except Exception as e:
            health_status['checks']['files'] = f'unhealthy: {str(e)}'
            health_status['status'] = 'unhealthy'
        
        # Return appropriate HTTP status code
        status_code = 200 if health_status['status'] == 'healthy' else 503
        
        return jsonify(health_status), status_code
    
    @app.route('/metrics')
    def metrics():
        """Prometheus-style metrics endpoint"""
        try:
            # System metrics
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            metrics = f"""# HELP system_cpu_percent CPU usage percentage
# TYPE system_cpu_percent gauge
system_cpu_percent {cpu_percent}

# HELP system_memory_percent Memory usage percentage
# TYPE system_memory_percent gauge
system_memory_percent {memory.percent}

# HELP system_disk_percent Disk usage percentage
# TYPE system_disk_percent gauge
system_disk_percent {(disk.used / disk.total) * 100}

# HELP app_uptime_seconds Application uptime in seconds
# TYPE app_uptime_seconds counter
app_uptime_seconds {psutil.Process().create_time()}
"""
            
            return metrics, 200, {'Content-Type': 'text/plain'}
            
        except Exception as e:
            return f"# ERROR: {str(e)}", 500, {'Content-Type': 'text/plain'}
'''
        
        with open('health_endpoint.py', 'w', encoding='utf-8') as f:
            f.write(health_code)
        
        print("Health check endpoint generated successfully!")

# Global instances
docker_manager = DockerManager()
cicd_manager = CICDManager()
production_config = ProductionConfig()
health_check = HealthCheckEndpoint()

def init_production_deployment():
    """Khởi tạo production deployment"""
    print("Initializing production deployment...")
    
    # Generate Docker files
    docker_manager.generate_dockerfile()
    docker_manager.generate_docker_compose()
    docker_manager.generate_nginx_config()
    
    # Generate CI/CD files
    cicd_manager.generate_github_actions()
    cicd_manager.generate_deployment_script()
    
    # Generate production configuration
    production_config.generate_production_config()
    production_config.generate_environment_file()
    
    # Generate health check endpoint
    health_check.generate_health_endpoint()
    
    # Generate deployment documentation
    generate_deployment_docs()
    
    print("Production deployment setup completed successfully!")
    print("\\nNext steps:")
    print("1. Review and update configuration files")
    print("2. Set up SSL certificates")
    print("3. Configure environment variables")
    print("4. Run: ./deploy.sh")

def generate_deployment_docs():
    """Tạo deployment documentation"""
    docs_content = """# Phase 4: Production Deployment Guide

## Overview
This guide covers deploying the PO System to production using Docker and modern DevOps practices.

## Prerequisites
- Docker and Docker Compose installed
- SSL certificates (for HTTPS)
- Domain name configured
- Server with at least 2GB RAM and 10GB disk space

## Quick Start

### 1. Clone and Setup
```bash
git clone <your-repo>
cd po-system
cp .env.production .env
```

### 2. Configure Environment
Edit `.env` file with your production settings:
```bash
SECRET_KEY=your-secure-secret-key
DATABASE_URL=sqlite:///po_system.db
```

### 3. Deploy
```bash
chmod +x deploy.sh
./deploy.sh
```

## Manual Deployment

### Using Docker Compose
```bash
docker-compose up -d
```

### Using Docker
```bash
docker build -t po-system:latest .
docker run -d -p 5000:5000 --name po-system-prod po-system:latest
```

## Configuration

### Environment Variables
- `FLASK_ENV=production`
- `SECRET_KEY` - Secure random key
- `DATABASE_URL` - Database connection string
- `LOG_LEVEL` - Logging level (INFO, DEBUG, etc.)

### SSL/TLS Setup
1. Obtain SSL certificates
2. Place certificates in `ssl/` directory
3. Update nginx configuration if needed

## Monitoring

### Health Checks
- Application: `http://0.0.0.0:5000/health`
- Metrics: `http://0.0.0.0:5000/metrics`

### Logs
```bash
docker logs po-system-prod
```

### Backup
Backups are automatically created and stored in `backups/` directory.

## Security

### Production Checklist
- [ ] Change default secret key
- [ ] Enable HTTPS
- [ ] Configure firewall
- [ ] Regular security updates
- [ ] Monitor logs
- [ ] Backup strategy

### Firewall Rules
```bash
# Allow HTTP/HTTPS
ufw allow 80
ufw allow 443

# Allow SSH (if needed)
ufw allow 22
```

## Troubleshooting

### Common Issues
1. **Container won't start**: Check logs with `docker logs po-system-prod`
2. **Database errors**: Ensure database file permissions
3. **SSL errors**: Verify certificate paths and permissions
4. **Performance issues**: Check resource usage with `docker stats`

### Logs
- Application logs: `logs/app.log`
- Error logs: `logs/errors.log`
- Security logs: `logs/security.log`

## Maintenance

### Updates
1. Pull latest code
2. Rebuild Docker image
3. Deploy with `./deploy.sh`

### Backup
- Full backups: Weekly
- Incremental backups: Daily
- Retention: 30 days

### Monitoring
- CPU usage < 80%
- Memory usage < 85%
- Disk usage < 90%

## Support
For issues and support, check:
1. Application logs
2. Health check endpoint
3. System metrics
4. Documentation

## Performance Optimization

### Production Settings
- Enable caching
- Use production WSGI server
- Configure reverse proxy
- Enable compression
- Set up CDN (if needed)

### Scaling
- Horizontal scaling with load balancer
- Database optimization
- Caching layer (Redis)
- Static file serving
"""
    
    with open('DEPLOYMENT_PRODUCTION.md', 'w', encoding='utf-8') as f:
        f.write(docs_content)
    
    print("Deployment documentation generated successfully!")

if __name__ == "__main__":
    init_production_deployment()
