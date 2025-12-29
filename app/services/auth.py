from datetime import datetime, timedelta
from typing import Optional
from jose import jwt
from ..core.config import settings
from ..core.security import create_access_token, verify_password, get_password_hash
from ..crud.user import CRUDUser
from ..schemas.user import TokenData

# Crear instancia del CRUD
crud_user = CRUDUser()


class AuthService:
    def authenticate_user(self, db, email: str, password: str):
        user = crud_user.authenticate(db, email=email, password=password)
        if not user:
            return None
        return user
    
    def create_token(self, user_id: int, role: str) -> str:
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        return create_access_token(
            subject=str(user_id), expires_delta=access_token_expires
        )
    
    def verify_token(self, token: str) -> Optional[TokenData]:
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            user_id: str = payload.get("sub")
            if user_id is None:
                return None
            return TokenData(user_id=int(user_id))
        except jwt.JWTError:
            return None


auth_service = AuthService()