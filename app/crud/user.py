from typing import Optional, List
from sqlalchemy.orm import Session
from ..core.security import get_password_hash
from ..models.user import User, UserRole
from ..schemas.user import UserCreate, UserUpdate
from .base import CRUDBase

class CRUDUser(CRUDBase):
    def __init__(self):
        super().__init__(User)
    
    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()
    
    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        db_obj = User(
            email=obj_in.email,
            name=obj_in.name,
            lastname=obj_in.lastname,
            hashed_password=get_password_hash(obj_in.password),
            is_verified=False
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update(
        self, db: Session, *, db_obj: User, obj_in: UserUpdate
    ) -> User:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        return super().update(db, db_obj=db_obj, obj_in=update_data)
    
    def authenticate(self, db: Session, email: str, password: str) -> Optional[User]:
        user = self.get_by_email(db, email=email)
        if not user:
            return None
        if not user.is_active or not user.is_verified:
            return None
        from ..core.security import verify_password
        if not verify_password(password, user.hashed_password):
            return None
        return user
    
    def get_operators(self, db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        return db.query(User).filter(
            User.role == UserRole.operator,
            User.is_active == True
        ).offset(skip).limit(limit).all()
    
    def get_supervisors(self, db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        return db.query(User).filter(
            User.role == UserRole.supervisor,
            User.is_active == True
        ).offset(skip).limit(limit).all()
    
    def is_active(self, user: User) -> bool:
        return user.is_active
    
    def is_superuser(self, user: User) -> bool:
        return user.role == UserRole.admin