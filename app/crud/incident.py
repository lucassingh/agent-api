from typing import Optional, List
from sqlalchemy.orm import Session
from ..models.incident import Incident, IncidentStatus
from ..schemas.incident import IncidentCreate, IncidentUpdate
from .base import CRUDBase


class CRUDIncident(CRUDBase):
    def __init__(self):
        super().__init__(Incident)
    
    def get_multi_by_user(
        self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[Incident]:
        return db.query(Incident).filter(
            Incident.user_id == user_id
        ).offset(skip).limit(limit).all()
    
    def get_multi_with_filters(
        self, db: Session, *, 
        user_id: Optional[int] = None,
        status: Optional[IncidentStatus] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> List[Incident]:
        query = db.query(Incident)
        
        if user_id:
            query = query.filter(Incident.user_id == user_id)
        
        if status:
            query = query.filter(Incident.status == status)
        
        return query.order_by(Incident.created_at.desc()).offset(skip).limit(limit).all()
    
    def update_status(
        self, db: Session, *, db_obj: Incident, status: IncidentStatus, is_resolved: bool
    ) -> Incident:
        db_obj.status = status
        db_obj.is_resolved = is_resolved
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def add_solution_audio(
        self, db: Session, *, db_obj: Incident, solution_audio_path: str, is_resolved: bool
    ) -> Incident:
        db_obj.solution_audio_path = solution_audio_path
        if is_resolved:
            db_obj.status = IncidentStatus.resolved
        else:
            db_obj.status = IncidentStatus.unresolved
        db_obj.is_resolved = is_resolved
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj