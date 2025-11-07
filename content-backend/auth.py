"""
JWT Authentication and Authorization System
Supports role-based access control (RBAC) and scopes (read/write)
"""
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional, List
from pydantic import BaseModel
import os

from logger import get_logger

logger = get_logger("auth")

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security scheme
security = HTTPBearer()


# ==========================================
# Pydantic Models
# ==========================================

class TokenData(BaseModel):
    """JWT token payload data"""
    user_id: int
    email: str
    role: str = "user"  # user, admin, superadmin
    scopes: List[str] = []  # read, write, admin, analytics
    project_ids: Optional[List[int]] = None  # Project-level permissions


class User(BaseModel):
    """User model"""
    id: int
    email: str
    role: str
    is_active: bool = True


class TokenResponse(BaseModel):
    """Token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


# ==========================================
# Password Utilities
# ==========================================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash password"""
    return pwd_context.hash(password)


# ==========================================
# JWT Token Utilities
# ==========================================

def create_access_token(
    user_id: int,
    email: str,
    role: str = "user",
    scopes: List[str] = None,
    project_ids: List[int] = None,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT access token

    Args:
        user_id: User ID
        email: User email
        role: User role (user, admin, superadmin)
        scopes: List of permission scopes (read, write, admin, analytics)
        project_ids: List of accessible project IDs
        expires_delta: Token expiration time

    Returns:
        JWT token string
    """
    if scopes is None:
        scopes = ["read", "write"]  # Default scopes

    to_encode = {
        "user_id": user_id,
        "email": email,
        "role": role,
        "scopes": scopes,
        "type": "access"
    }

    if project_ids:
        to_encode["project_ids"] = project_ids

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode["exp"] = expire
    to_encode["iat"] = datetime.utcnow()

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(user_id: int, email: str) -> str:
    """Create JWT refresh token"""
    to_encode = {
        "user_id": user_id,
        "email": email,
        "type": "refresh",
        "exp": datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        "iat": datetime.utcnow()
    }

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> TokenData:
    """
    Decode and validate JWT token

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        user_id: int = payload.get("user_id")
        email: str = payload.get("email")
        role: str = payload.get("role", "user")
        scopes: List[str] = payload.get("scopes", [])
        project_ids: Optional[List[int]] = payload.get("project_ids")

        if user_id is None or email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )

        return TokenData(
            user_id=user_id,
            email=email,
            role=role,
            scopes=scopes,
            project_ids=project_ids
        )

    except JWTError as e:
        logger.error(f"JWT decode error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )


# ==========================================
# Dependencies
# ==========================================

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> TokenData:
    """
    Get current authenticated user from JWT token

    Usage:
        @app.get("/protected")
        async def protected_route(user: TokenData = Depends(get_current_user)):
            return {"user_id": user.user_id}
    """
    token = credentials.credentials
    return decode_token(token)


class PermissionChecker:
    """
    Check user permissions (scopes and role)

    Usage:
        @app.post("/campaigns", dependencies=[Depends(PermissionChecker(scopes=["write"]))])
        async def create_campaign(...):
            ...
    """

    def __init__(
        self,
        scopes: Optional[List[str]] = None,
        roles: Optional[List[str]] = None
    ):
        self.required_scopes = scopes or []
        self.required_roles = roles or []

    async def __call__(self, user: TokenData = Depends(get_current_user)) -> TokenData:
        """Check if user has required permissions"""

        # Check scopes
        if self.required_scopes:
            missing_scopes = set(self.required_scopes) - set(user.scopes)
            if missing_scopes:
                logger.warning(
                    f"User {user.user_id} missing scopes: {missing_scopes}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing required scopes: {list(missing_scopes)}"
                )

        # Check roles
        if self.required_roles:
            if user.role not in self.required_roles:
                logger.warning(
                    f"User {user.user_id} has role {user.role}, required: {self.required_roles}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Required role: {self.required_roles}"
                )

        return user


class ProjectAccessChecker:
    """
    Check project-level access

    Usage:
        @app.get("/campaigns/{campaign_id}")
        async def get_campaign(
            campaign_id: int,
            user: TokenData = Depends(ProjectAccessChecker())
        ):
            ...
    """

    async def __call__(
        self,
        campaign_id: int = None,
        user: TokenData = Depends(get_current_user)
    ) -> TokenData:
        """Check if user has access to project/campaign"""

        # Admins have access to all projects
        if user.role in ["admin", "superadmin"]:
            return user

        # Check project-level permissions
        if campaign_id and user.project_ids:
            # TODO: Query database to get campaign's project_id
            # For now, allow access if user has any project permissions
            pass

        return user


# ==========================================
# Optional: Simple User Store (for demo)
# ==========================================

# In production, this should be in database
DEMO_USERS = {
    "admin@artify.com": {
        "id": 1,
        "email": "admin@artify.com",
        "password_hash": get_password_hash("admin123"),
        "role": "admin",
        "scopes": ["read", "write", "admin", "analytics"]
    },
    "user@artify.com": {
        "id": 2,
        "email": "user@artify.com",
        "password_hash": get_password_hash("user123"),
        "role": "user",
        "scopes": ["read", "write"]
    }
}


def authenticate_user(email: str, password: str) -> Optional[dict]:
    """
    Authenticate user (demo implementation)

    In production, query database
    """
    user = DEMO_USERS.get(email)
    if not user:
        return None

    if not verify_password(password, user["password_hash"]):
        return None

    return user


# ==========================================
# Helper Functions
# ==========================================

def has_scope(user: TokenData, scope: str) -> bool:
    """Check if user has specific scope"""
    return scope in user.scopes


def has_role(user: TokenData, role: str) -> bool:
    """Check if user has specific role"""
    return user.role == role or user.role == "superadmin"


def can_access_project(user: TokenData, project_id: int) -> bool:
    """Check if user can access project"""
    if user.role in ["admin", "superadmin"]:
        return True

    if user.project_ids and project_id in user.project_ids:
        return True

    return False
