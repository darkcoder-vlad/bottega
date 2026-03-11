from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Boolean, Text
from sqlalchemy.orm import relationship
from .base import Base


class Receipt(Base):
    __tablename__ = 'receipts'

    id = Column(Integer, primary_key=True, autoincrement=True)
    receipt_id = Column(String, unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    telegram_id = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    file_id = Column(String, nullable=False)
    caption = Column(Text, nullable=True)
    
    # Status
    is_confirmed = Column(Boolean, default=False)
    is_rejected = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    confirmed_at = Column(DateTime, nullable=True)
    confirmed_by = Column(String, nullable=True)
    
    user = relationship("User", backref="receipts")

    def __repr__(self):
        return f"<Receipt(id={self.receipt_id}, amount={self.amount})>"
