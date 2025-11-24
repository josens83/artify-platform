/**
 * Editor Authentication Initialization
 * Loads auth modals and initializes authentication UI for editor page
 */

(function() {
    'use strict';

    // Load auth modals HTML
    function loadAuthModals() {
        fetch('auth-modals.html')
            .then(response => response.text())
            .then(html => {
                // Create a container for modals
                const container = document.createElement('div');
                container.innerHTML = html;
                document.body.appendChild(container);

                // Initialize auth UI after modals are loaded
                initializeEditorAuth();
            })
            .catch(error => {
                console.error('Failed to load auth modals:', error);
            });
    }

    // Initialize editor authentication UI
    function initializeEditorAuth() {
        if (typeof AuthUI === 'undefined' || typeof window.auth === 'undefined') {
            console.error('AuthUI or auth not found');
            return;
        }

        // Override updateUserUI for editor
        const originalUpdateUserUI = AuthUI.updateUserUI;

        AuthUI.updateUserUI = function() {
            const container = document.getElementById('editor-auth-container');
            if (!container) {
                // Fallback to original if container not found
                if (originalUpdateUserUI) originalUpdateUserUI();
                return;
            }

            if (window.auth.isAuthenticated()) {
                // Show user profile
                container.innerHTML = `
                    <div class="user-profile">
                        <div class="user-avatar" onclick="AuthUI.toggleProfileDropdown(event)">
                            ${window.auth.getUserInitials()}
                        </div>
                        <div class="profile-dropdown" id="profile-dropdown">
                            <div class="dropdown-header">
                                <div class="dropdown-user-name">${window.auth.getUserDisplayName()}</div>
                                <div class="dropdown-user-email">${window.auth.currentUser.email}</div>
                            </div>
                            <div class="dropdown-divider"></div>
                            <button class="dropdown-item" onclick="AuthUI.showProfileModal()">
                                <span>👤</span> 내 프로필
                            </button>
                            <button class="dropdown-item" onclick="alert('설정 기능 준비 중')">
                                <span>⚙️</span> 설정
                            </button>
                            <button class="dropdown-item" onclick="alert('사용 통계 준비 중')">
                                <span>📊</span> 사용 통계
                            </button>
                            <div class="dropdown-divider"></div>
                            <button class="dropdown-item" onclick="window.auth.logout()">
                                <span>🚪</span> 로그아웃
                            </button>
                        </div>
                    </div>
                `;
            } else {
                // Show login button
                container.innerHTML = `
                    <button class="btn-login" onclick="AuthUI.showLoginModal()">
                        로그인
                    </button>
                `;
            }
        };

        // Initialize UI
        AuthUI.updateUserUI();

        console.log('Editor authentication initialized');
    }

    // Initialize when DOM is loaded
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', loadAuthModals);
    } else {
        loadAuthModals();
    }
})();
