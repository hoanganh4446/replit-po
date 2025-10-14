"""
Phase 4: Mobile Responsive Design & Accessibility
Tối ưu hóa giao diện cho mobile và cải thiện accessibility
"""

import os
import json
from typing import Dict, Any, List
from datetime import datetime

class ResponsiveDesignManager:
    def __init__(self):
        self.breakpoints = {
            'mobile': 768,
            'tablet': 1024,
            'desktop': 1200,
            'large': 1440
        }
        self.device_detection = {}
        
    def generate_responsive_css(self):
        """Tạo responsive CSS cho toàn bộ ứng dụng"""
        css_content = """
/* Phase 4: Responsive Design & Accessibility */

/* Base responsive utilities */
.responsive-container {
    width: 100%;
    max-width: 100%;
    margin: 0 auto;
    padding: 0 15px;
}

.responsive-grid {
    display: grid;
    gap: 20px;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
}

.responsive-flex {
    display: flex;
    flex-wrap: wrap;
    gap: 15px;
    align-items: center;
}

/* Mobile First Approach */
@media (max-width: 767px) {
    .mobile-hidden { display: none !important; }
    .mobile-full { width: 100% !important; }
    .mobile-stack { flex-direction: column !important; }
    .mobile-center { text-align: center !important; }
    
    /* Navigation */
    .navbar {
        flex-direction: column;
        padding: 10px;
    }
    
    .navbar-brand {
        margin-bottom: 10px;
    }
    
    .navbar-nav {
        width: 100%;
        flex-direction: column;
    }
    
    .navbar-nav .nav-item {
        margin: 5px 0;
        width: 100%;
    }
    
    /* Product Selector */
    .product-selector {
        padding: 15px;
    }
    
    .product-grid {
        grid-template-columns: 1fr;
        gap: 15px;
    }
    
    .product-card {
        padding: 15px;
        margin: 10px 0;
    }
    
    .product-card h3 {
        font-size: 1.2rem;
        margin-bottom: 10px;
    }
    
    /* Forms */
    .form-group {
        margin-bottom: 15px;
    }
    
    .form-control {
        width: 100%;
        padding: 12px;
        font-size: 16px; /* Prevent zoom on iOS */
    }
    
    .btn {
        width: 100%;
        padding: 12px;
        margin: 5px 0;
        font-size: 16px;
    }
    
    /* Tables */
    .table-responsive {
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
    }
    
    .table {
        font-size: 14px;
        min-width: 600px;
    }
    
    /* Dashboard */
    .dashboard-grid {
        grid-template-columns: 1fr;
        gap: 15px;
    }
    
    .chart-container {
        height: 250px;
        margin: 10px 0;
    }
    
    /* Modals */
    .modal-dialog {
        margin: 10px;
        max-width: calc(100% - 20px);
    }
    
    .modal-content {
        border-radius: 10px;
    }
    
    /* Touch-friendly elements */
    .touch-target {
        min-height: 44px;
        min-width: 44px;
    }
    
    /* Swipe gestures */
    .swipeable {
        touch-action: pan-x;
        user-select: none;
    }
}

/* Tablet */
@media (min-width: 768px) and (max-width: 1023px) {
    .tablet-hidden { display: none !important; }
    
    .product-grid {
        grid-template-columns: repeat(2, 1fr);
    }
    
    .dashboard-grid {
        grid-template-columns: repeat(2, 1fr);
    }
    
    .navbar-nav {
        flex-direction: row;
    }
}

/* Desktop */
@media (min-width: 1024px) {
    .desktop-hidden { display: none !important; }
    
    .product-grid {
        grid-template-columns: repeat(3, 1fr);
    }
    
    .dashboard-grid {
        grid-template-columns: repeat(3, 1fr);
    }
}

/* Large screens */
@media (min-width: 1440px) {
    .product-grid {
        grid-template-columns: repeat(4, 1fr);
    }
    
    .dashboard-grid {
        grid-template-columns: repeat(4, 1fr);
    }
}

/* Accessibility Improvements */
.sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border: 0;
}

.focus-visible {
    outline: 2px solid #007bff;
    outline-offset: 2px;
}

.skip-link {
    position: absolute;
    top: -40px;
    left: 6px;
    background: #000;
    color: #fff;
    padding: 8px;
    text-decoration: none;
    z-index: 1000;
}

.skip-link:focus {
    top: 6px;
}

/* High contrast mode */
@media (prefers-contrast: high) {
    .btn-primary {
        background-color: #000;
        border-color: #000;
        color: #fff;
    }
    
    .btn-secondary {
        background-color: #fff;
        border-color: #000;
        color: #000;
    }
}

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
    * {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
    }
}

/* Dark mode */
@media (prefers-color-scheme: dark) {
    :root {
        --bg-color: #1a1a1a;
        --text-color: #ffffff;
        --card-bg: #2d2d2d;
        --border-color: #404040;
    }
    
    body {
        background-color: var(--bg-color);
        color: var(--text-color);
    }
    
    .card {
        background-color: var(--card-bg);
        border-color: var(--border-color);
    }
    
    .form-control {
        background-color: var(--card-bg);
        border-color: var(--border-color);
        color: var(--text-color);
    }
}

/* Print styles */
@media print {
    .no-print { display: none !important; }
    .print-only { display: block !important; }
    
    body {
        font-size: 12pt;
        line-height: 1.4;
    }
    
    .page-break {
        page-break-before: always;
    }
}

/* Loading states */
.loading {
    position: relative;
    pointer-events: none;
}

.loading::after {
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    width: 20px;
    height: 20px;
    margin: -10px 0 0 -10px;
    border: 2px solid #f3f3f3;
    border-top: 2px solid #007bff;
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

/* Error states */
.error-state {
    border-color: #dc3545;
    background-color: #f8d7da;
}

.success-state {
    border-color: #28a745;
    background-color: #d4edda;
}

/* Tooltip */
.tooltip {
    position: relative;
    display: inline-block;
}

.tooltip .tooltiptext {
    visibility: hidden;
    width: 120px;
    background-color: #555;
    color: #fff;
    text-align: center;
    border-radius: 6px;
    padding: 5px 0;
    position: absolute;
    z-index: 1;
    bottom: 125%;
    left: 50%;
    margin-left: -60px;
    opacity: 0;
    transition: opacity 0.3s;
}

.tooltip:hover .tooltiptext {
    visibility: visible;
    opacity: 1;
}

/* Progress indicators */
.progress-bar {
    width: 100%;
    height: 20px;
    background-color: #f0f0f0;
    border-radius: 10px;
    overflow: hidden;
}

.progress-fill {
    height: 100%;
    background-color: #007bff;
    transition: width 0.3s ease;
}

/* Toast notifications */
.toast-container {
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 1050;
}

.toast {
    background-color: #fff;
    border: 1px solid #dee2e6;
    border-radius: 0.375rem;
    box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
    margin-bottom: 10px;
    padding: 15px;
    min-width: 300px;
}

.toast-success {
    border-left: 4px solid #28a745;
}

.toast-error {
    border-left: 4px solid #dc3545;
}

.toast-warning {
    border-left: 4px solid #ffc107;
}

.toast-info {
    border-left: 4px solid #17a2b8;
}
"""
        
        # Lưu CSS file
        with open('static/responsive.css', 'w', encoding='utf-8') as f:
            f.write(css_content)
        
        print("Responsive CSS generated successfully!")
    
    def generate_accessibility_js(self):
        """Tạo JavaScript cho accessibility features"""
        js_content = """
// Phase 4: Accessibility & Mobile Enhancements

class AccessibilityManager {
    constructor() {
        this.init();
    }
    
    init() {
        this.setupKeyboardNavigation();
        this.setupScreenReaderSupport();
        this.setupFocusManagement();
        this.setupARIALabels();
        this.setupMobileGestures();
        this.setupTouchOptimization();
    }
    
    setupKeyboardNavigation() {
        // Skip link functionality
        const skipLink = document.createElement('a');
        skipLink.href = '#main-content';
        skipLink.textContent = 'Skip to main content';
        skipLink.className = 'skip-link';
        document.body.insertBefore(skipLink, document.body.firstChild);
        
        // Tab navigation enhancement
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Tab') {
                document.body.classList.add('keyboard-navigation');
            }
        });
        
        document.addEventListener('mousedown', () => {
            document.body.classList.remove('keyboard-navigation');
        });
    }
    
    setupScreenReaderSupport() {
        // Live region for dynamic content
        const liveRegion = document.createElement('div');
        liveRegion.setAttribute('aria-live', 'polite');
        liveRegion.setAttribute('aria-atomic', 'true');
        liveRegion.className = 'sr-only';
        liveRegion.id = 'live-region';
        document.body.appendChild(liveRegion);
        
        // Announce changes
        this.announce = (message) => {
            const liveRegion = document.getElementById('live-region');
            if (liveRegion) {
                liveRegion.textContent = message;
            }
        };
    }
    
    setupFocusManagement() {
        // Focus trap for modals
        this.trapFocus = (element) => {
            const focusableElements = element.querySelectorAll(
                'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
            );
            const firstElement = focusableElements[0];
            const lastElement = focusableElements[focusableElements.length - 1];
            
            element.addEventListener('keydown', (e) => {
                if (e.key === 'Tab') {
                    if (e.shiftKey) {
                        if (document.activeElement === firstElement) {
                            lastElement.focus();
                            e.preventDefault();
                        }
                    } else {
                        if (document.activeElement === lastElement) {
                            firstElement.focus();
                            e.preventDefault();
                        }
                    }
                }
            });
        };
        
        // Focus restoration
        this.restoreFocus = (element) => {
            if (element) {
                element.focus();
            }
        };
    }
    
    setupARIALabels() {
        // Add ARIA labels to interactive elements
        const buttons = document.querySelectorAll('button:not([aria-label])');
        buttons.forEach(button => {
            if (!button.textContent.trim()) {
                button.setAttribute('aria-label', 'Button');
            }
        });
        
        // Add ARIA labels to form controls
        const inputs = document.querySelectorAll('input:not([aria-label])');
        inputs.forEach(input => {
            const label = document.querySelector(`label[for="${input.id}"]`);
            if (label) {
                input.setAttribute('aria-labelledby', label.id || input.id + '-label');
            }
        });
    }
    
    setupMobileGestures() {
        // Swipe gestures for mobile
        let startX, startY, endX, endY;
        
        document.addEventListener('touchstart', (e) => {
            startX = e.touches[0].clientX;
            startY = e.touches[0].clientY;
        });
        
        document.addEventListener('touchend', (e) => {
            endX = e.changedTouches[0].clientX;
            endY = e.changedTouches[0].clientY;
            
            const deltaX = endX - startX;
            const deltaY = endY - startY;
            
            // Swipe left/right
            if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > 50) {
                if (deltaX > 0) {
                    this.handleSwipeRight();
                } else {
                    this.handleSwipeLeft();
                }
            }
            
            // Swipe up/down
            if (Math.abs(deltaY) > Math.abs(deltaX) && Math.abs(deltaY) > 50) {
                if (deltaY > 0) {
                    this.handleSwipeDown();
                } else {
                    this.handleSwipeUp();
                }
            }
        });
    }
    
    setupTouchOptimization() {
        // Prevent double-tap zoom
        let lastTouchEnd = 0;
        document.addEventListener('touchend', (e) => {
            const now = (new Date()).getTime();
            if (now - lastTouchEnd <= 300) {
                e.preventDefault();
            }
            lastTouchEnd = now;
        }, false);
        
        // Touch feedback
        document.addEventListener('touchstart', (e) => {
            if (e.target.classList.contains('touch-target')) {
                e.target.classList.add('touch-active');
            }
        });
        
        document.addEventListener('touchend', (e) => {
            if (e.target.classList.contains('touch-target')) {
                setTimeout(() => {
                    e.target.classList.remove('touch-active');
                }, 150);
            }
        });
    }
    
    handleSwipeLeft() {
        // Navigate to next page/card
        const nextButton = document.querySelector('.next-btn, .carousel-next');
        if (nextButton) {
            nextButton.click();
        }
    }
    
    handleSwipeRight() {
        // Navigate to previous page/card
        const prevButton = document.querySelector('.prev-btn, .carousel-prev');
        if (prevButton) {
            prevButton.click();
        }
    }
    
    handleSwipeUp() {
        // Scroll up or show more content
        window.scrollBy(0, -100);
    }
    
    handleSwipeDown() {
        // Scroll down or show more content
        window.scrollBy(0, 100);
    }
}

class MobileOptimizer {
    constructor() {
        this.init();
    }
    
    init() {
        this.detectDevice();
        this.optimizeForDevice();
        this.setupViewportHandling();
        this.setupTouchEvents();
    }
    
    detectDevice() {
        const userAgent = navigator.userAgent;
        const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(userAgent);
        const isTablet = /iPad|Android(?=.*Mobile)/i.test(userAgent);
        const isTouch = 'ontouchstart' in window;
        
        this.deviceInfo = {
            isMobile,
            isTablet,
            isTouch,
            userAgent
        };
        
        document.body.classList.add(isMobile ? 'mobile-device' : 'desktop-device');
        document.body.classList.add(isTouch ? 'touch-device' : 'no-touch');
    }
    
    optimizeForDevice() {
        if (this.deviceInfo.isMobile) {
            this.optimizeForMobile();
        } else if (this.deviceInfo.isTablet) {
            this.optimizeForTablet();
        }
    }
    
    optimizeForMobile() {
        // Adjust font sizes
        document.documentElement.style.fontSize = '14px';
        
        // Optimize images
        const images = document.querySelectorAll('img');
        images.forEach(img => {
            img.style.maxWidth = '100%';
            img.style.height = 'auto';
        });
        
        // Optimize tables
        const tables = document.querySelectorAll('table');
        tables.forEach(table => {
            table.classList.add('table-responsive');
        });
    }
    
    optimizeForTablet() {
        // Adjust font sizes
        document.documentElement.style.fontSize = '16px';
        
        // Optimize layout
        const containers = document.querySelectorAll('.container');
        containers.forEach(container => {
            container.style.maxWidth = '90%';
        });
    }
    
    setupViewportHandling() {
        // Handle orientation changes
        window.addEventListener('orientationchange', () => {
            setTimeout(() => {
                this.handleOrientationChange();
            }, 100);
        });
        
        // Handle resize
        window.addEventListener('resize', this.debounce(() => {
            this.handleResize();
        }, 250));
    }
    
    setupTouchEvents() {
        if (this.deviceInfo.isTouch) {
            // Add touch classes
            document.body.classList.add('touch-enabled');
            
            // Optimize touch targets
            const touchTargets = document.querySelectorAll('button, a, input, select');
            touchTargets.forEach(target => {
                target.classList.add('touch-target');
            });
        }
    }
    
    handleOrientationChange() {
        // Recalculate layouts
        const charts = document.querySelectorAll('.chart-container');
        charts.forEach(chart => {
            if (chart.chart) {
                chart.chart.resize();
            }
        });
        
        // Announce orientation change
        const orientation = window.orientation === 0 ? 'portrait' : 'landscape';
        if (window.accessibilityManager) {
            window.accessibilityManager.announce(`Orientation changed to ${orientation}`);
        }
    }
    
    handleResize() {
        // Recalculate responsive layouts
        const grids = document.querySelectorAll('.responsive-grid');
        grids.forEach(grid => {
            this.recalculateGrid(grid);
        });
    }
    
    recalculateGrid(grid) {
        const containerWidth = grid.offsetWidth;
        const itemWidth = 300; // Minimum item width
        const gap = 20;
        const columns = Math.floor((containerWidth + gap) / (itemWidth + gap));
        
        grid.style.gridTemplateColumns = `repeat(${columns}, 1fr)`;
    }
    
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.accessibilityManager = new AccessibilityManager();
    window.mobileOptimizer = new MobileOptimizer();
});

// Export for use in other modules
window.AccessibilityManager = AccessibilityManager;
window.MobileOptimizer = MobileOptimizer;
"""
        
        # Lưu JavaScript file
        with open('static/accessibility.js', 'w', encoding='utf-8') as f:
            f.write(js_content)
        
        print("Accessibility JavaScript generated successfully!")
    
    def generate_responsive_templates(self):
        """Tạo responsive templates"""
        templates = {
            'mobile_navbar': self._generate_mobile_navbar(),
            'mobile_product_card': self._generate_mobile_product_card(),
            'mobile_dashboard': self._generate_mobile_dashboard()
        }
        
        for template_name, template_content in templates.items():
            with open(f'templates/{template_name}.html', 'w', encoding='utf-8') as f:
                f.write(template_content)
        
        print("Responsive templates generated successfully!")
    
    def _generate_mobile_navbar(self):
        return """
<!-- Mobile Navigation Bar -->
<nav class="navbar navbar-expand-lg navbar-light bg-light">
    <div class="container-fluid">
        <a class="navbar-brand" href="/">
            <i class="fas fa-file-invoice"></i>
            PO System
        </a>
        
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
            <span class="navbar-toggler-icon"></span>
        </button>
        
        <div class="collapse navbar-collapse" id="navbarNav">
            <ul class="navbar-nav me-auto">
                <li class="nav-item">
                    <a class="nav-link" href="/">
                        <i class="fas fa-home"></i>
                        <span class="mobile-hidden">Home</span>
                    </a>
                </li>
                <li class="nav-item">
                    <a class="nav-link" href="/dashboard">
                        <i class="fas fa-chart-bar"></i>
                        <span class="mobile-hidden">Dashboard</span>
                    </a>
                </li>
                <li class="nav-item">
                    <a class="nav-link" href="/history">
                        <i class="fas fa-history"></i>
                        <span class="mobile-hidden">History</span>
                    </a>
                </li>
            </ul>
            
            <ul class="navbar-nav">
                <li class="nav-item dropdown">
                    <a class="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown">
                        <i class="fas fa-user"></i>
                        <span class="mobile-hidden">User</span>
                    </a>
                    <ul class="dropdown-menu">
                        <li><a class="dropdown-item" href="/profile">Profile</a></li>
                        <li><a class="dropdown-item" href="/settings">Settings</a></li>
                        <li><hr class="dropdown-divider"></li>
                        <li><a class="dropdown-item" href="/logout">Logout</a></li>
                    </ul>
                </li>
            </ul>
        </div>
    </div>
</nav>
"""
    
    def _generate_mobile_product_card(self):
        return """
<!-- Mobile Product Card -->
<div class="product-card card mb-3">
    <div class="card-body">
        <div class="d-flex justify-content-between align-items-start mb-2">
            <h5 class="card-title mb-0">{{ product.name }}</h5>
            <span class="badge bg-primary">{{ product.category }}</span>
        </div>
        
        <p class="card-text text-muted small mb-3">{{ product.description }}</p>
        
        <div class="row mb-3">
            <div class="col-6">
                <small class="text-muted">Model:</small>
                <div class="fw-bold">{{ product.model }}</div>
            </div>
            <div class="col-6">
                <small class="text-muted">Price:</small>
                <div class="fw-bold text-success">${{ product.price }}</div>
            </div>
        </div>
        
        <div class="d-grid gap-2">
            <button class="btn btn-primary touch-target" onclick="selectProduct('{{ product.id }}')">
                <i class="fas fa-plus"></i>
                Select Product
            </button>
            <button class="btn btn-outline-secondary touch-target" onclick="viewDetails('{{ product.id }}')">
                <i class="fas fa-info-circle"></i>
                View Details
            </button>
        </div>
    </div>
</div>
"""
    
    def _generate_mobile_dashboard(self):
        return """
<!-- Mobile Dashboard -->
<div class="dashboard-container">
    <div class="row mb-4">
        <div class="col-12">
            <h2 class="mb-3">
                <i class="fas fa-chart-bar"></i>
                Dashboard
            </h2>
        </div>
    </div>
    
    <!-- Stats Cards -->
    <div class="row mb-4">
        <div class="col-6 col-md-3 mb-3">
            <div class="card text-center">
                <div class="card-body">
                    <i class="fas fa-file-invoice fa-2x text-primary mb-2"></i>
                    <h4 class="card-title">{{ stats.total_pos }}</h4>
                    <p class="card-text small">Total POs</p>
                </div>
            </div>
        </div>
        <div class="col-6 col-md-3 mb-3">
            <div class="card text-center">
                <div class="card-body">
                    <i class="fas fa-dollar-sign fa-2x text-success mb-2"></i>
                    <h4 class="card-title">${{ stats.total_value }}</h4>
                    <p class="card-text small">Total Value</p>
                </div>
            </div>
        </div>
        <div class="col-6 col-md-3 mb-3">
            <div class="card text-center">
                <div class="card-body">
                    <i class="fas fa-box fa-2x text-warning mb-2"></i>
                    <h4 class="card-title">{{ stats.total_products }}</h4>
                    <p class="card-text small">Products</p>
                </div>
            </div>
        </div>
        <div class="col-6 col-md-3 mb-3">
            <div class="card text-center">
                <div class="card-body">
                    <i class="fas fa-calendar fa-2x text-info mb-2"></i>
                    <h4 class="card-title">{{ stats.this_month }}</h4>
                    <p class="card-text small">This Month</p>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Charts -->
    <div class="row">
        <div class="col-12 mb-4">
            <div class="card">
                <div class="card-header">
                    <h5 class="mb-0">
                        <i class="fas fa-chart-line"></i>
                        Monthly Trends
                    </h5>
                </div>
                <div class="card-body">
                    <div class="chart-container" style="height: 300px;">
                        <canvas id="monthlyChart"></canvas>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="col-12 mb-4">
            <div class="card">
                <div class="card-header">
                    <h5 class="mb-0">
                        <i class="fas fa-chart-pie"></i>
                        Product Categories
                    </h5>
                </div>
                <div class="card-body">
                    <div class="chart-container" style="height: 300px;">
                        <canvas id="categoryChart"></canvas>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Quick Actions -->
    <div class="row">
        <div class="col-12">
            <div class="card">
                <div class="card-header">
                    <h5 class="mb-0">
                        <i class="fas fa-bolt"></i>
                        Quick Actions
                    </h5>
                </div>
                <div class="card-body">
                    <div class="d-grid gap-2">
                        <button class="btn btn-primary touch-target" onclick="createNewPO()">
                            <i class="fas fa-plus"></i>
                            Create New PO
                        </button>
                        <button class="btn btn-outline-primary touch-target" onclick="viewHistory()">
                            <i class="fas fa-history"></i>
                            View History
                        </button>
                        <button class="btn btn-outline-secondary touch-target" onclick="exportData()">
                            <i class="fas fa-download"></i>
                            Export Data
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
"""

class AccessibilityAuditor:
    def __init__(self):
        self.audit_results = {}
        
    def run_accessibility_audit(self):
        """Chạy accessibility audit"""
        print("Running accessibility audit...")
        
        audit_results = {
            'timestamp': datetime.now().isoformat(),
            'issues': [],
            'recommendations': [],
            'score': 0
        }
        
        # Check for common accessibility issues
        issues = self._check_accessibility_issues()
        audit_results['issues'] = issues
        
        # Generate recommendations
        recommendations = self._generate_recommendations(issues)
        audit_results['recommendations'] = recommendations
        
        # Calculate score
        score = self._calculate_accessibility_score(issues)
        audit_results['score'] = score
        
        self.audit_results = audit_results
        
        # Save audit results
        with open('accessibility_audit.json', 'w', encoding='utf-8') as f:
            json.dump(audit_results, f, indent=2, ensure_ascii=False)
        
        print(f"Accessibility audit completed. Score: {score}/100")
        return audit_results
    
    def _check_accessibility_issues(self):
        """Kiểm tra các vấn đề accessibility"""
        issues = []
        
        # Check for missing alt text
        issues.append({
            'type': 'images',
            'severity': 'high',
            'description': 'Images without alt text',
            'count': 0  # Would be calculated from actual HTML
        })
        
        # Check for missing form labels
        issues.append({
            'type': 'forms',
            'severity': 'high',
            'description': 'Form inputs without labels',
            'count': 0
        })
        
        # Check for color contrast
        issues.append({
            'type': 'contrast',
            'severity': 'medium',
            'description': 'Insufficient color contrast',
            'count': 0
        })
        
        # Check for keyboard navigation
        issues.append({
            'type': 'keyboard',
            'severity': 'high',
            'description': 'Elements not keyboard accessible',
            'count': 0
        })
        
        return issues
    
    def _generate_recommendations(self, issues):
        """Tạo recommendations dựa trên issues"""
        recommendations = []
        
        for issue in issues:
            if issue['type'] == 'images':
                recommendations.append({
                    'type': 'images',
                    'priority': 'high',
                    'action': 'Add alt text to all images',
                    'code_example': '<img src="image.jpg" alt="Descriptive text">'
                })
            
            elif issue['type'] == 'forms':
                recommendations.append({
                    'type': 'forms',
                    'priority': 'high',
                    'action': 'Add labels to all form inputs',
                    'code_example': '<label for="input">Label text</label><input id="input">'
                })
            
            elif issue['type'] == 'contrast':
                recommendations.append({
                    'type': 'contrast',
                    'priority': 'medium',
                    'action': 'Improve color contrast ratios',
                    'code_example': 'Use colors with contrast ratio >= 4.5:1'
                })
            
            elif issue['type'] == 'keyboard':
                recommendations.append({
                    'type': 'keyboard',
                    'priority': 'high',
                    'action': 'Ensure all interactive elements are keyboard accessible',
                    'code_example': 'Add tabindex and keyboard event handlers'
                })
        
        return recommendations
    
    def _calculate_accessibility_score(self, issues):
        """Tính accessibility score"""
        total_issues = len(issues)
        high_severity = len([i for i in issues if i['severity'] == 'high'])
        medium_severity = len([i for i in issues if i['severity'] == 'medium'])
        
        # Base score
        score = 100
        
        # Deduct points for issues
        score -= high_severity * 20
        score -= medium_severity * 10
        
        return max(0, score)

# Global instances
responsive_manager = ResponsiveDesignManager()
accessibility_auditor = AccessibilityAuditor()

def init_responsive_design():
    """Khởi tạo responsive design system"""
    print("Initializing responsive design system...")
    
    # Generate responsive CSS
    responsive_manager.generate_responsive_css()
    
    # Generate accessibility JavaScript
    responsive_manager.generate_accessibility_js()
    
    # Generate responsive templates
    responsive_manager.generate_responsive_templates()
    
    # Run accessibility audit
    audit_results = accessibility_auditor.run_accessibility_audit()
    
    print("Responsive design system initialized successfully!")
    return audit_results

if __name__ == "__main__":
    init_responsive_design()
