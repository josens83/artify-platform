/**
 * Authentication Manager
 * Handles login, registration, profile management, and token management
 */

class AuthManager {
    constructor() {
        this.currentUser = null;
        this.accessToken = null;
        this.refreshToken = null;

        // Load tokens from localStorage
        this.loadTokens();

        // Auto-refresh token before expiry
        this.startTokenRefreshTimer();
    }

    /**
     * Load tokens from localStorage
     */
    loadTokens() {
        this.accessToken = localStorage.getItem('access_token');
        this.refreshToken = localStorage.getItem('refresh_token');
        const userJson = localStorage.getItem('current_user');

        if (userJson) {
            try {
                this.currentUser = JSON.parse(userJson);
            } catch (e) {
                console.error('Failed to parse user data:', e);
                this.logout();
            }
        }
    }

    /**
     * Save tokens to localStorage
     */
    saveTokens(accessToken, refreshToken) {
        this.accessToken = accessToken;
        this.refreshToken = refreshToken;

        localStorage.setItem('access_token', accessToken);
        if (refreshToken) {
            localStorage.setItem('refresh_token', refreshToken);
        }
    }

    /**
     * Clear tokens from localStorage
     */
    clearTokens() {
        this.accessToken = null;
        this.refreshToken = null;
        this.currentUser = null;

        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('current_user');
    }

    /**
     * Check if user is authenticated
     */
    isAuthenticated() {
        return !!this.accessToken && !!this.currentUser;
    }

    /**
     * Get authorization header
     */
    getAuthHeader() {
        if (!this.accessToken) return {};
        return {
            'Authorization': `Bearer ${this.accessToken}`
        };
    }

    /**
     * Login with email and password
     */
    async login(email, password) {
        try {
            const response = await fetch(`${window.APP_CONFIG.CONTENT_BACKEND_URL}/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ email, password })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Login failed');
            }

            const data = await response.json();

            // Save tokens
            this.saveTokens(data.access_token, data.refresh_token);

            // Fetch user info
            await this.fetchCurrentUser();

            return { success: true, user: this.currentUser };
        } catch (error) {
            console.error('Login error:', error);
            return { success: false, error: error.message };
        }
    }

    /**
     * Register new user
     */
    async register(name, email, password) {
        try {
            // Note: Backend doesn't have register endpoint yet, using demo approach
            // In production, this should call POST /auth/register

            // For now, auto-login with demo account
            UI.toast('회원가입 기능은 준비 중입니다. 데모 계정으로 로그인합니다.', 'info');

            // Try demo login
            return await this.login('user@artify.com', 'user123');
        } catch (error) {
            console.error('Register error:', error);
            return { success: false, error: error.message };
        }
    }

    /**
     * Logout
     */
    logout() {
        this.clearTokens();

        // Redirect to home page
        if (window.router) {
            window.router.navigate('/');
        } else {
            window.location.href = 'index.html';
        }

        UI.toast('로그아웃되었습니다', 'info');
    }

    /**
     * Fetch current user info
     */
    async fetchCurrentUser() {
        try {
            const response = await fetch(`${window.APP_CONFIG.CONTENT_BACKEND_URL}/auth/me`, {
                headers: {
                    ...this.getAuthHeader()
                }
            });

            if (!response.ok) {
                throw new Error('Failed to fetch user info');
            }

            const data = await response.json();
            this.currentUser = data;
            localStorage.setItem('current_user', JSON.stringify(data));

            return data;
        } catch (error) {
            console.error('Fetch user error:', error);
            // If token is invalid, logout
            this.logout();
            return null;
        }
    }

    /**
     * Refresh access token
     */
    async refreshAccessToken() {
        if (!this.refreshToken) {
            return false;
        }

        try {
            const response = await fetch(`${window.APP_CONFIG.CONTENT_BACKEND_URL}/auth/refresh`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    refresh_token: this.refreshToken
                })
            });

            if (!response.ok) {
                throw new Error('Token refresh failed');
            }

            const data = await response.json();
            this.saveTokens(data.access_token, this.refreshToken);

            console.log('Access token refreshed');
            return true;
        } catch (error) {
            console.error('Token refresh error:', error);
            this.logout();
            return false;
        }
    }

    /**
     * Start token refresh timer (refresh 5 minutes before expiry)
     */
    startTokenRefreshTimer() {
        // JWT tokens typically expire in 1 hour
        // Refresh every 55 minutes
        const refreshInterval = 55 * 60 * 1000;

        setInterval(async () => {
            if (this.isAuthenticated()) {
                console.log('Auto-refreshing token...');
                await this.refreshAccessToken();
            }
        }, refreshInterval);
    }

    /**
     * Change password
     */
    async changePassword(currentPassword, newPassword) {
        try {
            const response = await fetch(`${window.APP_CONFIG.CONTENT_BACKEND_URL}/auth/change-password`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...this.getAuthHeader()
                },
                body: JSON.stringify({
                    current_password: currentPassword,
                    new_password: newPassword
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Password change failed');
            }

            return { success: true };
        } catch (error) {
            console.error('Change password error:', error);
            return { success: false, error: error.message };
        }
    }

    /**
     * Request password reset
     */
    async requestPasswordReset(email) {
        try {
            const response = await fetch(`${window.APP_CONFIG.CONTENT_BACKEND_URL}/auth/password-reset`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ email })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Password reset request failed');
            }

            const data = await response.json();
            return { success: true, token: data.token };
        } catch (error) {
            console.error('Password reset error:', error);
            return { success: false, error: error.message };
        }
    }

    /**
     * Get user initials for avatar
     */
    getUserInitials() {
        if (!this.currentUser || !this.currentUser.email) {
            return '?';
        }

        const email = this.currentUser.email;
        return email.charAt(0).toUpperCase();
    }

    /**
     * Get user display name
     */
    getUserDisplayName() {
        if (!this.currentUser) {
            return 'Guest';
        }

        return this.currentUser.name || this.currentUser.email.split('@')[0];
    }
}

// Create global instance
window.auth = new AuthManager();


/**
 * UI Components for Authentication
 */

class AuthUI {
    /**
     * Show login modal
     */
    static showLoginModal() {
        const modal = document.getElementById('login-modal');
        if (modal) {
            modal.classList.add('active');

            // Clear previous errors
            const errorDiv = modal.querySelector('.error-message');
            if (errorDiv) errorDiv.style.display = 'none';

            // Clear form
            modal.querySelector('#login-email').value = '';
            modal.querySelector('#login-password').value = '';
        }
    }

    /**
     * Hide login modal
     */
    static hideLoginModal() {
        const modal = document.getElementById('login-modal');
        if (modal) {
            modal.classList.remove('active');
        }
    }

    /**
     * Show register modal
     */
    static showRegisterModal() {
        // Hide login modal first
        AuthUI.hideLoginModal();

        const modal = document.getElementById('register-modal');
        if (modal) {
            modal.classList.add('active');

            // Clear previous errors
            const errorDiv = modal.querySelector('.error-message');
            if (errorDiv) errorDiv.style.display = 'none';

            // Clear form
            modal.querySelector('#register-name').value = '';
            modal.querySelector('#register-email').value = '';
            modal.querySelector('#register-password').value = '';
            modal.querySelector('#register-password-confirm').value = '';
        }
    }

    /**
     * Hide register modal
     */
    static hideRegisterModal() {
        const modal = document.getElementById('register-modal');
        if (modal) {
            modal.classList.remove('active');
        }
    }

    /**
     * Show profile modal
     */
    static showProfileModal() {
        const modal = document.getElementById('profile-modal');
        if (modal) {
            modal.classList.add('active');

            // Populate user info
            if (window.auth.currentUser) {
                const nameEl = modal.querySelector('#profile-user-name');
                const emailEl = modal.querySelector('#profile-user-email');

                if (nameEl) nameEl.textContent = window.auth.getUserDisplayName();
                if (emailEl) emailEl.textContent = window.auth.currentUser.email;
            }
        }
    }

    /**
     * Hide profile modal
     */
    static hideProfileModal() {
        const modal = document.getElementById('profile-modal');
        if (modal) {
            modal.classList.remove('active');
        }
    }

    /**
     * Handle login form submit
     */
    static async handleLogin(e) {
        e.preventDefault();

        const email = document.getElementById('login-email').value.trim();
        const password = document.getElementById('login-password').value;
        const errorDiv = document.querySelector('#login-modal .error-message');
        const submitBtn = document.querySelector('#login-modal .btn-submit');

        // Validation
        if (!email || !password) {
            errorDiv.textContent = '이메일과 비밀번호를 입력해주세요';
            errorDiv.style.display = 'block';
            return;
        }

        // Show loading
        submitBtn.disabled = true;
        submitBtn.textContent = '로그인 중...';
        errorDiv.style.display = 'none';

        // Call auth API
        const result = await window.auth.login(email, password);

        if (result.success) {
            AuthUI.hideLoginModal();
            UI.toast('로그인 성공!', 'success');

            // Update UI
            AuthUI.updateUserUI();
        } else {
            errorDiv.textContent = result.error || '로그인에 실패했습니다';
            errorDiv.style.display = 'block';
        }

        // Reset button
        submitBtn.disabled = false;
        submitBtn.textContent = '로그인';
    }

    /**
     * Handle register form submit
     */
    static async handleRegister(e) {
        e.preventDefault();

        const name = document.getElementById('register-name').value.trim();
        const email = document.getElementById('register-email').value.trim();
        const password = document.getElementById('register-password').value;
        const passwordConfirm = document.getElementById('register-password-confirm').value;
        const errorDiv = document.querySelector('#register-modal .error-message');
        const submitBtn = document.querySelector('#register-modal .btn-submit');

        // Validation
        if (!name || !email || !password || !passwordConfirm) {
            errorDiv.textContent = '모든 필드를 입력해주세요';
            errorDiv.style.display = 'block';
            return;
        }

        if (password !== passwordConfirm) {
            errorDiv.textContent = '비밀번호가 일치하지 않습니다';
            errorDiv.style.display = 'block';
            return;
        }

        if (password.length < 6) {
            errorDiv.textContent = '비밀번호는 최소 6자 이상이어야 합니다';
            errorDiv.style.display = 'block';
            return;
        }

        // Show loading
        submitBtn.disabled = true;
        submitBtn.textContent = '가입 중...';
        errorDiv.style.display = 'none';

        // Call auth API
        const result = await window.auth.register(name, email, password);

        if (result.success) {
            AuthUI.hideRegisterModal();
            UI.toast('회원가입 성공! 로그인되었습니다', 'success');

            // Update UI
            AuthUI.updateUserUI();
        } else {
            errorDiv.textContent = result.error || '회원가입에 실패했습니다';
            errorDiv.style.display = 'block';
        }

        // Reset button
        submitBtn.disabled = false;
        submitBtn.textContent = '회원가입';
    }

    /**
     * Handle change password
     */
    static async handleChangePassword(e) {
        e.preventDefault();

        const currentPassword = document.getElementById('current-password').value;
        const newPassword = document.getElementById('new-password').value;
        const confirmPassword = document.getElementById('confirm-new-password').value;
        const errorDiv = document.querySelector('#profile-modal .error-message');
        const submitBtn = e.target.querySelector('.btn-submit');

        // Validation
        if (!currentPassword || !newPassword || !confirmPassword) {
            errorDiv.textContent = '모든 필드를 입력해주세요';
            errorDiv.style.display = 'block';
            return;
        }

        if (newPassword !== confirmPassword) {
            errorDiv.textContent = '새 비밀번호가 일치하지 않습니다';
            errorDiv.style.display = 'block';
            return;
        }

        if (newPassword.length < 6) {
            errorDiv.textContent = '비밀번호는 최소 6자 이상이어야 합니다';
            errorDiv.style.display = 'block';
            return;
        }

        // Show loading
        submitBtn.disabled = true;
        submitBtn.textContent = '변경 중...';
        errorDiv.style.display = 'none';

        // Call API
        const result = await window.auth.changePassword(currentPassword, newPassword);

        if (result.success) {
            UI.toast('비밀번호가 변경되었습니다', 'success');

            // Clear form
            document.getElementById('current-password').value = '';
            document.getElementById('new-password').value = '';
            document.getElementById('confirm-new-password').value = '';
        } else {
            errorDiv.textContent = result.error || '비밀번호 변경에 실패했습니다';
            errorDiv.style.display = 'block';
        }

        // Reset button
        submitBtn.disabled = false;
        submitBtn.textContent = '비밀번호 변경';
    }

    /**
     * Update user UI based on auth state
     */
    static updateUserUI() {
        const headerActions = document.querySelector('.header-actions');
        if (!headerActions) return;

        if (window.auth.isAuthenticated()) {
            // Show user profile
            headerActions.innerHTML = `
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
            headerActions.innerHTML = `
                <button class="btn-login" onclick="AuthUI.showLoginModal()">
                    로그인
                </button>
            `;
        }
    }

    /**
     * Toggle profile dropdown
     */
    static toggleProfileDropdown(event) {
        event.stopPropagation();
        const dropdown = document.getElementById('profile-dropdown');
        if (dropdown) {
            dropdown.classList.toggle('active');
        }
    }

    /**
     * Password strength indicator
     */
    static checkPasswordStrength(password) {
        let strength = 0;

        if (password.length >= 6) strength++;
        if (password.length >= 10) strength++;
        if (/[a-z]/.test(password) && /[A-Z]/.test(password)) strength++;
        if (/\d/.test(password)) strength++;
        if (/[^a-zA-Z\d]/.test(password)) strength++;

        return {
            score: strength,
            label: strength <= 1 ? '약함' : strength <= 3 ? '보통' : '강함',
            color: strength <= 1 ? '#ef4444' : strength <= 3 ? '#f59e0b' : '#10b981'
        };
    }

    /**
     * Update password strength indicator
     */
    static updatePasswordStrength(inputId, indicatorId) {
        const input = document.getElementById(inputId);
        const indicator = document.getElementById(indicatorId);

        if (!input || !indicator) return;

        input.addEventListener('input', () => {
            const password = input.value;
            const strength = AuthUI.checkPasswordStrength(password);

            indicator.style.display = password ? 'block' : 'none';
            indicator.textContent = `비밀번호 강도: ${strength.label}`;
            indicator.style.color = strength.color;
        });
    }
}

// Close dropdown when clicking outside
document.addEventListener('click', () => {
    const dropdown = document.getElementById('profile-dropdown');
    if (dropdown && dropdown.classList.contains('active')) {
        dropdown.classList.remove('active');
    }
});

// Initialize UI on load
document.addEventListener('DOMContentLoaded', () => {
    AuthUI.updateUserUI();

    // Setup password strength indicators
    AuthUI.updatePasswordStrength('register-password', 'password-strength');
});
