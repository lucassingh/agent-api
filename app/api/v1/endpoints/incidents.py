from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from ...deps import get_db, require_admin, require_supervisor_or_admin, get_current_active_user, require_operator_or_higher
from ....crud.incident import CRUDIncident
from ....crud.user import CRUDUser
from ....models.incident import IncidentStatus
from ....schemas.incident import (
    IncidentResponse, IncidentCreate, IncidentUpdate, 
    IncidentWithUser, IncidentAudioUpload
)
from ....services.storage import audio_storage
from typing import Optional, List, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.orm import Session

router = APIRouter()

# Crear instancias del CRUD
crud_incident = CRUDIncident()
crud_user = CRUDUser()


@router.get("/", response_model=List[IncidentWithUser])
def read_incidents(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_supervisor_or_admin),
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    status: Optional[IncidentStatus] = Query(None, description="Filter by status"),
) -> Any:
    """
    Retrieve incidents.
    Admin and supervisors can see all incidents.
    """
    try:
        # Obtener incidentes con filtros
        incidents = crud_incident.get_multi_with_filters(
            db, user_id=user_id, status=status, skip=skip, limit=limit
        )
        
        # Debug: verificar que se obtienen incidentes
        print(f"Incidents found: {len(incidents)}")
        if incidents:
            print(f"First incident: {incidents[0].id}, user_id: {incidents[0].user_id}")
        
        # Construir respuesta
        result = []
        for incident in incidents:
            # Obtener usuario
            user = crud_user.get(db, id=incident.user_id)
            if not user:
                print(f"Warning: User {incident.user_id} not found for incident {incident.id}")
                continue
            
            # Convertir incidente a esquema Pydantic v2
            incident_dict = {
                "id": incident.id,
                "title": incident.title,
                "problem_audio_path": incident.problem_audio_path,
                "solution_audio_path": incident.solution_audio_path,
                "observations": incident.observations,
                "status": incident.status,
                "is_resolved": incident.is_resolved,
                "user_id": incident.user_id,
                "created_at": incident.created_at,
                "updated_at": incident.updated_at,
                "user_name": user.name,
                "user_lastname": user.lastname,
                "user_email": user.email,
                "user_role": user.role.value  # Asegúrate que role sea Enum o string
            }
            
            incident_data = IncidentWithUser.model_validate(incident_dict)
            result.append(incident_data)
        
        print(f"Returning {len(result)} incidents")
        return result
        
    except Exception as e:
        print(f"Error in read_incidents: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/", response_model=IncidentResponse, status_code=status.HTTP_201_CREATED)
async def create_incident(
    *,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_operator_or_higher),
    title: str = Form(...),
    problem_audio: UploadFile = File(...),
    observations: str = Form(None),
) -> Any:
    """
    Create new incident with problem audio.
    Only operators can create incidents.
    """
    print(f"=== CREATE INCIDENT STARTED ===")
    
    if current_user["role"] not in ["operator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only operators can create incidents",
        )
    
    # Save problem audio
    print("Saving audio file...")
    problem_audio_path = await audio_storage.save_audio_file(
        problem_audio, current_user["id"]
    )
    print(f"Audio saved at: {problem_audio_path}")
    
    # Create incident DIRECTAMENTE con el modelo
    from ....models.incident import Incident
    
    incident = Incident(
        title=title,
        problem_audio_path=problem_audio_path,
        observations=observations,
        user_id=current_user["id"],
        status="initiated",  # String directamente
        is_resolved=False
    )
    
    print(f"Adding incident to DB: {incident.title}, user_id: {incident.user_id}")
    
    db.add(incident)
    db.commit()
    db.refresh(incident)
    
    print(f"Incident created with ID: {incident.id}")
    
    # Get user info for response
    user = crud_user.get(db, id=current_user["id"])
    
    # Build response using Pydantic model
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
    
    print("=== CREATE INCIDENT SUCCESS ===")
    return response


@router.post("/{incident_id}/solution", response_model=IncidentResponse)
async def add_solution_audio(
    *,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user),
    incident_id: int,
    solution_audio: UploadFile = File(...),
    is_resolved: bool = Form(True),
    observations: str = Form(None),
) -> Any:
    """
    Add solution audio to incident.
    Only the creator can add solution audio.
    """
    incident = crud_incident.get(db, id=incident_id)
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )
    
    # Check permissions
    if incident.user_id != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # Check if solution already exists
    if incident.solution_audio_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solution audio already exists for this incident",
        )
    
    # Save solution audio
    solution_audio_path = await audio_storage.save_audio_file(
        solution_audio, current_user["id"], incident_id
    )
    
    # Update incident
    incident = crud_incident.add_solution_audio(
        db, db_obj=incident, 
        solution_audio_path=solution_audio_path,
        is_resolved=is_resolved
    )
    
    # Update observations if provided
    if observations:
        incident.observations = observations
        db.commit()
        db.refresh(incident)
    
    # Get user info for response
    user = crud_user.get(db, id=current_user["id"])
    
    # Construir respuesta manualmente
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
    
    return response


@router.get("/{incident_id}", response_model=IncidentWithUser)
def read_incident(
    incident_id: int,
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get incident by ID.
    """
    incident = crud_incident.get(db, id=incident_id)
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )
    
    # Check permissions
    if current_user["role"] in ["operator"]:
        if incident.user_id != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )
    
    user = crud_user.get(db, id=incident.user_id)
    response = IncidentWithUser.from_orm(incident)
    response.user_name = user.name
    response.user_lastname = user.lastname
    response.user_email = user.email
    response.user_role = user.role.value
    
    return response


@router.get("/{incident_id}/audio/{audio_type}")
def get_audio_url(
    incident_id: int,
    audio_type: str,
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get audio file URL.
    audio_type: 'problem' or 'solution'
    """
    incident = crud_incident.get(db, id=incident_id)
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )
    
    # Check permissions
    if current_user["role"] in ["operator"]:
        if incident.user_id != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )
    
    if audio_type == "problem":
        audio_path = incident.problem_audio_path
    elif audio_type == "solution":
        audio_path = incident.solution_audio_path
        if not audio_path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Solution audio not found",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid audio type. Use 'problem' or 'solution'",
        )
    
    audio_url = audio_storage.get_audio_url(audio_path)
    return {"audio_url": f"/{audio_url}"}


@router.get("/user/{user_id}", response_model=List[IncidentResponse])
def read_user_incidents(
    user_id: int,
    current_user: dict = Depends(require_supervisor_or_admin),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Get incidents for a specific user.
    Admin and supervisors only.
    """
    # Check if user exists
    user = crud_user.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Check permissions for supervisors
    if current_user["role"] == "supervisor":
        if user.role != "operator":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Supervisors can only view operator incidents",
            )
    
    incidents = crud_incident.get_multi_by_user(
        db, user_id=user_id, skip=skip, limit=limit
    )
    
    # Add user info for response
    result = []
    for incident in incidents:
        response = IncidentResponse.from_orm(incident)
        response.user_name = user.name
        response.user_lastname = user.lastname
        result.append(response)
    
    return result