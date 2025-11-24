# Artify Authentication System

Complete login/profile system implemented for both `index.html` and `editor.html`.

## 📋 Features Implemented

### 1. 로그인 모달 (Login Modal)
- ✅ 이메일 입력 필드
- ✅ 비밀번호 입력 필드
- ✅ "로그인" 버튼
- ✅ "회원가입" 링크 (회원가입 모달로 전환)
- ✅ 에러 메시지 표시 영역
- ✅ 데모 계정 안내 (user@artify.com / user123)

### 2. 회원가입 모달 (Register Modal)
- ✅ 이름 입력 필드
- ✅ 이메일 입력 필드
- ✅ 비밀번호 입력 필드
- ✅ 비밀번호 강도 표시 (약함/보통/강함)
- ✅ 비밀번호 확인 필드
- ✅ "회원가입" 버튼
- ✅ "이미 계정이 있으신가요? 로그인" 링크

### 3. 프로필 드롭다운 메뉴 (Profile Dropdown)

#### 로그인 전:
- ✅ "로그인" 버튼만 표시
- ✅ 클릭 시 로그인 모달 오픈

#### 로그인 후:
- ✅ 프로필 아이콘 + 사용자 이니셜 표시
- ✅ 드롭다운 메뉴:
  - 👤 내 프로필
  - ⚙️ 설정
  - 📊 사용 통계
  - 🚪 로그아웃

### 4. 프로필 페이지 (Profile Modal)
- ✅ 사용자 정보 표시 (이름, 이메일)
- ✅ 비밀번호 변경 기능
  - 현재 비밀번호 입력
  - 새 비밀번호 입력
  - 새 비밀번호 확인
- ✅ 계정 삭제 (위험 영역)
  - 확인 모달로 안전성 보장

## 🗂️ File Structure

```
frontend/
├── index.html                      # Updated with auth modals and scripts
├── editor.html                     # Updated with auth integration
├── auth-modals.html               # Shared modal HTML (for reference)
├── css/
│   └── auth.css                    # Authentication styles (shared)
└── js/
    ├── auth.js                     # Main authentication manager
    └── editor-auth-init.js        # Editor-specific auth initialization
```

## 🔧 Core Components

### 1. `js/auth.js`
**AuthManager Class:**
- `login(email, password)` - Login with credentials
- `register(name, email, password)` - Register new user
- `logout()` - Logout and clear tokens
- `fetchCurrentUser()` - Get current user info
- `refreshAccessToken()` - Auto-refresh JWT tokens
- `changePassword(current, new)` - Change password
- `isAuthenticated()` - Check auth status
- `getAuthHeader()` - Get Authorization header for API calls

**AuthUI Class:**
- `showLoginModal()` / `hideLoginModal()`
- `showRegisterModal()` / `hideRegisterModal()`
- `showProfileModal()` / `hideProfileModal()`
- `updateUserUI()` - Update header based on auth state
- `toggleProfileDropdown(event)` - Toggle dropdown
- `handleLogin(event)` - Handle login form submit
- `handleRegister(event)` - Handle register form submit
- `handleChangePassword(event)` - Handle password change
- `checkPasswordStrength(password)` - Password strength indicator

### 2. `css/auth.css`
Shared styles for:
- Login/Register modals
- Profile dropdown
- Form inputs and buttons
- Error messages
- Password strength indicator
- Profile info display
- Danger zone styling

### 3. `js/editor-auth-init.js`
Editor-specific initialization:
- Loads `auth-modals.html` dynamically
- Overrides `AuthUI.updateUserUI()` for editor layout
- Updates `#editor-auth-container` in header

## 🔌 Backend API Integration

### Authentication Endpoints Used:
```
POST   /auth/login                 # Login
POST   /auth/refresh              # Refresh token
GET    /auth/me                   # Get current user
POST   /auth/change-password      # Change password
POST   /auth/password-reset       # Request password reset
```

### Configuration:
```javascript
window.APP_CONFIG = {
    BACKEND_URL: 'http://localhost:3000',
    CONTENT_BACKEND_URL: 'https://artify-content-api.onrender.com'
};
```

## 💾 Token Management

- **Access Token**: Stored in `localStorage.access_token`
- **Refresh Token**: Stored in `localStorage.refresh_token`
- **Current User**: Stored in `localStorage.current_user` (JSON)
- **Auto-Refresh**: Tokens refresh every 55 minutes automatically

## 🎨 UI/UX Features

### Password Strength Indicator
Real-time feedback on password strength:
- **약함 (Weak)**: < 6 characters or simple
- **보통 (Medium)**: 6-10 characters with mixed case
- **강함 (Strong)**: 10+ characters with mixed case, numbers, special chars

### Form Validation
- Email format validation
- Password minimum length (6 characters)
- Password confirmation matching
- Real-time error messages

### Animations
- Modal fade-in with `modalPop` animation
- Dropdown slide-in with transform transition
- Button hover effects with scale and shadow
- Smooth color transitions

## 🔐 Security Features

1. **JWT Token Authentication** - Bearer token in Authorization header
2. **Token Auto-Refresh** - Prevents session expiration
3. **Password Validation** - Minimum requirements enforced
4. **Logout Confirmation** - Clears all local storage
5. **CORS Protection** - Backend whitelist configuration

## 🚀 Demo Credentials

Use these credentials to test the system:

```
Email: user@artify.com
Password: user123

Email: admin@artify.com
Password: admin123
```

## 📱 Responsive Design

- Mobile-friendly modal sizing (`max-width: 480px` for auth modals)
- Touch-friendly button sizes (min 44x44px)
- Responsive form inputs
- Auto-closing dropdown on outside click

## 🎯 Usage Example

### Login Flow
```javascript
// User clicks "로그인" button
AuthUI.showLoginModal();

// User enters credentials and submits
// auth.js handles:
const result = await auth.login(email, password);

if (result.success) {
    // Token stored in localStorage
    // User info fetched from /auth/me
    // UI updated to show profile
    AuthUI.updateUserUI();
}
```

### Logout Flow
```javascript
// User clicks "로그아웃" from dropdown
auth.logout();
// Clears tokens from localStorage
// Redirects to home page
// UI updated to show login button
```

### Token Refresh Flow
```javascript
// Automatic every 55 minutes
setInterval(async () => {
    if (auth.isAuthenticated()) {
        await auth.refreshAccessToken();
    }
}, 55 * 60 * 1000);
```

## 🐛 Troubleshooting

### Modal not showing?
- Check if `auth-modals.html` is loaded (editor.html only)
- Verify `AuthUI` is defined in console
- Check browser console for errors

### Login not working?
- Verify backend is running at `CONTENT_BACKEND_URL`
- Check network tab for 401/403 errors
- Confirm credentials match demo accounts

### Dropdown not appearing?
- Check if user is authenticated: `auth.isAuthenticated()`
- Verify `profile-dropdown` element exists
- Check z-index conflicts with other elements

## 🔄 Future Enhancements

- [ ] Email verification on registration
- [ ] "Forgot Password" flow implementation
- [ ] Two-factor authentication (2FA)
- [ ] OAuth integration (Google, GitHub)
- [ ] User avatar upload
- [ ] Account settings page
- [ ] Usage statistics dashboard
- [ ] Session management (view active sessions)

## 📞 Support

For issues or questions:
- Check browser console for errors
- Verify backend API is accessible
- Review network requests in DevTools
- Ensure localStorage is not disabled

---

**Last Updated**: 2025-11-07
**Version**: 1.0.0
