from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base


class Consent(Base):
    __tablename__ = 'consents'

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(String, unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # Consent status
    is_accepted = Column(Boolean, default=False)
    accepted_at = Column(DateTime, nullable=True)
    policy_version = Column(String, default="1.0")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Consent(telegram_id={self.telegram_id}, accepted={self.is_accepted})>"
