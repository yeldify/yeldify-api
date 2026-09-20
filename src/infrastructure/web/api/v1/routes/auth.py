"""
Authentication routes for JWT token management.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from src.infrastructure.web.api.v1.schemas.auth_schema import Token, UserLogin
from src.infrastructure.web.api.v1.auth.jwt_auth import create_access_token, security
from typing import Optional

router = APIRouter(prefix="/auth", tags=["auth"])


# In a real application, you would have a user service/database
# For this example, we'll use a simple mock user database
MOCK_USERS = {
    "user-123": {"user_id": "user-123", "username": "john_doe", "disabled": False},
    "user-456": {"user_id": "user-456", "username": "jane_doe", "disabled": False},
}


def get_user_from_db(user_id: str) -> Optional[dict]:
    """
    Mock function to get user from database.
    In a real application, this would query your user repository.
    """
    return MOCK_USERS.get(user_id)


@router.post(
    "/token",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    summary="Obtém um token JWT de acesso",
    description="Autentica um usuário e retorna um token JWT. Em um sistema real, validaria senha.",
)
async def login_for_access_token(
    user_login: UserLogin,
):
    """
    Generate a JWT access token for a user.
    
    In a production environment, this would:
    1. Validate user credentials (username/password)
    2. Check if user is active
    3. Generate and return a JWT token
    
    For this example, we accept any user_id from the mock database.
    """
    # Get user from mock database
    user = get_user_from_db(user_login.user_id)
    
    if user is None or user.get("disabled", True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or disabled",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create token data
    token_data = {
        "sub": user["user_id"],
        "username": user.get("username"),
    }
    
    # Generate token
    access_token = create_access_token(token_data)
    
    return Token(
        access_token=access_token,
        token_type="bearer",
    )


@router.post(
    "/refresh",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    summary="Renova o token JWT",
    description="Renova o token de acesso (requer token válido).",
)
async def refresh_token(
    current_token: str = Depends(security),
):
    """
    Refresh an existing JWT token.
    
    Note: In a production environment, you might want to:
    - Validate the existing token
    - Check if it's expired or about to expire
    - Generate a new token with extended expiration
    """
    # For simplicity, we just create a new token with the same data
    # In a real app, you would verify the current token first
    
    # Decode without verification (just for demo)
    from jose import jwt
    from src.infrastructure.web.api.v1.auth.jwt_auth import SECRET_KEY, ALGORITHM
    
    try:
        payload = jwt.decode(current_token.credentials, SECRET_KEY, algorithms=[ALGORITHM])
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create new token
    access_token = create_access_token({
        "sub": payload.get("sub"),
        "username": payload.get("username"),
    })
    
    return Token(
        access_token=access_token,
        token_type="bearer",
    )
