"""
JWT Authentication module for Yeldify API.
Handles token creation, verification, and user extraction.
"""
import os
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from pydantic import BaseModel
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# HTTPBearer for token extraction
security = HTTPBearer()


class TokenData(BaseModel):
    """Data contained in the JWT token."""
    user_id: str
    username: Optional[str] = None


class User(BaseModel):
    """User model for authentication."""
    user_id: str
    username: str
    disabled: bool = False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Dictionary with token claims (typically user_id, username, etc.)
        expires_delta: Optional timedelta for token expiration. 
                      Default: ACCESS_TOKEN_EXPIRE_MINUTES
    
    Returns:
        str: JWT token as string
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access_token"
    })
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> TokenData:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token string
    
    Returns:
        TokenData: Extracted token data
    
    Raises:
        HTTPException: 401 if token is invalid or expired
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        username: Optional[str] = payload.get("username")
        
        if user_id is None:
            raise credentials_exception
        
        return TokenData(user_id=user_id, username=username)
    
    except JWTError:
        raise credentials_exception


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenData:
    """
    FastAPI dependency to extract and verify JWT token from Authorization header.
    
    Args:
        credentials: HTTPAuthorizationCredentials from HTTPBearer
    
    Returns:
        TokenData: Extracted user data from token
    
    Raises:
        HTTPException: 401 if token is missing or invalid
    """
    token = credentials.credentials
    return verify_token(token)


def get_current_user_optional(
    authorization: Optional[str] = Header(None, alias="Authorization")
) -> Optional[TokenData]:
    """
    FastAPI dependency to optionally extract and verify JWT token.
    Returns None if no token is provided (useful for development).
    
    Args:
        authorization: Optional Authorization header
    
    Returns:
        Optional[TokenData]: Extracted user data, or None if no token
    """
    if authorization is None:
        return None
    
    # Extract token from "Bearer <token>"
    if not authorization.startswith("Bearer "):
        return None
    
    token = authorization.split("Bearer ")[1].strip()
    
    try:
        return verify_token(token)
    except HTTPException:
        return None


def get_user_id_from_token_or_query(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    user_id: Optional[str] = None,
) -> str:
    """
    Hybrid dependency: tries JWT token first, falls back to query param.
    Useful for development/transition period.
    
    Args:
        authorization: Optional Authorization header
        user_id: Optional user_id from query param
    
    Returns:
        str: user_id from token or query param
    
    Raises:
        HTTPException: 401 if neither token nor query param is provided
    """
    # Try JWT token first
    if authorization is not None and authorization.startswith("Bearer "):
        token = authorization.split("Bearer ")[1].strip()
        try:
            token_data = verify_token(token)
            return token_data.user_id
        except JWTError:
            pass  # Fall through to query param
    
    # Fall back to query param (for development)
    if user_id is not None:
        return user_id
    
    # Neither provided
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated. Provide a valid JWT token in Authorization header or user_id query param (dev only)",
        headers={"WWW-Authenticate": "Bearer"},
    )
