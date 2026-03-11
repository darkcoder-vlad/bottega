from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from .base import Base


class Reward(Base):
    __tablename__ = 'rewards'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    reward_code = Column(String, unique=True, nullable=False, index=True)
    
    # Status
    is_used = Column(Boolean, default=False)
    used_at = Column(DateTime, nullable=True)
    generated_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", backref="rewards")

    def __repr__(self):
        return f"<Reward(code={self.reward_code}, user_id={self.user_id}, used={self.is_used})>"

    @staticmethod
    def generate_code() -> str:
        """Generate unique reward code in format BTG-XXXX-XX"""
        import random
        import string
        chars = string.ascii_uppercase + string.digits
        part1 = ''.join(random.choices(chars, k=4))
        part2 = ''.join(random.choices(chars, k=2))
        return f"BTG-{part1}-{part2}"
