/**
 * Enhancements.js - UI Enhancement Features
 * Phase 1: Basic enhancements for PO System
 */

// Toast notification system
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        background: ${type === 'success' ? '#28a745' : type === 'error' ? '#dc3545' : '#17a2b8'};
        color: white;
        border-radius: 5px;
        z-index: 9999;
        animation: slideIn 0.3s ease;
    `;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Auto-save indicator
let autoSaveTimeout;
function showAutoSaveIndicator(status = 'saving') {
    const indicator = document.getElementById('autosave-indicator') || createAutoSaveIndicator();
    indicator.textContent = status === 'saving' ? 'Đang lưu...' : 'Đã lưu';
    indicator.style.opacity = '1';
    
    clearTimeout(autoSaveTimeout);
    autoSaveTimeout = setTimeout(() => {
        indicator.style.opacity = '0';
    }, 2000);
}

function createAutoSaveIndicator() {
    const indicator = document.createElement('div');
    indicator.id = 'autosave-indicator';
    indicator.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        padding: 10px 15px;
        background: #6c757d;
        color: white;
        border-radius: 5px;
        opacity: 0;
        transition: opacity 0.3s;
        z-index: 9998;
    `;
    document.body.appendChild(indicator);
    return indicator;
}

// Dark mode toggle
function toggleDarkMode() {
    document.body.classList.toggle('dark-mode');
    const isDark = document.body.classList.contains('dark-mode');
    localStorage.setItem('darkMode', isDark);
}

// Initialize dark mode from localStorage
document.addEventListener('DOMContentLoaded', function() {
    if (localStorage.getItem('darkMode') === 'true') {
        document.body.classList.add('dark-mode');
    }
});

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + K for search
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        const searchInput = document.getElementById('searchInput');
        if (searchInput) searchInput.focus();
    }
    
    // Ctrl/Cmd + D for dark mode
    if ((e.ctrlKey || e.metaKey) && e.key === 'd') {
        e.preventDefault();
        toggleDarkMode();
    }
});

// Progress overlay
function showProgressOverlay(message = 'Đang xử lý...') {
    const overlay = document.createElement('div');
    overlay.id = 'progress-overlay';
    overlay.innerHTML = `
        <div style="text-align: center; color: white;">
            <div class="spinner-border" role="status">
                <span class="sr-only">Loading...</span>
            </div>
            <p style="margin-top: 15px;">${message}</p>
        </div>
    `;
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.7);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10000;
    `;
    document.body.appendChild(overlay);
}

function hideProgressOverlay() {
    const overlay = document.getElementById('progress-overlay');
    if (overlay) overlay.remove();
}

console.log('Enhancements.js loaded successfully');
