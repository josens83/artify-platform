"""
Authentication API Endpoints
Login, token refresh, password reset
"""
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
import secrets
import hashlib
from datetime import datetime, timedelta

from auth import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    get_current_user,
    TokenResponse,
    TokenData,
    DEMO_USERS
)
from logger import get_logger

logger = get_logger("auth_api")
router = APIRouter(prefix="/auth", tags=["authentication"])


# ==========================================
# Pydantic Models
# ==========================================

class LoginRequest(BaseModel):
    """Login request"""
    email: EmailStr
    password: str = Field(..., min_length=6)


class RefreshTokenRequest(BaseModel):
    """Refresh token request"""
    refresh_token: str


class PasswordResetRequest(BaseModel):
    """Password reset request"""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation"""
    token: str
    new_password: str = Field(..., min_length=8)


class ChangePasswordRequest(BaseModel):
    """Change password request"""
    old_password: str
    new_password: str = Field(..., min_length=8)


# ==========================================
# In-memory token store (for demo)
# ==========================================
# In production, use Redis or database

password_reset_tokens = {}  # {token: {email, expires_at}}


# ==========================================
# Authentication Endpoints
# ==========================================

@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """
    User login with email and password

    Returns access token and refresh token

    **Demo credentials:**
    - admin@artify.com / admin123 (admin role)
    - user@artify.com / user123 (user role)
    """
    user = authenticate_user(request.email, request.password)

    if not user:
        logger.warning(f"Failed login attempt for {request.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    # Create tokens
    access_token = create_access_token(
        user_id=user["id"],
        email=user["email"],
        role=user["role"],
        scopes=user["scopes"]
    )

    refresh_token = create_refresh_token(
        user_id=user["id"],
        email=user["email"]
    )

    logger.info(f"User logged in: {user['email']} (role: {user['role']})")

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=60 * 60  # 1 hour
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshTokenRequest):
    """
    Refresh access token using refresh token

    Returns new access token and refresh token
    """
    try:
        # Decode refresh token
        token_data = decode_token(request.refresh_token)

        # Get user (in production, query database)
        user = DEMO_USERS.get(token_data.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )

        # Create new tokens
        access_token = create_access_token(
            user_id=user["id"],
            email=user["email"],
            role=user["role"],
            scopes=user["scopes"]
        )

        refresh_token = create_refresh_token(
            user_id=user["id"],
            email=user["email"]
        )

        logger.info(f"Token refreshed for: {user['email']}")

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=60 * 60
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@router.post("/password-reset")
async def request_password_reset(request: PasswordResetRequest):
    """
    Request password reset

    Sends reset token (in production, send via email)

    **For demo:** Returns token directly
    """
    # Check if user exists
    user = DEMO_USERS.get(request.email)
    if not user:
        # Don't reveal if email exists (security best practice)
        return {
            "success": True,
            "message": "If email exists, password reset link has been sent"
        }

    # Generate reset token
    token = secrets.token_urlsafe(32)

    # Store token (in production, use Redis with TTL)
    password_reset_tokens[token] = {
        "email": request.email,
        "expires_at": datetime.utcnow() + timedelta(hours=1)
    }

    logger.info(f"Password reset requested for: {request.email}")

    # In production, send email with reset link
    # For demo, return token directly
    return {
        "success": True,
        "message": "Password reset token generated",
        "token": token,  # Remove in production
        "reset_url": f"/auth/password-reset/confirm?token={token}"  # Remove in production
    }


@router.post("/password-reset/confirm")
async def confirm_password_reset(request: PasswordResetConfirm):
    """
    Confirm password reset with token

    Sets new password
    """
    # Verify token
    token_data = password_reset_tokens.get(request.token)

    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    # Check expiration
    if datetime.utcnow() > token_data["expires_at"]:
        del password_reset_tokens[request.token]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired"
        )

    email = token_data["email"]

    # Update password (in production, update database)
    if email in DEMO_USERS:
        DEMO_USERS[email]["password_hash"] = get_password_hash(request.new_password)

        # Delete token
        del password_reset_tokens[request.token]

        logger.info(f"Password reset completed for: {email}")

        return {
            "success": True,
            "message": "Password has been reset successfully"
        }

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found"
    )


@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    user: TokenData = Depends(get_current_user)
):
    """
    Change password (requires authentication)

    User must provide old password
    """
    # Get user
    user_data = DEMO_USERS.get(user.email)
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Verify old password
    user_auth = authenticate_user(user.email, request.old_password)
    if not user_auth:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect old password"
        )

    # Update password
    DEMO_USERS[user.email]["password_hash"] = get_password_hash(request.new_password)

    logger.info(f"Password changed for: {user.email}")

    return {
        "success": True,
        "message": "Password changed successfully"
    }


@router.get("/me")
async def get_current_user_info(user: TokenData = Depends(get_current_user)):
    """
    Get current user information

    Requires authentication
    """
    return {
        "user_id": user.user_id,
        "email": user.email,
        "role": user.role,
        "scopes": user.scopes,
        "project_ids": user.project_ids
    }
