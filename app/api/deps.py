from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..core.config import settings
from ..core.security import verify_token
from ..crud.user import CRUDUser
from ..models.user import UserRole

security = HTTPBearer()

# Crear instancia del CRUD
crud_user = CRUDUser()  # <-- AÑADE ESTO


def get_current_user(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = credentials.credentials
    user_id = verify_token(token)
    if user_id is None:
        raise credentials_exception
    
    user = crud_user.get(db, id=int(user_id))
    if user is None or not user.is_active:
        raise credentials_exception
    
    return {
        "id": user.id,
        "email": user.email,
        "role": user.role,
        "is_verified": user.is_verified
    }


def get_current_active_user(
    current_user: dict = Depends(get_current_user),
) -> dict:
    if not current_user.get("is_verified"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not verified"
        )
    return current_user


def require_admin(current_user: dict = Depends(get_current_active_user)) -> dict:
    if current_user["role"] != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


def require_supervisor_or_admin(current_user: dict = Depends(get_current_active_user)) -> dict:
    if current_user["role"] not in [UserRole.admin, UserRole.supervisor]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Supervisor or admin privileges required"
        )
    return current_user


def require_operator_or_higher(current_user: dict = Depends(get_current_active_user)) -> dict:
    # All roles are allowed
    return current_user