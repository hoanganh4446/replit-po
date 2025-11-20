/**
 * Utility functions for PO System
 * Uses Tailwind CSS classes and Lucide icons
 */

// Show notification (Toast)
function showNotification(message, type = 'info') {
    // Create container if not exists
    let container = document.getElementById('notification-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'notification-container';
        container.className = 'fixed top-5 right-5 z-50 flex flex-col gap-3';
        document.body.appendChild(container);
    }

    const notification = document.createElement('div');
    
    // Define styles based on type
    let bgClass, borderClass, textClass, iconName;
    switch (type) {
        case 'success':
            bgClass = 'bg-emerald-500/10';
            borderClass = 'border-emerald-500/20';
            textClass = 'text-emerald-400';
            iconName = 'check-circle';
            break;
        case 'error':
            bgClass = 'bg-red-500/10';
            borderClass = 'border-red-500/20';
            textClass = 'text-red-400';
            iconName = 'alert-circle';
            break;
        case 'warning':
            bgClass = 'bg-amber-500/10';
            borderClass = 'border-amber-500/20';
            textClass = 'text-amber-400';
            iconName = 'alert-triangle';
            break;
        default: // info
            bgClass = 'bg-blue-500/10';
            borderClass = 'border-blue-500/20';
            textClass = 'text-blue-400';
            iconName = 'info';
    }

    notification.className = `p-4 rounded-lg border backdrop-blur-md shadow-lg transition-all duration-300 transform translate-x-full opacity-0 flex items-center gap-3 min-w-[300px] ${bgClass} ${borderClass} ${textClass}`;
    
    notification.innerHTML = `
        <i data-lucide="${iconName}" class="w-5 h-5 shrink-0"></i>
        <span class="flex-1 text-sm font-medium text-slate-200">${message}</span>
        <button class="hover:opacity-70 transition-opacity ml-2">
            <i data-lucide="x" class="w-4 h-4"></i>
        </button>
    `;

    // Close button handler
    notification.querySelector('button').addEventListener('click', () => {
        closeNotification(notification);
    });

    container.appendChild(notification);
    
    // Initialize icons for this new element
    if (window.lucide) {
        lucide.createIcons({
            root: notification
        });
    }

    // Animate in
    requestAnimationFrame(() => {
        notification.classList.remove('translate-x-full', 'opacity-0');
    });

    // Auto dismiss
    setTimeout(() => {
        closeNotification(notification);
    }, 5000);
}

function closeNotification(notification) {
    notification.classList.add('opacity-0', 'translate-x-full');
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
        // Remove container if empty
        const container = document.getElementById('notification-container');
        if (container && container.children.length === 0) {
            container.remove();
        }
    }, 300);
}

// Format date
function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('vi-VN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    }).format(date);
}

// Format currency
function formatCurrency(amount) {
    return new Intl.NumberFormat('vi-VN', {
        style: 'currency',
        currency: 'VND'
    }).format(amount);
}

// Copy to clipboard
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showNotification('Đã sao chép vào clipboard', 'success');
    }).catch(err => {
        showNotification('Không thể sao chép', 'error');
        console.error('Copy failed:', err);
    });
}

// Debounce function
function debounce(func, wait) {
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
