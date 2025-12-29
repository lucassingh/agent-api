from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from ...deps import get_db, require_admin, require_supervisor_or_admin, get_current_active_user
from ...deps import get_db, get_current_active_user, require_admin
from ....crud.user import CRUDUser
from ....models.user import UserRole
from ....schemas.user import UserResponse, UserUpdate, UserCreate
from ....crud.incident import CRUDIncident

from ....schemas.incident import IncidentResponse

router = APIRouter()

# Crear instancia del CRUD
crud_user = CRUDUser()


@router.get("/", response_model=List[UserResponse])
def read_users(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_supervisor_or_admin),
    skip: int = 0,
    limit: int = 100,
    role: UserRole = Query(None, description="Filter by role"),
) -> Any:
    """
    Retrieve users.
    """
    if current_user["role"] == UserRole.admin:
        if role:
            users = db.query(crud_user.model).filter(
                crud_user.model.role == role,
                crud_user.model.is_active == True
            ).offset(skip).limit(limit).all()
        else:
            users = crud_user.get_multi(db, skip=skip, limit=limit)
    else:  # Supervisor
        # Supervisors can only see operators
        users = crud_user.get_operators(db, skip=skip, limit=limit)
    
    return users


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    *,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
    user_in: UserCreate,
    role: UserRole = UserRole.operator,
) -> Any:
    """
    Create new user (admin only).
    """
    user = crud_user.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists",
        )
    
    user = crud_user.create(db, obj_in=user_in)
    user.role = role
    user.is_verified = True  # Admin created users are auto-verified
    db.commit()
    db.refresh(user)
    
    return user


@router.get("/{user_id}", response_model=UserResponse)
def read_user_by_id(
    user_id: int,
    current_user: dict = Depends(require_supervisor_or_admin),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get a specific user by id.
    """
    user = crud_user.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Check permissions
    if current_user["role"] == UserRole.supervisor:
        if user.role != UserRole.operator:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Supervisors can only view operators",
            )
    
    return user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    *,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_supervisor_or_admin),
    user_id: int,
    user_in: UserUpdate,
) -> Any:
    """
    Update a user.
    """
    user = crud_user.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Check permissions
    if current_user["role"] == UserRole.supervisor:
        if user.role != UserRole.operator:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Supervisors can only update operators",
            )
        # Supervisors cannot change role
        if user_in.role and user_in.role != UserRole.operator:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Supervisors cannot change user roles",
            )
    
    user = crud_user.update(db, db_obj=user, obj_in=user_in)
    return user


@router.delete("/{user_id}", response_model=UserResponse)
def delete_user(
    *,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_supervisor_or_admin),
    user_id: int,
) -> Any:
    """
    Delete a user (soft delete).
    """
    user = crud_user.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Check permissions
    if current_user["role"] == UserRole.supervisor:
        if user.role != UserRole.operator:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Supervisors can only delete operators",
            )
    
    # Soft delete (deactivate)
    user.is_active = False
    db.commit()
    db.refresh(user)
    
    return user


@router.get("/me/incidents", response_model=List[IncidentResponse])
def get_my_incidents(
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Get incidents for the current user.
    """
    # Usar el CRUD de incidents para obtener los incidentes del usuario
    from ....crud.incident import CRUDIncident
    crud_incident = CRUDIncident()
    
    incidents = crud_incident.get_multi_by_user(
        db, user_id=current_user["id"], skip=skip, limit=limit
    )
    
    # Obtener información del usuario
    user = crud_user.get(db, id=current_user["id"])
    
    # Convertir a IncidentResponse
    result = []
    for incident in incidents:
        response = IncidentResponse(
            id=incident.id,
            title=incident.title,
            problem_audio_path=incident.problem_audio_path,
            solution_audio_path=incident.solution_audio_path,
            observations=incident.observations,
            status=incident.status,
            is_resolved=incident.is_resolved,
            user_id=incident.user_id,
            created_at=incident.created_at,
            updated_at=incident.updated_at,
            user_name=user.name,
            user_lastname=user.lastname
        )
        result.append(response)
    
    return result