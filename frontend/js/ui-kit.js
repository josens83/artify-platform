// UI-Kit.js - 공통 UI 컴포넌트
const UI = {
    // 로딩 스피너 표시
    showLoading(message = '로딩 중...') {
        const existing = document.getElementById('global-loading');
        if (existing) existing.remove();

        const loading = document.createElement('div');
        loading.id = 'global-loading';
        loading.innerHTML = `
            <div style="
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(255, 255, 255, 0.9);
                display: flex;
                align-items: center;
                justify-center;
                z-index: 10000;
                backdrop-filter: blur(4px);
            ">
                <div style="text-align: center;">
                    <div class="spinner" style="
                        border: 4px solid #f3f3f3;
                        border-top: 4px solid #667eea;
                        border-radius: 50%;
                        width: 50px;
                        height: 50px;
                        animation: spin 1s linear infinite;
                        margin: 0 auto 20px;
                    "></div>
                    <p style="color: #667eea; font-size: 16px; font-weight: 500;">${message}</p>
                </div>
            </div>
        `;
        document.body.appendChild(loading);
    },

    hideLoading() {
        const loading = document.getElementById('global-loading');
        if (loading) loading.remove();
    },

    // Toast 알림
    toast(message, type = 'info') {
        const colors = {
            success: '#10b981',
            error: '#ef4444',
            warning: '#f59e0b',
            info: '#667eea'
        };

        const toast = document.createElement('div');
        toast.className = 'toast';
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${colors[type]};
            color: white;
            padding: 16px 24px;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            z-index: 10001;
            animation: slideIn 0.3s ease-out;
            font-size: 14px;
            font-weight: 500;
        `;
        toast.textContent = message;
        document.body.appendChild(toast);

        setTimeout(() => {
            toast.style.animation = 'slideOut 0.3s ease-in';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    },

    // 모달 다이얼로그
    modal(title, content, buttons = []) {
        const existing = document.getElementById('global-modal');
        if (existing) existing.remove();

        const modal = document.createElement('div');
        modal.id = 'global-modal';
        modal.innerHTML = `
            <div class="modal-overlay" style="
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.5);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 9999;
                animation: fadeIn 0.2s ease-out;
            ">
                <div class="modal-content" style="
                    background: white;
                    border-radius: 16px;
                    padding: 32px;
                    max-width: 500px;
                    width: 90%;
                    max-height: 90vh;
                    overflow-y: auto;
                    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                    animation: scaleIn 0.2s ease-out;
                ">
                    <h2 style="margin: 0 0 20px; font-size: 24px; color: #1a1a1a;">${title}</h2>
                    <div class="modal-body" style="margin-bottom: 24px; color: #4a4a4a; line-height: 1.6;">
                        ${content}
                    </div>
                    <div class="modal-buttons" style="display: flex; gap: 12px; justify-content: flex-end;">
                        ${buttons.map(btn => `
                            <button
                                class="modal-btn ${btn.primary ? 'btn-primary' : 'btn-secondary'}"
                                data-action="${btn.action}"
                                style="
                                    padding: 12px 24px;
                                    border-radius: 8px;
                                    border: none;
                                    cursor: pointer;
                                    font-size: 14px;
                                    font-weight: 500;
                                    transition: all 0.2s;
                                    ${btn.primary ?
                                        'background: #667eea; color: white;' :
                                        'background: #f3f4f6; color: #4a4a4a;'}
                                "
                            >${btn.label}</button>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // Button click handlers
        modal.querySelectorAll('.modal-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const action = btn.dataset.action;
                const button = buttons.find(b => b.action === action);
                if (button && button.onClick) {
                    button.onClick();
                }
                modal.remove();
            });

            btn.addEventListener('mouseenter', (e) => {
                e.target.style.transform = 'scale(1.02)';
            });
            btn.addEventListener('mouseleave', (e) => {
                e.target.style.transform = 'scale(1)';
            });
        });

        // Close on overlay click
        modal.querySelector('.modal-overlay').addEventListener('click', (e) => {
            if (e.target.classList.contains('modal-overlay')) {
                modal.remove();
            }
        });

        return modal;
    },

    // 확인 다이얼로그
    confirm(message, onConfirm) {
        return this.modal('확인', message, [
            { label: '취소', action: 'cancel' },
            { label: '확인', action: 'confirm', primary: true, onClick: onConfirm }
        ]);
    },

    // 카드 컴포넌트
    card(options) {
        const {
            title,
            description,
            icon,
            onClick,
            thumbnail,
            meta
        } = options;

        const card = document.createElement('div');
        card.className = 'ui-card';
        card.style.cssText = `
            background: white;
            border-radius: 14px;
            padding: 24px;
            cursor: pointer;
            transition: all 0.2s;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        `;

        // Handle thumbnail - check if it's a gradient or URL
        const thumbnailStyle = thumbnail
            ? (thumbnail.startsWith('linear-gradient') || thumbnail.startsWith('radial-gradient')
                ? `background-image: ${thumbnail};`
                : `background-image: url('${thumbnail}');`)
            : '';

        card.innerHTML = `
            ${thumbnail ? `
                <div class="card-thumbnail" style="
                    width: 100%;
                    height: 160px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    border-radius: 10px;
                    margin-bottom: 16px;
                    ${thumbnailStyle}
                    background-size: cover;
                    background-position: center;
                "></div>
            ` : ''}
            ${icon ? `<div style="font-size: 32px; margin-bottom: 12px;">${icon}</div>` : ''}
            <h3 style="margin: 0 0 8px; font-size: 18px; color: #1a1a1a;">${title}</h3>
            ${description ? `<p style="margin: 0; color: #6b7280; font-size: 14px; line-height: 1.5;">${description}</p>` : ''}
            ${meta ? `<div style="margin-top: 12px; font-size: 12px; color: #9ca3af;">${meta}</div>` : ''}
        `;

        card.addEventListener('mouseenter', () => {
            card.style.transform = 'translateY(-4px) scale(1.02)';
            card.style.boxShadow = '0 12px 24px rgba(0,0,0,0.12)';
        });

        card.addEventListener('mouseleave', () => {
            card.style.transform = 'translateY(0) scale(1)';
            card.style.boxShadow = '0 2px 8px rgba(0,0,0,0.08)';
        });

        if (onClick) {
            card.addEventListener('click', onClick);
        }

        return card;
    },

    // 버튼 컴포넌트
    button(label, onClick, options = {}) {
        const button = document.createElement('button');
        button.textContent = label;
        button.style.cssText = `
            padding: 12px 24px;
            border-radius: 8px;
            border: none;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.2s;
            ${options.primary ?
                'background: #667eea; color: white;' :
                'background: #f3f4f6; color: #4a4a4a;'}
            ${options.fullWidth ? 'width: 100%;' : ''}
        `;

        button.addEventListener('click', onClick);
        button.addEventListener('mouseenter', () => {
            button.style.transform = 'scale(1.02)';
            button.style.boxShadow = '0 4px 12px rgba(102, 126, 234, 0.3)';
        });
        button.addEventListener('mouseleave', () => {
            button.style.transform = 'scale(1)';
            button.style.boxShadow = 'none';
        });

        return button;
    }
};

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    @keyframes scaleIn {
        from { transform: scale(0.9); opacity: 0; }
        to { transform: scale(1); opacity: 1; }
    }
`;
document.head.appendChild(style);
