from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from ...deps import get_db, get_current_user
from ....core.config import settings
from ....core.security import create_access_token, verify_password, get_password_hash
from ....crud.user import CRUDUser
from ....schemas.user import (
    UserCreate, UserResponse, Token, 
    VerificationRequest, PasswordResetRequest, PasswordResetConfirm
)
from ....services.email import email_service, generate_verification_code, generate_reset_token
from ....services.auth import auth_service
from fastapi import Header

router = APIRouter()

crud_user = CRUDUser()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate,
) -> Any:
    """
    Register a new user.
    """
    # Check if user already exists
    user = crud_user.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists",
        )
    
    # Create user
    user = crud_user.create(db, obj_in=user_in)
    
    # Generate verification code
    verification_code = generate_verification_code()
    user.verification_code = verification_code
    db.commit()
    
    # Send verification email
    email_service.send_verification_email(user.email, verification_code)
    
    return user


@router.post("/login", response_model=Token)
def login(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    user = crud_user.authenticate(db, email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not verified",
        )
    
    access_token = create_access_token(
        subject=str(user.id), 
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/verify-email", response_model=UserResponse)
def verify_email(
    *,
    db: Session = Depends(get_db),
    verification_data: VerificationRequest,
) -> Any:
    """
    Verify user's email with the verification code.
    """
    user = crud_user.get_by_email(db, email=verification_data.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already verified",
        )
    
    if user.verification_code != verification_data.code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code",
        )
    
    user.is_verified = True
    user.verification_code = None
    db.commit()
    db.refresh(user)
    
    return user


@router.post("/resend-verification")
def resend_verification(
    *,
    db: Session = Depends(get_db),
    email: str = Body(..., embed=True),
) -> Any:
    """
    Resend verification email.
    """
    user = crud_user.get_by_email(db, email=email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already verified",
        )
    
    # Generate new verification code
    verification_code = generate_verification_code()
    user.verification_code = verification_code
    db.commit()
    
    # Send verification email
    email_service.send_verification_email(user.email, verification_code)
    
    return {"message": "Verification email sent"}


@router.post("/forgot-password")
def forgot_password(
    *,
    db: Session = Depends(get_db),
    reset_data: PasswordResetRequest,
) -> Any:
    """
    Request password reset.
    """
    user = crud_user.get_by_email(db, email=reset_data.email)
    if not user:
        # Don't reveal that user doesn't exist
        return {"message": "If the email exists, a reset token will be sent"}
    
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not verified",
        )
    
    # Generate reset token (using JWT)
    reset_token = create_access_token(
        subject=str(user.id),
        expires_delta=timedelta(hours=1)
    )
    
    # Send reset email
    email_service.send_password_reset_email(user.email, reset_token)
    
    return {"message": "Password reset email sent"}


@router.post("/reset-password")
def reset_password(
    *,
    db: Session = Depends(get_db),
    reset_data: PasswordResetConfirm,
) -> Any:
    """
    Reset password with token.
    """
    try:
        payload = jwt.decode(
            reset_data.token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token",
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token",
        )
    
    user = crud_user.get(db, id=int(user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Update password
    user.hashed_password = get_password_hash(reset_data.new_password)
    db.commit()
    
    return {"message": "Password updated successfully"}


@router.get("/me", response_model=UserResponse)
def read_users_me(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get current user.
    """
    user = crud_user.get(db, id=current_user["id"])
    return user

@router.post("/logout")
def logout(
    authorization: str = Header(None)
) -> dict:
    """
    Logout user.
    
    Since we use stateless JWT tokens, logout is handled client-side.
    The client should delete the stored token from its storage.
    
    This endpoint provides a formal way to trigger logout and
    can be extended later with token blacklisting if needed.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No authorization token provided"
        )
    
    # Extract the token
    token = authorization.split(" ")[1]
    
    # Note: In a production system with immediate token invalidation needs,
    # you would add the token to a blacklist here.
    # For now, we rely on client-side token deletion.
    
    return {
        "success": True,
        "message": "Successfully logged out",
        "instructions": "Please delete the token from client storage (localStorage, sessionStorage, or cookies)",
        "client_actions": [
            "1. Remove the token from browser storage",
            "2. Clear user data from application state",
            "3. Redirect to login page"
        ]
    }