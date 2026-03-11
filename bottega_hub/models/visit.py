from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
from .base import Base


class Visit(Base):
    __tablename__ = 'visits'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    visit_date = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    amount = Column(Float, nullable=False)
    shift_code = Column(String, nullable=False)
    
    # Status
    is_valid = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", backref="visits")

    def __repr__(self):
        return f"<Visit(id={self.id}, user_id={self.user_id}, date={self.visit_date}, amount={self.amount})>"
