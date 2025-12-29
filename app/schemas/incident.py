from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime
from ..models.incident import IncidentStatus

class IncidentBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    observations: Optional[str] = Field(None, max_length=1000)

class IncidentCreate(IncidentBase):
    problem_audio_path: str
    user_id: int
    status: IncidentStatus = IncidentStatus.initiated
    is_resolved: bool = False 

class IncidentUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    observations: Optional[str] = Field(None, max_length=1000)
    status: Optional[IncidentStatus] = None
    is_resolved: Optional[bool] = None

class IncidentInDB(IncidentBase):
    id: int
    problem_audio_path: str
    solution_audio_path: Optional[str] = None
    status: IncidentStatus
    is_resolved: bool
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class IncidentResponse(IncidentInDB):
    user_name: str
    user_lastname: str
    
    class Config:
        from_attributes = True


class IncidentWithUser(IncidentResponse):
    user_email: str
    user_role: str

    class Config:
        from_attributes = True 

class IncidentAudioUpload(BaseModel):
    is_solution: bool = False