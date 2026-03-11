from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from .base import Base


class ShiftCode(Base):
    __tablename__ = 'shift_codes'

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String, unique=True, nullable=False, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<ShiftCode(code={self.code}, active={self.is_active})>"
