from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from ..core.database import Base


class IncidentStatus(str, enum.Enum):
    initiated = "initiated"
    resolved = "resolved"
    unresolved = "unresolved"


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    problem_audio_path = Column(String, nullable=False)
    solution_audio_path = Column(String, nullable=True)
    observations = Column(Text, nullable=True)
    status = Column(Enum(IncidentStatus), default=IncidentStatus.initiated, nullable=False)
    is_resolved = Column(Boolean, default=False, nullable=False)
    
    # Foreign keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="incidents")