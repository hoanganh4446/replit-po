/**
 * Notifications & Modals System
 * Handles Toasts, Modals, and System Alerts
 */

class NotificationSystem {
    constructor() {
        this.toastContainer = null;
        this.init();
    }

    init() {
        // Create Toast Container if not exists
        if (!document.getElementById('toast-container')) {
            this.toastContainer = document.createElement('div');
            this.toastContainer.id = 'toast-container';
            document.body.appendChild(this.toastContainer);
        } else {
            this.toastContainer = document.getElementById('toast-container');
        }

        // Handle Esc key for modals
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                const openModals = document.querySelectorAll('.custom-modal-backdrop.show');
                if (openModals.length > 0) {
                    const topModal = openModals[openModals.length - 1];
                    // Check if it's a mandatory modal (e.g. deactivation)
                    if (!topModal.dataset.static) {
                        this.closeModal(topModal.id);
                    }
                }
            }
        });
    }

    // ============================================
    // TOASTS
    // ============================================
    showToast(message, type = 'info', duration = 5000) {
        const id = 'toast-' + Date.now();
        const iconMap = {
            success: 'check-circle',
            warning: 'alert-triangle',
            error: 'alert-circle',
            info: 'info'
        };
        const titleMap = {
            success: 'Thành công',
            warning: 'Cảnh báo',
            error: 'Lỗi',
            info: 'Thông tin'
        };

        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.id = id;

        toast.innerHTML = `
            <div class="toast-icon">
                <i data-lucide="${iconMap[type]}"></i>
            </div>
            <div class="toast-content">
                <div class="toast-title">${titleMap[type]}</div>
                <div class="toast-message">${message}</div>
            </div>
            <button class="toast-close" onclick="notifications.dismissToast('${id}')">
                <i data-lucide="x" style="width: 16px; height: 16px;"></i>
            </button>
            <div class="toast-progress">
                <div class="toast-progress-bar" style="animation-duration: ${duration}ms"></div>
            </div>
        `;

        this.toastContainer.appendChild(toast);

        // Initialize icons
        if (window.lucide) lucide.createIcons({ root: toast });

        // Animate in
        requestAnimationFrame(() => {
            toast.classList.add('show');
        });

        // Auto dismiss
        if (duration > 0) {
            setTimeout(() => {
                this.dismissToast(id);
            }, duration);
        }

        return id;
    }

    dismissToast(id) {
        const toast = document.getElementById(id);
        if (toast) {
            toast.classList.remove('show');
            toast.classList.add('hiding');
            setTimeout(() => {
                if (toast.parentElement) toast.parentElement.removeChild(toast);
            }, 300);
        }
    }

    // ============================================
    // MODALS
    // ============================================

    /**
     * Open a modal by ID (for pre-defined HTML modals)
     */
    openModal(modalId) {
        const backdrop = document.getElementById(modalId);
        if (backdrop) {
            backdrop.classList.add('show');
            // Trap focus logic could go here
            const firstInput = backdrop.querySelector('input, button, select, textarea');
            if (firstInput) firstInput.focus();
        }
    }

    closeModal(modalId) {
        const backdrop = document.getElementById(modalId);
        if (backdrop) {
            backdrop.classList.remove('show');
        }
    }

    /**
     * Create and show a dynamic confirmation modal
     */
    confirm({ title, message, type = 'warning', confirmText = 'Xác nhận', cancelText = 'Hủy', onConfirm }) {
        const id = 'modal-confirm-' + Date.now();
        const iconMap = {
            warning: 'alert-triangle',
            danger: 'alert-circle',
            info: 'info'
        };

        const backdrop = document.createElement('div');
        backdrop.className = 'custom-modal-backdrop modal-confirm';
        backdrop.id = id;

        // Close on backdrop click
        backdrop.addEventListener('click', (e) => {
            if (e.target === backdrop) this.closeModal(id);
        });

        const modalHtml = `
            <div class="custom-modal custom-modal-sm">
                <div class="custom-modal-header">
                    <button class="custom-modal-close" onclick="notifications.closeModal('${id}')">
                        <i data-lucide="x"></i>
                    </button>
                </div>
                <div class="custom-modal-body">
                    <div class="modal-confirm-icon ${type}">
                        <i data-lucide="${iconMap[type] || 'alert-circle'}"></i>
                    </div>
                    <h3 class="custom-modal-title" style="justify-content: center; margin-bottom: 8px;">${title}</h3>
                    <p>${message}</p>
                </div>
                <div class="custom-modal-footer">
                    <button class="btn-modal btn-modal-secondary" onclick="notifications.closeModal('${id}')">${cancelText}</button>
                    <button class="btn-modal ${type === 'danger' ? 'btn-modal-danger' : 'btn-modal-primary'}" id="${id}-confirm">${confirmText}</button>
                </div>
            </div>
        `;

        backdrop.innerHTML = modalHtml;
        document.body.appendChild(backdrop);

        if (window.lucide) lucide.createIcons({ root: backdrop });

        // Bind confirm action
        document.getElementById(`${id}-confirm`).addEventListener('click', () => {
            if (onConfirm) onConfirm();
            this.closeModal(id);
        });

        // Show
        requestAnimationFrame(() => {
            backdrop.classList.add('show');
        });

        // Cleanup after close (wait for transition)
        const originalClose = this.closeModal;
        this.closeModal = (mid) => {
            if (mid === id) {
                const el = document.getElementById(mid);
                if (el) {
                    el.classList.remove('show');
                    setTimeout(() => {
                        if (el.parentElement) el.parentElement.removeChild(el);
                    }, 300);
                }
            } else {
                // Call original for other modals
                const el = document.getElementById(mid);
                if (el) el.classList.remove('show');
            }
        };
    }

    // ============================================
    // SPECIAL SCENARIOS
    // ============================================

    showWelcomeModal() {
        if (localStorage.getItem('welcomeShown')) return;

        const id = 'modal-welcome';
        // Check if already exists
        if (document.getElementById(id)) return;

        const backdrop = document.createElement('div');
        backdrop.className = 'custom-modal-backdrop';
        backdrop.id = id;

        backdrop.innerHTML = `
            <div class="custom-modal">
                <div class="custom-modal-header">
                    <h3 class="custom-modal-title">👋 Chào mừng đến với PO System</h3>
                    <button class="custom-modal-close" onclick="notifications.closeModal('${id}')"><i data-lucide="x"></i></button>
                </div>
                <div class="custom-modal-body">
                    <p>Hệ thống quản lý PO mới với giao diện hiện đại và hiệu suất cao hơn.</p>
                    <ul style="margin-top: 10px; margin-left: 20px; list-style: disc;">
                        <li>Giao diện Dark Mode tối ưu.</li>
                        <li>Xử lý hàng loạt nhanh chóng.</li>
                        <li>Báo cáo và Analytics trực quan.</li>
                    </ul>
                </div>
                <div class="custom-modal-footer">
                    <button class="btn-modal btn-modal-primary" onclick="notifications.closeModal('${id}'); localStorage.setItem('welcomeShown', 'true');">Bắt đầu ngay</button>
                </div>
            </div>
        `;

        document.body.appendChild(backdrop);
        if (window.lucide) lucide.createIcons({ root: backdrop });

        setTimeout(() => this.openModal(id), 100);
    }

    showCookieConsent() {
        if (localStorage.getItem('cookieConsent')) return;

        const bar = document.createElement('div');
        bar.className = 'cookie-consent-bar';
        bar.id = 'cookie-consent';
        bar.innerHTML = `
            <div>
                <h4 style="color: #fff; font-weight: 600; margin-bottom: 4px;">🍪 Chúng tôi sử dụng Cookies</h4>
                <p style="color: #aaa; font-size: 0.9rem; margin: 0;">Chúng tôi sử dụng cookies để cải thiện trải nghiệm của bạn và đảm bảo an toàn hệ thống.</p>
            </div>
            <div style="display: flex; gap: 10px;">
                <button class="btn-modal btn-modal-secondary" onclick="document.getElementById('cookie-consent').classList.remove('show');">Từ chối</button>
                <button class="btn-modal btn-modal-primary" onclick="localStorage.setItem('cookieConsent', 'true'); document.getElementById('cookie-consent').classList.remove('show');">Chấp nhận</button>
            </div>
        `;

        document.body.appendChild(bar);

        setTimeout(() => {
            bar.classList.add('show');
        }, 1000);
    }

    showDeactivationModal() {
        // Example usage: notifications.showDeactivationModal()
        const id = 'modal-deactivation';
        const backdrop = document.createElement('div');
        backdrop.className = 'custom-modal-backdrop';
        backdrop.id = id;
        backdrop.dataset.static = "true"; // Prevent closing with Esc or click outside

        backdrop.innerHTML = `
            <div class="custom-modal custom-modal-sm">
                <div class="custom-modal-body" style="text-align: center; padding-top: 40px; padding-bottom: 40px;">
                    <div class="modal-confirm-icon danger" style="margin-bottom: 20px;">
                        <i data-lucide="lock"></i>
                    </div>
                    <h3 class="custom-modal-title" style="justify-content: center; margin-bottom: 10px;">Hệ thống đang bảo trì</h3>
                    <p>Chúng tôi đang tiến hành nâng cấp hệ thống. Vui lòng quay lại sau.</p>
                </div>
            </div>
        `;

        document.body.appendChild(backdrop);
        if (window.lucide) lucide.createIcons({ root: backdrop });

        setTimeout(() => backdrop.classList.add('show'), 100);
    }
}

// Initialize Global Instance
const notifications = new NotificationSystem();

// Expose global functions for backward compatibility or ease of use
window.showToast = (msg, type) => notifications.showToast(msg, type);
window.showModal = (id) => notifications.openModal(id);
window.closeModal = (id) => notifications.closeModal(id);
window.confirmAction = (options) => notifications.confirm(options);

// Auto-run on load
document.addEventListener('DOMContentLoaded', () => {
    notifications.showWelcomeModal();
    notifications.showCookieConsent();
});
