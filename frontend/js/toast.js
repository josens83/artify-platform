/**
 * Toast Notification System
 * Provides elegant toast notifications instead of alert()
 */

class ToastManager {
    constructor() {
        this.container = null;
        this.toasts = [];
        this.init();
    }

    /**
     * Initialize toast container
     */
    init() {
        // Create container if not exists
        if (!document.getElementById('toast-container')) {
            this.container = document.createElement('div');
            this.container.id = 'toast-container';
            this.container.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 99999;
                display: flex;
                flex-direction: column;
                gap: 10px;
                pointer-events: none;
            `;
            document.body.appendChild(this.container);
        } else {
            this.container = document.getElementById('toast-container');
        }

        // Add styles
        this.addStyles();
    }

    /**
     * Add CSS styles for toasts
     */
    addStyles() {
        if (document.getElementById('toast-styles')) return;

        const styles = document.createElement('style');
        styles.id = 'toast-styles';
        styles.textContent = `
            .toast {
                display: flex;
                align-items: center;
                gap: 12px;
                padding: 14px 20px;
                border-radius: 8px;
                background: white;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                font-size: 14px;
                min-width: 300px;
                max-width: 450px;
                pointer-events: auto;
                transform: translateX(120%);
                transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            }

            .toast.show {
                transform: translateX(0);
            }

            .toast.hide {
                transform: translateX(120%);
            }

            .toast-icon {
                font-size: 20px;
                flex-shrink: 0;
            }

            .toast-content {
                flex: 1;
            }

            .toast-title {
                font-weight: 600;
                margin-bottom: 2px;
            }

            .toast-message {
                color: #666;
                line-height: 1.4;
            }

            .toast-close {
                background: none;
                border: none;
                cursor: pointer;
                font-size: 18px;
                color: #999;
                padding: 0;
                margin-left: 8px;
                transition: color 0.2s;
            }

            .toast-close:hover {
                color: #333;
            }

            /* Toast types */
            .toast.success {
                border-left: 4px solid #10b981;
            }

            .toast.success .toast-icon {
                color: #10b981;
            }

            .toast.error {
                border-left: 4px solid #ef4444;
            }

            .toast.error .toast-icon {
                color: #ef4444;
            }

            .toast.warning {
                border-left: 4px solid #f59e0b;
            }

            .toast.warning .toast-icon {
                color: #f59e0b;
            }

            .toast.info {
                border-left: 4px solid #3b82f6;
            }

            .toast.info .toast-icon {
                color: #3b82f6;
            }

            /* Progress bar */
            .toast-progress {
                position: absolute;
                bottom: 0;
                left: 0;
                height: 3px;
                background: rgba(0, 0, 0, 0.1);
                border-radius: 0 0 0 8px;
                transition: width linear;
            }
        `;
        document.head.appendChild(styles);
    }

    /**
     * Get icon for toast type
     */
    getIcon(type) {
        const icons = {
            success: '✅',
            error: '❌',
            warning: '⚠️',
            info: 'ℹ️'
        };
        return icons[type] || icons.info;
    }

    /**
     * Show a toast notification
     * @param {string} message - Toast message
     * @param {string} type - Toast type: 'success', 'error', 'warning', 'info'
     * @param {object} options - Additional options
     */
    show(message, type = 'info', options = {}) {
        const {
            title = null,
            duration = 4000,
            closable = true
        } = options;

        // Create toast element
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <span class="toast-icon">${this.getIcon(type)}</span>
            <div class="toast-content">
                ${title ? `<div class="toast-title">${this.escapeHtml(title)}</div>` : ''}
                <div class="toast-message">${this.escapeHtml(message)}</div>
            </div>
            ${closable ? '<button class="toast-close">&times;</button>' : ''}
        `;

        // Add close handler
        if (closable) {
            const closeBtn = toast.querySelector('.toast-close');
            closeBtn.addEventListener('click', () => this.dismiss(toast));
        }

        // Add to container
        this.container.appendChild(toast);
        this.toasts.push(toast);

        // Trigger animation
        requestAnimationFrame(() => {
            toast.classList.add('show');
        });

        // Auto dismiss
        if (duration > 0) {
            setTimeout(() => this.dismiss(toast), duration);
        }

        return toast;
    }

    /**
     * Dismiss a toast
     */
    dismiss(toast) {
        if (!toast || !toast.parentNode) return;

        toast.classList.remove('show');
        toast.classList.add('hide');

        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
            this.toasts = this.toasts.filter(t => t !== toast);
        }, 300);
    }

    /**
     * Dismiss all toasts
     */
    dismissAll() {
        this.toasts.forEach(toast => this.dismiss(toast));
    }

    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Convenience methods
    success(message, options = {}) {
        return this.show(message, 'success', options);
    }

    error(message, options = {}) {
        return this.show(message, 'error', { duration: 6000, ...options });
    }

    warning(message, options = {}) {
        return this.show(message, 'warning', options);
    }

    info(message, options = {}) {
        return this.show(message, 'info', options);
    }
}

// Create global instance
const Toast = new ToastManager();

// Make available globally
window.Toast = Toast;

// Export for ES modules
export { Toast, ToastManager };
export default Toast;
